import argparse
import base64
import copy
import io
import json
import mimetypes
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image
from .workflow import STYLES, KINDS, build

ROOT = Path(__file__).resolve().parents[1]
COMFY = 'http://127.0.0.1:8189'
DATA = ROOT / 'data'
INPUT = ROOT / 'ComfyUI/input'
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class RemoteRejected(ValueError):
    pass


def remote(path, body=None, raw=False):
    request = urllib.request.Request(COMFY+path, data=json.dumps(body).encode() if body is not None else None,
                                     headers={'Content-Type':'application/json'})
    try:
        with OPENER.open(request, timeout=60) as response:
            result = response.read()
    except urllib.error.HTTPError as exc:
        message=exc.read().decode('utf-8', errors='replace')[:2000]
        if exc.code==400: raise RemoteRejected(message) from exc
        raise ValueError(message) from exc
    return result if raw else json.loads(result)


class Jobs:
    def __init__(self):
        DATA.mkdir(exist_ok=True)
        self.path = DATA / 'jobs.json'
        self.lock = threading.RLock()
        self.items = json.loads(self.path.read_text('utf-8')) if self.path.exists() else []
        for job in self.items:
            if job['status'] == 'submitting':
                job.update(status='needs_review', error='提交时曾中断。请核对 ComfyUI 队列，避免重复生成。')
        self.save()

    def save(self):
        temporary=self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(self.path)

    def all(self):
        with self.lock: return copy.deepcopy(list(reversed(self.items)))

    def update(self, job, **changes):
        with self.lock:
            job.update(changes, updated=time.time()); self.save()

    def add(self, body):
        prompts=body.get('prompts',[]); p=body.get('params',{})
        if not isinstance(prompts,list) or not 1<=len(prompts)<=20 or any(not isinstance(s,str) or not s.strip() or len(s)>8000 for s in prompts):
            raise ValueError('每批填写 1–20 条需求，每条最多 8000 字')
        if p.get('kind') not in KINDS or p.get('style') not in STYLES: raise ValueError('类型或风格无效')
        for key,lo,hi in [('width',256,2048),('height',256,2048),('steps',1,100)]:
            p[key]=int(p.get(key,0))
            if not lo<=p[key]<=hi: raise ValueError(key+' 超出支持范围')
        if p['width']%8 or p['height']%8: raise ValueError('宽高需要为8的倍数')
        p['cfg']=float(p.get('cfg',7)); p['denoise']=float(p.get('denoise',0.65)); p['upscale']=int(p.get('upscale',1))
        if not 0<=p['cfg']<=30 or not 0<p['denoise']<=1 or p['upscale'] not in (1,2): raise ValueError('采样参数无效')
        seed=str(p.get('seed','')).strip()
        seed=int(seed) if seed else secrets.randbelow(2**32)
        if not 0<=seed<2**53: raise ValueError('种子范围为0至2的53次方减1')
        p['negative']=str(p.get('negative','text, watermark, blurry, low quality'))
        if p.get('mask') and not p.get('image'): raise ValueError('局部重绘需要参考图')
        for key in ('image','mask'):
            name=p.get(key)
            if name and (Path(name).name!=name or not name.startswith('gameart-') or not (INPUT/name).is_file()):
                raise ValueError('请重新上传参考图或蒙版')
        info=remote('/object_info/CheckpointLoaderSimple')
        available=info['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]
        if p.get('checkpoint') not in available: raise ValueError('模型尚未下载完成，或已被移动')
        # Searge's conditioning is specifically SDXL; do not pass other model families.
        if not p['checkpoint'].lower().startswith('sd_xl_base_1.0'): raise ValueError('当前简化工作流使用 SDXL Base 1.0')
        created=[]
        with self.lock:
            for index,prompt in enumerate(prompts):
                ident=uuid.uuid4().hex
                job=dict(id=ident,prompt=prompt.strip(),params={**p,'seed':seed+index},status='queued',
                         prompt_id=None,files=[],error='',created=time.time(),updated=time.time())
                self.items.append(job); created.append(copy.deepcopy(job))
            self.save()
        return created

    def check(self,job):
        if not job['prompt_id']:
            history=remote('/history')
            queued=remote('/queue')
            candidates=[h.get('prompt',[]) for h in history.values()]
            candidates+=queued.get('queue_running',[])+queued.get('queue_pending',[])
            for prompt in candidates:
                if len(prompt)>3 and prompt[3].get('gameart_id')==job['id']:
                    self.update(job,prompt_id=prompt[1],status='running',error=''); break
            if not job['prompt_id']: return
        history=remote('/history/'+job['prompt_id'])
        item=history.get(job['prompt_id'])
        if not item:
            if time.time()-job['updated']>120:
                state=remote('/queue')
                active=state.get('queue_running',[])+state.get('queue_pending',[])
                if not any(p[1]==job['prompt_id'] for p in active):
                    self.update(job,status='needs_review',error='ComfyUI 队列和历史中找不到此任务，可能引擎曾重启。不会自动重复生成。')
            return
        status=item.get('status',{})
        if status.get('status_str')=='error':
            messages=[m[1].get('exception_message',m[0]) for m in status.get('messages',[]) if m[0]=='execution_error']
            self.update(job,status='error',error='\n'.join(messages)[:1800] or 'ComfyUI 执行失败'); return
        if not status.get('completed'): return
        images=item.get('outputs',{}).get('6',{}).get('images',[])
        if not images: raise ValueError('任务结束但未返回图片，请检查 ComfyUI 日志')
        directory=DATA/'outputs'/job['id']; directory.mkdir(parents=True,exist_ok=True)
        files=[]
        for i,image in enumerate(images):
            content=remote('/view?'+urllib.parse.urlencode(image),raw=True)
            name=f'result-{i+1}.png'; (directory/name).write_bytes(content); files.append(name)
        (directory/'workflow-api.json').write_text(json.dumps(build(job),ensure_ascii=False,indent=2),encoding='utf-8')
        (directory/'parameters.json').write_text(json.dumps({k:job[k] for k in ('id','prompt','params','created')},ensure_ascii=False,indent=2),encoding='utf-8')
        self.update(job,status='complete',error='',files=files+['workflow-api.json','parameters.json'])

    def work(self):
        while True:
            with self.lock:
                job=next((j for j in self.items if j['status'] in ('queued','running')),None)
            if job:
                try:
                    if job['status']=='queued':
                        # Check server readiness before marking a write as uncertain.
                        remote('/system_stats')
                        with self.lock:
                            if job['status']!='queued': continue
                            self.update(job,status='submitting')
                        response=remote('/prompt',{'prompt':build(job),'client_id':'gameart-'+job['id'], 'extra_data':{'gameart_id':job['id']}})
                        self.update(job,status='running',prompt_id=response['prompt_id'],error='')
                    self.check(job)
                except RemoteRejected as exc:
                    self.update(job,status='error',error='ComfyUI 拒绝了任务：'+str(exc)[:1800])
                except Exception as exc:
                    if job['status']=='submitting': self.update(job,status='needs_review',error=str(exc)[:1800])
                    else: self.update(job,error='连接或下载暂时失败：'+str(exc)[:1200])
            time.sleep(3)


def serve(port=5213):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def reply(self,data,status=200):
            content=json.dumps(data,ensure_ascii=False).encode()
            self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(content))); self.send_header('Cache-Control','no-store')
            self.end_headers(); self.wfile.write(content)
        def local(self):
            allowed={f'127.0.0.1:{port}',f'localhost:{port}'}
            if self.headers.get('Host') not in allowed or (self.headers.get('Origin') and self.headers['Origin'] not in {'http://'+h for h in allowed}):
                self.reply({'error':'仅允许本机访问'},403); return False
            return True
        def do_GET(self):
            if not self.local(): return
            try:
                path=urllib.parse.urlparse(self.path).path
                if path=='/api/state': self.reply({'jobs':jobs.all()}); return
                if path=='/api/config':
                    info=remote('/object_info/CheckpointLoaderSimple')
                    stats=remote('/system_stats')
                    names=info['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]
                    self.reply({'checkpoints':[n for n in names if n.lower().startswith('sd_xl_base_1.0')], 'devices':[d['name'] for d in stats.get('devices',[])]}); return
                if path.startswith('/outputs/'):
                    root=(DATA/'outputs').resolve(); target=(root/urllib.parse.unquote(path[9:])).resolve()
                else:
                    root=(ROOT/'gameart/web').resolve(); target=(root/(urllib.parse.unquote(path).lstrip('/') or 'index.html')).resolve()
                if not target.is_relative_to(root) or not target.is_file(): self.reply({'error':'文件不存在'},404); return
                content=target.read_bytes(); self.send_response(200)
                self.send_header('Content-Type',mimetypes.guess_type(target.name)[0] or 'application/octet-stream')
                self.send_header('X-Content-Type-Options','nosniff')
                self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'")
                self.send_header('Content-Length',str(len(content))); self.end_headers(); self.wfile.write(content)
            except Exception as exc: self.reply({'error':str(exc)[:1800]},400)
        def do_POST(self):
            if not self.local(): return
            try:
                size=int(self.headers.get('Content-Length',0))
                if self.headers.get('Content-Type','').split(';')[0]!='application/json' or not 0<size<30*1024*1024: raise ValueError('JSON 请求格式或大小无效')
                body=json.loads(self.rfile.read(size))
                if self.path=='/api/jobs': self.reply(jobs.add(body),201)
                elif self.path=='/api/upload':
                    binary=base64.b64decode(body['data'],validate=True)
                    image=Image.open(io.BytesIO(binary))
                    if image.width*image.height>32_000_000: raise ValueError('图片过大')
                    image.load()
                    name='gameart-'+uuid.uuid4().hex+'.png'; INPUT.mkdir(exist_ok=True)
                    image.convert('RGB').save(INPUT/name); self.reply({'name':name})
                elif self.path in ('/api/cancel','/api/check'):
                    with jobs.lock:
                        job=next((j for j in jobs.items if j['id']==body['id']),None)
                        if job is None: raise ValueError('任务不存在')
                        if self.path=='/api/cancel':
                            if job['status']!='queued': raise ValueError('只能取消尚未提交的任务')
                            jobs.update(job,status='cancelled')
                        elif job['status']!='needs_review': raise ValueError('该任务无需核对')
                    if self.path=='/api/check': jobs.check(job)
                    self.reply({'ok':True})
                else: self.reply({'error':'接口不存在'},404)
            except Exception as exc: self.reply({'error':str(exc)[:1800]},400)
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    jobs=Jobs()
    threading.Thread(target=jobs.work,daemon=True).start()
    print(f'Game Art: http://127.0.0.1:{port}',flush=True)
    server.serve_forever()

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=5213)
    serve(parser.parse_args().port)

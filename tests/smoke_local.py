"""Explicit local integration test; runs two GPU jobs using the existing generated fixture."""
import base64
import io
import json
import time
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def request(path,body=None):
    data=json.dumps(body).encode() if body is not None else None
    with opener.open(urllib.request.Request('http://127.0.0.1:5213'+path,data=data,headers={'Content-Type':'application/json'}),timeout=60) as response:
        return json.load(response)

if __name__=='__main__':
    first=next(j for j in request('/api/state')['jobs'] if j['status']=='complete')
    source=(ROOT/'data/outputs'/first['id']/'result-1.png').read_bytes()
    image=request('/api/upload',{'data':base64.b64encode(source).decode()})['name']
    mask_image=Image.new('RGB',(1024,1024),'black')
    ImageDraw.Draw(mask_image).rectangle((320,420,720,740),fill='white')
    buffer=io.BytesIO(); mask_image.save(buffer,format='PNG')
    mask=request('/api/upload',{'data':base64.b64encode(buffer.getvalue()).decode()})['name']
    params={**first['params'],'width':768,'height':768,'steps':12,'image':image,'seed':42,'denoise':0.6}
    a=request('/api/jobs',{'prompts':['a brass lantern with soft blue magical light, white background'],'params':params})[0]
    b=request('/api/jobs',{'prompts':['a brass lantern containing a bright emerald green crystal, white background'],'params':{**params,'mask':mask,'upscale':2}})[0]
    ids={a['id'],b['id']}
    for _ in range(120):
        jobs=[j for j in request('/api/state')['jobs'] if j['id'] in ids]
        print([(j['id'],j['status']) for j in jobs],flush=True)
        if all(j['status']=='complete' for j in jobs):
            for j in jobs:
                path=ROOT/'data/outputs'/j['id']/'result-1.png'
                with Image.open(path) as image_result:
                    image_result.verify()
                with Image.open(path) as image_result:
                    expected=j['params']['width']*j['params']['upscale']
                    assert image_result.size==(expected,expected)
            (ROOT/'data/smoke-report.json').write_text(json.dumps({'passed':True,'jobs':jobs},ensure_ascii=False,indent=2),encoding='utf-8')
            print('PASS: reference image, inpaint mask, queue, download and 2x output',flush=True)
            break
        if any(j['status'] in ('error','needs_review') for j in jobs):
            raise RuntimeError(json.dumps(jobs,ensure_ascii=False))
        time.sleep(5)
    else: raise TimeoutError('GPU smoke test did not finish in 10 minutes')

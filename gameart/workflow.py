"""Searge prompt composition with standard ComfyUI sampling and image operations."""
STYLES = {
    "concept": "game concept art, detailed material design, cinematic lighting, professional illustration",
    "anime": "anime game illustration, clean linework, cel shading, expressive colors",
    "painterly": "hand painted game art, painterly brush strokes, atmospheric lighting",
    "realistic": "realistic game asset concept, physically based materials, studio lighting",
}
KINDS = {
    "character": "full body character concept, readable silhouette, character design",
    "scene": "environment concept art, coherent perspective, layered foreground and background",
    "prop": "single game prop, centered composition, plain background, clear silhouette",
}


def build(job):
    p = job['params']; w, h = p['width'], p['height']
    graph = {
        '1': {'class_type':'CheckpointLoaderSimple', 'inputs':{'ckpt_name':p['checkpoint']}},
        '2': {'class_type':'SeargeGameArtConditioning', 'inputs':{
            'clip':['1',1], 'prompt':job['prompt'], 'style':KINDS[p['kind']]+', '+STYLES[p['style']],
            'negative':p['negative'], 'width':w, 'height':h}},
        '3': {'class_type':'EmptyLatentImage', 'inputs':{'width':w,'height':h,'batch_size':1}},
        '4': {'class_type':'KSampler','inputs':{'model':['1',0],'positive':['2',0],'negative':['2',1],
            'latent_image':['3',0], 'seed':p['seed'], 'steps':p['steps'], 'cfg':p['cfg'],
            'sampler_name':'dpmpp_2m', 'scheduler':'karras','denoise':1.0}},
        '5': {'class_type':'VAEDecodeTiled','inputs':{'samples':['4',0],'vae':['1',2],'tile_size':512,'overlap':64,'temporal_size':64,'temporal_overlap':8}},
        '6': {'class_type':'SaveImage','inputs':{'images':['5',0],'filename_prefix':'GameArt/'+job['id']}},
    }
    if p.get('image'):
        graph['7']={'class_type':'LoadImage','inputs':{'image':p['image']}}
        graph['8']={'class_type':'ImageScale','inputs':{'image':['7',0],'upscale_method':'lanczos','width':w,'height':h,'crop':'center'}}
        graph['9']={'class_type':'VAEEncode','inputs':{'pixels':['8',0],'vae':['1',2]}}
        if p.get('mask'):
            graph['10']={'class_type':'LoadImage','inputs':{'image':p['mask']}}
            graph['12']={'class_type':'ImageScale','inputs':{'image':['10',0],'upscale_method':'nearest-exact','width':w,'height':h,'crop':'center'}}
            graph['13']={'class_type':'ImageToMask','inputs':{'image':['12',0],'channel':'red'}}
            # Preserve the original latent for partial denoise on the SDXL base model.
            graph['14']={'class_type':'SetLatentNoiseMask','inputs':{'samples':['9',0],'mask':['13',0]}}
            graph['15']={'class_type':'ImageCompositeMasked','inputs':{'destination':['8',0],'source':['5',0],'x':0,'y':0,'resize_source':False,'mask':['13',0]}}
            graph['6']['inputs']['images']=['15',0]
        graph['4']['inputs'].update(latent_image=['9',0], denoise=p['denoise'])
        if p.get('mask'): graph['4']['inputs']['latent_image']=['14',0]
    if p['upscale'] == 2:
        graph['11']={'class_type':'ImageScaleBy','inputs':{'image':graph['6']['inputs']['images'],'upscale_method':'lanczos','scale_by':2.0}}
        graph['6']['inputs']['images']=['11',0]
    return graph

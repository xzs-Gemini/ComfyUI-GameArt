import copy
import unittest
from gameart.workflow import build

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.job={'id':'test','prompt':'brass lantern','params':{'checkpoint':'sd_xl_base_1.0.safetensors',
            'width':768,'height':768,'kind':'prop','style':'concept','negative':'blurry',
            'seed':42,'steps':12,'cfg':7,'denoise':0.6,'upscale':1}}
    def test_text_to_image_routes_through_searge(self):
        graph=build(self.job)
        self.assertEqual(graph['2']['class_type'],'SeargeGameArtConditioning')
        self.assertEqual(graph['4']['inputs']['positive'],['2',0])
        self.assertEqual(graph['4']['inputs']['denoise'],1)
        self.assertEqual(graph['3']['inputs']['batch_size'],1)
    def test_reference_image_changes_latent_and_strength(self):
        self.job['params']['image']='gameart-example.png'
        graph=build(self.job)
        self.assertEqual(graph['4']['inputs']['latent_image'],['9',0])
        self.assertEqual(graph['4']['inputs']['denoise'],0.6)
        self.assertEqual(graph['9']['class_type'],'VAEEncode')
    def test_mask_has_same_crop_as_reference(self):
        self.job['params'].update(image='gameart-example.png',mask='gameart-mask.png')
        graph=build(self.job)
        self.assertEqual(graph['9']['class_type'],'VAEEncode')
        self.assertEqual(graph['8']['inputs']['crop'],graph['12']['inputs']['crop'])
        self.assertEqual(graph['14']['inputs']['mask'],['13',0])
        self.assertEqual(graph['4']['inputs']['latent_image'],['14',0])
        self.assertEqual(graph['6']['inputs']['images'],['15',0])
    def test_upscale_routes_saved_image(self):
        self.job['params']['upscale']=2
        graph=build(self.job)
        self.assertEqual(graph['6']['inputs']['images'],['11',0])
        self.assertEqual(graph['11']['inputs']['scale_by'],2)
    def test_graph_links_are_valid_and_input_unchanged(self):
        before=copy.deepcopy(self.job); graph=build(self.job)
        for node in graph.values():
            for value in node['inputs'].values():
                if isinstance(value,list): self.assertIn(value[0],graph)
        self.assertEqual(self.job,before)

if __name__=='__main__': unittest.main()

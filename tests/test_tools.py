import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_gif import build, natural_key
from export_image import export
from image_utils import visible_bytes


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.frames = self.root / 'frames'
        self.frames.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def frame(self, name, x=8, size=(48, 48)):
        im = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(im)
        draw.rectangle((x, 8, x+16, 24), fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=2)
        im.save(self.frames / name)

    def inspect(self, *args):
        return subprocess.run([sys.executable, str(ROOT/'scripts/inspect_images.py'), *map(str,args)],
                              capture_output=True, text=True, check=False)

    def test_numeric_frame_order(self):
        names = [Path('10.png'), Path('2.png'), Path('1.png')]
        self.assertEqual([p.name for p in sorted(names, key=natural_key)], ['1.png', '2.png', '10.png'])

    def test_gif_loop_transparency_black_and_fixed_caption(self):
        for name, x in [('1.png',8), ('2.png',10), ('10.png',12)]:
            self.frame(name, x)
        caption = Image.new('RGBA', (96,96), (0,0,0,0))
        ImageDraw.Draw(caption).rectangle((20,82,65,88), fill=(40,20,10,255))
        caption.save(self.root/'caption.png')
        output = build(self.frames, self.root/'result.gif', size=96,
                       durations=[100,120,140], caption=self.root/'caption.png')
        captions = []
        with Image.open(output) as gif:
            self.assertEqual(gif.size, (96,96))
            self.assertEqual(gif.n_frames, 3)
            self.assertEqual(gif.info['loop'], 0)
            for i in range(3):
                gif.seek(i)
                rgba = gif.convert('RGBA')
                self.assertEqual(rgba.getpixel((0,0))[3], 0)
                self.assertEqual(rgba.getpixel((26,32))[3], 255)
                captions.append(rgba.crop((20,82,66,89)).tobytes())
        self.assertEqual(len(set(captions)), 1)
        checked = self.inspect(output, '--width',96,'--height',96,'--require-animation',
                               '--require-loop','--require-transparency')
        self.assertEqual(checked.returncode, 0, checked.stderr+checked.stdout)
        self.assertTrue(json.loads(checked.stdout)['visual_review_required'])

    def test_duplicate_frames_are_not_animation(self):
        self.frame('1.png')
        self.frame('2.png')
        with self.assertRaisesRegex(ValueError,'no actual visual changes'):
            build(self.frames,self.root/'fake.gif')

    def test_hidden_rgb_changes_are_not_visible_animation(self):
        a=Image.new('RGBA',(48,48),(255,0,0,0))
        b=Image.new('RGBA',(48,48),(0,0,255,0))
        a.save(self.frames/'1.png')
        b.save(self.frames/'2.png')
        self.assertNotEqual(a.tobytes(),b.tobytes())
        self.assertEqual(visible_bytes(a),visible_bytes(b))
        with self.assertRaisesRegex(ValueError,'no actual visual changes'):
            build(self.frames,self.root/'hidden.gif')

    def test_motion_lost_in_transparency_conversion_rejected(self):
        for n,x in [(1,8),(2,16)]:
            im=Image.new('RGBA',(48,48),(0,0,0,0))
            ImageDraw.Draw(im).rectangle((x,8,x+10,20),fill=(255,0,0,50))
            im.save(self.frames/f'{n}.png')
        with self.assertRaisesRegex(ValueError,'No visible motion remains'):
            build(self.frames,self.root/'invisible.gif')

    def test_mismatched_source_canvases_rejected(self):
        self.frame('1.png')
        self.frame('2.png',size=(64,48))
        with self.assertRaisesRegex(ValueError,'share one source canvas'):
            build(self.frames,self.root/'bad.gif')

    def test_bad_durations_rejected(self):
        self.frame('1.png')
        self.frame('2.png',x=10)
        with self.assertRaises(ValueError):
            build(self.frames,self.root/'bad.gif',durations=[100])
        with self.assertRaises(ValueError):
            build(self.frames,self.root/'bad.gif',duration=125)

    def test_png_export_keeps_transparency(self):
        self.frame('1.png')
        output=self.root/'cover.png'
        count=export(self.frames/'1.png',output,240,240,500000,'contain')
        self.assertLessEqual(count,500000)
        with Image.open(output) as im:
            self.assertEqual(im.size,(240,240))
            self.assertEqual(im.convert('RGBA').getpixel((0,0))[3],0)

    def test_jpeg_budget_and_dimensions(self):
        self.frame('1.png')
        output=self.root/'banner.jpg'
        count=export(self.frames/'1.png',output,750,400,80000)
        self.assertLessEqual(count,80000)
        with Image.open(output) as im:
            self.assertEqual(im.format,'JPEG')
            self.assertEqual(im.size,(750,400))

    def test_impossible_budget_fails_without_output(self):
        self.frame('1.png')
        output=self.root/'too-small.png'
        with self.assertRaisesRegex(ValueError,'Cannot meet byte budget'):
            export(self.frames/'1.png',output,240,240,1)
        self.assertFalse(output.exists())

    def test_inspector_rejects_static_and_wrong_dimensions(self):
        self.frame('1.png')
        result=self.inspect(self.frames/'1.png','--width',240,'--require-animation')
        self.assertEqual(result.returncode,1)
        report=json.loads(result.stdout)
        self.assertFalse(report['passed'])
        self.assertGreaterEqual(len(report['images'][0]['errors']),2)

    def test_inspector_missing_input_fails(self):
        result=self.inspect(self.root/'missing')
        self.assertEqual(result.returncode,1)
        self.assertFalse(json.loads(result.stdout)['passed'])


if __name__=='__main__':
    unittest.main()

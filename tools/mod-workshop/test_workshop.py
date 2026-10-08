import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
import wave
import zipfile

from PIL import Image
from formats import model_asset, read_obj, write_chunks
from workshop import make_pack, read_pack, install_pack, installed, toggle_mod, export_mod

OBJ = '''v -1 0 -1
v 1 0 -1
v 1 0 1
v -1 0 1
v 0 2 0
vt 0 0
vt 1 0
vt 0.5 1
f 1/1 5/3 2/2
f 2/1 5/3 3/2
f 3/1 5/3 4/2
f 4/1 5/3 1/2
f 1/1 2/2 3/3
f 1/1 3/3 4/2
'''


class WorkshopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'game'
        (self.game / 'Microsoft Kids' / '3D Movie Maker').mkdir(parents=True)
        self.obj = self.root / 'pyramid.obj'
        self.obj.write_text(OBJ)
        self.png = self.root / 'texture.png'
        Image.new('RGB', (32, 32), (250, 120, 30)).save(self.png)

    def test_model_native_layout(self):
        content, thumbs = model_asset(self.obj, 'Pyramid', self.png)
        model = next(c.data for c in content if c.tag == 'BMDL')
        nv, nf = struct.unpack_from('<hh', model, 4)
        self.assertEqual(nf, 6)
        self.assertEqual(len(model), 48 + 32 * (nv + nf))
        self.assertEqual(struct.unpack_from('<i', model, 8)[0], 0)  # native engine prepares normals
        for offset in range(48 + nv * 32, len(model), 32):
            self.assertTrue(all(i < nv for i in struct.unpack_from('<3H', model, offset)))
        native = write_chunks(content)
        length, index, index_size = struct.unpack_from('<III', native, 16)
        self.assertEqual(length, len(native))
        self.assertEqual(index + index_size, length)
        count, attrs = struct.unpack_from('<II', native, index + 4)
        self.assertEqual(count, len(content))
        tags = []
        for n in range(count):
            offset, size = struct.unpack_from('<II', native, index + 20 + attrs + 8*n)
            pos = index + 20 + offset
            tag, number, address = struct.unpack_from('<4sII', native, pos)
            tags.append((tag[::-1], number))
            self.assertGreaterEqual(size, 20)
            self.assertGreaterEqual(address, 128)
            self.assertLess(address, index)
        self.assertEqual(tags, sorted(tags))
        self.assertEqual(thumbs[0].tag, 'PRTH')

    def test_install_export_and_toggle_preserve_identity(self):
        pack = self.root / 'model.zip'
        original = make_pack(self.obj, pack)
        install_pack(pack, self.game)
        self.assertEqual(installed(self.game)[0][2]['id'], original['id'])
        self.assertFalse(toggle_mod(self.game, original['source_id']))
        self.assertFalse(installed(self.game)[0][1])
        self.assertTrue(toggle_mod(self.game, original['source_id']))
        exported = self.root / 'export.zip'
        export_mod(self.game, original['source_id'], exported)
        self.assertEqual(read_pack(pack), read_pack(exported))
        with self.assertRaises(ValueError):
            install_pack(pack, self.game)

    def test_texture_and_sound(self):
        tex = self.root / 'texture.zip'
        self.assertEqual(make_pack(self.png, tex)['kind'], 'texture')
        wav = self.root / 'beep.wav'
        with wave.open(str(wav), 'wb') as audio:
            audio.setparams((1, 2, 22050, 0, 'NONE', 'not compressed'))
            audio.writeframes(struct.pack('<h', 1000) * 2205)
        pack = self.root / 'sound.zip'
        self.assertEqual(make_pack(wav, pack)['kind'], 'sound')
        read_pack(pack)

    def test_reject_bad_obj(self):
        for text in [OBJ.replace('f 1/1 5/3 2/2', 'f 0/1 5/3 2/2'),
                     OBJ.replace('v -1 0 -1', 'v nan 0 -1'),
                     OBJ + 'f 1 2 3 4\n', 'v 0 0 0\n']:
            self.obj.write_text(text)
            with self.assertRaises(ValueError):
                read_obj(self.obj)

    def test_reject_path_traversal_and_tampering(self):
        pack = self.root / 'bad.zip'
        with zipfile.ZipFile(pack, 'w') as archive:
            archive.writestr('../escape', 'bad')
        with self.assertRaises(ValueError):
            install_pack(pack, self.game)
        self.assertFalse((self.root / 'escape').exists())
        good = self.root / 'good.zip'
        make_pack(self.png, good)
        manifest, files = read_pack(good)
        files['assets.3cn'] += b'changed'
        with zipfile.ZipFile(pack, 'w') as archive:
            for name, data in files.items():
                archive.writestr(name, data)
        with self.assertRaises(ValueError):
            install_pack(pack, self.game)
        self.assertEqual(installed(self.game), [])

    def test_existing_export_is_preserved(self):
        pack = self.root / 'keep.zip'
        pack.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):
            make_pack(self.png, pack)
        self.assertEqual(pack.read_bytes(), b'keep')


if __name__ == '__main__':
    unittest.main()

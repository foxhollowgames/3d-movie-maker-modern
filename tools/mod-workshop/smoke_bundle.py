"""Exercise dynamic dependencies inside the Windows executable, without a GUI."""
from pathlib import Path
import subprocess
import sys
import tempfile
import wave

from PIL import Image
from test_workshop import OBJ
from workshop import read_pack

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    (root / 'model.obj').write_text(OBJ, encoding='utf-8')
    Image.new('RGB', (32, 32), (50, 150, 220)).save(root / 'texture.png')
    with wave.open(str(root / 'sound.wav'), 'wb') as audio:
        audio.setparams((1, 2, 22050, 0, 'NONE', 'not compressed'))
        audio.writeframes(b'\x01\x02' * 2205)
    for name, kind in [('model.obj', 'prop'), ('texture.png', 'texture'), ('sound.wav', 'sound')]:
        destination = root / (name + '.zip')
        subprocess.run([str(Path(sys.argv[1]).resolve()), 'build', str(root / name), str(destination)],
                       check=True, timeout=60)
        manifest, _ = read_pack(destination)
        assert manifest['kind'] == kind
        print(f'Packaged executable: {kind} import passed')

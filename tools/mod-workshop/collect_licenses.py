"""Collect notices for the dependencies bundled by PyInstaller."""
import importlib.metadata
from pathlib import Path
import sys

with Path(sys.argv[1]).open('w', encoding='utf-8') as out:
    out.write('Mod Workshop includes Python, Tcl/Tk, Pillow, miniaudio, and CFFI.\n')
    for name in ('Pillow', 'miniaudio', 'cffi', 'pycparser', 'pyinstaller'):
        dist = importlib.metadata.distribution(name)
        out.write(f'\n===== {name} {dist.version} =====\n')
        for file in dist.files or []:
            if 'license' in str(file).lower() or 'copying' in str(file).lower():
                try:
                    out.write(dist.locate_file(file).read_text(encoding='utf-8') + '\n')
                except (UnicodeError, IsADirectoryError):
                    pass
    for path in [Path(sys.base_prefix) / 'LICENSE.txt', *Path(sys.base_prefix).glob('tcl/*/license.terms')]:
        if path.is_file():
            out.write(f'\n===== {path.name} =====\n' + path.read_text(encoding='utf-8'))

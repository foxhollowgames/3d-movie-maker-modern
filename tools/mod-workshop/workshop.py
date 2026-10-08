"""Portable mod builder and installer. Run without arguments for the desktop UI."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import uuid
import zipfile

from formats import model_asset, sound_asset, texture_asset, write_chunks

VERSION = '1.0.0'
MAX_PACK = 40 * 1024 * 1024
FILES = {'mod.json', 'assets.3cn', 'assets.3th'}


def make_pack(source, destination, name=None, texture=None, size=5.0):
    source, destination = Path(source), Path(destination)
    name = (name or source.stem).strip()
    if not name or len(name) > 80:
        raise ValueError('Choose a name with 1 to 80 characters')
    ext = source.suffix.lower()
    if ext == '.obj':
        content, thumbs = model_asset(source, name, texture, size)
        kind = 'prop'
    elif ext in {'.png', '.jpg', '.jpeg', '.bmp'}:
        content, thumbs = texture_asset(source, name)
        kind = 'texture'
    elif ext in {'.wav', '.mp3', '.flac', '.ogg'}:
        content, thumbs = sound_asset(source, name)
        kind = 'sound'
    else:
        raise ValueError('Choose OBJ, PNG, JPG, BMP, WAV, MP3, FLAC, or OGG')
    uid = uuid.uuid4()
    sid = 1_000_000 + uid.int % (2_147_483_646 - 1_000_000)
    files = {'assets.3cn': write_chunks(content), 'assets.3th': write_chunks(thumbs)}
    manifest = {'format': 1, 'id': str(uid), 'source_id': sid, 'name': name,
                'kind': kind, 'workshop_version': VERSION,
                'sha256': {key: hashlib.sha256(data).hexdigest() for key, data in files.items()}}
    files['mod.json'] = json.dumps(manifest, indent=2).encode('utf-8')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects an existing shared pack and its persistent ID.
    with destination.open('xb') as stream:
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
            for key, data in files.items():
                archive.writestr(key, data)
    return manifest


def read_pack(path):
    if Path(path).stat().st_size > MAX_PACK:
        raise ValueError('Pack exceeds 40 MB')
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) != 3 or {i.filename for i in entries} != FILES:
            raise ValueError('Pack must contain only mod.json, assets.3cn, and assets.3th at its root')
        if sum(i.file_size for i in entries) > MAX_PACK:
            raise ValueError('Expanded pack exceeds 40 MB')
        for i in entries:
            if i.flag_bits & 1 or ((i.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError('Encrypted files and symbolic links are not supported')
            if i.filename == 'mod.json' and i.file_size > 8192:
                raise ValueError('Manifest exceeds 8 KB')
        files = {i.filename: archive.read(i) for i in entries}
    manifest = validate_manifest(json.loads(files['mod.json']))
    for key in ('assets.3cn', 'assets.3th'):
        if hashlib.sha256(files[key]).hexdigest() != manifest['sha256'].get(key):
            raise ValueError(f'{key} checksum does not match the manifest')
        if not files[key].startswith(b'CHN2'):
            raise ValueError(f'{key} is not a chunky content file')
    return manifest, files


def validate_manifest(manifest):
    if not isinstance(manifest, dict) or manifest.get('format') != 1:
        raise ValueError('Unsupported mod pack format')
    if not isinstance(manifest.get('id'), str) or str(uuid.UUID(manifest['id'])) != manifest['id']:
        raise ValueError('Invalid mod UUID')
    sid = manifest.get('source_id')
    if type(sid) is not int or not 1000 <= sid <= 2147483646:
        raise ValueError('Invalid source ID')
    if not isinstance(manifest.get('name'), str) or not 1 <= len(manifest['name']) <= 80:
        raise ValueError('Invalid mod name')
    if not isinstance(manifest.get('sha256'), dict):
        raise ValueError('Missing checksums')
    return manifest


def content_root(game):
    game = Path(game).resolve()
    candidates = [game / 'Microsoft Kids', game / '3D Movie Maker.app' / 'Contents' / 'Resources' / 'Microsoft Kids']
    if game.name == 'Microsoft Kids':
        candidates.insert(0, game)
    for root in candidates:
        if (root / '3D Movie Maker').is_dir():
            return root
    raise ValueError('Select the extracted game folder that contains Microsoft Kids')


def install_pack(pack, game):
    manifest, files = read_pack(pack)
    root = content_root(game)
    folder = root / f"FHMod{manifest['source_id']}"
    disabled = root.parent / 'Disabled Mods' / folder.name
    # Never overwrite a source ID: old movies may refer to its original content.
    if folder.exists() or disabled.exists():
        raise ValueError('This source ID is already installed. Existing content was kept.')
    with tempfile.TemporaryDirectory(prefix='.mod-install-', dir=root.parent) as temp:
        for key, data in files.items():
            (Path(temp) / key).write_bytes(data)
        # Rename is atomic and stays on the same volume.
        Path(temp).rename(folder)
    return manifest


def installed(game):
    root = content_root(game)
    result = []
    for parent, enabled in [(root, True), (root.parent / 'Disabled Mods', False)]:
        if not parent.is_dir():
            continue
        for folder in sorted(parent.iterdir()):
            if folder.is_symlink() or not re.fullmatch(r'FHMod[1-9][0-9]{3,9}', folder.name):
                continue
            try:
                manifest = validate_manifest(json.loads((folder / 'mod.json').read_text(encoding='utf-8')))
                if folder.name != f"FHMod{manifest['source_id']}":
                    continue
                result.append((folder, enabled, manifest))
            except (OSError, ValueError, TypeError):
                continue
    return result


def toggle_mod(game, sid):
    root = content_root(game)
    for folder, enabled, _ in installed(game):
        if folder.name == f'FHMod{sid}':
            target_parent = root.parent / 'Disabled Mods' if enabled else root
            target_parent.mkdir(exist_ok=True)
            target = target_parent / folder.name
            if target.exists():
                raise ValueError('A mod with this source ID already exists at the destination')
            folder.rename(target)
            return not enabled
    raise ValueError('Mod was not found')


def export_mod(game, sid, destination):
    for folder, _, manifest in installed(game):
        if manifest['source_id'] == sid:
            with Path(destination).open('xb') as stream:
                with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
                    for key in sorted(FILES):
                        archive.write(folder / key, key)
            return
    raise ValueError('Mod was not found')


def gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    root = tk.Tk()
    root.title('3D Movie Maker — Mod Workshop')
    root.geometry('820x640')
    root.minsize(760, 620)
    frame = ttk.Frame(root, padding=18)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Mod Workshop', font=('Segoe UI', 20, 'bold')).pack(anchor='w')
    ttk.Label(frame, text='Import your assets. Share portable mod packs.', font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 12))
    default = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path.cwd()
    game = tk.StringVar(value=str(default))
    source, texture, name = tk.StringVar(), tk.StringVar(), tk.StringVar()
    size = tk.StringVar(value='5')
    def pick(var, directory=False):
        value = filedialog.askdirectory() if directory else filedialog.askopenfilename()
        if value:
            var.set(value)
    def row(parent, label, var, directory=False):
        box = ttk.Frame(parent)
        box.pack(fill='x', pady=4)
        ttk.Label(box, text=label, width=19).pack(side='left')
        ttk.Entry(box, textvariable=var).pack(side='left', fill='x', expand=True)
        ttk.Button(box, text='Browse…', command=lambda: pick(var, directory)).pack(side='left', padx=(6,0))
    row(frame, 'Game folder', game, True)
    tabs = ttk.Notebook(frame)
    tabs.pack(fill='both', expand=True, pady=10)
    create = ttk.Frame(tabs, padding=12)
    manage = ttk.Frame(tabs, padding=12)
    tabs.add(create, text='Import assets')
    tabs.add(manage, text='Installed mods')
    row(create, 'Asset file', source)
    row(create, 'OBJ texture (optional)', texture)
    box = ttk.Frame(create)
    box.pack(fill='x', pady=4)
    ttk.Label(box, text='Display name', width=19).pack(side='left')
    ttk.Entry(box, textvariable=name).pack(side='left', fill='x', expand=True)
    box = ttk.Frame(create)
    box.pack(fill='x', pady=4)
    ttk.Label(box, text='Model size', width=19).pack(side='left')
    ttk.Entry(box, textvariable=size, width=10).pack(side='left')
    ttk.Label(box, text='  Largest dimension in scene units (0.01–100)').pack(side='left')
    ttk.Label(create, justify='left', wraplength=710, text=(
        'Models: triangulated OBJ, Y-up, up to 10,000 triangles. Use one baked texture with UV coordinates. '
        'MTL files, rigs, and animation are not imported.\n\n'
        'Textures: PNG, JPG, BMP. Images become opaque palette textures, up to 256 × 256 pixels.\n\n'
        'Sounds: WAV, MP3, FLAC, OGG. Up to 90 seconds. Sounds appear in Sound Effects.')).pack(anchor='w', pady=14)
    status = tk.StringVar(value='Close 3D Movie Maker before changing installed mods. Restart it to load new content.')
    def action(fn):
        try:
            fn()
        except Exception as exc:
            messagebox.showerror('Mod Workshop', str(exc), parent=root)
    def build(install):
        if not source.get():
            raise ValueError('Select an asset file first')
        if install:
            with tempfile.TemporaryDirectory() as temp:
                pack = Path(temp) / 'asset.3dmm-mod.zip'
                make_pack(source.get(), pack, name.get() or None, texture.get() or None, float(size.get()))
                item = install_pack(pack, game.get())
            status.set(f"Installed {item['name']}. Restart the game. Open Props, Materials, or Sound Effects.")
            refresh()
        else:
            destination = filedialog.asksaveasfilename(defaultextension='.3dmm-mod.zip', initialfile=Path(source.get()).stem + '.3dmm-mod.zip')
            if destination:
                make_pack(source.get(), destination, name.get() or None, texture.get() or None, float(size.get()))
                status.set('Pack created. Share this ZIP to preserve its asset ID.')
    buttons = ttk.Frame(create)
    buttons.pack(fill='x', pady=4)
    ttk.Button(buttons, text='Import into game', command=lambda: action(lambda: build(True))).pack(side='left')
    ttk.Button(buttons, text='Create shareable pack…', command=lambda: action(lambda: build(False))).pack(side='left', padx=8)
    tree = ttk.Treeview(manage, columns=('state','name','kind'), show='headings', height=9)
    for col, width in [('state',90),('name',380),('kind',100)]:
        tree.heading(col, text=col.title())
        tree.column(col, width=width)
    tree.pack(fill='both', expand=True)
    def refresh():
        tree.delete(*tree.get_children())
        for _, enabled, item in installed(game.get()):
            tree.insert('', 'end', iid=str(item['source_id']), values=('Enabled' if enabled else 'Disabled', item['name'], item.get('kind','asset')))
    def selected():
        if not tree.selection():
            raise ValueError('Select an installed mod first')
        return int(tree.selection()[0])
    def toggle():
        enabled = toggle_mod(game.get(), selected())
        refresh()
        status.set(('Enabled' if enabled else 'Disabled') + ' mod. Restart the game. Saved movies need their mods enabled.')
    def export():
        sid = selected()
        destination = filedialog.asksaveasfilename(defaultextension='.3dmm-mod.zip')
        if destination:
            export_mod(game.get(), sid, destination)
            status.set('Pack exported with its original asset ID.')
    def install():
        source_path = filedialog.askopenfilename(filetypes=[('Mod packs','*.zip')])
        if source_path:
            item = install_pack(source_path, game.get())
            refresh()
            status.set(f"Installed {item['name']}. Restart the game.")
    controls = ttk.Frame(manage)
    controls.pack(fill='x', pady=10)
    for label, fn in [('Refresh',refresh),('Install pack…',install),('Enable / disable',toggle),('Export pack…',export)]:
        ttk.Button(controls, text=label, command=lambda fn=fn: action(fn)).pack(side='left', padx=(0,6))
    ttk.Label(frame, textvariable=status, wraplength=760).pack(fill='x', pady=(4,0))
    try:
        refresh()
    except ValueError:
        status.set('Select the extracted game folder above. Close the game before installing mods.')
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command')
    build = sub.add_parser('build')
    build.add_argument('source', type=Path)
    build.add_argument('output', type=Path)
    build.add_argument('--name')
    build.add_argument('--texture', type=Path)
    build.add_argument('--size', type=float, default=5)
    install = sub.add_parser('install')
    install.add_argument('pack', type=Path)
    install.add_argument('--game', required=True, type=Path)
    args = parser.parse_args()
    if args.command == 'build':
        print(json.dumps(make_pack(args.source, args.output, args.name, args.texture, args.size), indent=2))
    elif args.command == 'install':
        print(json.dumps(install_pack(args.pack, args.game), indent=2))
    else:
        gui()


if __name__ == '__main__':
    main()

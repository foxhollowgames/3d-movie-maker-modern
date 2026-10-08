# Mod Workshop

Import static props, textures, and sound effects into 3D Movie Maker Modern.
The Windows download includes Python and its dependencies.

## Use the Windows app

1. Extract the latest game release into a writable folder.
2. Put `Mod Workshop.exe` beside `3dmovie.exe`.
3. Close the game and open Mod Workshop.
4. Select an asset and click **Import into game**.
5. Restart the game. Find the asset in **Props**, **3D Words → Patterns & Colors**, or **Sound Effects**.

Use **Installed mods** to enable, disable, install, or export packs.
Keep each exported `.3dmm-mod.zip` file. It contains the stable asset ID that saved movies need.
Share that same pack with anyone who opens your movie.
Creating a new pack from the source asset creates a new ID.

## Supported assets

| Asset | Input | Limits |
|---|---|---|
| Static prop | OBJ | Y-up, triangulated faces, 10,000 triangles, 30,000 vertices after UV seams |
| Prop texture | PNG/JPG/BMP | One baked texture, selected separately in the OBJ texture field |
| 3D text material | PNG/JPG/BMP | Imported into 3D Words → Patterns & Colors |
| Sound effect | WAV/MP3/FLAC/OGG | Up to 90 seconds, decoded as stereo 16-bit PCM at 44.1 kHz |

Textures use the game's fixed 256-color palette. The converter resizes them to power-of-two dimensions, at most 256 × 256.
Transparency becomes opaque black. Model size sets the largest dimension in scene units. The default is 5.
Export models from Blender with **Triangulate Faces** enabled and **Y Up** selected.
Bake all materials into one texture and export UV coordinates.
MTL files, separate submesh materials, rigging, animation, FBX, glTF, and V3DMM VXP files are not imported.
This release adds props, materials, and effects. It does not add scenes or animated characters.

## Packs and saved movies

The game discovers `Microsoft Kids/FHMod<source_id>/` folders at startup.
Each folder contains `mod.json`, `assets.3cn`, and `assets.3th`.
The canonical source ID is an integer from 1000 to 2147483646.
Workshop generates random IDs. It refuses to overwrite an installed ID, including a disabled one.
Disabled packs move into `Disabled Mods` beside `Microsoft Kids`.
Do not rename mod folders or alter IDs. Saved movies store those references.
Keep required packs enabled when you open a movie.
Close the game before any install, enable, or disable operation.

Only install packs from sources you trust. Checksums detect damage; they do not establish who created a pack.
The legacy game parses native binary assets and was not designed as a secure sandbox for hostile files.
Workshop accepts only its three-file pack layout. It rejects path traversal, symbolic links, and oversized archives.

## Run from source on Windows, macOS, or Linux

Use Python 3.12 with Tk installed. Select the extracted game folder in the app.
The macOS layout `3D Movie Maker.app/Contents/Resources/Microsoft Kids` is supported.

```sh
python -m pip install -r tools/mod-workshop/requirements.txt
python tools/mod-workshop/workshop.py
python -m unittest discover -s tools/mod-workshop -v
```

Command-line examples:

```sh
python tools/mod-workshop/workshop.py build pyramid.obj pyramid.3dmm-mod.zip --texture colors.png --name "My pyramid"
python tools/mod-workshop/workshop.py install pyramid.3dmm-mod.zip --game "/path/to/extracted/game"
```

## Attribution

The converter uses format definitions from the MIT-licensed Microsoft source.
`palette.rgb` is the palette from `src/studio/bmp/socpal.bmp` in that source.
Ben Stone's MIT [pymaginopolis](https://github.com/benstone/pymaginopolis) helped document the CHN2 container layout.
Pillow handles images. Irmen de Jong's miniaudio bindings decode audio.
The Windows package includes dependency license notices.

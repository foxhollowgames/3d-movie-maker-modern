# 3D Movie Maker Modern

**Play the classic 3D Movie Maker on modern computers.**

[Download the latest release](https://github.com/foxhollowgames/3d-movie-maker-modern/releases/latest)

This Fox Hollow Games distribution builds on [3DMMEx](https://github.com/benstone/3DMMEx),
[3DMMForever](https://github.com/foone/3DMMForever), and the
[Microsoft source release](https://github.com/microsoft/Microsoft-3D-Movie-Maker).
The community port provides modern compiler support, 64-bit support, and improved input and audio handling.
The original scenes, characters, sounds, tutorials, and sample movies are included.

## Play on Windows

1. Download `3D-Movie-Maker-Modern-Windows-x64.zip` for an Intel or AMD computer.
   Use the `Windows-ARM64` ZIP for a Windows on ARM computer.
2. Extract the complete ZIP to a writable folder.
3. Open `Start 3D Movie Maker.cmd` or `3dmovie.exe`.
4. Enter the studio through the introduction.
5. Open a sample movie from `Microsoft Kids/Users/McZee` and select Play.

Windows 10 and Windows 11 are the intended Windows targets.
No original CD, administrator access, or installation is required.
Keep the `Microsoft Kids` folder beside the executable.
Save your movies in a writable folder, such as Documents.

## Other systems

- **macOS on Apple Silicon:** Extract the `macOS-ARM64` ZIP and open `3D Movie Maker.app`.
  The application is not notarized. macOS can block its first launch.
  Cutscene playback is not implemented upstream. Movie creation and sample movies use the SDL port.
- **Linux:** Build from source with the instructions below. CI builds and tests Linux, but no portable Linux package is supplied.
- **Intel Macs:** No prebuilt download is supplied or tested by this distribution.

The classic interface scales to fit modern displays, including 1080p, 1440p, 4K, and ultrawide screens.
It keeps the original 4:3 proportions. A dark theater fabric texture fills unused space around the picture.
The app detects the current monitor resolution and starts in fullscreen by default.
Press **F11** to open **Display Settings**. Select automatic fullscreen or a window resolution, then save.
The app remembers these settings for the next launch. **Reset to automatic** restores fullscreen startup on Windows.
Alt/Option-Enter temporarily switches between fullscreen and windowed mode without changing the saved startup setting.
Resize or maximize the window to change the display size in windowed mode.
Fullscreen uses the current monitor resolution. It does not change the desktop display mode.
The artwork and movie canvas retain their original 640 by 480 layout and detail.
On Windows, leaving fullscreen restores the previous window size and position.
Window sizes that exceed the available display area are reduced to fit.
Fullscreen always follows the current desktop resolution, including after a display change.
Resolution settings control presentation size. They do not add detail to the original artwork.

Windows users can also open **Display Settings** from the window's title-bar menu.
Advanced settings are stored in `%APPDATA%/3DMMEx/3dmovie.ini` on Windows.
In its `[3dmovie]` section, `displayfullscreen = 1` selects fullscreen startup (`0` selects a window).
`windowwidth` and `windowheight` set the window's content size in pixels. Set both to `0` for automatic sizing.
Invalid sizes fall back to automatic sizing. Close the app before editing this file.

## Build from source

Use Git, CMake 3.28 or later, and Ninja. The first configure step downloads dependencies.
Use Visual Studio 2022 with the Desktop development with C++ workload on Windows.
Open its **x64 Native Tools Command Prompt** and run:

```bat
git clone https://github.com/foxhollowgames/3d-movie-maker-modern.git
cd 3d-movie-maker-modern
cmake --preset x64-msvc-relwithdebinfo -D3DMM_PACKAGE_WIX=OFF
cmake --build build/x64-msvc-relwithdebinfo --target studio tests
ctest --test-dir build/x64-msvc-relwithdebinfo --output-on-failure
cmake --install build/x64-msvc-relwithdebinfo
```

The runnable folder is `dist/x64-msvc-relwithdebinfo`.
For Windows ARM64, use the ARM64 compiler environment and the `arm64-msvc-relwithdebinfo` preset.

On Ubuntu, install dependencies first:

```sh
sudo apt-get update
sudo apt-get install -y g++ cmake ninja-build libsdl2-dev libsdl2-ttf-dev libgtk-3-dev libfontconfig-dev libfluidsynth-dev fluidsynth libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-good zenity
```

On macOS, install Xcode command-line tools, CMake, and Ninja. Install the remaining libraries with Homebrew:

```sh
brew install cmake ninja fontconfig fluidsynth
```

Build on Linux or macOS:

```sh
cmake --preset sdl-relwithdebinfo
cmake --build build/sdl-relwithdebinfo --target studio tests
ctest --test-dir build/sdl-relwithdebinfo --output-on-failure
cmake --install build/sdl-relwithdebinfo
```

On Linux, run `dist/sdl-relwithdebinfo/3dmovie`.
On macOS, open `dist/sdl-relwithdebinfo/3D Movie Maker.app`.
The full upstream build guide is in [docs/UPSTREAM.md](docs/UPSTREAM.md).

## Release checks

GitHub Actions compiles Windows x64, Windows ARM64, macOS ARM64, and Linux x64.
It runs the upstream unit tests and checks installed content before uploading build artifacts.
Windows and macOS ZIPs include licenses and quick-start instructions.
Each ZIP has a SHA-256 checksum file.
Automated tests do not prove every editor feature or audio device works.

See [docs/RELEASING.md](docs/RELEASING.md) for the GH CLI release procedure.
Report problems in [this repository's issues](https://github.com/foxhollowgames/3d-movie-maker-modern/issues).

## Credits and license

This is an independent community distribution, not a Microsoft product or sponsored release.
The application continues to identify itself as 3DMMEx to preserve upstream attribution.
The starting source is 3DMMEx commit `9a4431449a7df0c5acd4be01e972c6fd991962d8`, based on version 0.7.0.
Fox Hollow Games adds distribution documentation, a Windows launcher, dependency commit pins, release checks, compiler discovery, and fullscreen startup at the desktop resolution.

The original source history and notices are retained.
See [LICENSE](LICENSE), [THIRD_PARTY_LICENSES.txt](THIRD_PARTY_LICENSES.txt), and
[upstream acknowledgments](docs/UPSTREAM.md#legal-stuff).
Microsoft and third-party trademarks remain the property of their owners.

# Custom assets and mod packs

Use **Mod Workshop** to import static OBJ props, PNG/JPG/BMP textures, and WAV/MP3/FLAC/OGG sound effects.
Download the game and Workshop from [Releases](https://github.com/foxhollowgames/3d-movie-maker-modern/releases).
Read the [import guide](tools/mod-workshop/README.md) for asset limits and pack sharing.

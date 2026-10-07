# Publish a release with GH CLI

1. Push the release source to `main`.
2. Wait for the `build` workflow to pass on that exact commit.
3. Download its artifacts with `gh run download RUN_ID --dir out/artifacts`.
4. Validate each installed folder with `scripts/Test-Package.ps1`.
5. Test the Windows application before publishing the packaged downloads.

The original upstream workflow remains unchanged. It builds Windows x86, x64,
ARM64, SDL debug, Linux debug, and macOS ARM64 configurations.
Release only the Windows x64, Windows ARM64, and macOS ARM64 folders.
Rename the x64 artifact's `3dmovie-x64.exe` to `3dmovie.exe` before validation.
This is the name expected by the Windows launcher.

Example package validation:

```powershell
./scripts/Test-Package.ps1 -Path 'out/artifacts/3DMMEx Windows x64' -Platform Windows
./scripts/Test-Package.ps1 -Path 'out/artifacts/3DMMEx Windows ARM64' -Platform Windows
./scripts/Test-Package.ps1 -Path 'out/artifacts/3DMMEx macOS arm64 Release' -Platform macOS
```

Create ZIP archives with the installed files at the archive root.
For macOS, use the ZIP created during installation on the Mac runner. It preserves symbolic links and executable permissions.
Generate a SHA-256 checksum file for each ZIP with `Get-FileHash` or `shasum`.
Extract the Windows ZIP and check launch, sample playback, and movie save/reopen.
macOS requires a separate interactive check to claim manual macOS validation.

Use a new version tag for each release. Replace `COMMIT_SHA` with the tested workflow's full commit SHA.
Keep release notes in a local text file. List platform test results and known limitations.

```powershell
gh release create v0.7.0-fhg.1 --repo foxhollowgames/3d-movie-maker-modern --target COMMIT_SHA --title '3D Movie Maker Modern 0.7.0-fhg.1' --notes-file out/release-notes.md --draft
$assets = Get-ChildItem out/release -File | Where-Object { $_.Name -match '\.(zip|sha256)$' }
gh release upload v0.7.0-fhg.1 @($assets.FullName) --repo foxhollowgames/3d-movie-maker-modern
gh release edit v0.7.0-fhg.1 --repo foxhollowgames/3d-movie-maker-modern --draft=false --latest
```

Never reuse archives from an earlier commit after changing application source.
Linux CI output depends on system libraries and is not distributed as a portable binary.

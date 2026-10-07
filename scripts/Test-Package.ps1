param(
    [Parameter(Mandatory)] [string] $Path,
    [ValidateSet('Windows', 'macOS', 'Linux')] [string] $Platform = 'Windows'
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $Path).Path
$resources = $root
$required = @('LICENSE', 'THIRD_PARTY_LICENSES.txt', 'QUICKSTART.txt')
switch ($Platform) {
    'Windows' { $required += @('3dmovie.exe', 'Start 3D Movie Maker.cmd') }
    'Linux' { $required += '3dmovie' }
    'macOS' {
        $required += '3D Movie Maker.app/Contents/MacOS/3D Movie Maker'
        $resources = Join-Path $root '3D Movie Maker.app/Contents/Resources'
    }
}
foreach ($file in $required) {
    $item = Get-Item -LiteralPath (Join-Path $root $file)
    if ($item.Length -eq 0) { throw "Empty package file: $file" }
}
$content = Join-Path $resources 'Microsoft Kids/3D Movie Maker'
foreach ($file in @('3dmovie.chk', 'studio.chk', 'building.chk', 'bldghd.chk',
                    'help.chk', 'helpaud.chk', 'sharecd.chk', 'shared.chk',
                    'tmpls.3cn', 'bkgds.3cn', 'mtrls.3cn', 'snds.3cn', 'tdfs.3cn')) {
    $item = Get-Item -LiteralPath (Join-Path $content $file.ToLowerInvariant())
    if ($item.Length -eq 0) { throw "Empty content file: $file" }
}
foreach ($user in @('McZee', 'Melanie')) {
    $movies = @(Get-ChildItem -LiteralPath (Join-Path $resources "Microsoft Kids/Users/$user") -Filter '*.3mm')
    if ($movies.Count -eq 0) { throw "No movies found for $user" }
}
Write-Output "Package verified: $Platform. Executable, licenses, content, and sample movies are present."

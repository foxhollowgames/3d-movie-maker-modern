@echo off
setlocal
pushd "%~dp0"
if not exist "3dmovie.exe" goto missing
if not exist "Microsoft Kids\3D Movie Maker\3dmovie.chk" goto missing
start "" "3dmovie.exe" %*
popd
exit /b 0
:missing
echo The application files are missing. Extract the complete release ZIP first.
pause
popd
exit /b 1

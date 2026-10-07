@echo off
rem Run in the caller's environment so compiler variables survive this script.
set "THREEDMM_VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%THREEDMM_VSWHERE%" (
    echo Visual Studio Installer vswhere.exe was not found. 1>&2
    exit /b 1
)
set "THREEDMM_VS_INSTALL="
for /f "usebackq tokens=*" %%i in (`"%THREEDMM_VSWHERE%" -latest -products * -property installationPath`) do set "THREEDMM_VS_INSTALL=%%i"
if not exist "%THREEDMM_VS_INSTALL%\VC\Auxiliary\Build\vcvarsall.bat" (
    echo Visual Studio C++ build tools were not found. 1>&2
    exit /b 1
)
call "%THREEDMM_VS_INSTALL%\VC\Auxiliary\Build\vcvarsall.bat" %*
exit /b %errorlevel%

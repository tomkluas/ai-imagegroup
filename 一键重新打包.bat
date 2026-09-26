@echo off
setlocal EnableExtensions
title ImageGroup - Build and Package

cd /d "%~dp0"
if errorlevel 1 goto :failed

echo ============================================================
echo ImageGroup - Test, build, and publish
echo Project: %CD%
echo ============================================================
echo.

where uv >nul 2>&1
if errorlevel 1 (
    echo [ERROR] uv was not found.
    echo Install uv, then run this file again:
    echo https://docs.astral.sh/uv/getting-started/installation/
    set "BUILD_EXIT_CODE=1"
    goto :failed_with_code
)

echo [1/6] Syncing development dependencies...
call uv sync --extra dev
if errorlevel 1 goto :failed

echo.
echo [2/6] Running automated tests...
call uv run --extra dev pytest -q --basetemp .tmp\pytest-build
if errorlevel 1 goto :failed

echo.
echo [3/6] Checking code style...
call uv run --extra dev ruff check src tests
if errorlevel 1 goto :failed

echo.
echo [4/6] Building the single-file EXE...
call uv run --extra dev pyinstaller --noconfirm --clean packaging\ImageGroup.spec
if errorlevel 1 goto :failed

for %%F in ("dist\*.exe") do set "BUILT_EXE=%%~fF"
if not defined BUILT_EXE (
    echo [ERROR] PyInstaller finished without producing an EXE.
    set "BUILD_EXIT_CODE=1"
    goto :failed_with_code
)
for %%F in ("%BUILT_EXE%") do set "PUBLISHED_EXE=releases\%%~nxF"

echo.
echo [5/6] Updating the releases directory...
if not exist "releases" mkdir "releases"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Copy-Item -LiteralPath $env:BUILT_EXE -Destination 'releases' -Force"
if errorlevel 1 goto :failed

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$exe = Join-Path 'releases' ([IO.Path]::GetFileName($env:BUILT_EXE)); if (Test-Path -LiteralPath 'releases\ImageGroup-portable-win64.zip') { Remove-Item -LiteralPath 'releases\ImageGroup-portable-win64.zip' -Force }; Compress-Archive -LiteralPath $exe -DestinationPath 'releases\ImageGroup-portable-win64.zip' -CompressionLevel Optimal"
if errorlevel 1 goto :failed

echo.
echo [6/6] Calculating SHA256 checksums...
echo EXE:
certutil.exe -hashfile "%PUBLISHED_EXE%" SHA256
if errorlevel 1 goto :failed
echo ZIP:
certutil.exe -hashfile "releases\ImageGroup-portable-win64.zip" SHA256
if errorlevel 1 goto :failed

echo.
echo ============================================================
echo BUILD SUCCEEDED.
echo Output directory: %CD%\releases
echo ============================================================
if not defined IMAGEGROUP_NO_PAUSE pause
exit /b 0

:failed
set "BUILD_EXIT_CODE=%ERRORLEVEL%"
if "%BUILD_EXIT_CODE%"=="0" set "BUILD_EXIT_CODE=1"

:failed_with_code
echo.
echo ============================================================
echo [FAILED] Build did not complete. Review the last error above.
echo Exit code: %BUILD_EXIT_CODE%
echo ============================================================
if not defined IMAGEGROUP_NO_PAUSE pause
exit /b %BUILD_EXIT_CODE%

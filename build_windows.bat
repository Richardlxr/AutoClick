@echo off
setlocal
cd /d "%~dp0"

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist package rmdir /s /q package
if exist ClickMacro.spec del ClickMacro.spec

py -3 -m venv .venv-build
if errorlevel 1 goto :error

call .venv-build\Scripts\activate.bat
if errorlevel 1 goto :error

python -m pip install --upgrade pip
if errorlevel 1 goto :error

python -m pip install pyinstaller
if errorlevel 1 goto :error

python -m PyInstaller --noconfirm --clean --onefile --windowed --name ClickMacro app.py
if errorlevel 1 goto :error

mkdir package\ClickMacro
copy dist\ClickMacro.exe package\ClickMacro\ClickMacro.exe
copy README.md package\ClickMacro\README.md

powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path package\ClickMacro -DestinationPath ClickMacro-windows.zip -Force"
if errorlevel 1 goto :error

echo.
echo Built ClickMacro-windows.zip
exit /b 0

:error
echo.
echo Build failed.
pause
exit /b 1

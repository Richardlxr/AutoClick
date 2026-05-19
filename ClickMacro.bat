@echo off
setlocal
cd /d "%~dp0"
python app.py
if errorlevel 1 (
  echo.
  echo Click Macro exited with an error.
  pause
)

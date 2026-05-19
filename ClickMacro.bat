@echo off
setlocal
cd /d "%~dp0"
python app.py
if errorlevel 1 (
  echo.
  echo 自动点击器运行出错。
  pause
)

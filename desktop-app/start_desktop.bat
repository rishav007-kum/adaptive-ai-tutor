@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0desktop\start_desktop.ps1"
if errorlevel 1 (
  echo.
  echo Desktop setup or startup failed. See the message above.
  pause
)

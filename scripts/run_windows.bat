@echo off
setlocal
if not exist .venv\Scripts\python.exe (
  echo Missing .venv. Run powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1 first.
  exit /b 1
)
.venv\Scripts\python.exe app.py

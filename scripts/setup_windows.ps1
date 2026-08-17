$ErrorActionPreference = "Stop"

$python = Get-Command py -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Python launcher 'py' not found. Install Python 3.12 from python.org first."
    exit 1
}

py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m realistic_dance_avatar.cli download-model

Write-Host "Setup complete. Run scripts\run_windows.bat"

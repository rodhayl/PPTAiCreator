$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$venv = ".\.venv"
$pythonCmd = "python"
if (-Not (Get-Command python -ErrorAction SilentlyContinue)) {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py -3"
  } else {
    Write-Error "Python launcher not found. Install Python 3.11+ and ensure python or py is available."
    exit 1
  }
}

if (Test-Path $venv) {
  if (-Not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Remove-Item -Recurse -Force $venv
  }
}

if (-Not (Test-Path $venv)) {
  Invoke-Expression "$pythonCmd -m venv $venv"
}
if (-Not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Error "Virtual environment creation failed. Check Python installation."
    exit 1
}
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
pip install -e .

# Create .env if missing
if (-Not (Test-Path ".\.env")) {
  @"
MODE=offline
DB_PATH=checkpoints.db
OLLAMA_BASE=http://localhost:11434/v1
OPENROUTER_BASE=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=
"@ | Out-File -Encoding utf8 ".\.env"
}

Write-Host "Environment ready. To run GUI: powershell -ExecutionPolicy Bypass -File .\scripts\run_gui.ps1"

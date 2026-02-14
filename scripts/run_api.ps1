$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$activatePath = Join-Path $repoRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $activatePath) {
	& $activatePath
}

$env:MODE = "offline"
python -m uvicorn src.server:app --host 127.0.0.1 --port 8000

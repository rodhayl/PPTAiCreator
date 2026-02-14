$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$activatePath = Join-Path $repoRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $activatePath) {
	& $activatePath
}

$env:MODE = "offline"
python -m streamlit run "src\app.py" --server.headless=true --browser.gatherUsageStats=false

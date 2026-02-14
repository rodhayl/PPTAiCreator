$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$activatePath = Join-Path $repoRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $activatePath) {
	& $activatePath
}

python -m ruff check --fix .
python -m black .

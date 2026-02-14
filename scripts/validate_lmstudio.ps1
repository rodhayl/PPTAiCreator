param(
	[string]$BaseUrl = "http://127.0.0.1:1234/v1",
	[string]$Model = "gpt-oss-20b"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-Not (Test-Path $python)) {
	Write-Error "Virtual environment not found at .venv. Run scripts/dev.ps1 first."
	exit 1
}

$modelsUrl = "$BaseUrl/models"
try {
	$models = Invoke-RestMethod -Uri $modelsUrl -Method Get -TimeoutSec 10
} catch {
	Write-Error "Cannot reach LM Studio endpoint at $modelsUrl"
	exit 1
}

if (-Not $models.data) {
	Write-Error "No models were returned from LM Studio endpoint $modelsUrl"
	exit 1
}

$available = @($models.data | ForEach-Object { $_.id })
Write-Host "LM Studio models:" -ForegroundColor Cyan
$available | ForEach-Object { Write-Host "  - $_" }

if ($available -notcontains $Model) {
	Write-Warning "Requested model '$Model' not listed by LM Studio. Continuing anyway."
}

$env:RUN_REAL_AI_TESTS = "true"
$env:SKIP_OPENROUTER_TESTS = "false"
$env:OPENROUTER_BASE_URL = $BaseUrl
$env:OPENROUTER_MODEL = $Model
$env:OPENROUTER_API_KEY = "lmstudio-local"

Write-Host "Running real-model validation against LM Studio..." -ForegroundColor Cyan

& $python -m pytest tests\e2e\test_real_models_e2e.py::TestOpenRouterE2E::test_full_pipeline_openrouter_free -q
if ($LASTEXITCODE -ne 0) {
	Write-Error "LM Studio validation failed for test_full_pipeline_openrouter_free"
	exit $LASTEXITCODE
}

& $python -m pytest tests\e2e\test_real_models_e2e.py::TestOpenRouterE2E::test_langgraph_openrouter -q
if ($LASTEXITCODE -ne 0) {
	Write-Error "LM Studio validation failed for test_langgraph_openrouter"
	exit $LASTEXITCODE
}

Write-Host "LM Studio validation passed for standard + LangGraph pipelines." -ForegroundColor Green

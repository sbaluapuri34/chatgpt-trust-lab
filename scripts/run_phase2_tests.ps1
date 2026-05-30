# Run Phase 2 unit tests (requires Python 3.11+)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    $py = "python"
}

& $py -m pytest tests/phase2 -v

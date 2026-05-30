# Phase 3 tests: offline unit tests + live Groq/Gemini integration (requires .env keys)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

Write-Host "=== Offline tests (mock) ==="
& $py -m pytest tests/phase3 -v -m "not integration"

Write-Host ""
Write-Host "=== Live LLM integration tests (Groq + Gemini) ==="
& $py -m pytest tests/phase3 -v -m integration

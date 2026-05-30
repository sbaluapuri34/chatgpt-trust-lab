# Standard pipeline entry — starts at Phase 2 (never collects Reddit data).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

Write-Host "PHASE_1_LOCKED=TRUE — using authoritative dataset posts_20260529.json"
Write-Host ""

Write-Host "=== Phase 2: ingest + preprocess + select ==="
& $py scripts/ingest.py
& $py -m phase2.preprocess
& $py -m phase2.select_candidates

Write-Host ""
Write-Host "=== Phase 3: LLM relevance + deep analysis (Groq) ==="
& $py scripts/run_relevance.py
& $py scripts/run_deep_analysis.py

Write-Host ""
Write-Host "Done. Phase 4 (aggregate) and Phase 5 (dashboard) are not yet automated in this script."

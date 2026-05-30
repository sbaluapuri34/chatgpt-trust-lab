# Preserve locked Phase 1 dataset and key documentation (read-only copy).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$dest = Join-Path $Root "data\backups\phase1_locked\$stamp"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$files = @(
    "data\raw\posts_20260529.json",
    "data\raw\collection_manifest.json",
    "docs\VALIDATION_REPORT.md",
    "docs\RECALL_ANALYSIS.md",
    "docs\DEPLOYMENT_GUIDE.md",
    "docs\PHASE_1_CHECKPOINT.md",
    "project_state.yaml"
)

foreach ($rel in $files) {
    $src = Join-Path $Root $rel
    if (Test-Path $src) {
        $targetDir = Join-Path $dest (Split-Path $rel -Parent)
        New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
        Copy-Item $src (Join-Path $dest $rel) -Force
        Write-Host "Backed up $rel"
    } else {
        Write-Warning "Missing: $rel"
    }
}

Write-Host "Phase 1 backup complete: $dest"

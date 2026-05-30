# Run Phase 1 unit tests (requires Python 3.11+)
Set-Location $PSScriptRoot\..

if (Get-Command python -ErrorAction SilentlyContinue) {
    $py = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $py = "py"
} else {
    Write-Error "Python not found. Install from https://www.python.org/downloads/"
    exit 1
}

& $py -m pip install -r requirements.txt -q
& $py -m pytest tests/phase1 -v -m "not integration"
exit $LASTEXITCODE

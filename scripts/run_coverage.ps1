# Ejecuta la suite de tests con cobertura y el gate (fail_under=75 en pyproject).
# Uso:  pwsh -File scripts/run_coverage.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
Write-Host "Running pytest + coverage en $root"
python -m pytest tests `
    --cov=dxfstructuraljm `
    --cov-report=term-missing `
    --cov-report=html:htmlcov
exit $LASTEXITCODE

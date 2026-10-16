[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$python = Join-Path $repoRoot 'backend\.venv\Scripts\python.exe'
$oldBytecode = $env:PYTHONDONTWRITEBYTECODE
$oldTelemetry = $env:NEXT_TELEMETRY_DISABLED
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:NEXT_TELEMETRY_DISABLED = '1'
Push-Location $repoRoot
try {
    & (Join-Path $PSScriptRoot 'Test-Mailbox.ps1')
    & $python -B scripts/verification/check_base001.py
    if ($LASTEXITCODE -ne 0) { throw 'Historical source reference changed.' }
    & $python -B -m unittest discover -s scripts/verification/tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Reference integrity regression tests failed.' }
    & $python -B -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Historical tests failed.' }
    & node --check script.js
    if ($LASTEXITCODE -ne 0) { throw 'Historical script.js syntax failed.' }
    & node --check admin.js
    if ($LASTEXITCODE -ne 0) { throw 'Historical admin.js syntax failed.' }
    & $python -B scripts/verification/verify_core_database.py --check-test-access
    if ($LASTEXITCODE -ne 0) { throw 'Actual PostgreSQL verification failed.' }
    & $python -B backend/manage.py check
    if ($LASTEXITCODE -ne 0) { throw 'Django check failed.' }
    & $python -B backend/manage.py makemigrations --check --dry-run --settings=config.settings.migration
    if ($LASTEXITCODE -ne 0) { throw 'Uncommitted Django model migration required.' }
    # Working directory is intentional: avoid discovering root legacy tests twice.
    Push-Location (Join-Path $repoRoot 'backend')
    try {
        & $python -B manage.py test tests --settings=config.settings.test --noinput --verbosity 2
        if ($LASTEXITCODE -ne 0) { throw 'Django foundation tests failed.' }
    } finally { Pop-Location }
    & npm.cmd run test:contracts
    if ($LASTEXITCODE -ne 0) { throw 'Frontend health contracts failed.' }
    & npm.cmd run test:auth
    if ($LASTEXITCODE -ne 0) { throw 'Frontend authentication client tests failed.' }
    & npm.cmd run typecheck
    if ($LASTEXITCODE -ne 0) { throw 'TypeScript check failed.' }
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Studio build failed.' }
    Write-Host 'Foundation checks passed. No production or Windows-native claim follows automatically.'
} finally {
    Pop-Location
    $env:PYTHONDONTWRITEBYTECODE = $oldBytecode
    $env:NEXT_TELEMETRY_DISABLED = $oldTelemetry
}

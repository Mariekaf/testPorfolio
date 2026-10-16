[CmdletBinding()]
param([string]$AdminUser = 'postgres')
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$python = Join-Path $repoRoot 'backend\.venv\Scripts\python.exe'
$configPath = Join-Path $repoRoot 'infra\env\development.local.json'
if (-not (Test-Path -LiteralPath $configPath)) { throw 'Run Initialize-Development.ps1 first.' }
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
Push-Location $repoRoot
try {
    if ($config.database_mode -eq 'docker') {
        & docker compose --env-file infra/env/development.local.env -f infra/compose.yaml up -d --wait postgres
        if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL Docker startup failed.' }
    } elseif ($config.database_mode -eq 'native') {
        $reachable = Test-NetConnection -ComputerName $config.database.host -Port $config.database.port -WarningAction SilentlyContinue
        if (-not $reachable.TcpTestSucceeded) { throw 'Native PostgreSQL is not listening on the configured local port.' }
    } else { throw 'Unknown database mode; no action performed.' }
    & $python -B scripts/development/provision_database.py --admin-user $AdminUser
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL provisioning failed.' }
    & $python -B backend/manage.py migrate --settings=config.settings.migration --noinput
    if ($LASTEXITCODE -ne 0) { throw 'Django migrations failed.' }
    & $python -B scripts/verification/verify_core_database.py
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL runtime verification failed.' }
} finally { Pop-Location }

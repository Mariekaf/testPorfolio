[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$python = Join-Path $repoRoot 'backend\.venv\Scripts\python.exe'
Push-Location $repoRoot
try {
    & (Join-Path $PSScriptRoot "Initialize-Mailbox.ps1")
    & $python -B backend/manage.py runserver 127.0.0.1:8001
    if ($LASTEXITCODE -ne 0) { throw 'Backend stopped with an error.' }
} finally { Pop-Location }

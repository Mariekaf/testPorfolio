[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$python = Join-Path $repoRoot 'backend\.venv\Scripts\python.exe'
Push-Location $repoRoot
try {
    & $python -B scripts/development/prepare_tpl001_cd_validation.py
    if ($LASTEXITCODE -ne 0) { throw 'Validation configuration preparation failed.' }
    $path = Join-Path $repoRoot 'infra\env\tpl001-cd.validation.local.json'
    $acl = [System.Security.AccessControl.FileSecurity]::new()
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($sid in @([System.Security.Principal.WindowsIdentity]::GetCurrent().User,
                      [System.Security.Principal.SecurityIdentifier]::new('S-1-5-18'))) {
        $acl.AddAccessRule([System.Security.AccessControl.FileSystemAccessRule]::new($sid, 'FullControl', 'Allow'))
    }
    [System.IO.FileInfo]::new($path).SetAccessControl($acl)
    Write-Host 'Private validation configuration ready. Database creation and migrations are separate explicit steps.'
} finally { Pop-Location }

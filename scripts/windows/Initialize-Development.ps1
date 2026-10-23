[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('native', 'docker')]
    [string]$DatabaseMode,
    [ValidateRange(1024, 65535)]
    [int]$Port = 5433
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$python = Join-Path $repoRoot 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Create backend\.venv with Python 3.13 first.' }
Push-Location $repoRoot
try {
    & $python -B scripts/development/initialize_development.py --mode $DatabaseMode --port $Port
    if ($LASTEXITCODE -ne 0) { throw 'Local initialization failed; existing settings preserved.' }
    # chmod on Windows is not a complete ACL boundary. Restrict only generated files.
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
    $system = [System.Security.Principal.SecurityIdentifier]::new('S-1-5-18')
    foreach ($name in @('development.local.json', 'development.local.env')) {
        $privateFile = Join-Path $repoRoot ('infra\env\' + $name)
        if (Test-Path -LiteralPath $privateFile) {
            $acl = [System.Security.AccessControl.FileSecurity]::new()
            $acl.SetAccessRuleProtection($true, $false)
            $acl.AddAccessRule([System.Security.AccessControl.FileSystemAccessRule]::new($identity, 'FullControl', 'Allow'))
            $acl.AddAccessRule([System.Security.AccessControl.FileSystemAccessRule]::new($system, 'FullControl', 'Allow'))
            Set-Acl -LiteralPath $privateFile -AclObject $acl
        }
    }
} finally { Pop-Location }

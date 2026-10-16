[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$mailbox = Join-Path $repoRoot 'infra\mailbox'
if ($env:SAAS_MAILBOX_PATH) { $mailbox = $env:SAAS_MAILBOX_PATH }
if (-not (Test-Path -LiteralPath $mailbox)) { New-Item -ItemType Directory -Path $mailbox | Out-Null }
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$system = [System.Security.Principal.SecurityIdentifier]::new('S-1-5-18')
$acl = [System.Security.AccessControl.DirectorySecurity]::new()
$acl.SetAccessRuleProtection($true, $false)
foreach ($sid in @($identity, $system)) {
    $acl.AddAccessRule([System.Security.AccessControl.FileSystemAccessRule]::new(
        $sid, 'FullControl', 'ContainerInherit, ObjectInherit', 'None', 'Allow'))
}
# Windows PowerShell 5.1 Set-Acl can attempt to persist audit information
# (SACL), requiring SeSecurityPrivilege. The .NET setter persists only the
# modified access section (DACL); owner/group/audit sections are untouched.
[System.IO.DirectoryInfo]::new($mailbox).SetAccessControl($acl)
# Restrict existing files as well; never display mail content.
Get-ChildItem -LiteralPath $mailbox -File | ForEach-Object {
    $fileAcl = [System.Security.AccessControl.FileSecurity]::new()
    $fileAcl.SetAccessRuleProtection($true, $false)
    foreach ($sid in @($identity, $system)) {
        $fileAcl.AddAccessRule([System.Security.AccessControl.FileSystemAccessRule]::new($sid, 'FullControl', 'Allow'))
    }
    [System.IO.FileInfo]::new($_.FullName).SetAccessControl($fileAcl)
}
Write-Host 'Private mailbox ACL configured. No message content displayed.'

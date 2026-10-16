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
Set-Acl -LiteralPath $mailbox -AclObject $acl
# Refuse existing files with explicit unrelated ACLs; never expose mail content.
Get-ChildItem -LiteralPath $mailbox -File | ForEach-Object {
    $fileAcl = [System.Security.AccessControl.FileSecurity]::new()
    $fileAcl.SetAccessRuleProtection($true, $false)
    foreach ($sid in @($identity, $system)) {
        $fileAcl.AddAccessRule([System.Security.AccessControl.FileSystemAccessRule]::new($sid, 'FullControl', 'Allow'))
    }
    Set-Acl -LiteralPath $_.FullName -AclObject $fileAcl
}
Write-Host 'Private mailbox ACL configured. No message content displayed.'

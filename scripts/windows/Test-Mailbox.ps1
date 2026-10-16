[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$previousMailbox = $env:SAAS_MAILBOX_PATH
$temporaryMailbox = Join-Path ([System.IO.Path]::GetTempPath()) ('portfolio-mailbox-check-' + [guid]::NewGuid().ToString('N'))
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$expected = @($currentUser, 'S-1-5-18')
$accessSection = [System.Security.AccessControl.AccessControlSections]::Access

function Assert-PrivateAccess($security) {
    $rules = @($security.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]))
    if ($rules.Count -ne 2) { throw 'Unexpected number of private mailbox access rules.' }
    foreach ($rule in $rules) {
        if ($rule.IdentityReference.Value -notin $expected -or
            $rule.AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow -or
            $rule.FileSystemRights -ne [System.Security.AccessControl.FileSystemRights]::FullControl) {
            throw 'Unexpected private mailbox permissions.'
        }
    }
    foreach ($sid in $expected) {
        if (@($rules | Where-Object { $_.IdentityReference.Value -eq $sid }).Count -ne 1) {
            throw 'Required private mailbox access rule missing.'
        }
    }
}

try {
    $env:SAAS_MAILBOX_PATH = $temporaryMailbox
    # First initialization, inherited permissions for a new synthetic file,
    # then repeat initialization to exercise existing-file and directory ACLs.
    & (Join-Path $PSScriptRoot 'Initialize-Mailbox.ps1')
    $folder = [System.IO.DirectoryInfo]::new($temporaryMailbox)
    $security = $folder.GetAccessControl($accessSection)
    if (-not $security.AreAccessRulesProtected) { throw 'Directory ACL inheritance must be disabled.' }
    Assert-PrivateAccess $security
    $probePath = Join-Path $temporaryMailbox 'synthetic-permission-check.txt'
    [System.IO.File]::WriteAllText($probePath, 'Synthetic permission check only.')
    $probe = [System.IO.FileInfo]::new($probePath)
    Assert-PrivateAccess ($probe.GetAccessControl($accessSection))
    & (Join-Path $PSScriptRoot 'Initialize-Mailbox.ps1')
    $security = $probe.GetAccessControl($accessSection)
    if (-not $security.AreAccessRulesProtected) { throw 'Existing file ACL inheritance must be disabled.' }
    Assert-PrivateAccess $security
    if ([System.IO.File]::ReadAllText($probePath) -ne 'Synthetic permission check only.') {
        throw 'Synthetic file content changed.'
    }
    Write-Host 'Private mailbox regression checks passed: first/repeated initialization, inherited/restricted file ACLs, content preserved.'
} finally {
    $env:SAAS_MAILBOX_PATH = $previousMailbox
    if (Test-Path -LiteralPath $temporaryMailbox) {
        Remove-Item -LiteralPath $temporaryMailbox -Recurse -Force
    }
}

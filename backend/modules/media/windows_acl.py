"""DACL inspection only: no SACL access, ACL mutation or optional dependency."""
import base64
import json
import os
import re
import subprocess

# CPython 3.13 mkdir(0700) uses OW, not the concrete owner's SID.
# OW is OWNER RIGHTS (S-1-3-4), not CREATOR OWNER (S-1-3-0).
OWNER_RIGHTS = 'S-1-3-4'
TRUSTED_SYSTEM = frozenset({'S-1-5-18', 'S-1-5-32-544'})

INSPECT_DACL = r"""
$ErrorActionPreference='Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$acl=Get-Acl -LiteralPath $env:MEDIA001_ACL_PATH
$raw=[System.Security.AccessControl.RawSecurityDescriptor]::new($acl.GetSecurityDescriptorBinaryForm(),0)
$allow=@($acl.GetAccessRules($true,$true,[System.Security.Principal.SecurityIdentifier]) | Where-Object { $_.AccessControlType -eq 'Allow' } | ForEach-Object { $_.IdentityReference.Value })
[ordered]@{
 current_sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
 owner_sid=$acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value
 dacl_present=($null -ne $raw.DiscretionaryAcl)
 allow_sids=@($allow)
} | ConvertTo-Json -Compress -Depth 3
"""


def acl_is_private(report):
    """Fail closed; an owner-relative ACE is safe only for a trusted owner."""
    if not isinstance(report, dict) or set(report) != {'current_sid', 'owner_sid', 'dacl_present', 'allow_sids'}:
        return False
    current, owner = report['current_sid'], report['owner_sid']
    if not isinstance(current, str) or re.fullmatch(r'S-1-(?:[0-9]+-)*[0-9]+', current) is None:
        return False
    trusted = TRUSTED_SYSTEM | {current}
    if not isinstance(owner, str) or owner not in trusted or report['dacl_present'] is not True:
        return False
    entries = report['allow_sids']
    return (isinstance(entries, list) and bool(entries)
            and all(isinstance(sid, str) and sid in trusted | {OWNER_RIGHTS} for sid in entries))


def inspect_private_acl(root):
    # EncodedCommand avoids command-line quoting and non-ASCII path interpolation.
    encoded = base64.b64encode(INSPECT_DACL.encode('utf-16-le')).decode('ascii')
    env = os.environ.copy()
    env['MEDIA001_ACL_PATH'] = os.fspath(root)
    result = subprocess.run(
        ['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
        env=env, capture_output=True, encoding='utf-8', errors='strict', timeout=10,
    )
    if result.returncode != 0:
        raise OSError('Windows DACL inspection failed')
    try:
        report = json.loads(result.stdout)
    except (ValueError, TypeError) as exc:
        raise OSError('Invalid Windows DACL inspection result') from exc
    if not acl_is_private(report):
        raise OSError('Windows DACL is not private')

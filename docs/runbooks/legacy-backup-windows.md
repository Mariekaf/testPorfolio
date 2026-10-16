# Sauvegarde privée du CMS historique — Windows PowerShell

Procédure destinée au propriétaire sur son ordinateur. **Elle est documentée, pas exécutée par BASE-001 sur les données de l'utilisateur.** Aucune source réelle, archive privée ou authentification ne doit être jointe à une PR ou committée.

## 1. Trouver la source et arrêter les écritures

Dans le terminal ayant servi à lancer le CMS, arrêter le serveur avec Ctrl+C. Fermer les autres instances qui utilisent les mêmes données. Ne pas terminer des processus Python inconnus. Les exportations faites pendant les écritures ne constituent pas une sauvegarde à froid cohérente.

Depuis le dossier contenant server.py :

```powershell
$ErrorActionPreference = 'Stop'
$repoRoot = (Get-Location).Path
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot 'server.py'))) {
    throw 'Se placer dans le dossier du CMS.'
}
if ([string]::IsNullOrWhiteSpace($env:PORTFOLIO_DATA_DIR)) {
    $sourceData = [IO.Path]::GetFullPath((Join-Path $repoRoot '.local'))
} else {
    $sourceData = [IO.Path]::GetFullPath($env:PORTFOLIO_DATA_DIR)
}
if (-not (Test-Path -LiteralPath (Join-Path $sourceData 'content.json'))) {
    throw 'Source non identifiée : ne pas lancer le serveur pour la recréer.'
}
```

Une variable définie dans un autre terminal n'est pas nécessairement visible ici : confirmer le chemin réellement utilisé à l'époque. Ne pas rechercher ou afficher les valeurs de secrets. Repérer aussi les exports JSON/ZIP enregistrés ailleurs et les installations multiples ; ne pas les fusionner automatiquement.

## 2. Choisir un emplacement privé hors dépôt

Choisir un volume privé, idéalement chiffré et non partagé/synchronisé publiquement. Exemple à adapter :

```powershell
$backupRoot = Join-Path $env:LOCALAPPDATA 'PortfolioPrivateBackups'
$backupRoot = [IO.Path]::GetFullPath($backupRoot)
$separator = [IO.Path]::DirectorySeparatorChar
$sourcePrefix = $sourceData.TrimEnd($separator) + $separator
$repoPrefix = $repoRoot.TrimEnd($separator) + $separator
if ($backupRoot.Equals($sourceData, [StringComparison]::OrdinalIgnoreCase) -or
    $backupRoot.StartsWith($sourcePrefix, [StringComparison]::OrdinalIgnoreCase) -or
    $backupRoot.Equals($repoRoot, [StringComparison]::OrdinalIgnoreCase) -or
    $backupRoot.StartsWith($repoPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'La sauvegarde doit être hors des données et du dépôt.'
}
$backupPath = Join-Path $backupRoot ('legacy-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N'))
$copiedData = Join-Path $backupPath 'data'
New-Item -ItemType Directory -Path $copiedData | Out-Null
```

Cette copie complète inclut potentiellement auth.json et initial-password.txt. La garder privée ; ne pas lire leur contenu dans des captures, logs ou transcriptions. Les permissions POSIX du CMS ne suffisent pas à protéger une copie Windows : vérifier les ACL du dossier privé et le chiffrement avec les outils Windows. Un ZIP standard n'est pas chiffré.

## 3. Copier tous les fichiers et vérifier leurs empreintes

Ne pas se limiter aux images référencées. Préserver les sous-dossiers vides, médias orphelins et sauvegardes précédentes. Ne pas suivre des liens vers d'autres emplacements : si des liens/reparse points existent, arrêter et inventorier leurs cibles séparément.

```powershell
$items = @(Get-Item -LiteralPath $sourceData -Force) + @(Get-ChildItem -LiteralPath $sourceData -Recurse -Force)
if ($items | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) {
    throw 'Lien ou reparse point détecté : traitement manuel requis.'
}
function Get-PrivateManifest([string]$rootPath) {
    $prefix = $rootPath.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    @(Get-ChildItem -LiteralPath $rootPath -Recurse -Force -File |
        Sort-Object FullName | ForEach-Object {
            [pscustomobject]@{
                path = $_.FullName.Substring($prefix.Length).Replace('\', '/')
                bytes = $_.Length
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
            }
        })
}
$before = @(Get-PrivateManifest $sourceData)
Get-ChildItem -LiteralPath $sourceData -Force |
    Copy-Item -Destination $copiedData -Recurse -Force
$after = @(Get-PrivateManifest $sourceData)
$copied = @(Get-PrivateManifest $copiedData)
$beforeJson = ConvertTo-Json -InputObject $before -Depth 5 -Compress
if ($beforeJson -cne (ConvertTo-Json -InputObject $after -Depth 5 -Compress) -or
    $beforeJson -cne (ConvertTo-Json -InputObject $copied -Depth 5 -Compress)) {
    throw 'Source modifiée pendant la copie ou copie différente. Conserver les originaux, enquêter avant de recommencer.'
}
$utf8 = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $backupPath 'manifest.private.json'),
    (ConvertTo-Json -InputObject $copied -Depth 5), $utf8)
Write-Host 'Copie privée vérifiée par SHA-256. Aucune donnée source supprimée.'
```

Le manifeste privé contient des noms de fichiers et empreintes sensibles : il reste avec la sauvegarde hors Git. La vérification par fichier ne prouve pas à elle seule qu'une sauvegarde se restaure ; suivre l'étape suivante. Vérifier également les dossiers vides si leur présence a une signification locale.

## 4. Vérifier une restauration isolée

Dupliquer la sauvegarde dans un **autre dossier de test privé neuf**, jamais dans la source d'origine. Ce dossier sera modifié par les essais. Définir `PORTFOLIO_DATA_DIR` pour le seul processus de test et choisir un port libre, par exemple 8010. Dans un terminal dédié :

```powershell
# Remplacer par un NOUVEAU chemin privé après y avoir copié backup/data.
$restoreData = 'D:\PrivatePortfolioRestore\data'
if (-not (Test-Path -LiteralPath (Join-Path $restoreData 'content.json'))) {
    throw 'Copie de restauration absente : ne pas initialiser une source vide.'
}
$previousDataDir = $env:PORTFOLIO_DATA_DIR
try {
    $env:PORTFOLIO_DATA_DIR = $restoreData
    py -X utf8 -B .\server.py --host 127.0.0.1 --port 8010
} finally {
    $env:PORTFOLIO_DATA_DIR = $previousDataDir
}
```

Ouvrir localement le site et /admin, vérifier textes, ordre, thèmes, projets publiés/brouillons, couvertures et sections. Utiliser les identifiants localement, sans les transmettre. Si une réinitialisation est nécessaire, elle concerne uniquement la copie de restauration, jamais la sauvegarde maître. Arrêter avec Ctrl+C, noter hors Git résultat/date/version du CMS. Conserver source et sauvegarde maître intactes.

Reprendre le serveur d'origine uniquement après confirmation de son chemin de données initial. Aucune étape ne demande de supprimer `.local/`, d'écraser la source ou de pousser les médias privés sur GitHub.

## 5. Différences entre les sauvegardes

| Méthode | Inclut | N'inclut pas / limites |
|---|---|---|
| Export JSON de l'UI | Contenu en mémoire, modifications non sauvegardées comprises | Fichiers images, auth, version précédente |
| Export ZIP de l'UI | Contenu enregistré + fichiers uploads, orphelins compris | Auth, sauvegarde précédente, changements non sauvegardés ; pas de chiffrement |
| Copie privée complète à froid | Tous les fichiers/dossiers de la source réelle | Médias externes et exports situés ailleurs à inventorier séparément |

Une archive d'interface peut contenir des données personnelles même sans auth : elle n'est pas une fixture publique. Ne télécharger aucune URL externe automatiquement. BASE-001 fournit une procédure ; la sauvegarde et la restauration sur le PC restent à réaliser par son propriétaire avant une future migration.

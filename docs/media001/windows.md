# MEDIA-001 — Validation Windows native, sans Docker

**Non exécutée sous Windows par l'agent.** E.07.04 est accepté MVP selon votre
validation Windows (deux tests ignorés). Cette preuve n'est pas une validation
Windows de MEDIA-001. Le lecteur d'écran reste ouvert.

Python3.13, Node24/npm11 et PostgreSQL17 natif sont nécessaires. Ne pas utiliser
Initialize-Database, migrate ou Test-Foundations sur votre configuration habituelle.
Ne pas choisir un ancien cluster ni un stockage personnel. Le runner ci-dessous
crée lui-même les deux ressources temporaires et les supprime dans finally.

## Récupérer et installer les dépendances verrouillées

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
if (git status --porcelain) { throw 'Préserver les modifications locales avant de changer de branche.' }
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'Fetch failed.' }
git switch feature/media-001
if ($LASTEXITCODE -ne 0) { throw 'Switch failed.' }
git pull --ff-only origin feature/media-001
if ($LASTEXITCODE -ne 0) { throw 'Pull failed.' }
git log -1 --format="%H %s"
py -3.13 --version
node --version
& 'C:\Program Files\PostgreSQL\17\bin\initdb.exe' --version
& .\backend\.venv\Scripts\python.exe -m pip install --require-hashes -r .\backend\requirements\development.txt
if ($LASTEXITCODE -ne 0) { throw 'Hashed Python installation failed.' }
& .\backend\.venv\Scripts\python.exe -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Python dependency check failed.' }
& .\backend\.venv\Scripts\python.exe -c "from PIL import Image,features; print('Pillow',Image.__version__,'WebP',features.check('webp')); assert features.check('webp')"
if ($LASTEXITCODE -ne 0) { throw 'WebP codec unavailable.' }
npm.cmd ci --ignore-scripts
if ($LASTEXITCODE -ne 0) { throw 'Locked npm install failed.' }
```

Pillow13.0.0 est la seule nouvelle dépendance applicative. Les versions existantes
restent identiques. Les locks universels incluent le wheel CPython3.13 WindowsAMD64.
Si le venv n'existe pas, le créer au préalable avec `py -3.13 -m venv backend\.venv`.
Aucune migration n'est exécutée par cette installation.

## Tests sans base, puis build

```powershell
$mediaNodeTests = @(Get-ChildItem packages/content-contracts/test/*.test.mjs, packages/content-contracts/test/*.test.ts, apps/studio/test/*.test.mjs | ForEach-Object { $_.FullName })
node --test $mediaNodeTests
if ($LASTEXITCODE -ne 0) { throw 'Node checks failed.' }
npm.cmd run typecheck
if ($LASTEXITCODE -ne 0) { throw 'Strict TypeScript failed.' }
$env:NEXT_TELEMETRY_DISABLED = '1'
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
& .\backend\.venv\Scripts\python.exe -B scripts/verification/check_base001.py
if ($LASTEXITCODE -ne 0) { throw 'Historical reference changed.' }
& .\backend\.venv\Scripts\python.exe -B -m unittest discover -s scripts/verification/tests -v
if ($LASTEXITCODE -ne 0) { throw 'Integrity checks failed.' }
& .\backend\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Historical CMS checks failed.' }
```

## Suite Django complète dans un cluster neuf et un stockage neuf

```powershell
$mediaEvidence = Join-Path $env:TEMP ('media001-' + [guid]::NewGuid().ToString('N'))
& .\backend\.venv\Scripts\python.exe -B scripts/verification/run_media001_isolated.py `
    --engine native --pg-bin 'C:\Program Files\PostgreSQL\17\bin' `
    --output $mediaEvidence --execute-isolated-migrations
if ($LASTEXITCODE -ne 0) { throw "Validation échouée : consulter $mediaEvidence. Aucune base habituelle utilisée." }
Get-Content (Join-Path $mediaEvidence 'django-tests.log') -Encoding UTF8 -Tail 15
Get-Content (Join-Path $mediaEvidence 'isolated-environment.json') -Encoding UTF8
```

Le runner crée un répertoire TEMP privé (DACL utilisateur/SYSTEM), puis initdb17,
port aléatoire loopback, rôles aléatoires distincts et fichier de configuration privé.
Il vérifie la version et `SHOW data_directory` avant provisioning/migrations. Les
préfixes e04_/test_e04_ respectent les gardes historiques ; le cluster est neuf
MEDIA-001. Il fixe SAAS_MEDIA_ROOT sur **son sous-répertoire média temporaire** et
les autorisations de migration uniquement pour ses processus enfants. Les cookies,
secrets, bases et fichiers d'environnement habituels ne sont pas utilisés.

Les ACL du stockage Windows sont vérifiées via DACL seulement : aucun accès SACL,
Set-Acl ou SeSecurityPrivilege requis. Le service PostgreSQL17 installé sur le PC
n'est ni redémarré ni modifié. Ne pas lancer PowerShell en administrateur pour
forcer un test de symlink : consigner un test ignoré comme tel, pas comme réussi.
Les nombres exacts de skips doivent être rapportés ; ne pas présumer les deux skips
historiques d'E.07.04 identiques sur cette branche.

## Recette navigateur complète et captures

Installer les seuls outils de recette dans un venv séparé sous TEMP :

```powershell
$mediaBrowserVenv = Join-Path $env:TEMP ('media001-browser-' + [guid]::NewGuid().ToString('N'))
py -3.13 -m venv $mediaBrowserVenv
$mediaBrowserPython = Join-Path $mediaBrowserVenv 'Scripts\python.exe'
& $mediaBrowserPython -m pip install 'playwright==1.62.0' 'Pillow==13.0.0'
if ($LASTEXITCODE -ne 0) { throw 'Browser tooling failed.' }
$env:SAAS_TEST_CHROMIUM = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if (-not (Test-Path $env:SAAS_TEST_CHROMIUM)) { throw 'Indiquer le chemin réel de Edge/Chromium installé.' }
$mediaJourneyEvidence = Join-Path $env:TEMP ('media001-journey-' + [guid]::NewGuid().ToString('N'))
try {
    & .\backend\.venv\Scripts\python.exe -B scripts/verification/run_media001_isolated.py `
        --engine native --pg-bin 'C:\Program Files\PostgreSQL\17\bin' `
        --output $mediaJourneyEvidence --execute-isolated-migrations `
        --browser --browser-python $mediaBrowserPython
    if ($LASTEXITCODE -ne 0) { throw "Recette échouée : consulter $mediaJourneyEvidence" }
    Get-Content (Join-Path $mediaJourneyEvidence 'browser-results.json') -Encoding UTF8
    Start-Process $mediaJourneyEvidence
} finally {
    Remove-Item Env:\SAAS_TEST_CHROMIUM -ErrorAction SilentlyContinue
}
```

Django et Next sont démarrés par le runner sur leurs propres ports libres, puis
arrêtés avec leurs processus enfants. Il génère les images synthétiques de test,
crée les comptes de recette, vérifie upload/association/cadrage/sauvegarde/reconnexion,
refus inter-comptes, erreurs, suppression et un multipart réel de12Mio via Next.
Les seules images copiées dans les preuves sont synthétiques. Le stockage de test
est détruit avec le cluster ; seules les preuves restent dans mediaJourneyEvidence.

Les outils `purge_assets` et `reconcile_media` sont dry-run par défaut. Ne pas les
exécuter sur la configuration habituelle : ils sont exercés dans les tests isolés.
L'installation sur une base persistante et un stockage réel exige une autorisation
séparée et une sauvegarde DB+binaires cohérente. Aucun PUB ou déploiement n'est inclus.

Référence de cette livraison Linux :389 Django,220 Node,15 intégrité/initialisation,
6 CMS, soit630 tests réussis ;6 groupes navigateur et7 captures. Rapporter les
résultats Windows réellement exécutés, avec le nom et la raison des tests ignorés.

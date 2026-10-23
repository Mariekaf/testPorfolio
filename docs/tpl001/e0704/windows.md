# E.07.04 — Windows natif, validation exclusivement jetable

**Commandes proposées, non exécutées sous Windows par l'agent.** E.07.03 Windows
et session lecteur d'écran restent ouverts malgré la recette visuelle MVP acceptée.
Ne pas lancer Initialize-Database, migrate ou Test-Foundations sur la configuration
habituelle. La nouvelle migration est volontairement bloquée hors du runner isolé.
Aucun changement des données existantes n'est autorisé.

## Préparer les sources et les tests sans base

Python3.13, Node24/npm11 et PostgreSQL17 natif installés ; pas de Docker nécessaire.
Depuis un terminal PowerShell normal (sans administrateur) :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
if (git status --porcelain) { throw 'Préserver les modifications locales avant de changer de branche.' }
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'Fetch failed.' }
git switch feature/tpl-001-e0704
if ($LASTEXITCODE -ne 0) { throw 'Switch failed.' }
git pull --ff-only origin feature/tpl-001-e0704
if ($LASTEXITCODE -ne 0) { throw 'Pull failed.' }
git log -1 --format="%H %s"
py -3.13 --version
node --version
& 'C:\Program Files\PostgreSQL\17\bin\initdb.exe' --version
npm.cmd ci --ignore-scripts
if ($LASTEXITCODE -ne 0) { throw 'Locked npm install failed.' }
& .\backend\.venv\Scripts\python.exe -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Python dependency check failed.' }
$readyNodeTests = @(Get-ChildItem packages/content-contracts/test/*.test.mjs, packages/content-contracts/test/*.test.ts, apps/studio/test/*.test.mjs | ForEach-Object { $_.FullName })
node --test $readyNodeTests
if ($LASTEXITCODE -ne 0) { throw 'Node checks failed.' }
npm.cmd run typecheck
if ($LASTEXITCODE -ne 0) { throw 'TypeScript failed.' }
$env:NEXT_TELEMETRY_DISABLED = '1'
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
& .\backend\.venv\Scripts\python.exe -B scripts/verification/check_base001.py
if ($LASTEXITCODE -ne 0) { throw 'Historical reference changed.' }
& .\backend\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Historical tests failed.' }
```

Les dépendances Python restent celles du lock development.txt ; si le venv manque,
le créer avec Python3.13 et installer avec `--require-hashes` comme CORE-001.

## Exécuter PostgreSQL17 jetable + migrations + suite Django complète

```powershell
$readyEvidence = Join-Path $env:TEMP ('tpl-e0704-' + [guid]::NewGuid().ToString('N'))
& .\backend\.venv\Scripts\python.exe -B scripts/verification/run_e0704_isolated.py `
    --engine native `
    --pg-bin 'C:\Program Files\PostgreSQL\17\bin' `
    --output $readyEvidence `
    --execute-isolated-migrations
if ($LASTEXITCODE -ne 0) { throw "Validation échouée. Voir $readyEvidence ; aucune base habituelle utilisée." }
Get-Content (Join-Path $readyEvidence 'isolated-environment.json')
Get-Content (Join-Path $readyEvidence 'django-tests.log') -Tail 15
```

Le runner ne reçoit aucun DSN existant. Il crée un répertoire temporaire privé,
exécute initdb17 neuf avec scram, utilise un port libre et des rôles aléatoires,
vérifie `SHOW data_directory` et server_version avant provisioning/migrations.
Les préfixes `e04_`/`test_e04_` sont conservés uniquement pour respecter la garde
SQL historique E.04 ; le cluster est **neuf E.07.04**, pas une réutilisation E.04.
Le runner définit les deux autorisations isolées E.04/E.07.04 dans ses seuls
sous-processus. Il ne modifie ni les variables persistantes, services Windows,
ports PostgreSQL existants, `.local/`, ni le fichier development.local.json.
Il arrête et supprime son propre cluster dans finally, même après échec.

Un test de symlink peut être ignoré faute de privilège Windows : le signaler,
ne pas le compter réussi et ne pas demander des droits élevés pour ce seul test.

## Recette navigateur authentifiée dans un nouveau cluster

Outil de test séparé hors dépôt, pas une dépendance applicative :

```powershell
$readyBrowserVenv = Join-Path $env:TEMP ('tpl-e0704-browser-' + [guid]::NewGuid().ToString('N'))
py -3.13 -m venv $readyBrowserVenv
$readyBrowserPython = Join-Path $readyBrowserVenv 'Scripts\python.exe'
& $readyBrowserPython -m pip install 'playwright==1.62.0'
if ($LASTEXITCODE -ne 0) { throw 'Browser tooling failed.' }
$env:SAAS_TEST_CHROMIUM = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if (-not (Test-Path $env:SAAS_TEST_CHROMIUM)) {
    throw 'Indiquer le chemin réel de Edge/Chromium installé dans SAAS_TEST_CHROMIUM.'
}
$readyBrowserEvidence = Join-Path $env:TEMP ('tpl-e0704-journey-' + [guid]::NewGuid().ToString('N'))
try {
    & .\backend\.venv\Scripts\python.exe -B scripts/verification/run_e0704_isolated.py `
        --engine native --pg-bin 'C:\Program Files\PostgreSQL\17\bin' `
        --output $readyBrowserEvidence --execute-isolated-migrations `
        --browser --browser-python $readyBrowserPython
    if ($LASTEXITCODE -ne 0) { throw "Recette échouée : $readyBrowserEvidence" }
    Get-Content (Join-Path $readyBrowserEvidence 'browser-results.json')
    Start-Process $readyBrowserEvidence
} finally {
    Remove-Item Env:\SAAS_TEST_CHROMIUM -ErrorAction SilentlyContinue
}
```

Django et Next sont démarrés uniquement pendant cette recette, sur deux ports
loopback temporaires ; seules les instances enfant démarrées par le runner sont
arrêtées. Le navigateur crée un compte fictif dans la base jetable. Aucun cookie,
compte ou fichier média personnel utilisé. Les captures et logs restent dans TEMP.
Cette recette est automatisée ; une vraie session NVDA/VoiceOver et l'ergonomie
Windows doivent être rapportées séparément. Aucun lien public n'est publié.

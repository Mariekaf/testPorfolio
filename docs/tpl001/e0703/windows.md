# E.07.03 — Validation et preview Windows, sans base

**Non exécutée par l'agent sous Windows.** E.07.02 est validée par le demandeur
(449 réussis, 1 symlink ignoré), mais E.07.03 nécessite sa propre vérification.
PowerShell5.1+, Python3.13, Node24/npm11, dépendances verrouillées déjà présentes
dans backend\.venv. Aucun Docker, PostgreSQL, Django, fichier d'environnement,
authentification, upload ou donnée réelle nécessaire. Ne pas exécuter migrate,
Initialize-Database, Test-Foundations ou le helper E.04.

## Récupérer la branche

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
if (git status --porcelain) { throw 'Préserver les modifications locales avant le changement de branche.' }
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'Fetch failed.' }
git switch feature/tpl-001-e0703
if ($LASTEXITCODE -ne 0) { throw 'Switch failed.' }
git pull --ff-only origin feature/tpl-001-e0703
if ($LASTEXITCODE -ne 0) { throw 'Fast-forward failed.' }
git log -1 --format="%H %s"
node --version
py -3.13 --version
npm.cmd ci --ignore-scripts
if ($LASTEXITCODE -ne 0) { throw 'Locked install failed.' }
git check-attr eol -- contracts/fixtures/ready-rendering/assets/portrait-a.svg contracts/fixtures/ready-rendering/assets/index.v1.json
```

Comparer le SHA à la livraison, eol doit valoir lf. Les SVG/JSON synthétiques
sont hashés : ne pas reformater/contourner leurs empreintes. Aucun paquet
applicatif nouveau n'est nécessaire pour le renderer ou l'export HTML.

## Tests hors ligne

```powershell
$previousRenderPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = (Join-Path (Get-Location) 'backend')
    & .\backend\.venv\Scripts\python.exe -B -m unittest backend.tests.test_hero_contracts backend.tests.test_hero_resolution backend.tests.test_hero_conversion backend.tests.test_hero_rendering backend.tests.test_hero_text_layouts backend.tests.test_ready_templates backend.tests.test_ready_rendering -v
    if ($LASTEXITCODE -ne 0) { throw 'Python fixture/SSR/parity checks failed.' }
} finally {
    $env:PYTHONPATH = $previousRenderPythonPath
}
$renderNodeTests = @(Get-ChildItem packages/content-contracts/test/*.test.mjs, packages/content-contracts/test/*.test.ts, apps/studio/test/*.test.mjs | ForEach-Object { $_.FullName })
node --test $renderNodeTests
if ($LASTEXITCODE -ne 0) { throw 'Node renderer or historical references failed.' }
node node_modules/typescript/bin/tsc --noEmit --strict --module nodenext --target es2022 --allowImportingTsExtensions --resolveJsonModule --esModuleInterop --types node packages/content-contracts/src/ready-contracts.ts packages/content-contracts/src/ready-registry.ts packages/content-contracts/src/ready-fixture-media.ts
if ($LASTEXITCODE -ne 0) { throw 'Strict TypeScript contracts/media failed.' }
& .\backend\.venv\Scripts\python.exe -B scripts/verification/check_base001.py
if ($LASTEXITCODE -ne 0) { throw 'Historical references changed.' }
& .\backend\.venv\Scripts\python.exe -B -m unittest discover -s scripts/verification/tests -v
if ($LASTEXITCODE -ne 0) { throw 'Integrity tests failed.' }
& .\backend\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Legacy tests failed.' }
npm.cmd run typecheck
if ($LASTEXITCODE -ne 0) { throw 'Next TypeScript failed.' }
$previousRenderTelemetry = $env:NEXT_TELEMETRY_DISABLED
try {
    $env:NEXT_TELEMETRY_DISABLED = '1'
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Next build failed.' }
} finally {
    $env:NEXT_TELEMETRY_DISABLED = $previousRenderTelemetry
}
```

Référence Linux : 242 Python, 208 Node, 12 intégrité, 6 historiques : **468
réussis**, zéro ignoré. Le symlink historique peut être ignoré faute de privilège
Windows : le consigner, ne pas le compter réussi et ne pas demander des droits
administrateur pour le transformer artificiellement en succès. Exécuter typecheck
et build séquentiellement (ils partagent .next/types).

## Voir les deux portfolios et leurs variantes

Dans un **premier terminal PowerShell**, depuis la racine du dépôt :

```powershell
$proofE0703 = Join-Path $env:TEMP ('tpl001-e0703-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $proofE0703 -ErrorAction Stop | Out-Null
$previewE0703 = Join-Path $proofE0703 'html'
node scripts/verification/render_ready_e0703.mjs $previewE0703
if ($LASTEXITCODE -ne 0) { throw 'Isolated preview export failed.' }
Write-Host ('Dossier des preuves : ' + $proofE0703)
& .\backend\.venv\Scripts\python.exe -B scripts/verification/serve_ready_e0703.py --directory $previewE0703 --port 3017
```

Le terminal reste occupé par ce **serveur de fichiers synthétiques**, pas Django.
Dans un **deuxième terminal PowerShell** :

```powershell
Start-Process 'http://127.0.0.1:3017/'
```

Choisir studio-a puis studio-b : textes, portrait, logo et trois projets changent,
la composition reste la même. Vérifier aussi paper-serif (palette/police autorisées)
et empty-draft (placeholders sans identité inventée, sections vides omises).
Redimensionner, tester Tab/Entrée, zoom200%, textes/alt et contraste. Arrêter
le serveur du premier terminal avec Ctrl+C. Ne pas lancer python -m http.server
sur le dépôt ; le helper limite explicitement les fichiers accessibles.

## Vérifications Chromium automatiques et captures

Après arrêt du serveur manuel, dans le **premier terminal** qui conserve
$proofE0703 et $previewE0703 :

```powershell
$renderBrowserEnv = Join-Path $proofE0703 'browser-venv'
py -3.13 -m venv $renderBrowserEnv
if ($LASTEXITCODE -ne 0) { throw 'Test-only browser environment failed.' }
$renderBrowserPython = Join-Path $renderBrowserEnv 'Scripts\python.exe'
& $renderBrowserPython -m pip install 'playwright==1.62.0'
if ($LASTEXITCODE -ne 0) { throw 'Test-only Playwright install failed.' }
$renderChromium = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if (-not (Test-Path -LiteralPath $renderChromium)) { throw 'Indiquer le chemin de Chrome ou Edge installé.' }
& $renderBrowserPython -B scripts/verification/browser_ready_e0703.py --html $previewE0703 --evidence (Join-Path $proofE0703 'browser-evidence') --chromium $renderChromium
if ($LASTEXITCODE -ne 0) { throw 'Creative Editorial browser checks failed.' }
git status --short
```

Le script utilise le navigateur déjà installé, aucun téléchargement de browser
ou ajout au lockfile. Il sert les seuls fichiers exportés sur un port éphémère
127.0.0.1, puis s'arrête. Attendu Linux : 24 largeurs, 24 cas zoom/textes longs,
4 forced-colors, 6 comparaisons de substitution et 12 PNG. Le mode reduced-motion
est actif ; aucune requête média distante. Les polices et les retours à la ligne
peuvent varier Windows/Linux : ne pas imposer une identité pixel entre plateformes.

La structure sémantique et les alt sont contrôlés automatiquement ; une session
NVDA/VoiceOver n'est pas exécutée par ce script. Vérifier manuellement si disponible
la navigation par landmarks, titres, ordre de lecture et noms des liens/images.
Noter ce qui a réellement été testé ; ne pas déclarer un lecteur d'écran réussi
sans session correspondante. Safari/Firefox et scaling OS sont des contrôles distincts.

Partager commit, versions, comptes de tests (dont skips), résultat de la recette
et éventuellement PNG synthétiques. Aucun secret ni contenu réel à transmettre.
Aucun résultat ne vaut publication, catalogue available ou autorisation E.07.04.

# E.05 — Vérification Windows native, sans base

**Non exécutée par l'agent sous Windows.** Les commandes ci-dessous restent à
exécuter sur le PC ; aucune migration, aucun serveur Django et aucun accès SQL
ne sont nécessaires. Ne pas utiliser Test-Foundations.ps1, migrate,
Initialize-Database.ps1 ou le helper E.04 dans cette vérification E.05.

## Récupérer la branche

Depuis PowerShell 5.1 ou ultérieur, avec Python 3.13, Node 24, npm 11 et les
dépendances backend verrouillées déjà installées dans `backend\.venv` :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
if (git status --porcelain) { throw 'Préserver les modifications locales avant de changer de branche.' }
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'Fetch failed.' }
git switch feature/tpl-001-e05
if ($LASTEXITCODE -ne 0) { throw 'Switch failed.' }
git pull --ff-only origin feature/tpl-001-e05
if ($LASTEXITCODE -ne 0) { throw 'Fast-forward failed.' }
git log -1 --format="%H %s"
py -3.13 --version
node --version
npm.cmd --version
npm.cmd ci --ignore-scripts
if ($LASTEXITCODE -ne 0) { throw 'Locked npm install failed.' }
```

Comparer le SHA au commit fourni dans la livraison avant de poursuivre.
Ne pas afficher ou partager les fichiers de configuration privée.

## Tests sans SQL

```powershell
$previousHeroPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = (Join-Path (Get-Location) 'backend')
    & .\backend\.venv\Scripts\python.exe -B -m unittest backend.tests.test_hero_contracts backend.tests.test_hero_resolution backend.tests.test_hero_conversion backend.tests.test_hero_rendering -v
    if ($LASTEXITCODE -ne 0) { throw 'Python contracts, resolution, explicit conversion or rendering failed.' }
} finally {
    $env:PYTHONPATH = $previousHeroPythonPath
}

$heroNodeTests = @(Get-ChildItem packages/content-contracts/test/*.test.mjs, packages/content-contracts/test/*.test.ts, apps/studio/test/*.test.mjs | ForEach-Object { $_.FullName })
node --test $heroNodeTests
if ($LASTEXITCODE -ne 0) { throw 'Node renderer or v1 regression tests failed.' }

& .\backend\.venv\Scripts\python.exe -B scripts/verification/check_base001.py
if ($LASTEXITCODE -ne 0) { throw 'Historical reference changed.' }
& .\backend\.venv\Scripts\python.exe -B -m unittest discover -s scripts/verification/tests -v
if ($LASTEXITCODE -ne 0) { throw 'Integrity tests failed.' }
& .\backend\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Legacy tests failed.' }

npm.cmd run typecheck
if ($LASTEXITCODE -ne 0) { throw 'TypeScript failed.' }
$previousHeroTelemetry = $env:NEXT_TELEMETRY_DISABLED
try {
    $env:NEXT_TELEMETRY_DISABLED = '1'
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Next build failed.' }
} finally {
    $env:NEXT_TELEMETRY_DISABLED = $previousHeroTelemetry
}
```

Référence Linux : **158 tests Python**, **99 tests Node**, **12 tests d'intégrité**,
**6 tests historiques** ; contrôles des 11 sources historiques et 4 empreintes
de fixture ; typecheck et build réussis. Total unittest/Node : **275 réussis**,
aucun ignoré. Les 2 tests Python E.05 appellent explicitement le convertisseur
pur E.04 puis le vrai renderer Node sur les deux snapshots Git : aucune sauvegarde
ni migration ne s'ensuit. Ne pas compter ces tests comme un nouvel essai des
transactions SQL E.04, qui n'est pas exécuté ici.

## Références HTML locales et navigateur (optionnel, recommandé)

Générer les quatre vrais rendus dans un **nouveau** dossier temporaire :

```powershell
$proofE05 = Join-Path $env:TEMP ('tpl001-e05-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $proofE05 -ErrorAction Stop | Out-Null
$heroHtml = Join-Path $proofE05 'html'
node scripts/verification/render_hero_e05.mjs $heroHtml
if ($LASTEXITCODE -ne 0) { throw 'Static Hero generation failed.' }
Start-Process (Join-Path $heroHtml 'centered.html')
```

Ouvrir aussi split-screen.html, fullscreen.html et typographic.html, redimensionner
à 375/768/1440 px et vérifier les quatre rendus, les contrastes et le clavier.
Aucun rendu ne s'ajoute au Studio courant : il reste en v1 par défaut.

Pour reproduire les vérifications automatiques Chromium, utiliser un outil de
test **isolé hors dépôt**, Playwright 1.62.0 (version utilisée sous Linux).
Aucune dépendance applicative ni navigateur supplémentaire n'est ajouté :
le script utilise Chrome/Edge déjà installé. Adapter le chemin si nécessaire.

```powershell
$heroBrowserEnv = Join-Path $proofE05 'browser-venv'
py -3.13 -m venv $heroBrowserEnv
if ($LASTEXITCODE -ne 0) { throw 'Browser test environment failed.' }
$heroBrowserPython = Join-Path $heroBrowserEnv 'Scripts\python.exe'
& $heroBrowserPython -m pip install 'playwright==1.62.0'
if ($LASTEXITCODE -ne 0) { throw 'Test-only Playwright installation failed.' }
$heroChromium = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if (-not (Test-Path -LiteralPath $heroChromium)) { throw 'Indiquer le chemin de Chrome ou Edge installé dans $heroChromium.' }
& $heroBrowserPython -B scripts/verification/browser_hero_e05.py --html $heroHtml --evidence (Join-Path $proofE05 'browser-evidence') --chromium $heroChromium
if ($LASTEXITCODE -ne 0) { throw 'Browser validation failed; inspect the temporary evidence.' }
```

Le script sert exclusivement les HTML synthétiques sur un port éphémère
127.0.0.1, puis arrête ce serveur statique. Il ne sert pas le dépôt ou `.local/`.
Il contrôle 24 couples layout/largeur, 24 cas texte long + zoom CSS 200 %, quatre
cas forced-colors et produit douze PNG. Le mode reduced-motion est activé.
L'installation du paquet de test peut nécessiter Internet ; le rendu ne dépend
d'aucune ressource distante. Si le navigateur ou une politique locale bloque
l'exécution, consigner l'échec et ne pas le déclarer réussi.

À transmettre pour la revue : SHA, versions, nombres réellement exécutés,
succès/échecs, observation manuelle et éventuellement les PNG synthétiques.
Windows, Firefox, Safari, lecteur d'écran et appareils physiques restent des
vérifications distinctes. Aucun skip n'est assimilé à un succès.

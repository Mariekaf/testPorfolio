# E.07.02 — Vérification Windows sans base ni Docker

**Non exécutée sous Windows par l'agent.** Python3.13, Node24 et npm11 requis,
ainsi que les dépendances verrouillées du backend déjà installées dans
`backend\.venv`. Aucun service PostgreSQL ou Django, aucun fichier d'environnement
privé et aucune configuration média nécessaires. Ne pas lancer Test-Foundations,
Initialize-Database, migrate ou le helper E.04 pour cette vérification.

## Récupération

Depuis PowerShell5.1 ou ultérieur, arrêter si le clone a des modifications locales :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
if (git status --porcelain) { throw 'Préserver les modifications locales avant de changer de branche.' }
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'Fetch failed.' }
git switch feature/tpl-001-e0702
if ($LASTEXITCODE -ne 0) { throw 'Switch failed.' }
git pull --ff-only origin feature/tpl-001-e0702
if ($LASTEXITCODE -ne 0) { throw 'Fast-forward failed.' }
git log -1 --format="%H %s"
py -3.13 --version
node --version
npm.cmd --version
npm.cmd ci --ignore-scripts
if ($LASTEXITCODE -ne 0) { throw 'Locked dependency install failed.' }
git check-attr eol -- contracts/ready-templates/manifest.v2.json contracts/ready-templates/creative-editorial/1.0.0/snapshot.json
```

Comparer le SHA à la livraison ; les deux eol doivent être **lf**. La règle est
sous `contracts/ready-templates/.gitattributes`, sans modifier les règles historiques.
Ne pas éditer/reformater les payloads pour faire passer une empreinte : toute
modification réelle de leurs octets doit être détectée, pas contournée.

## Contrats et parité hors ligne

```powershell
$previousReadyPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = (Join-Path (Get-Location) 'backend')
    & .\backend\.venv\Scripts\python.exe -B -m unittest backend.tests.test_hero_contracts backend.tests.test_hero_resolution backend.tests.test_hero_conversion backend.tests.test_hero_rendering backend.tests.test_hero_text_layouts backend.tests.test_ready_templates -v
    if ($LASTEXITCODE -ne 0) { throw 'Offline Python validation or Node parity failed.' }
} finally {
    $env:PYTHONPATH = $previousReadyPythonPath
}
$readyNodeTests = @(Get-ChildItem packages/content-contracts/test/*.test.mjs, packages/content-contracts/test/*.test.ts, apps/studio/test/*.test.mjs | ForEach-Object { $_.FullName })
node --test $readyNodeTests
if ($LASTEXITCODE -ne 0) { throw 'Node contracts or historical renderer checks failed.' }
node --input-type=module -e "import {loadReadyRegistry} from './packages/content-contracts/src/ready-registry.ts'; console.log(loadReadyRegistry().get().status)"
if ($LASTEXITCODE -ne 0) { throw 'Offline ready registry failed.' }
```

Le dernier affichage doit être **draft**, jamais available. Référence Linux :
**239 tests Python** (dont76 E.07.02), **193 tests Node** (dont77 E.07.02).
70 vecteurs communs sont exécutés par les deux langues avec comparaison réelle,
ainsi que14 corruptions de registre et9 entrées JSON invalides dans les tests
Python. Les sous-cas ne sont pas comptés comme des tests unittest supplémentaires.
Les faits `account_id/projects/assets` sont synthétiques et ne créent rien.

La création de symlink peut être indisponible sans privilège Windows : le test
le signale alors **ignoré**, pas réussi. Consigner le nombre réel d'ignorés et la
raison. Ne pas demander des droits administrateur ni désactiver une protection
pour transformer ce skip en réussite. Linux a exécuté le test sans skip.

## TypeScript strict, intégrité et build

```powershell
node node_modules/typescript/bin/tsc --noEmit --strict --module nodenext --target es2022 --allowImportingTsExtensions --types node packages/content-contracts/src/ready-contracts.ts packages/content-contracts/src/ready-registry.ts packages/content-contracts/test/ready-support.ts packages/content-contracts/test/ready-contracts.test.ts
if ($LASTEXITCODE -ne 0) { throw 'Strict ready TypeScript failed.' }
& .\backend\.venv\Scripts\python.exe -B scripts/verification/check_base001.py
if ($LASTEXITCODE -ne 0) { throw 'Historical references changed.' }
& .\backend\.venv\Scripts\python.exe -B -m unittest discover -s scripts/verification/tests -v
if ($LASTEXITCODE -ne 0) { throw 'Integrity tests failed.' }
& .\backend\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Legacy tests failed.' }
npm.cmd run typecheck
if ($LASTEXITCODE -ne 0) { throw 'Next TypeScript failed.' }
$previousReadyTelemetry = $env:NEXT_TELEMETRY_DISABLED
try {
    $env:NEXT_TELEMETRY_DISABLED = '1'
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Next build failed.' }
} finally {
    $env:NEXT_TELEMETRY_DISABLED = $previousReadyTelemetry
}
git status --short
```

Ne pas lancer typecheck et build en parallèle, car ils partagent `.next/types`.
Référence supplémentaire Linux : 12 tests d'intégrité, 6 tests historiques,
11 sources historiques inchangées et4 empreintes de fixture vérifiées ; total
**450 tests réussis** sans ignoré sous Linux. Les tests historiques utilisent
leur propre serveur/dossier temporaire et ne touchent pas aux données historiques.
Aucun navigateur n'est nécessaire : aucun nouveau rendu n'est livré dans E.07.02.

À rapporter : commit, versions, sorties finales, nombres réussis/échoués/ignorés,
raison d'un éventuel skip symlink et statut draft du registre. Ne partager aucun
secret, configuration privée ou donnée réelle. Un résultat Windows antérieur
E.06 n'est pas une validation Windows E.07.02.

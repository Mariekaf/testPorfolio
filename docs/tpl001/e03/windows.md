# E.03 — Vérification Windows sans base

Exécuter depuis la racine du dépôt sur la branche `feature/tpl-001-e03`, Python 3.13 et Node 24 installés. Ne pas utiliser Test-Foundations.ps1 : il comporte des accès PostgreSQL. Aucune configuration privée ou base n'est nécessaire ici.

Pour récupérer la branche, depuis le clone existant ; ne pas poursuivre si `git status --short` montre des modifications locales à préserver :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
git status --short
git fetch origin
git switch feature/tpl-001-e03
git pull --ff-only origin feature/tpl-001-e03
git log -1 --format="%H %s"
```

Vérifier le SHA annoncé dans la livraison, puis installer le lockfile mis à jour (Ajv) :

```powershell
npm.cmd ci --ignore-scripts
if ($LASTEXITCODE -ne 0) { throw 'Locked dependency installation failed.' }
```

Les commandes suivantes exécutent E.02, E.03, la vraie parité Python/Node et les références HTML v1 :

```powershell
$previousPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = (Join-Path (Get-Location) 'backend')
    & .\backend\.venv\Scripts\python.exe -B -m unittest backend.tests.test_hero_contracts backend.tests.test_hero_resolution -v
    if ($LASTEXITCODE -ne 0) { throw 'Python contracts/resolution/parity failed.' }

    node --test packages/content-contracts/test/hero-contracts.test.ts packages/content-contracts/test/hero-resolution.test.ts packages/content-contracts/test/hero-v1-golden.test.mjs
    if ($LASTEXITCODE -ne 0) { throw 'TypeScript resolution/v1 golden tests failed.' }

    node node_modules/typescript/bin/tsc --noEmit --strict --module nodenext --target es2022 --allowImportingTsExtensions --types node packages/content-contracts/src/hero-contracts.ts packages/content-contracts/src/hero-resolution.ts packages/content-contracts/test/hero-contracts.test.ts packages/content-contracts/test/hero-resolution-support.ts packages/content-contracts/test/hero-resolution-driver.ts packages/content-contracts/test/hero-resolution.test.ts
    if ($LASTEXITCODE -ne 0) { throw 'Strict TypeScript check failed.' }

    & .\backend\.venv\Scripts\python.exe -B scripts/verification/check_base001.py
    if ($LASTEXITCODE -ne 0) { throw 'Historical reference changed.' }
} finally {
    $env:PYTHONPATH = $previousPythonPath
}
```

Résultats Linux de référence : **151 tests Python**, dont 61 E.03 ; **63 tests Node**, dont 59 de résolution et 2 références HTML v1 ; contrôle TypeScript strict réussi. E.02 représente les 90 tests Python et 2 tests Node restants. Aucun test ne doit être compté réussi s'il est ignoré ou non exécuté. Node absent fait échouer la vraie parité, pas un skip silencieux.

À consigner sur Windows : commit exact, versions Python/Node/npm, résultats et nombres de tests, éventuelles erreurs. Ne partager aucune configuration privée. Les tests lisent les fixtures avec encoding UTF-8 explicite ; le sous-processus Node est décodé en UTF-8 côté Python. Le succès Windows natif E.02 rapporté par le demandeur ne vaut pas exécution native E.03.

Aucun serveur ni endpoint n'est requis. La recette visuelle manuelle C+D reste séparée : ces vérifications ne dessinent aucun nouveau Hero.

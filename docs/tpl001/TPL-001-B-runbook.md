# TPL-001.B — Exécuter les aperçus et vérifications

B ajoute des lectures authentifiées et un renderer, **aucune migration**. C/D/E restent non autorisées. Les aperçus ne créent ni ne publient de portfolio. Le dashboard historique du SaaS continue de proposer la création vierge ; la création depuis un template reste indisponible.

## Windows natif — commandes à vérifier sur le PC

Ces commandes ne sont pas une preuve d’exécution Windows. Utiliser uniquement la configuration de validation synthétique PORT déjà préparée selon [le guide isolé](../runbooks/port001-windows-development.md). Si elle est absente, préparer une base séparée avec ce guide ; ne pas appliquer de migration à la base réelle et ne pas réinitialiser les configurations privées existantes.

Après réception de la branche et vérification d’un arbre Git propre, terminal 1 depuis la racine du clone :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
git fetch origin
git switch feature/tpl-001-b
$env:SAAS_CONFIG_FILE = Join-Path (Get-Location) 'infra\env\port001.validation.local.json'
& .\scripts\windows\Start-Backend.ps1
```

Terminal 2 :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
npm.cmd ci --ignore-scripts
$env:NEXT_TELEMETRY_DISABLED = '1'
npm.cmd run dev --workspace @portfolio/studio
```

Se connecter au studio avec un compte synthétique de **cette base de validation** (ou s’inscrire pour les essais). Ouvrir `/templates`, puis `/templates/minimal/1.0.0` et `/templates/editorial/1.0.0` sur le studio local port 3000. Les boutons Desktop/Mobile utilisent le même renderer ; ils n’enregistrent aucune donnée. Tester aussi une fenêtre réellement étroite.

Pour les contrôles, arrêter Next avant typecheck/build comme dans les guides existants. Dans un terminal à la racine :

```powershell
$env:SAAS_CONFIG_FILE = Join-Path (Get-Location) 'infra\env\port001.validation.local.json'
& .\scripts\windows\Test-Foundations.ps1
```

La suite inclut désormais les tests du registre/API via Django et `npm.cmd run test:templates`. Elle utilise la base de tests dédiée pour les tests DB. Les empreintes des nouveaux bundles nécessitent UTF-8/LF ; `.gitattributes` impose LF pour `contracts/templates/**`, sans modifier la tolérance historique LF/CRLF du CMS. Ne jamais recalculer les hashes pour contourner un échec : diagnostiquer checkout/intégrité.

## Vérifications Linux exécutées pour B

Python 3.13 et environnement Python verrouillé déjà préparé ; Node 24/npm 11 ; PostgreSQL 17 synthétique. Les commandes principales sont :

```bash
python -B scripts/verification/check_base001.py
python -B -m unittest discover -s scripts/verification/tests -v
python -B -m unittest discover -s tests -v
# Avec SAAS_CONFIG_FILE pointant vers la configuration synthétique, jamais réelle :
python -B backend/manage.py check
python -B backend/manage.py makemigrations --check --dry-run --settings=config.settings.migration
(cd backend && python -B manage.py test tests --settings=config.settings.test --noinput)
npm run test:contracts
npm run test:auth
npm run test:portfolios
npm run test:templates
npm run typecheck
npm run build
```

Le test navigateur optionnel nécessite Playwright et Chromium existants ; aucune dépendance de production n’a été ajoutée pour lui :

```bash
python scripts/verification/browser_tpl001.py --origin http://127.0.0.1:3005 --chromium /usr/bin/chromium --evidence /tmp/tpl001-evidence --disposable-database
```

**Ne lancer ce test navigateur que contre une base synthétique jetable** : il crée un utilisateur fictif pour vérifier les vraies sessions, mais aucun portfolio. Le drapeau ne détecte pas automatiquement la base du serveur : vérifier sa configuration avant exécution. Aucun secret, cookie ou fichier d’authentification ne doit être envoyé dans les preuves. Dans la validation B, Django et Next utilisaient respectivement 8005 et 3005, avec SAAS_API_ORIGIN pointant vers 8005 au build et au démarrage, et SAAS_STUDIO_ORIGIN vers 3005.

## Cohérence du contrat avant activation

L’OpenAPI actif [templates.v1.json](../../contracts/api/templates.v1.json) couvre seulement les trois lectures B et les erreurs réellement retournées. Les réponses sont validées contre ces schémas dans les tests API, avec formats, sécurité, version exacte, filtres et no-store. Les routes de création/design proposées dans le dossier A ne sont pas activées. Aucun validateur OpenAPI externe supplémentaire ni dépendance n’est ajouté ; la conformité est vérifiée par résolution des références, revue sémantique et tests de réponses réelles, pas par une certification exhaustive d’outil.

Activation : bundles et descripteurs source immuables ; le manifeste de révision 1 projette available après validations du registre et du renderer. Le registre vérifie à chaque lecture les limites, hashes et capacités/layouts connus. Une modification invalide fait échouer la bibliothèque entière en 503 générique ; aucun fallback vers des données non validées. La disponibilité désigne l’aperçu utilisable, jamais un site publié ni une autorisation de démarrer C.

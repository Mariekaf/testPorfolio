# E.04 — Vérification native Windows, sans Docker et sans base existante

**Non exécutée dans l'environnement Linux de livraison.** Les succès Windows
E.02/E.03 rapportés ne valent pas validation native E.04.

Prérequis : Python 3.13, Node 24, dépendances backend et npm du dépôt, programmes
PostgreSQL 17 installés. Utiliser PowerShell ordinaire, pas besoin de droits
administrateur ni d'installation/reconfiguration de service. Le service PostgreSQL
existant sur 5432 ne sera ni interrogé, ni arrêté, ni modifié.

Récupérer la branche seulement avec un arbre de travail propre :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
git status --short
git fetch origin
git switch feature/tpl-001-e04
git pull --ff-only origin feature/tpl-001-e04
git log -1 --format="%H %s"
```

S'il existe des modifications locales, les préserver et résoudre ce point avant
de changer de branche. Vérifier le SHA annoncé dans la livraison. Ne pas exécuter
Initialize-Database.ps1, migrate ou Test-Foundations.ps1 avec une configuration
de développement/validation existante pour ce ticket.

Créer exclusivement le cluster temporaire E04 et exécuter les tests autorisés :

```powershell
$proofE04 = Join-Path $env:TEMP ("tpl001-e04-proof-" + [guid]::NewGuid().ToString('N'))
& .\backend\.venv\Scripts\python.exe -B scripts/verification/run_e04_isolated.py --engine native --pg-bin 'C:\Program Files\PostgreSQL\17\bin' --execute-isolated-migrations --output $proofE04
if ($LASTEXITCODE -ne 0) { throw "Validation E04 interrompue ; consulter les preuves dans $proofE04" }
Get-Content (Join-Path $proofE04 'django-tests.log') -Tail 12
Get-Content (Join-Path $proofE04 'runtime-privileges.log')
Get-Content (Join-Path $proofE04 'isolated-environment.json')
```

Le flag --execute-isolated-migrations matérialise l'autorisation **limitée au
cluster neuf**. Sans ce flag, le helper refuse avant création de fichier de preuve
ou connexion. Il n'accepte ni nom de base, ni fichier de configuration existant.
Le dossier de preuves doit être neuf ou vide ; une preuve existante n'est pas
écrasée.

Le helper :

1. Crée un répertoire temporaire privé avec ACL utilisateur courant + SYSTEM,
   sans Set-Acl ni SeSecurityPrivilege. Génère des credentials synthétiques privés.
2. Lance initdb et pg_ctl sur son nouveau data directory, UTF8, scram-sha-256,
   écoute 127.0.0.1 uniquement et port libre choisi automatiquement. Aucun service.
3. Génère sa propre configuration temporaire et impose SAAS_CONFIG_FILE à ses
   seuls sous-processus. Ne lit pas infra/env/development.local.json ni `.local/`.
4. Provisionne des rôles distincts runtime/DDL/test et des bases e04_/test_e04_
   nouvelles. Exécute les migrations autorisées, le contrôle de modèles et les
   privilèges réels, puis la suite Django complète avec les tests de concurrence.
5. Force UTF-8 pour les sous-processus Python et place la boîte locale éventuelle
   dans ce même répertoire temporaire. Aucun SMTP existant n'est utilisé.
6. Arrête **son** cluster dans finally puis retire ses fichiers/credentials
   temporaires. Conserve seulement les journaux dans $proofE04. En cas d'échec de
   nettoyage, ne pas déclarer la validation réussie ; examiner l'erreur avant reprise.

Référence Linux : 263 tests Django réussis, 0 échec, 0 ignoré ; aucune modification
de modèle non migrée ; runtime sans superuser/DDL/CREATEDB/BYPASSRLS. Le test
symlink hérité peut être ignoré selon les capacités Windows : le consigner comme
**ignoré**, pas réussi. Un test de parité sans Node échoue au lieu de passer en skip.

Compléter par les vérifications Node sans base :

```powershell
node --test packages/content-contracts/test/hero-contracts.test.ts packages/content-contracts/test/hero-resolution.test.ts packages/content-contracts/test/hero-v1-golden.test.mjs
if ($LASTEXITCODE -ne 0) { throw 'Contrats, parité et références v1 Node en échec.' }
node --test packages/content-contracts/test/health.test.mjs apps/studio/test/auth.test.mjs apps/studio/test/portfolios.test.mjs apps/studio/test/templates.test.mjs apps/studio/test/template-instances.test.mjs
if ($LASTEXITCODE -ne 0) { throw 'Tests frontend historiques en échec.' }
```

Références Linux : respectivement 63 et 23 tests Node. Les commandes de typecheck
strict et d'intégrité sans base sont également celles du guide E.03 ; elles
n'appliquent aucune migration. `npm.cmd ci --ignore-scripts` peut être nécessaire
si node_modules n'est pas installé selon le lockfile approuvé.

À communiquer pour revue : commit, versions et résultats exacts, erreurs et skips
éventuels. Ne pas publier le data directory, la configuration temporaire, un mot
de passe, un cookie ou un export de données. Les exemples d'API du guide de
récupération ne sont pas une instruction à convertir des portfolios réels.

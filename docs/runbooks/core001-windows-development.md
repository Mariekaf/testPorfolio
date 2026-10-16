# CORE-001 — Démarrage Windows PowerShell

Socle SaaS parallèle. Le CMS historique reste inchangé et conserve son port 8000 et ses données. Le nouveau backend ne consulte jamais `.local/`.

## 1. Prérequis

- Clone Git du dépôt, branche `arch/core-001` (pas main).
- Python **3.13 x64** et son launcher `py` ; une ancienne version du CMS peut conserver son Python actuel.
- Node.js **24 LTS**, npm **11.x** (vérifié avec 11.9.0).
- Au choix : PostgreSQL **17.x natif Windows**, ou Docker Desktop + Compose prenant en charge `up --wait`.
- PowerShell 5.1+ ; pas de modification globale de l'ExecutionPolicy.

Commandes à partir de la racine du clone :

```powershell
git fetch origin arch/core-001
git switch arch/core-001
py -0p
py -3.13 --version
node --version
npm.cmd --version
py -3.13 -m venv .\backend\.venv
& .\backend\.venv\Scripts\python.exe -m pip install --require-hashes -r .\backend\requirements\development.txt
```

Ne pas écraser le dossier d'une installation contenant des données. Si le dossier actuel vient d'un ZIP, cloner dans un autre dossier ; conserver la source locale historique. Les noms d'utilisateur et e-mails du CMS ne sont pas importés.

## 2A. PostgreSQL natif, sans Docker

Installer PostgreSQL 17 x64 depuis la page officielle https://www.postgresql.org/download/windows/ et son fournisseur d'installateur, dans un dossier de données dédié hors Git et hors `.local/`. Les étapes d'installateur, service et configuration restent à vérifier sur votre PC.

- Choisir le port **5433** si libre, sinon adapter `-Port` ci-dessous.
- Limiter `listen_addresses` à `localhost`, et les accès pg_hba.conf aux interfaces locales avec authentification SCRAM ; aucune règle `trust` ou ouverture réseau générale.
- Conserver le mot de passe d'administration privé. Le backend ne l'utilisera pas.
- Ne supprimer aucune installation/base existante ; ne pas exposer le port au réseau.

Vérifier le service et le client (adapter le chemin de version installé) :

```powershell
$pgBin = 'C:\Program Files\PostgreSQL\17\bin'
& (Join-Path $pgBin 'psql.exe') --version
Get-Service -Name 'postgresql*'
Get-NetTCPConnection -LocalPort 5433 -State Listen
& (Join-Path $pgBin 'pg_isready.exe') -h 127.0.0.1 -p 5433
```

Puis initialiser le socle :

```powershell
& .\scripts\windows\Initialize-Development.ps1 -DatabaseMode native -Port 5433
& .\scripts\windows\Initialize-Database.ps1 -AdminUser postgres
```

Le second script demande le mot de passe administrateur en saisie masquée, crée les rôles/base dédiés si absents, applique les migrations sous rôle DDL et vérifie le rôle runtime. **Aucune commande Docker n'est lancée dans ce mode.** Le mot de passe administrateur n'est pas enregistré.

Les rôles existants sont vérifiés (privilèges et authentification). Une base ayant un autre propriétaire n'est pas adoptée. L'outil ne réinitialise pas leurs mots de passe et ne supprime pas les données pour contourner une erreur.

## 2B. Alternative Docker explicite

Utiliser ce parcours à la place du mode natif, pas en plus sur le même port :

```powershell
& .\scripts\windows\Initialize-Development.ps1 -DatabaseMode docker -Port 5433
& .\scripts\windows\Initialize-Database.ps1
```

Compose démarre PostgreSQL avec une image verrouillée par digest, un port lié à 127.0.0.1 et un volume distinct. Aucun dossier historique n'est monté. Une configuration déjà créée n'est pas remplacée par un changement de mode ou de port : conserver sa copie privée et effectuer le changement intentionnellement avant toute nouvelle initialisation.

## 3. Installer le studio

Après l'initialisation (qui ajoute une exclusion Git locale pour les dépendances npm, sans modifier le `.gitignore` historique) :

```powershell
npm.cmd ci --ignore-scripts
```

Les fichiers privés `infra/env/development.local.json` et, en mode Docker, `development.local.env` sont ignorés par Git. Ne pas les afficher, copier dans une issue, committer ou joindre à un rapport. Le wrapper Windows pose des ACL sur ces fichiers pour l'utilisateur courant et SYSTEM ; cette opération reste à confirmer sur votre poste. Un exemple sans secret est fourni, mais doit être utilisé comme documentation, pas comme configuration exécutable.

## 4. Démarrer

Terminal 1, backend :

```powershell
& .\scripts\windows\Start-Backend.ps1
```

Équivalent sans wrapper PowerShell :

```powershell
& .\backend\.venv\Scripts\python.exe -B .\backend\manage.py runserver 127.0.0.1:8001
```

Terminal 2, studio :

```powershell
$env:NEXT_TELEMETRY_DISABLED = '1'
npm.cmd run dev --workspace @portfolio/studio
```

Sur **votre ordinateur**, ouvrir `http://127.0.0.1:3000`. C'est une page technique de fondations avec un bouton de vérification, pas encore l'éditeur SaaS. Le proxy `/api` cible Django sur 8001 ; pas de CORS général. Aucun compte SaaS n'est à créer pour ces contrôles.

Le CMS historique peut fonctionner à côté :

```powershell
py -X utf8 -B .\server.py --host 127.0.0.1 --port 8000
```

Ne pas démarrer le CMS historique pour initialiser ou tester de nouvelles données réelles : son fonctionnement reste celui d'origine.

## 5. Contrôles

Avec Django et PostgreSQL démarrés :

```powershell
Invoke-RestMethod 'http://127.0.0.1:8001/health/live'
Invoke-RestMethod 'http://127.0.0.1:8001/health/ready'
Invoke-RestMethod 'http://127.0.0.1:3000/api/v1/health/ready'
& .\scripts\windows\Test-Foundations.ps1
```

`live` vérifie le processus sans base. `ready` vérifie réellement PostgreSQL et la table utilisateur initiale ; il renvoie 503 si la base est indisponible ou non migrée. Pas de version SQL, nom d'utilisateur, mot de passe ou traceback dans la réponse publique.

Les tests Django utilisent un rôle dédié et une base `test_portfolio_core_dev`, créée puis supprimée par le runner. Ne pas y stocker de travail personnel. Ne pas donner CREATEDB au rôle d'exécution pour faire passer les tests. Les tests historiques gardent leurs dossiers temporaires.

## 6. Rôles et configuration

| Rôle | Usage | Limites |
|---|---|---|
| portfolio_core_app | Serveur Django | Pas de DDL, CREATEDB, superutilisateur ou BYPASSRLS |
| portfolio_core_migrator | Migrations explicites | Propriétaire de la base de développement ; pas le rôle runtime |
| portfolio_core_test | Base de tests | CREATEDB dédié aux tests ; jamais le rôle runtime |

Les credentials de ces trois rôles sont générés localement. Le fichier est une commodité de développement, pas une séparation de secrets de production. Le profil `config.settings.production` refuse volontairement de démarrer : le déploiement sécurisé est hors CORE-001.

La sélection du rôle DDL est explicite : `--settings=config.settings.migration`. Le runner de tests utilise `config.settings.test`. Les rôles runtime et migrator n'ont pas CREATEDB. L'isolation multi-tenant sera traitée dans SEC-001 avant toute donnée multi-utilisateur.

## 7. Arrêter sans perdre les données

Ctrl+C dans chaque terminal applicatif. En mode Docker seulement :

```powershell
docker compose --env-file infra/env/development.local.env -f infra/compose.yaml stop postgres
```

En mode natif, arrêter uniquement le service PostgreSQL identifié si vous le souhaitez et si aucune autre application n'en dépend. Aucune commande de suppression de base, volume ou dossier n'est nécessaire.

## Validation restant à effectuer sous Windows

Le backend, les migrations, les rôles, la connexion TCP et le studio ont été testés sous Linux. Les roues Windows CPython 3.13 x64 ont été téléchargées avec vérification des hashes. Cela ne remplace pas une installation Windows. Restent à confirmer : launcher Python, installateur/service PostgreSQL natif, pg_hba.conf, prompts masqués, ACL PowerShell, scripts complets, npm et accès navigateur sur votre PC.

## Contrôle des empreintes et fins de ligne Windows

Git peut extraire les textes en CRLF (`core.autocrlf=true`) alors que les sources de référence sont en LF. Le vérificateur corrigé sur `fix/core-001-windows` accepte uniquement cette équivalence pour les fichiers UTF-8 reconnus ; les fichiers binaires restent comparés octet par octet. Les manifestes SHA-256 historiques ne sont pas recalculés.

Diagnostic non destructif :

```powershell
git status --short
git ls-files --eol -- .gitignore
& .\backend\.venv\Scripts\python.exe -B .\scripts\verification\check_base001.py
```

`i/lf w/crlf` avec un état Git propre correspond à une conversion normale au checkout. Une différence réelle de contenu, d'espaces, de BOM, d'encodage ou de média reste refusée. Ne pas retirer le contrôle, remplacer les empreintes, changer globalement core.autocrlf ou exécuter git reset/clean pour contourner une erreur. En cas d'échec persistant, conserver les fichiers et transmettre le diagnostic non secret.

Le script Test-Foundations exécute également les régressions d'intégrité avant les tests historiques. Les résultats Windows de bout en bout restent à confirmer après installation de cette correction.

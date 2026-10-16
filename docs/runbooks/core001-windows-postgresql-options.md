# Préparation documentaire CORE-001 — PostgreSQL sous Windows

**CORE-001 n'a pas commencé.** Aucun backend, framework, service, conteneur ou base n'est installé par BASE-001. Les commandes suivantes sont un parcours futur à vérifier sur Windows dans CORE-001 ; elles n'ont pas été exécutées dans cet environnement Linux.

## Deux parcours équivalents à prendre en charge

| Option | Prérequis | Contrat à vérifier dans CORE-001 |
|---|---|---|
| Docker Compose | Docker Desktop/Compose disponible | PostgreSQL 17, version/digest verrouillés, volume dédié, 127.0.0.1:5433 |
| PostgreSQL natif Windows | Installateur officiel PostgreSQL 17 et outils client | Même schéma/migrations, service Windows, données dédiées et port local 5433 |

Pas de fallback SQLite implicite. Le backend ne doit pas dépendre de Docker pour se connecter. Même ensemble de paramètres PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD (ou configuration Django équivalente), avec secrets locaux ignorés et jamais committés.

## Parcours natif proposé, sans Docker

1. Depuis https://www.postgresql.org/download/windows/, suivre le fournisseur d'installateur officiel. Choisir la version 17.x corrigée retenue dans CORE-001 ; vérifier l'origine et les vérifications disponibles avant installation. Ne pas désactiver TLS/signatures pour contourner un problème.
2. Installer serveur et outils client ; choisir un dossier de données dédié hors du dépôt et de `.local/`. Conserver les bases existantes. Pas d'extension supplémentaire requise pour les fondations.
3. Retenir le port 5433 si libre ; si un autre port est nécessaire, le documenter et configurer explicitement le backend. Définir les accès locaux avec authentification SCRAM, pas trust. Pas d'ouverture du pare-feu réseau requise pour un développement local.
4. Dans postgresql.conf, limiter `listen_addresses` aux interfaces locales, puis redémarrer uniquement le service identifié. Dans pg_hba.conf, autoriser les connexions locales prévues avec `scram-sha-256`, sans règle réseau large. Sauvegarder les configurations avant modification.
5. Le mot de passe du superutilisateur de maintenance reste privé et n'est jamais celui utilisé par l'application.

Vérifications PowerShell futures (adapter le chemin installé) :

```powershell
$pgBin = 'C:\Program Files\PostgreSQL\17\bin'
& (Join-Path $pgBin 'psql.exe') --version
Get-Service -Name 'postgresql*'
Get-NetTCPConnection -LocalPort 5433 -State Listen
& (Join-Path $pgBin 'pg_isready.exe') -h 127.0.0.1 -p 5433
& (Join-Path $pgBin 'psql.exe') -h 127.0.0.1 -p 5433 -U postgres -d postgres -W
```

La dernière commande saisit le mot de passe via invite, sans l'inclure dans la ligne de commande. Ne pas copier la session ou sa sortie sensible dans un commit. Dans psql, création initiale **seulement si ces noms n'existent pas** :

```sql
SET password_encryption = 'scram-sha-256';
CREATE ROLE portfolio_migrator LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
\password portfolio_migrator
CREATE DATABASE portfolio_dev OWNER portfolio_migrator ENCODING 'UTF8' TEMPLATE template0;
CREATE ROLE portfolio_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
\password portfolio_app
\q
```

Les secrets sont choisis dans les invites ; aucun exemple de mot de passe n'est fourni. Cette création n'accorde pas encore au rôle applicatif l'accès aux tables : CORE-001 doit fournir les grants minimaux et leur vérification, ainsi que les privilèges par défaut pour les objets créés par le rôle de migration. Le propriétaire de schéma de migration ne doit pas servir de rôle d'exécution en production. La conception détaillée RLS appartient au ticket sécurité, pas à une configuration fictivement sécurisée ici.

Vérifier ensuite l'authentification du rôle applicatif :

```powershell
& (Join-Path $pgBin 'psql.exe') -h 127.0.0.1 -p 5433 -U portfolio_app -d portfolio_dev -W `
  -c 'SELECT current_user, current_database();'
```

## Impacts exigés sur CORE-001

- Initialisation avec choix explicite Docker/natif ; ne jamais démarrer Docker si le mode natif est sélectionné.
- Détecter une base/installation existante, ne pas recréer ou effacer ses données.
- Séparer credentials de migration et d'exécution. Préparer un mécanisme contrôlé de création de base de tests ; ne pas donner CREATEDB au rôle runtime pour faciliter les tests.
- Documenter la version client/serveur, les chemins Windows, le service et les paramètres locaux.
- Garder le CMS historique sur 8000, Django prévu sur 8001 et Next.js sur 3000.
- Tester les mêmes migrations et contrôles de disponibilité PostgreSQL sur les deux parcours ; pas de déclaration « Windows validé » sur la seule base d'une simulation Linux.
- Ne pas exécuter de commande de suppression de volume, base ou dossier dans le parcours normal.
- Ne pas stocker de valeurs secrètes dans les exemples `.env` ; ne pas appliquer globalement une politique PowerShell permissive.

Réserves : service Windows, ACL, installateur et connexion native non testés dans BASE-001. Leur exécution est un critère de vérification futur, pas un blocage de la documentation actuelle.

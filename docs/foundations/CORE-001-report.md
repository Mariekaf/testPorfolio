# CORE-001 — Rapport d'exécution

Date : 16 octobre 2026. Branche : `arch/core-001`, créée depuis le commit BASE-001 validé `f2f8e5d27ceb9b8df1dce008ecda62e6e903460a`. Aucune modification directe de main.

**Socle livré et validé sous Linux avec PostgreSQL réel. Validation native Windows encore à effectuer. AUTH-001 non commencé.**

## Périmètre réalisé

- Django/DRF en parallèle du CMS, PostgreSQL exclusif (pas de fallback SQLite), configurations développement/migration/test séparées.
- Modèle utilisateur UUID minimal déclaré par AUTH_USER_MODEL dès la première migration. Aucun parcours d'inscription, login, compte, portfolio ou données métier ; aucun utilisateur personnel importé.
- Rôles runtime/migration/test séparés. Runtime sans superutilisateur, CREATEDB, CREATEROLE, REPLICATION, BYPASSRLS, propriété de base ni CREATE sur schéma.
- Contrôles santé `/health/live`, `/health/ready` et alias `/api/v1/health/*`, JSON générique et no-store. Ready vérifie PostgreSQL et la table initiale, pas seulement un port.
- Studio React/TypeScript/Next.js technique, avec bouton de vérification via proxy same-origin. Pas d'éditeur ou de publication fictive.
- Workspaces npm et contrats de santé versionnés, composants de rendu/animation réservés par documentation seulement. `apps/studio/AGENTS.md` est généré par Next dev et conservé conformément à ses instructions ; next-env.d.ts reste ignoré et est régénéré par next typegen.
- Scripts PowerShell pour initialisation native/Docker, DB, démarrage et contrôles. Installation native PostgreSQL Windows décrite, sans obligation Docker.
- Fichiers privés générés localement et ignorés ; pas de secret livré. Paramètres existants non écrasés ; fichier d'exemple non exécutable sans génération.
- CI Linux ajoutée pour les mêmes étapes. Son résultat sur GitHub ne peut pas être déduit de son ajout : vérifier l'exécution distante séparément.

## Compatibilité et versions

Python 3.13.5, Django 5.2.18 LTS, DRF 3.18.3, Psycopg/binary 3.3.6, PostgreSQL 17.11, Node 24.19.0, npm 11.9.0, Next 16.4.2, React/react-dom 19.3.1, TypeScript 5.9.3. Métadonnées de registres puis intégration réelle vérifiées ; voir `dependency-versions.md`.

Les dépendances Python directes et transitives sont verrouillées avec hashes, les dépendances npm avec intégrités dans package-lock, et l'image PostgreSQL par digest. L'installation pip --require-hashes a été rejouée dans un second venv Python 3.13 propre. npm ci --ignore-scripts a été exécuté avant le dernier build. Audit npm de production : 0 vulnérabilité signalée à l'exécution ; cela ne constitue pas un audit de sécurité complet.

Le téléchargement des roues Windows x64 CPython 3.13, tzdata compris, a réussi avec vérification des hashes. Cela vérifie la disponibilité des artefacts, pas leur exécution sur Windows.

## Vérifications exécutées

| Vérification | Résultat | Preuve |
|---|---|---|
| PostgreSQL réel sur TCP local | 17.11, UTF8, table initiale et droits runtime vérifiés | evidence/database.txt |
| Migrations sur base dédiée initialement vide | Toutes appliquées, dont identity.0001_initial | Réexécutées aussi lors des tests Django |
| Reprovisionnement même configuration | Réussi sans rotation des secrets ni suppression de données | Commande rejouée ; rôles/base préservés |
| Branche native de l'outil de provisionnement | Réussie contre le même PostgreSQL TCP, prompt administrateur simulé | Ce n'est pas un service natif Windows |
| Django check / makemigrations --check --dry-run | Aucun problème, aucun changement de modèle non migré | Commandes exécutées |
| Tests nouveaux Django | **12/12 réussis**, base test dédiée créée puis supprimée | evidence/django-tests.txt |
| Tests contrats frontend | **3/3 réussis** | evidence/frontend-contract-tests.txt |
| Tests historiques | **6/6 réussis**, dont cp1252 simulé | evidence/legacy-tests.txt |
| Scénarios navigateur historiques | **12/12 réussis**, uniquement fixtures synthétiques | evidence/legacy-browser.txt |
| Fichiers historiques | **11/11 empreintes identiques** | evidence/baseline.txt |
| TypeScript | Réussi après génération des types Next | evidence/frontend-typecheck.txt |
| Build Next production | Réussi, page technique générée | evidence/frontend-build.txt |
| Studio production + bouton React + proxy | Fonctionnel, mobile sans débordement | evidence/http-resilience.txt |
| Arrêt réel de PostgreSQL | Live 200 ; ready et proxy 503 ; message studio indisponible | evidence/http-resilience.txt |
| Redémarrage réel de PostgreSQL | Ready 200 et bouton studio de nouveau disponibles | evidence/http-resilience.txt |
| Studio en développement/Turbopack | Page 200, interaction et proxy fonctionnels | evidence/dev-studio.txt |
| Roues Windows x64 | Téléchargées et hashes vérifiés | evidence/windows-wheels.txt |
| Installation native et scripts PowerShell sous Windows | **Non exécutés** | À réaliser sur le PC utilisateur |

Le contrôle liveness ne fait aucun accès DB. Les erreurs readiness testées n'exposent ni détails de connexion ni traceback. Les tests vérifient aussi qu'aucun endpoint métier/authentication n'est exposé.

### Corrections de vérification pendant le ticket

- La première invocation Django depuis la racine découvrait les tests historiques homonymes : invocation corrigée en se plaçant dans backend. Les 12 nouveaux tests ci-dessus ont bien été exécutés sur leur propre base PostgreSQL.
- Le premier test de reprise utilisait `compose start --wait`, non fonctionnel dans cet environnement. Le harnais a été corrigé vers `up -d --wait`, puis la séquence arrêt/reprise complète a réussi. Aucun volume n'a été supprimé.
- Une première tentative de téléchargement croisé Windows avec pip sous Python 3.12 évaluait mal les marqueurs Python/OS cibles. La vérification a été refaite sous Python 3.13 avec le marqueur Windows rendu explicite dans un fichier temporaire ; hashes conservés.
- Les caches système non inscriptibles ont été remplacés par des caches dans /tmp, sans désactivation de TLS, signatures ou vérification d'intégrité.

## Critères d'acceptation

| Critère | Statut |
|---|---|
| Branche dédiée depuis f2f8e5d ; main préservée | Conforme |
| CMS historique conservé | Conforme : sources et tests, plus navigateur |
| Django connecté à PostgreSQL, sans SQLite implicite | Conforme, connexion réelle vérifiée |
| Migrations sur base vide | Conforme |
| Modèle utilisateur personnalisé initial | Conforme, UUID, sans fonctionnalité AUTH-001 |
| Studio minimal sans fonctions métier fictives | Conforme |
| Santé processus et readiness PostgreSQL/503 | Conforme, y compris panne réelle |
| Proxy frontend sans CORS général | Conforme et testé |
| Versions compatibles et verrouillées | Conforme sous environnement testé ; artefacts Windows vérifiés |
| Secrets générés localement et exclus de Git | Conforme ; ACL Windows livrées mais non testées nativement |
| PostgreSQL lié à l'interface locale | Conforme Docker ; configuration native prescrite, à contrôler sur PC |
| Runbook pour un second développeur Windows | Livré ; exécution de bout en bout sur Windows encore à valider |
| Contrôles backend, TypeScript et build | Conformes |
| Rôle d'exécution distinct de migration et tests | Conforme, droits vérifiés dans PostgreSQL |
| .local/ ni consulté, ni modifié, ni monté | Conforme : données historiques uniquement en répertoires temporaires par les tests existants |
| Aucune migration réelle / API métier / Experience Builder | Conforme |
| AUTH-001 non commencé | Conforme ; nouvelle validation requise |

## Fichiers

La liste exhaustive des fichiers créés est dans `files.txt`, générée depuis le diff Git de ce ticket. Aucun fichier suivi de BASE-001 ou du CMS n'est modifié. Les fichiers privés générés, caches, dépendances installées, sorties Next et venv ne figurent pas dans le commit.

Le `.gitignore` historique reste identique. Les nouveaux sous-dossiers ont leurs propres exclusions. Pour le node_modules du workspace racine, l'initialiseur ajoute uniquement une règle dans `.git/info/exclude` local, sans remplacer le fichier existant. Exécuter l'initialisation avant npm ci sur un nouveau clone.

## Windows : commandes et réserves

Le parcours complet est dans `../runbooks/core001-windows-development.md`. Après installation Python 3.13 x64, Node 24 et PostgreSQL 17 natif local sur 5433 :

```powershell
py -3.13 -m venv .\backend\.venv
& .\backend\.venv\Scripts\python.exe -m pip install --require-hashes -r .\backend\requirements\development.txt
& .\scripts\windows\Initialize-Development.ps1 -DatabaseMode native -Port 5433
& .\scripts\windows\Initialize-Database.ps1 -AdminUser postgres
npm.cmd ci --ignore-scripts
```

Puis deux terminaux :

```powershell
& .\scripts\windows\Start-Backend.ps1
```

```powershell
$env:NEXT_TELEMETRY_DISABLED = '1'
npm.cmd run dev --workspace @portfolio/studio
```

La base a été testée ici en conteneur PostgreSQL Linux avec accès TCP réel. **Restent à vérifier sur le PC** : service/installateur Windows, port 5433, règles SCRAM/locales, Python launcher, ACL, invites masquées, scripts PowerShell, installation npm et navigation locale. Le rôle de test peut créer sa base préfixée test_ ; la base de développement n'est pas réinitialisée par les tests.

Le profil production refuse de démarrer volontairement : déploiement, séparation de secrets de production, RLS multi-tenant et accès utilisateurs sont hors CORE-001. Le fichier de configuration locale rassemble les trois credentials pour faciliter le développement ; ce n'est pas une frontière de secrets de production.

## Blocages / suite

Aucun blocage PostgreSQL dans l'environnement courant. La validation native Windows n'est pas revendiquée et reste une réserve explicite. Ne pas démarrer AUTH-001 avant validation utilisateur de ce livrable et traitement des éventuels retours Windows.

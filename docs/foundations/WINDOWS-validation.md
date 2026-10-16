# CORE-001 — Rapport de validation Windows native

**Résultat final : parcours de développement Windows natif réussi, sans Docker**, d’après la sortie complète transmise par l’utilisateur après application de `2b7085d`. La suite atteint le message final « Foundation checks passed ». AUTH-001 reste soumis à une nouvelle validation explicite.

Branche de corrections : `fix/core-001-windows`, issue de `51128c6` (`arch/core-001`). AUTH-001 n'a pas commencé. Aucune donnée réelle, aucun secret, aucun média ou fichier d'authentification utilisé dans les tests ou ajouté aux commits.

## Éléments confirmés par les sorties du poste utilisateur

| Étape | Résultat observé |
|---|---|
| PowerShell | 5.1 |
| Git | 2.49.0.windows.1 |
| Python | 3.13.5, 64 bits |
| Node / npm | 24.22.0 / 11.14.0 |
| PostgreSQL natif | Serveur 17.6 Windows x64, port local 5432 |
| Configuration PostgreSQL | listen_addresses=localhost, password_encryption=scram-sha-256 |
| pg_hba_file_rules | Six règles locales/loopback SCRAM, sans erreur ni trust |
| Clone | arch/core-001, commit 51128c6, état Git propre initialement |
| Venv/dépendances | Installation avec --require-hashes réussie ; pip check sans incohérence |
| Initialisation native | Configuration générée, ignorée par Git ; script terminé sans erreur |
| Base et migrations | Rôles provisionnés, toutes migrations initiales OK ; dernière sortie du vérificateur DB fournie partiellement |
| Backend | /health/live et /health/ready retournent status=ok |
| Studio | npm ci réussi ; Next dev répond 200 ; bouton affiche backend et PostgreSQL disponibles |
| Suite Test-Foundations, premier passage | Arrêt au contrôle CRLF, corrigé sur la branche dédiée |
| Suite après correctif CRLF, avant correctif maintenance | 12 tests d'intégrité, 6 historiques et 12 Django réussis ; nettoyage de la base test échoué ; frontend non exécuté à ce stade |
| Suite finale après les deux corrections | 12 tests d'intégrité, 6 historiques, 14 Django et 3 contrats réussis ; nettoyage, TypeScript et build réussis |

Ces observations proviennent de l'utilisateur sur son PC, pas d'une exécution distante par l'agent. Aucun transcript personnel n'est recopié.

## Correction du contrôle d'intégrité

Cause reproduite ici : clone Git propre avec `core.autocrlf=true`, index LF et fichiers de travail CRLF. L'ancien vérificateur comparait leurs octets directement aux empreintes LF enregistrées, ce qui provoque exactement le message reçu, sans modification sémantique des sources.

Correction limitée à l'outillage :

- Comparaison SHA-256 brute en premier.
- En cas d'écart, uniquement pour `.gitignore` et les extensions texte connues `.py/.md/.html/.css/.js/.json` : vérifier UTF-8 strict et remplacer CRLF par LF en mémoire avant comparaison au même hash attendu.
- Aucun autre nettoyage : pas de suppression d'espaces, BOM, CR isolés ou modification de l'encodage.
- Aucune normalisation des PNG ou extensions inconnues.
- Confinement des chemins préservé.
- Manifestes historiques et fixtures existantes inchangés.
- Aucun fichier du CMS historique modifié ; aucune configuration PostgreSQL ou donnée privée changée par le correctif.

Le passage réussi du vérificateur sur le poste confirme désormais l'équivalence des sources selon cette règle stricte. Une modification réelle du contenu resterait refusée ; les empreintes de référence n'ont pas été remplacées.

## Vérifications de la correction réalisées sous Linux

- 12 tests d'intégrité : LF, CRLF, Unicode, mix LF/CRLF et refus des changements de contenu/espaces/BOM/CR isolé/UTF-8 invalide/binaire/extensions inconnues/chemins sortants.
- Clone propre CRLF : échec de l'ancien vérificateur reproduit, puis succès du vérificateur corrigé pour les 11 sources et 4 fichiers de fixture.
- Même clone avec ajout réel dans `.gitignore` : échec préservé.
- Vérificateur sur les fichiers LF courants : succès.
- Six tests historiques : réussis après correction.

Les tests supplémentaires sont inclus dans Test-Foundations.ps1 et la CI. Aucune installation de dépendance supplémentaire.

## Procédure de reprise suivie sur Windows

1. Conserver les deux serveurs et les fichiers privés ; vérifier l'état Git et les fins de ligne.
2. Récupérer la branche de correction sans reset, clean ni écrasement de modifications locales.
3. Relancer Test-Foundations.ps1 en entier.
4. Examiner chaque résultat : référence, intégrité, six tests historiques, PostgreSQL réel, contrôles Django, quatorze tests Django (dont deux nouveaux de précontrôle), trois tests de contrats, TypeScript et build.
5. Consigner les éventuels nouveaux problèmes spécifiques à Windows sur la même branche.

**Procédure terminée avec succès après la seconde correction**, résultats détaillés ci-dessous. Le succès a été observé dans le transcript complet, pas déduit du seul navigateur. Ne pas commencer AUTH-001 avant une nouvelle validation utilisateur.

## Deuxième correction : base de maintenance Django

Le transcript utilisateur confirme la réussite des assertions Django mais un avertissement d'accès à `postgres`, suivi d'un échec au DROP de la base actuellement ouverte. Ce cas a été reproduit sur un PostgreSQL Linux **isolé**, avec CONNECT retiré de PUBLIC sur `postgres` : ancien code, 12 tests OK puis même échec de nettoyage.

Correction : grant CONNECT sur `postgres` au seul rôle de test ; vérification des mots de passe existants via la base de développement appartenant au migrateur ; précontrôle direct de maintenance dans le script et le runner Django, qui échoue avant toute création si l'accès manque. Pas de modification des privilèges runtime/DDL, pas de mot de passe réinitialisé et pas de suppression manuelle de base.

Vérifications effectuées ici :

- Reprovisionnement idempotent de l'instance isolée avec les credentials existants.
- 14 tests Django réussis, création et nettoyage de la base test terminés sans fallback.
- Contrôle SQL confirmant le grant au test seulement ; runtime et migrateur sans nouvel accès à postgres dans ce cluster restreint.
- Révocation temporaire du grant de test dans ce cluster de régression : le runner échoue avant création, sans fallback ; aucune base test créée.
- 12 tests d'intégrité et 6 historiques restent réussis.

Les résultats de reproduction ci-dessus sont des tests Linux de la correction. Le passage Windows reçu ensuite est décrit dans la section finale suivante.

## Résultat final reçu du poste Windows

Après mise à jour fast-forward et réexécution d'Initialize-Database.ps1 : rôles existants préservés, aucune migration supplémentaire nécessaire, connexion de maintenance du rôle de test vérifiée et runtime toujours sans DDL/CREATEDB/superuser/BYPASSRLS.

| Contrôle du dernier Test-Foundations.ps1 | Résultat |
|---|---|
| Référence des sources historiques | 11 fichiers conformes, équivalence LF/CRLF seulement pour les textes reconnus |
| Fixtures synthétiques | 4 empreintes conformes |
| Régressions d'intégrité | 12 tests OK |
| Tests historiques | 6 tests OK |
| PostgreSQL natif | 17.6, UTF8, table initiale accessible et droits runtime vérifiés |
| Contrôles Django | Aucun problème, aucune migration manquante |
| Tests Django | 14 tests OK ; base dédiée créée puis supprimée |
| Contrats frontend | 3 tests OK, aucun skip annoncé |
| TypeScript | Types Next générés et contrôle réussi |
| Build Next.js | Compilation et génération statique réussies |
| Fin du script | Foundation checks passed |

Total : **35 tests réussis** (12 + 6 + 14 + 3), puis contrôles et build réussis. La base de test existait encore après l'échec précédent ; le runner l'a supprimée/recréée au début, puis son nettoyage final s'est terminé sans exception. Ce message initial n'est donc pas un échec de la dernière suite. Les messages readiness « failed » dans deux tests correspondent à des pannes simulées attendues et leurs assertions passent.

L'ancien CMS, ses médias et `.local/` n'ont pas été modifiés par les corrections ; aucune donnée utilisateur n'a été migrée. Le rapport enregistre les résultats transmis par le propriétaire du poste : l'agent n'a pas exécuté directement Windows ni inspecté les données privées.

### Corrections enregistrées

- `b1a63c6` : comparaison d'intégrité compatible CRLF, refus des vraies modifications, tests et branche de vérification.
- `2b7085d` : accès CONNECT de maintenance pour le rôle de test seulement, reprovisionnement compatible avec les rôles existants et précontrôle sans fallback.
- La présente mise à jour est documentaire : rapport et synthèse expurgée, aucun nouveau code métier.

Synthèse structurée sans chemins personnels ni secrets : `evidence/windows-native-summary.json`. Le transcript brut reçu n'est pas committé.

### Portée et décision suivante

La réserve Windows de CORE-001 est levée pour **ce poste et ce parcours de développement** : PostgreSQL natif local, Python 3.13, Node 24, Django et Next.js. Cela ne constitue ni une validation de production, ni un audit de sécurité complet, ni une garantie sur tous les postes Windows. La CI distante n'est pas déclarée validée par ces résultats locaux.

Aucun blocage observé dans la dernière suite. La branche de correction n'est pas fusionnée dans main. **AUTH-001 n'a pas commencé et attend l'accord explicite de l'utilisateur.**

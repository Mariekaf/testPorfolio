# AUTH-001 — Revue technique et clôture

Date : 16 octobre 2026 (Africa/Douala).
PR : https://github.com/Mariekaf/testPorfolio/pull/1
Branche : `feature/auth-001` ; base technique validée : `7331e5b`.

**Décision : revue technique terminée, AUTH-001 clôturé dans le suivi documentaire sur instruction de l’utilisateur. Aucune fusion, aucun déploiement, PORT-001 non commencé.**

Cette revue porte sur les sources de la branche et les correctifs inclus dans le présent commit. La tête de PR a été vérifiée par la référence Git `refs/pull/1/head`, identique à `feature/auth-001` au commit `466d87c` au début de la revue. L’API GraphQL GitHub reste refusée : aucune approbation formelle, modification de statut ou clôture d’objet GitHub n’est revendiquée. La PR est conservée en brouillon selon la dernière information utilisateur ; son état actuel et sa branche cible ne peuvent pas être relus via l’API.

## Constats et résolution

| Priorité | Constat | Résolution / preuve |
|---|---|---|
| P2 — corrigé | Une requête `me` déjà en cours pouvait réafficher l’identité après le début de la déconnexion. `check()` ne consultait pas l’état de départ après son `await`. | Le dashboard ignore les réponses et erreurs après le début du départ, bloque les nouveaux contrôles et marque aussi le départ sur expiration. Une session déjà expirée n’est pas affichée avant son timer. Régression Chromium avec réponse `me` et réponse logout volontairement retenues, desktop/mobile : réussite. |
| P2 — corrigé | Le chemin logout construisait un `BroadcastChannel` sans vérifier sa disponibilité, alors que le montage du dashboard la vérifiait. Son absence pouvait empêcher la redirection après révocation effective côté serveur. | Vérification de disponibilité avant notification. Parcours Chromium avec API BroadcastChannel désactivée : redirection réussie et `me` renvoie 401, desktop/mobile. |
| Blocage Windows antérieur — levé sur confirmation utilisateur | Le démarrage pouvait échouer sur `Set-Acl` avec `SeSecurityPrivilege`. | Correctif DACL `466d87c` et contrôle `Test-Mailbox.ps1`. L’utilisateur a répondu « oui » à la confirmation explicite de réussite de ce contrôle, du démarrage Django et des parcours Windows inscription/connexion/déconnexion/reset/expiration. Il s’agit d’une preuve déclarative utilisateur, sans nouveau transcript complet. |

Aucun autre défaut critique ou majeur identifié dans le périmètre examiné. Cette conclusion ne constitue pas un audit exhaustif ni une autorisation de déploiement public.

## Périmètre examiné

- Authentification par e-mail : sérialisation stricte, validation des mots de passe, normalisation, unicité PostgreSQL, UUID stable, absence de privilèges assignables par l’API.
- Sessions et autorisations : rotation, expiration absolue, cookies, CSRF anonyme et authentifié, profil lié à la session, protection serveur du dashboard, révocation lors de la déconnexion et du reset.
- Récupération : réponse générique, token Django temporaire et invalidé après changement de mot de passe, verrou utilisateur, suppression des sessions suivies, fragment effacé, liens absents des URL HTTP.
- Abus : limites transactionnelles PostgreSQL partagées, clés HMAC, purge des compteurs. La politique réseau/proxy de production reste hors livraison.
- Migrations : dépendances, contrôle préalable, atomicité, conservation UUID/hachages, contraintes. Migration complète sur base jetable et absence d’écart de modèle vérifiées.
- Confidentialité : boîte locale privée, ACL Windows ciblées DACL, erreurs SMTP expurgées, réponses limitées, aucun jeton localStorage, aucun contenu historique importé.
- Frontend : formulaires, gestion d’erreurs, chargements, protection initiale côté serveur, données affichées seulement après vérification client, déconnexion inter-onglets et réponses retardées.
- Compatibilité : scripts natifs Windows, invariants du CMS et sources historiques préservés.

## Résultats de cette revue — réellement exécutés sous Linux

| Contrôle | Résultat |
|---|---|
| Référence historique et fixture | 11 fichiers historiques inchangés, 4 empreintes conformes |
| Tests intégrité | 12/12 |
| Tests CMS historique | 6/6 |
| Tests Django, vraie base PostgreSQL de test | 33/33 |
| Contrats santé | 3/3 |
| Client auth | 4/4 |
| Total suites | **58/58** |
| TypeScript et build Next.js | réussis |
| Syntaxe des deux JS historiques | réussie |
| `makemigrations --check --dry-run` | aucun écart |
| PostgreSQL 17.11, rôles et maintenance | vérifiés |
| Migration de zéro sur base jetable de revue | réussie |
| Chromium 1280 px et 390 px | inscription, connexion, logout, reset boîte locale, refus réutilisation, protection route, cookies, absence localStorage, inter-onglets, liens absents des URL HTTP : réussis |
| Régressions revue Chromium | réponse `me` retardée pendant logout et logout sans BroadcastChannel : réussis dans les deux formats |

La base, les rôles et la boîte utilisés pour les parcours de revue sont jetables et distincts des données de développement. Aucune dépendance ajoutée. L’avertissement Node sur la détection de module reste non bloquant.

## Preuves Windows — distinction des versions

- Sur `ffc015b` : transcript utilisateur des **58 tests réussis**, TypeScript/build, PostgreSQL natif 17.6 vérifié. Python 3.13.5, Node 24.22.0, npm 11.14.0, PowerShell 5.1 précédemment fournis.
- Base de développement : transcript `showmigrations identity` avec `[X]` pour 0001 et 0002.
- Sur le correctif Windows `466d87c` : confirmation utilisateur « oui » pour Test-Mailbox, Django et les parcours inscription, connexion, déconnexion, récupération et expiration. Aucun transcript supplémentaire ni lecture de son PC n’est revendiqué.
- Les derniers ajustements frontend de cette revue et leurs nouveaux scénarios ont été exécutés sous Chromium Linux ; ils n’ont pas fait l’objet d’une nouvelle exécution Windows attestée. Ils ne changent pas les API, les migrations ou le mécanisme ACL Windows. Les résultats Windows précédents ne sont pas présentés comme une exécution du commit final.

La clôture technique s’appuie sur ces preuves combinées et la confirmation utilisateur. Aucun résultat manquant n’est reconstitué ou inventé.

## Statut final des critères

AC01–AC12 : validés par tests backend, contrats et parcours navigateur, complétés par la confirmation Windows pour les parcours principaux. AC13 : desktop/mobile validés sous Chromium Linux ; pas de test de lecteur d’écran revendiqué. AC14 : suite native Windows documentée, correctif de boîte et parcours confirmés par l’utilisateur, avec distinction de versions ci-dessus. AC15 : source historique et tests intacts. AC16 : vérifié sur les chemins testés ; aucune garantie sur de futurs journaux/proxys externes.

La revue technique est consignée ici ; elle ne remplace pas une approbation indépendante dans GitHub. Avant une éventuelle fusion, vérifier la branche cible et l’état de la PR dans GitHub et obtenir l’autorisation de fusion. PORT-001 reste soumis à une nouvelle autorisation explicite.

SMTP externe, lecteur d’écran, déploiement HTTPS public, proxy de confiance, vérification d’e-mail et exploitation prolongée restent hors validation de cette livraison locale.

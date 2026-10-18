# PORT-001 — Audit préalable et plan de reprise

Date : 18 octobre 2026 (Africa/Douala).
Statut : **préparation réalisée ; développement du nouveau périmètre bloqué par l’absence des contrats ARCH-002**. Aucun livrable final ni critère nouveau n’est déclaré validé.

## État réel du dépôt et des branches

- Checkout initial : branche `work` au commit `59f4e5c` (BASE-001 intégré). Aucune modification utilisateur présente.
- AUTH-001 validé : `2ff4fc1`, également tête Git de la PR nº 1 lors de la vérification.
- Une branche distante `feature/port-001` existait déjà, tête `669d573`, descendante de `2ff4fc1`. Le travail provisoire y a été conservé intégralement par avance rapide de la branche locale créée depuis AUTH-001 ; aucun historique réécrit, aucune PR fusionnée, aucun changement de `main`.
- L’API GraphQL GitHub répond `Forbidden` à la lecture de la PR nº 1. Sa référence Git est vérifiée ; son état ouvert/non fusionné est celui indiqué par l’utilisateur, non une vérification indépendante des métadonnées API.

## Blocage : source d’ARCH-002

`backend/modules/README.md` cite ARCH-002 mais le dépôt examiné ne contient ni son rapport, ni les contrats Account/AccountMembership, ni les schémas de blocs/composition/expérience évoqués. Le fichier `contracts/api/openapi.yaml` ne décrit que la santé CORE-001. Le schéma de session AUTH-001 existe séparément.

Le nouveau ticket exige de vérifier ARCH-002 avant de concevoir les modèles, de distinguer User/Account/AccountMembership et de ne pas substituer User à Account. Il faut donc obtenir le document approuvé ou son emplacement accessible avant de définir les relations, la création de l’espace propriétaire et les futures autorisations.

Question transmise à l’utilisateur : fournir le chemin, la branche ou le lien du contrat approuvé. Aucun modèle de compte, migration de propriété ou contrat prétendument approuvé n’a été inventé dans cette préparation.

## Écarts de l’implémentation provisoire

| Exigence du nouveau ticket | Constat sur `669d573` | Travail à prévoir |
|---|---|---|
| Propriété Account / AccountMembership | `Portfolio.owner` référence directement User | Aligner les relations sur ARCH-002 ; préparer une migration conservatrice si des données SaaS existent |
| Slug unique par espace propriétaire | Champ `slug unique=True`, validation globale | Contrainte PostgreSQL par propriétaire, gestion des collisions concurrentes |
| Actif / archivé / suppression logique | `deleted_at` existe ; pas d’archivage/restauration | Séparer état de gestion, suppression et publication ; filtrer et interdire les mutations non autorisées |
| Conflits de version | PATCH sans précondition de version | Aligner If-Match/ETag et erreurs 412/428 sur le contrat approuvé avant implémentation |
| Templates et thèmes versionnés | Absents | Schémas validables, référence d’origine facultative et thème initial ; pas de catalogue opérationnel |
| Workspace dédié et navigation | Formulaire/listing intégrés au dashboard | Création guidée, pages dédiées, rubriques indisponibles explicites, états vides, focus et mode sombre |
| Option template « Bientôt disponible » | Absente | Option visible réellement désactivée ; aucun faux catalogue |
| Confirmation de suppression | `window.confirm` frontend ; DELETE sans confirmation côté API | Définir une confirmation serveur explicite dans OpenAPI et un dialogue accessible |
| Pagination utilisable | API paginée, frontend limité à la première page | Navigation et états de chargement/erreur complets |
| API documentée avant code | Endpoints provisoires à slash final, OpenAPI santé uniquement | Définir les chemins canoniques et erreurs conformément aux conventions CORE/AUTH sans slash final ; documenter la compatibilité des URL provisoires |
| Tests du nouveau ticket | 6 tests portfolio provisoires | Ajouter archives, concurrence réelle, version, Account, références, CSRF, parcours et clavier |

Les contraintes SQL actuelles imposent brouillon/privé ; elles constituent une protection existante à préserver dans le nouveau périmètre. Aucun projet, média ou contenu public n’existe dans cette implémentation.

## Plan d’implémentation ordonné

1. **Contrats avant code** : lire ARCH-002 fourni, consigner les relations et règles d’appartenance retenues, publier les chemins/objets/erreurs/préconditions dans OpenAPI. Définir les schémas versionnés template, thème et références de composition/expérience sans implémenter leurs moteurs.
2. **Modèles et migrations** : fondations de propriété conformes, Portfolio avec états séparés, UUID stable, références cohérentes, version de concurrence et unicité PostgreSQL par espace. Préserver la migration provisoire et prévoir une évolution sans purge ni lecture du CMS. Tester sur base synthétique isolée.
3. **Services et API** : filtres d’autorisation communs, transactions, validation stricte, pagination, création vierge, PATCH conditionnel, duplication métadonnées, archivage/restauration et suppression logique confirmée. Aucune publication implicite.
4. **Studio** : dashboard actif/archives, création vierge et option template indisponible, workspace minimal, paramètres, confirmations accessibles et pagination. Mode sombre, responsive et reduced-motion ; aucun contenu ou chiffre fictif.
5. **Validation** : tests multi-utilisateurs et multi-comptes, collisions et écritures concurrentes sur PostgreSQL, CSRF/sessions, refus des mutations archivées, modèles/thèmes, parcours desktop/mobile et clavier, non-régression complète.
6. **Livraison** : rapport et fichiers exhaustifs, preuves expurgées, guide Windows natif, branche et commit final. Ne pas déclarer la validation Windows sans exécution effective et attendre la validation utilisateur après livraison. Pas de TPL-001 ni fusion.

## Vérifications réellement exécutées sur la base provisoire

Environnement Linux préparé avec Python 3.13.5, Node 24.19.0/npm 11.9.0 et PostgreSQL **17.11**, image épinglée par digest dans le compose existant. Un environnement virtuel neuf et des dépendances verrouillées avec hashes ont été utilisés. `python3.13 -m venv` n’a pas pu amorcer pip (ensurepip absent) ; création via l’outil uv déjà disponible réussie, sans modification des dépendances du projet.

| Contrôle | Résultat |
|---|---|
| Django (AUTH/CORE + ancien PORT) | 39/39 tests réussis, base de test PostgreSQL créée puis supprimée |
| Intégrité BASE | 12/12 |
| Tests CMS historique | 6/6 |
| Contrats santé | 3/3 |
| Client auth | 4/4 |
| Total suites existantes | **64/64** |
| TypeScript / build Next | réussis |
| Référence historique | 11 sources et 4 empreintes de fixture conformes |
| Syntaxe JS historique | deux fichiers acceptés |
| Installation/migration | base de développement de cet environnement fraîche et sans données personnelles, migrations existantes appliquées avec succès |
| PostgreSQL | UTF8, rôle runtime sans DDL/CREATEDB/superuser/BYPASSRLS, maintenance du rôle de test vérifiés |
| Écart de migration | aucun sur les modèles provisoires |
| Requêtes HTTP réelles | live/ready 200 ; portfolios anonyme 403 ; login 200 ; dashboard anonyme redirigé vers login |

Ces vérifications ne couvrent pas des fonctionnalités encore absentes. Aucun nouveau parcours complet portfolio desktop/mobile, contrôle clavier ni test Windows du nouveau PORT-001 n’a été exécuté. L’avertissement Node de détection de module est non bloquant.

## Périmètre de cette préparation

Seuls ce document et l’actualisation de `PORT-001-report.md` sont ajoutés/modifiés par cette préparation. Aucun code métier, migration, fichier historique, contenu de `.local/`, donnée personnelle ou fichier d’authentification n’est modifié/commité. Le travail provisoire distant préexistant est conservé.

Des instructions réutilisables d’installation et démarrage cloud ont été enregistrées dans le brouillon de configuration d’environnement. Ce brouillon n’est pas une publication de site ; aucun secret n’y figure. Les services SaaS de ce cloud ont été démarrés et vérifiés. Windows conserve l’alternative PostgreSQL native déjà documentée.

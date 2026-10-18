# PORT-001 — Contrats et limites de l’API

Référence machine : [OpenAPI portfolios.v1.json](../../contracts/api/portfolios.v1.json), référencée par l’OpenAPI existant. URL canoniques **sans slash final**. L’ancienne ébauche à slash final n’est pas conservée comme alias ; elle n’était pas une API validée. Le frontend et les tests sont adaptés ensemble.

| Méthode | Route | Réponse |
|---|---|---|
| GET | `/api/v1/portfolios?state=active&page=1` | 200, count, active_count, archived_count, page, page_size=12, results |
| POST | `/api/v1/portfolios` | 201, création vierge avec name, slug facultatif, description facultative |
| GET | `/api/v1/portfolios/{id}` | 200 détail privé + ETag |
| PATCH | `/api/v1/portfolios/{id}` | 200 ; seuls name/slug/description |
| POST | `/api/v1/portfolios/{id}/duplicate` | 201 ; objet JSON vide, source active, nouvelle instance |
| POST | `/api/v1/portfolios/{id}/archive` | 200 ; actif → archivé |
| POST | `/api/v1/portfolios/{id}/restore` | 200 ; archivé → actif, publication inchangée |
| DELETE | `/api/v1/portfolios/{id}` | 204 ; JSON strict `{confirm:true}`, suppression logique |

Toutes les routes exigent une session. Les mutations exigent CSRF (initialisation via `/api/v1/auth/csrf` et en-tête `X-CSRFToken`). Les mutations d’une ressource existante, duplication incluse, exigent `If-Match` égal à l’ETag fort `"portfolio:<uuid>:<version>"`. L’ETag est aussi dans le champ de réponse `etag` pour le client. Pas de wildcard ; absence 428, obsolescence 412.

Erreurs : `{error:{code,message,fields?}}` ; validation 400, authentification 401, CSRF 403, cible inconnue/étrangère/supprimée 404, slug/état/espace incohérent 409. Les routes sont typées UUID ; une URL qui ne correspond pas au routage Django n’est pas une réponse métier. Les détails privés sont sans cache. Aucun identifiant de compte fourni par le client n’est utilisé pour assigner la propriété.

Le compte personnel est déterminé par Account.owner et une unique Membership admin active du même User. Un compte incohérent n’est ni réparé ni ouvert. Les GET n’effectuent aucun provisioning. Une première création après création d’identité hors inscription peut provisionner son compte dans la même transaction. Les nouvelles inscriptions provisionnent User/Account/Membership atomiquement ; la réponse et le schéma de session AUTH restent inchangés.

Les slugs personnalisés sont normalisés en minuscules et uniques par compte, supprimés inclus. Le serveur traite la concurrence avec contrainte PostgreSQL et transactions. Les slugs automatiques utilisent le nom et un suffixe borné si collision ; un nom sans résultat ASCII utilise une base neutre. Deux comptes distincts peuvent choisir le même slug.

Les archives restent consultables mais PATCH et duplication sont refusés. Une répétition d’archivage/restauration déjà dans cet état répond 409. La suppression est logique et n’expose pas de récupération. La duplication ne change pas la version/date de sa source ; elle ne promet pas d’idempotence entre deux demandes indépendantes.

## Références, composition et publication

Thème initial : `studio-neutral@1.0.0`, descripteur réel dans `contracts/themes/`, validé via `schemas/themes/theme.v1.json` avant création. Les tokens servent de référence neutre documentée ; aucun moteur de changement de thème n’est livré. La préférence clair/sombre du studio est une préférence UI, pas un jeton d’authentification.

Template : schéma versionné `schemas/templates/template.v1.json`, catégories, références de thèmes, disponibilité et références de documents futurs séparant contenu/présentation/expérience. Aucun catalogue opérationnel ou template instanciable. Une création vierge conserve les deux références source à null ; l’API interdit de les assigner. Les contraintes SQL imposent présence conjointe et format si des références existent à l’avenir.

Gestion (active/archived), suppression (deleted_at), publication (`status` SQL exposé `publication_state`) et visibilité sont distinctes. SQL et API imposent draft/private dans PORT-001 ; aucune URL publique, publication, domaine, page, projet, média ou animation n’est créé. Les futures ressources devront être rattachées par l’UUID du Portfolio avec autorisation Account, pas par un slug global.

Les données d’instance et leurs futures personnalisations ne sont pas des mises à jour du template source. Les schémas de blocs et du moteur Experience Builder restent hors périmètre.

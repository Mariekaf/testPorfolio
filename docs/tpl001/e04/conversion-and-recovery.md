# E.04 — Conversion explicite et récupération

Référence de départ approuvée : `ef4139109032f6974bd4b88dd3995879319ada78`.
Les règles ci-dessous décrivent du code livré pour revue, sans autorisation
d'utiliser une base réelle. Le [plan préalable et l'autorisation limitée](recovery-plan.md)
restent la référence de périmètre.

## État par défaut

`SAAS_HERO_TRANSITIONS_ENABLED` est false par défaut. Les nouveaux endpoints de
transition/récupération renvoient 404 tant que cette option n'est pas activée
explicitement ; les écritures et duplications de designs v2 sont alors refusées.
La création depuis Minimal/Editorial continue à produire v1. Aucune lecture,
migration ou ouverture du Studio ne convertit un portfolio.

Le renderer et tous les fichiers du Studio sont inchangés. Aucun Hero modulaire
n'est disponible. Un ancien client ne reçoit pas un document qu'il interpréterait
à tort comme v1 : GET/PUT design négocient `Accept-Design-Schema` (absent=1 ; valeurs
exactes 1, 2, 1,2 ou 2,1), avec 406 si l'enveloppe stockée n'est pas acceptée.
Autorisation du portfolio avant négociation ; session/CSRF AUTH inchangés.

Ne pas activer cette option sur une configuration existante pour essayer E.04.
Le helper de test crée exclusivement un environnement neuf ; les tests activent
l'option dans leurs contextes isolés et la restaurent ensuite.

## Conversion v1 → v2

Route privée, sans slash final :

```http
POST /api/v1/portfolios/{id}/design/upgrade
Content-Type: application/json
If-Match: "portfolio:{id}:{version}"
Idempotency-Key: {nouvel-UUID-canonique}
X-CSRFToken: {jeton-de-la-session}

{"target_schema_version":2,"converter_version":"1.0.0"}
```

Le corps est fermé. Le convertisseur 1.0.0 reconnaît explicitement les variantes
historiques hero-centered et hero-split ; une variante inconnue n'a aucun fallback.
Il conserve contenus, UUID locaux, ordre, visibilité, thème et identité de template.
Les defaults de settings restent ceux du document local. Les anciens overrides
Hero `presentation` sont déplacés vers `hero.layout.settings` afin de conserver
leurs valeurs effectives sans les figer en nouveaux defaults ; les réglages des
autres sections restent inchangés. Le snapshot v1 original exact est conservé
avant cette transformation.

Le Hero reçoit une palette basée sur le thème neutre connu : text/accent du thème,
surface et background sur la couleur de fond historique ; system-sans/balanced,
flat et none. Les cinq layouts sans prérequis manquants peuvent être référencés
par la politique locale ; ils restent tous non implémentés/non sélectionnables.
Product Showcase/Bento, médias et moteurs d'expérience restent hors périmètre.

Le document cible passe les schémas et le résolveur E.03 complet, avec contraste
4,5:1, avant tout INSERT de révision ou UPDATE du design. Une combinaison invalide
échoue, sans correction de couleurs ou de propriété. Le catalogue n'est pas relu.
La provenance Portfolio et source_digest du bundle ne changent pas.

Succès 200 : document Design cohérent, ETag canonique et `recovery_revision_id`.
Le compteur `Portfolio.version` augmente une fois. La réponse est privée/no-store.
L'absence d'If-Match donne 428 ; une intention nouvelle sur un ancien ETag donne
412. Une cible étrangère/supprimée est invisible (404) ; un portfolio archivé est
en lecture seule ; un portfolio vierge ne reçoit pas de design inventé.

## Révisions immuables et transactions

`DesignTransition` est à la fois révision de récupération et journal d'idempotence.
Chaque ligne contient snapshots before/after complets, hashes SHA-256 JSON
canoniques, source_digest, versions Portfolio avant/après, auteur, action,
convertisseur, clé et empreinte de requête. La propriété reste dérivée du
portfolio/account, sans champ owner redondant.

« Snapshot exact » désigne les valeurs JSON, textes, UUID et ordre des tableaux ;
JSONB ne conserve pas les espaces ou l'ordre des clés d'un fichier JSON. Les hashes
de révision utilisent une sérialisation canonique à clés triées. Le source_digest
du bundle, distinct, reste l'empreinte de ses octets immuables d'origine.

La révision est insérée **avant** le remplacement du design, dans la même
transaction. Ordre de verrouillage : Portfolio puis PortfolioDesign. La mise à
jour du design et l'incrément du compteur sont également dans cette transaction.
Une erreur à tout point annule l'ensemble. La migration est transactionnelle,
sans backfill ni écriture automatique de documents.

Un trigger PostgreSQL interdit UPDATE et DELETE des révisions, y compris avec un
QuerySet/bypass de save(). Les FK PROTECT empêchent une suppression applicative
en cascade de cette histoire. Le rôle runtime n'a ni propriété/DDL ni TRUNCATE ;
le propriétaire DDL garde ses pouvoirs d'administration, qui ne sont pas donnés
aux utilisateurs. Les tests synthétiques peuvent TRUNCATE leurs tables pour le
nettoyage Django ; cette capacité du rôle de test n'est pas un endpoint de purge.
Aucune purge automatique ni expiration des clés de transition n'est implémentée.

## Idempotence et concurrence

L'unicité est design/user/Idempotency-Key. L'empreinte inclut action, corps fermé
et If-Match original. Après autorisation et verrouillage, même clé et même
intention renvoient le résultat original, même si le compteur a avancé depuis.
Changer le corps, l'action ou l'ETag avec cette clé donne 409 idempotency_conflict.
Une nouvelle clé sur un design déjà v2 donne 409 design_already_v2 si l'ETag est
actuel, ou 412 s'il est obsolète. Une nouvelle conversion après restauration v1
est possible avec un nouvel ETag/clé et crée une nouvelle révision indépendante.

Un replay retourne le snapshot/ETag **historique** de l'opération, pas l'état
courant ; un client doit relire GET design avant de poursuivre une édition.
Cela évite qu'une réponse perdue conduise à répéter une écriture. Deux requêtes
concurrentes avec la même clé sont sérialisées et partagent un seul résultat.
Deux intentions sur le même ETag ne peuvent pas toutes deux modifier le design.
Un timeout de verrou renvoie 503 avec Retry-After: 2 ; reprendre avec la même clé.

## Retrouver et restaurer v1

GET `/api/v1/portfolios/{id}/design/revisions?page=1` retourne au plus 20 métadonnées,
de la plus récente à la plus ancienne. Page bornée 1..1000000 ; paramètres
inconnus, doublons et nombres non ASCII refusés. GET
`/api/v1/portfolios/{id}/design/revisions/{revision_id}` expose les snapshots et
empreintes complets au seul propriétaire autorisé. Une révision d'un autre
portfolio reste 404, même dans le même compte. Les données restent privées.

Restauration explicite, option activée dans l'environnement autorisé :

```http
POST /api/v1/portfolios/{id}/design/restore
Content-Type: application/json
If-Match: "portfolio:{id}:{version-actuelle}"
Idempotency-Key: {nouvel-UUID-canonique}
X-CSRFToken: {jeton-de-la-session}

{"recovery_revision_id":"{UUID-de-la-conversion-v1-vers-v2}"}
```

Le serveur vérifie action, design, provenance, hashes et validité des documents
de la révision. Il copie son before v1 exact. **Avant** de l'appliquer, il crée une
nouvelle transition dont before contient le v2 courant, y compris les modifications
effectuées après conversion ; restored_from pointe vers la conversion choisie.
Le compteur augmente, il n'est jamais remis à l'ancienne valeur.

« Sans perte » signifie que le v1 exact redevient courant et que le v2 remplacé
reste consultable dans une révision immuable. Il n'y a pas de fusion silencieuse
des contenus ni de réapplication automatique des anciens overrides v2. Cette
livraison expose le snapshot v2 conservé en lecture ; elle ne crée pas une action
de restauration arbitraire de n'importe quelle révision v2. Une telle action
nécessiterait un ticket et un contrat spécifiques.

Un deuxième restore avec la même clé rejoue la réponse ; avec une nouvelle clé
sur un design déjà v1, il échoue sans créer de nouvelle révision. Aucun lien de
récupération ne permet de restaurer sur un design différent ou étranger.

## Schéma, rollback et limites

La migration 0002 conserve les migrations historiques et SQL NULL pour experience,
remplace uniquement le CHECK de version par {1,2}, ajoute la table et ses contraintes
ainsi que le trigger. Un précontrôle exige `SAAS_E04_ISOLATED_MIGRATIONS=1` et un nom
de base e04_ ou test_e04_. Le helper est le seul protocole fourni pour satisfaire
ces conditions : cluster et credentials nouveaux, base vide, aucune adoption.
Ce garde-fou est volontairement **non prêt pour un déploiement réel** ; toute
évolution devra être examinée et autorisée séparément, sans modifier l'historique
déjà livré silencieusement.

La migration inverse est bloquée dès qu'une révision ou un document v2 existe.
Une restauration applicative v1 ne supprime pas l'histoire et n'autorise donc
pas un downgrade destructif du schéma. Préférer correction en avant. Ne pas
revenir à un ancien backend incapable de lire v2 tant que des designs v2 existent.
Pour un arrêt temporaire, désactiver les nouvelles écritures tout en conservant
le code compatible ; réactiver explicitement l'option pour une récupération
autorisée, pas pour lancer une conversion globale.

Ces révisions ne remplacent pas une sauvegarde externe vérifiée. Aucune sauvegarde
réelle, donnée personnelle, ancienne base ou média local n'est lu ici. La rétention
des snapshots augmente le stockage ; aucune suppression n'est introduite dans E.04.
Les tests d'interruption simulent des erreurs transactionnelles, pas une panne
électrique ou une restauration physique du serveur PostgreSQL.

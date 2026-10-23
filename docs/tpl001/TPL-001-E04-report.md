# TPL-001.E.04 — Rapport de livraison pour revue

**Statut : implémenté, testé sous Linux/PostgreSQL synthétique, soumis à revue ;
non déclaré validé.** E.05 et les tickets ultérieurs ne sont pas commencés.

Branche dédiée `feature/tpl-001-e04`, issue directement du commit E.03 approuvé
`ef4139109032f6974bd4b88dd3995879319ada78`. Historique et arbre propre vérifiés
avant modification. E.03 est approuvée avec Windows natif rapporté réussi ; cette
preuve n'est pas attribuée à E.04.

## Autorisation et périmètre des migrations

La contrainte SQL v1 et l'absence de table de récupération ont été constatées
avant implémentation. Le [plan préalable](e04/recovery-plan.md) a été documenté,
puis l'autorisation spécifique « Autoriser uniquement le cluster synthétique
E.04 » a été reçue **avant la première exécution de migration**.

Les essais ont utilisé exclusivement des clusters PostgreSQL 17 neufs, jetables,
propres à E04, avec rôles/credentials et bases e04_/test_e04_ générés. Aucun accès
à une base existante ou ancienne validation, aucun import de données réelles,
aucune lecture de `.local/` ou configuration privée historique. Les clusters de
test et leurs configurations privées ont été supprimés ; seuls les journaux
synthétiques sont conservés dans le dépôt.

La migration 0002 est additive : CHECK version 1/2, table DesignTransition,
contraintes et trigger d'immuabilité. Les migrations historiques sont inchangées.
Pas de backfill ni conversion automatique. La migration comporte un garde-fou
qui refuse les noms hors e04_/test_e04_ ou l'absence d'autorisation isolée.
**Elle n'est pas autorisée ni prête à être appliquée sur une base réelle** ;
l'évolution de ce garde-fou demandera une revue distincte.

## Fonctionnement livré

- v1 reste le défaut pour la création, la lecture et le Studio.
- Conversion pure explicite v1→v2, sans mutation source, puis validation complète
  E.03 avant sauvegarde ; réglages historiques déplacés avec leur effet préservé.
- POST design/upgrade et design/restore, sessions/CSRF existantes, corps fermés,
  If-Match et Idempotency-Key canoniques. Endpoints désactivés par défaut.
- Avant chaque conversion : révision before/after immuable, empreintes, source,
  versions et intention ; remplacement et compteur dans la même transaction.
- Idempotence durable, replay exact, conflit de clé/intention, verrouillage commun
  avec PUT/metadata, timeout retryable sans écriture partielle.
- Restauration du v1 exact avec **nouvelle sauvegarde du v2 courant**, y compris
  ses modifications ultérieures. Aucun décrément du compteur ou mélange implicite.
- Lecture privée des révisions (pagination bornée) et snapshots conservés ;
  isolation par portfolio/account, révision étrangère invisible même dans un compte.
- GET/PUT design avec négociation de version ; aucun ancien client ne reçoit un
  snapshot v2 à interpréter comme v1. Pas de downgrade par PUT.
- Duplication v2 contrôlée quand l'option est activée, sans partage d'historique
  de récupération ; historique original intact.
- Contrats OpenAPI actifs correspondant à ces routes et réponses, avec gate
  documenté ; anciennes spécifications/schémas et bundles inchangés.

[Règles de conversion/restauration](e04/conversion-and-recovery.md) ·
[Commandes Windows natives isolées](e04/windows-isolated.md)

## Preuves exécutées sous Linux

Python 3.13.5, Django 5.2.18, PostgreSQL **17.11**, Node 24.19.0, TypeScript 5.9.3.
Docker a servi uniquement à créer les clusters jetables Linux ; aucune obligation
Docker sur Windows. L'image officielle PostgreSQL est épinglée dans le helper par
digest. Aucune dépendance applicative ni lockfile modifié dans E.04.

| Vérification | Résultat | Preuve |
|---|---|---|
| Migrations complètes depuis un cluster vierge | Réussies, uniquement synthétique | [Journal](e04/evidence/migrations.log) |
| Cohérence modèles/migrations | No changes detected | [Journal](e04/evidence/schema-check.log) |
| PostgreSQL réel, UTF8 et moindre privilège runtime | Réussi ; pas de superuser/DDL/CREATEDB/BYPASSRLS, maintenance du rôle de test vérifiée | [Journal](e04/evidence/runtime-privileges.log) |
| Suite Django complète | **263 réussis**, 0 échec, 0 ignoré | [Journal](e04/evidence/django-tests.log) |
| Contrats/résolveur/parité/références HTML Node | **63 réussis** | [Journal](e04/evidence/node-hero-tests.log) |
| Frontend existant santé/AUTH/PORT/templates/instances | **23 réussis** | [Journal](e04/evidence/existing-frontend.log) |
| Intégrité BASE | **12 réussis**, 11 sources historiques et 4 empreintes de fixtures conformes | [Journal](e04/evidence/base-integrity.log) |
| CMS historique sur données temporaires synthétiques | **6 réussis** | [Journal](e04/evidence/legacy-tests.log) |
| TypeScript strict des contrats et résolveurs existants | Réussi, code de sortie 0 | Commande E.03 réexécutée |

Total : **367 tests réussis**, 0 échec, 0 ignoré. La suite Django comprend **26
tests E.04** (5 conversion/helper purs + 21 persistance/API/concurrence/migration)
et les 237 tests précédents. Les exécutions intermédiaires de diagnostic ne sont
pas additionnées au total. Les preuves Django livrées proviennent de l'exécution
finale réussie depuis un cluster neuf, après les corrections et compléments.

Cas importants réellement testés : Minimal et Editorial ; UUID/provenance/digest
préservés ; conversion/restauration/conversion répétée ; replay après modification
v2 ; refus d'une nouvelle intention déjà v2/v1 ; absence d'If-Match ; conflits de
version/clé ; archive/suppression/propriété/Membership ; CSRF avec vraie session ;
contraste après fusion ; PUT v1 incapable d'écraser v2 ; révision étrangère ; trigger
SQL UPDATE/DELETE ; détection de snapshot corrompu ; interruption avant et après
remplacement ; même clé concurrente, clés différentes, restore concurrent, course
avec PUT v1 et lock timeout 503 suivi d'un retry réussi ; schéma additif sans
backfill et reverse bloqué ; réponses réelles validées contre OpenAPI.

Le script reproductible utilisé :

```bash
/tmp/port001-venv/bin/python -B scripts/verification/run_e04_isolated.py --engine docker --execute-isolated-migrations --output /tmp/e04-release-evidence
```

Il force son propre SAAS_CONFIG_FILE temporaire, crée et supprime son cluster,
vérifie migration/privilèges puis lance la suite complète dans une base de test
nouvelle. Les journaux ont ensuite été copiés dans e04/evidence, sans credentials.
Les contrôles Node/BASE/CMS ont été exécutés depuis la racine, sans connexion SQL.

## Limites explicitement non validées

**Windows natif E.04 non exécuté.** Le helper propose un chemin initdb/pg_ctl natif,
port libre, ACL privée, sans administrateur, service ou Docker ; ce chemin doit
encore être vérifié sur le PC du demandeur. Les skips éventuels (notamment symlink)
devront être rapportés comme ignorés, pas réussis.

Aucun test navigateur ni nouveau build Studio : aucun fichier du Studio ou du
renderer n'a changé. Références v1 et tests frontend existants réussis. La recette
visuelle manuelle C+D reste séparée. Aucun Hero modulaire, média, animation,
parallaxe ou 3D n'est activé ; les capacités du registre restent indisponibles.

La récupération conserve les valeurs JSON et les documents v2 remplacés ; elle
n'offre pas de fusion automatique ni d'action générique de réapplication d'un
ancien v2. Un replay est une réponse historique, pas une lecture de l'état courant.
Les tests d'interruption vérifient le rollback transactionnel, pas une panne
physique du serveur ou une restauration de sauvegarde externe. Ces révisions ne
remplacent pas une sauvegarde autorisée et vérifiée avant toute future base réelle.

## Fichiers créés et modifiés

Modifiés :

- `backend/config/settings/base.py` — option désactivée par défaut.
- `backend/modules/portfolios/urls.py` — routes privées de transition/récupération.
- `backend/modules/templates/models.py` — CHECK 1/2 et modèle append-only.
- `backend/modules/templates/validation.py` — dispatch v2 avec résolution complète.
- `backend/modules/templates/instance_views.py` — négociation et écritures v2 gated.
- `backend/modules/templates/instance_services.py` — duplication v2 gated.
- `contracts/api/openapi.yaml` — références des contrats E04.
- `docs/tpl001/README.md` — décisions d'approbation et livraison pour revue.

Créés :

- `backend/modules/templates/hero_conversion.py`.
- `backend/modules/templates/transitions.py`.
- `backend/modules/templates/transition_views.py`.
- `backend/modules/templates/migrations/0002_versioned_design_transitions.py`.
- `backend/tests/test_hero_conversion.py`.
- `backend/tests/test_design_transitions.py`.
- `contracts/api/hero-design.v2.json`.
- `scripts/verification/run_e04_isolated.py`.
- `docs/tpl001/e04/recovery-plan.md`.
- `docs/tpl001/e04/conversion-and-recovery.md`.
- `docs/tpl001/e04/windows-isolated.md`.
- `docs/tpl001/e04/evidence/{provision,migrations,schema-check,runtime-privileges,django-tests,node-hero-tests,existing-frontend,base-integrity,legacy-tests}.log`.
- `docs/tpl001/e04/evidence/isolated-environment.json`.
- `docs/tpl001/e04/evidence/validation-summary.json`.
- `docs/tpl001/TPL-001-E04-report.md` — ce rapport.

Les fichiers AUTH, comptes, CMS, Studio, renderer, schémas approuvés, anciens
bundles, leurs digests et migrations historiques restent inchangés. Aucun média,
secret ou export réel ajouté. Le SHA de livraison et le lien de branche sont
fournis dans le message final ; aucune PR, fusion ou déploiement.

## Statut des critères pour revue

| Critère | État livré |
|---|---|
| v1 par défaut, aucune conversion implicite | Implémenté et testé. |
| Conversion explicite avec révision préalable | Implémentée et testée, validation avant écriture. |
| Snapshots/provenance immuables | Préservés ; trigger SQL et empreintes testés. |
| Isolation des comptes et propriété | Tests positifs/négatifs et Membership incohérente sans réparation. |
| ETag / If-Match | Compteur commun, conflits et courses testés. |
| Idempotence / atomicité | Replay, concurrence, timeout et interruptions testés. |
| Retour v1 sans perte de l'état v2 remplacé | Restauration exacte + nouvelle révision récupérable en lecture. |
| Migrations autorisées uniquement sur neuf synthétique | Respecté et gardé ; aucun environnement réel autorisé. |
| Windows natif | **Non exécuté**, commandes isolées fournies. |
| Revue finale du demandeur | **En attente** ; E.04 non déclaré validé. |

Arrêt à E.04. E.05 ou toute application à une base existante demandent une
autorisation distincte.

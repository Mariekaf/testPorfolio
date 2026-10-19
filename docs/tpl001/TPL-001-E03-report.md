# TPL-001.E.03 — Rapport de livraison pour revue

**Statut : implémenté et testé sous Linux, soumis à revue ; non déclaré validé.** E.04 et les tickets ultérieurs ne sont pas commencés.

Branche : `feature/tpl-001-e03`, créée directement depuis la référence approuvée `76e8af02159ccc237a1f7e83f41d2b6d66db1aab`. Historique et état propre vérifiés avant modification. E.02 est approuvée par le demandeur, avec tests Windows natifs rapportés réussis ; cette preuve n'est pas attribuée à E.03.

## Livraison

- Résolveur Python `resolve_heroes` et factory TypeScript `createHeroResolver`, hors application, sans modèle, endpoint, stockage ni conversion.
- Defaults strictement locaux ; fusion déterministe avec priorité des settings, maps responsive indépendantes, remplacement atomique des unions et de la paire layout/version.
- Apparence indépendante du layout : palette, typographie, background, surface et comportement none combinables sous validation.
- Validation des valeurs effectives après fusion et de chacun des trois breakpoints ; contraste text/surface et accent/surface ≥4,5:1 sans arrondi.
- Reset pur par suppression de clés autorisées, idempotent, sans null, avec refus si le résultat effectif devient invalide. Aucune mutation des entrées ou alias entre résultats.
- 55 fixtures communes avec résultats attendus écrits indépendamment des résolveurs ; vraie comparaison des sorties Python/Node, erreurs et documents de reset.
- Références des 12 sources/snapshots/schémas v1 et du HTML statique réel de Minimal/Editorial, en complément des tests renderer existants.

[Règles détaillées et limites](e03/resolution.md) · [Commandes Windows sans base](e03/windows.md)

La résolution des cinq layouts sans prérequis manquants ne signifie pas disponibilité : le registre reste runtime_enabled=false, implemented=false et selectable=false. Product Showcase/Bento restent refusés dans cette matrice de documents. Un ID, une version ou une combinaison inconnue échoue sans fallback Centered.

## Résultats exécutés sous Linux

Python 3.13.5, jsonschema 4.26.0, Node 24.19.0, TypeScript 5.9.3, Ajv 8.20.0. Les suites n'initialisent pas Django et n'accèdent à aucune base. Les tests historiques HTTP utilisent leurs données temporaires synthétiques.

| Vérification | Résultat | Preuve |
|---|---|---|
| Python E.02 + E.03 | **151 réussis** : 90 E.02 + 61 E.03, dont vraie parité Node/Python | [Journal Python](e03/evidence/python-tests.log) |
| Node E.02 + E.03 + références HTML v1 | **63 réussis** : 2 corpus E.02 + 59 résolution E.03 + 2 références v1 | [Journal Node](e03/evidence/typescript-tests.log) |
| Frontend existant santé/AUTH/PORT/templates/instances | **23 réussis** | [Journal](e03/evidence/existing-frontend.log) |
| Vérification BASE et tests d'intégrité | 11 fichiers historiques et 4 empreintes de fixtures conformes ; **12 tests réussis** | [Journal](e03/evidence/base-integrity.log) |
| CMS historique, données temporaires | **6 réussis** | [Journal](e03/evidence/legacy-tests.log) |
| TypeScript strict, résolveur et outils de parité inclus | Réussi, code de sortie 0 | Commande dans le guide Windows |
| npm audit, dépendances hors dev | **0 vulnérabilité signalée** lors du contrôle | Synthèse de validation |

Total : **255 tests exécutés et réussis**, 0 échec, 0 ignoré. Le test de parité compare les 55 cas dans les deux langages ; il ne les ajoute pas une deuxième fois au total. Node manquant fait échouer ce test plutôt que le déclarer ignoré. Les résultats intermédiaires ayant révélé une mauvaise référence de section dans quatre nouveaux vecteurs ont été corrigés dans les fixtures ; les journaux livrés correspondent à l'exécution finale réussie.

Les tests couvrent notamment : priorités contradictoires, défauts responsive locaux, absence de fuite tablette vers desktop, modification du layout sans perte d'apparence, palette partielle sans contraste, seuil #767676/#777777, unions remplacées, reset total/par clé/absent/interdit, reset qui casserait le contraste, versions inconnues, politiques/prérequis refusés, UUID malformé, liens invalides, plusieurs Hero dont un masqué, résultat indépendant et entrées gelées côté TS.

Les références HTML sont obtenues avec le renderer historique réel et les mêmes classes CSS simulées que les tests existants. Les sources CSS sont épinglées séparément, avec uniquement l'équivalence LF/CRLF de checkout pour les fichiers texte. Il ne s'agit **pas** d'une recette visuelle ou d'une capture navigateur. Le nom du test historique WindowsEncodingTest décrit une simulation sous Linux, pas une exécution native Windows.

## Dépendance justifiée et sécurité

Ajv **8.20.0** est ajouté au package content-contracts, licence MIT, version directe exacte et quatre dépendances transitives verrouillées avec intégrités npm. Il applique les schémas Draft 2020-12 approuvés côté TypeScript ; aucune suppression de champs, coercition ou injection de defaults. La compilation n'accepte que des schémas de confiance fournis à la factory, sans réseau. Le point d'entrée existant du package, les routes et le Studio n'importent pas ce module ; aucun coût renderer ajouté par cette livraison.

La validation sémantique TypeScript reprend les invariants nécessaires du document complet, dont le contrôle HTTPS ; la configuration des formats est documentée pour rester cohérente avec jsonschema verrouillé. Les erreurs de résolution sont génériques, sans document privé. Aucun CSS, HTML ou JavaScript exécutable n'est accepté comme configuration. Les textes restent des données copiées. Aucun moteur d'animation ou 3D ajouté.

Avant une intégration navigateur ultérieure, examiner génération Ajv standalone au build et CSP. Les contrastes sur gradient/glass supposent toujours une couche opaque palette.surface derrière le texte ; le résolveur ne prouve pas la conformité visuelle d'un renderer qui n'est pas implémenté.

## Périmètre vérifié

Le seul changement à un fichier existant de documentation est l'index TPL. Les autres fichiers existants modifiés sont le manifeste content-contracts et son lockfile pour Ajv. Les modules E.02, schémas v1/v2 approuvés, bundles/digests, renderer/CSS historiques, AUTH, routes, modèles et migrations restent inchangés. Aucun accès à `.local/`, configuration privée, PostgreSQL ou ancienne base de validation. Aucun merge, PR, déploiement ou capacité activée.

**Non exécutés** : Windows natif E.03, build du Studio, parcours navigateur, tests de base ou migration. Aucun de ces résultats n'est revendiqué. La recette visuelle C+D demeure ouverte et séparée. Il n'y a aucun nouveau rendu à tester visuellement dans E.03.

## Fichiers créés et modifiés

Modifiés :

- `packages/content-contracts/package.json` — Ajv exact.
- `package-lock.json` — dépendances et intégrités.
- `docs/tpl001/README.md` — statut E.02 approuvé et E.03 pour revue.

Créés :

- `backend/modules/templates/hero_resolution.py` — résolution et reset purs.
- `backend/tests/test_hero_resolution.py` — 61 tests, dont vraie parité.
- `packages/content-contracts/src/hero-resolution.ts` — validation, résolution, reset et types effectifs.
- `packages/content-contracts/test/hero-resolution-support.ts` — chargement public des contrats et préparation des cas, tests uniquement.
- `packages/content-contracts/test/hero-resolution-driver.ts` — transport JSON pour la parité.
- `packages/content-contracts/test/hero-resolution.test.ts` — 59 tests de résolution/immutabilité.
- `packages/content-contracts/test/hero-v1-golden.test.mjs` — 2 références HTML v1.
- `contracts/fixtures/hero/resolution.v1.json` — 55 cas communs.
- `contracts/fixtures/hero/v1-reference.v1.json` — empreintes de référence v1.
- `docs/tpl001/e03/resolution.md` — règles et limites.
- `docs/tpl001/e03/windows.md` — commandes sans base.
- `docs/tpl001/e03/evidence/python-tests.log`.
- `docs/tpl001/e03/evidence/typescript-tests.log`.
- `docs/tpl001/e03/evidence/existing-frontend.log`.
- `docs/tpl001/e03/evidence/base-integrity.log`.
- `docs/tpl001/e03/evidence/legacy-tests.log`.
- `docs/tpl001/e03/evidence/validation-summary.json`.
- `docs/tpl001/TPL-001-E03-report.md` — ce rapport.

Le SHA de livraison est fourni avec le lien de branche dans le message final. Le rapport ne s'auto-référence pas avec un SHA antérieur à son propre commit.

## Critères et suite à examiner

| Critère | Livraison pour revue |
|---|---|
| Defaults locaux et overrides | Implémentés, aucune lecture du catalogue source pendant la résolution. |
| Priorités, responsive et reset | Implémentés et testés, desktop indépendant de tablette. |
| Combinaison des dimensions et none | Implémentée, versions/politiques/prérequis refusés sans correction silencieuse. |
| Validation effective et contraste | Effectuée après fusion et après reset. |
| Parité Python/TS et immutabilité | Résultats attendus communs, comparaison réelle et tests de non-alias. |
| Conservation v1 | Sources/empreintes et HTML statique vérifiés, renderer inchangé. |
| Absence d'activation/persistance/migration | Respectée ; capacités toujours indisponibles. |
| Windows natif E.03 | **Non exécuté**, guide fourni, à consigner séparément. |

À examiner : revue du code et de la dépendance Ajv, contrat de sortie transitoire, sémantique des resets et limites de contraste visuel ; exécution native Windows E.03. Aucun blocage Linux restant. **Arrêt à E.03, en attente de validation ; E.04 nécessite une autorisation distincte.**

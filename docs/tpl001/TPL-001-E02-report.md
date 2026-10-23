# TPL-001.E.02 — Rapport de livraison pour revue

**Statut : implémenté, soumis à revue ; non déclaré validé.** E.03 à E.11 non commencés.

Référence approuvée : `fc2f2b3d616de29bd9cb8a9f11a8c8608e1f3d30`, vérifiée avant modification. Branche dédiée `feature/tpl-001-e02`, créée directement depuis cette référence. H01–H07 et E.01 approuvées par le demandeur ; cette décision ne vaut pas validation anticipée de cette livraison.

## Résultat livré

- Design v2 fermé : composition2/content1/presentation2/customization2/experience=null. Schémas v1 conservés intégralement.
- HeroConfig v1 : dimensions layout/apparence/comportement indépendantes, palettes locales sans obligation de choisir un layout, contraintes de gradient/police/surface/responsive, aucun CSS/HTML/JS libre.
- Registre de sept layouts déclarés et capacités d'apparence ; **aucune capacité modulaire implémentée ou sélectionnable**, runtime désactivé. Le renderer v1 reste fonctionnel sans modification.
- Comportement reconnu exclusivement none ; extensions 3D/parallaxe/vidéo/carrousel/scrollytelling rejetées.
- Prévalidation hors application : schéma + invariants de sections, politiques, prérequis, gradients et contrastes explicitement calculables. Aucun convertisseur, résolveur effectif, endpoint, modèle ou écriture ajouté.
- Corpus commun de 81 cas synthétiques UTF-8 positifs/négatifs, utilisé par Python et TypeScript ; types TypeScript déclaratifs hors renderer.
- [Règles exactes, limites et commandes PowerShell](e02/contracts.md) ; [OpenAPI v2 proposé non actif](e02/openapi.v2.proposed.json).

## Preuves de tests exécutés

Environnement **Linux**, Python 3.13.5, jsonschema 4.26.0, Django installé 5.2.18, Node 24.19.0 et TypeScript 5.9.3. Aucune nouvelle dépendance installée ou verrou modifié.

| Vérification | Résultat | Preuve |
|---|---|---|
| Contrats Python E.02 | **90 réussis**, 0 échec, 0 ignoré : 81 vecteurs et 9 tests de frontières | [Journal](e02/evidence/python-contracts.log) |
| Corpus commun côté TypeScript | **2 réussis**, 0 échec, 0 ignoré | [Journal](e02/evidence/typescript-corpus.log) |
| Types TS E.02 en mode strict | Réussi, code de sortie 0 | Commande dans contracts.md |
| Frontend existant santé/AUTH/PORT/renderer/instances | **23 réussis**, 0 échec, 0 ignoré | Commande et résumé ci-dessous |
| Intégrité BASE | **12 réussis**, 0 échec, 0 ignoré | Commande et résumé ci-dessous |
| CMS historique, données temporaires synthétiques | **6 réussis**, 0 échec, 0 ignoré | [Journal](e02/evidence/legacy-tests.log) |
| Référence historique BASE | 11 sources et 4 empreintes de fixtures conformes | `check_base001.py` |
| Bundles Minimal/Editorial | Empreintes exactes et registre historique opérationnel | Test Python dédié |
| OpenAPI proposé | Références, corps/réponses JSON Schema, rejet des champs/version inconnus et contrat de session inchangé | Deux tests Python dédiés |

Total des tests exécutés : **133 réussis**, sans échec ni test ignoré. Les 2 tests TypeScript portent sur la consommation du corpus et les types, pas sur une seconde implémentation du validateur JSON Schema. Aucun test de résolution effective ou de rendu v2 n'est annoncé.

Commandes Linux exécutées depuis la racine, avec l'environnement existant `/tmp/port001-venv` :

```bash
PYTHONPATH=backend /tmp/port001-venv/bin/python -B -m unittest backend.tests.test_hero_contracts -v
node --test packages/content-contracts/test/hero-contracts.test.ts
node node_modules/typescript/bin/tsc --noEmit --strict --module nodenext --target es2022 --allowImportingTsExtensions --types node packages/content-contracts/src/hero-contracts.ts packages/content-contracts/test/hero-contracts.test.ts
/tmp/port001-venv/bin/python -B scripts/verification/check_base001.py
/tmp/port001-venv/bin/python -B -m unittest discover -s scripts/verification/tests -v
/tmp/port001-venv/bin/python -B -m unittest discover -s tests -v
node --test packages/content-contracts/test/health.test.mjs apps/studio/test/auth.test.mjs apps/studio/test/portfolios.test.mjs apps/studio/test/templates.test.mjs apps/studio/test/template-instances.test.mjs
git diff --check
```

Les tests historiques utilisent leur répertoire temporaire dédié, pas `.local/`. Le test nommé WindowsEncodingTest simule un cas d'encodage sous Linux : il ne prouve pas une exécution native Windows. Des avertissements Node existants MODULE_TYPELESS_PACKAGE_JSON sont observés sur les modules Studio ; ils ne provoquent aucun échec et aucun manifeste n'est modifié pour ce ticket.

**Non exécutés** : Windows natif E.02, recette visuelle, build du Studio, suite Django dépendante de PostgreSQL, migrations et tests de migration. Aucun changement d'UI ne justifie un nouveau build dans ce ticket ; les contrats ne sont pas importés par l'application. Aucun service de base n'a été sollicité, aucune configuration de base existante ou privée lue. Les preuves Windows C+D rapportées par le demandeur ne sont pas réattribuées à E.02.

## Critères et limites

| Critère demandé | État à la livraison |
|---|---|
| Schémas fermés et matrice versionnée | Implémentés, tests réussis, à revoir. |
| Dimensions indépendantes et couleurs sans dépendance au layout | Implémentées ; 7 vecteurs positifs dédiés. |
| Sept identifiants, disponibilité honnête | Implémentés ; toute tentative de sélection refusée, tout faux statut d'implémentation rejeté. |
| Contrats typographie/gradient/surface/responsive bornés | Implémentés, valeurs limites et négatives testées. |
| Behavior none uniquement | Implémenté et testé ; aucune dépendance moteur. |
| Fixtures communes et types | Livrés ; validation Python et consommation TS distinguées. |
| Fusion/reset/contraste/combinaisons documentés | Livrés ; le résolveur reste expressément hors E.02. |
| OpenAPI v2 préparé sans activation | Livré et testé, absent de l'index OpenAPI actif. |
| Schémas v1, bundles/digests et renderer historique conservés | Aucun changement ; tests d'intégrité et frontend réussis. |
| Pas de DB, migration, AUTH, CMS ou `.local/` modifiés | Respecté. Aucun endpoint ni écriture ajouté. |

Le contraste sur une **palette partielle** ne peut pas être garanti sans fusion avec les defaults. `validate_design` est volontairement une prévalidation des contrats ; E.03 devra fournir les résolveurs et contrôler l'apparence complète avec `validate_appearance(..., complete=True)` avant toute future activation. Le registre demeure intégralement indisponible. Glass est limité conceptuellement à un décor autour d'une couche de texte opaque ; aucune garantie de rendu n'est revendiquée avant E.05.

Product Showcase et Bento sont déclarés mais refusés comme layout effectif du design v2 actuel : leurs prérequis content v2/médias n'existent pas. Pas de remplacement par Centered, faux média ou composition fictive. L'injection de texte HTML n'est pas une extension de contenu : le renderer historique continue à l'échapper.

## Fichiers créés ou modifiés

Seul fichier préexistant modifié :

- `docs/tpl001/README.md` — index et état d'autorisation.

Fichiers créés :

- `backend/modules/templates/hero_contracts.py` — registre et validation hors application.
- `backend/tests/test_hero_contracts.py` — 90 tests sans initialisation Django/DB.
- `contracts/hero/capabilities.v1.json` — déclarations inactives.
- `contracts/schemas/hero/hero-config.v1.json` — Hero, defaults et dimensions typées.
- `contracts/schemas/hero/capabilities.v1.json` — structure fermée du registre.
- `contracts/schemas/templates/documents/composition.v2.json`.
- `contracts/schemas/templates/documents/presentation.v2.json`.
- `contracts/schemas/templates/documents/customization.v2.json`.
- `contracts/schemas/templates/documents/snapshot.v2.json`.
- `contracts/fixtures/hero/cases.v1.json` — 81 vecteurs synthétiques.
- `packages/content-contracts/src/hero-contracts.ts` — types, aucun validateur ou résolveur runtime.
- `packages/content-contracts/test/hero-contracts.test.ts` — consommation commune et vérification typée.
- `docs/tpl001/e02/contracts.md` — règles et commandes sans base.
- `docs/tpl001/e02/openapi.v2.proposed.json` — proposition isolée.
- `docs/tpl001/e02/evidence/python-contracts.log`.
- `docs/tpl001/e02/evidence/typescript-corpus.log`.
- `docs/tpl001/e02/evidence/legacy-tests.log`.
- `docs/tpl001/e02/evidence/validation-summary.json`.
- `docs/tpl001/TPL-001-E02-report.md` — présent rapport.

La référence documentaire approuvée E.01 reste inchangée. Le commit de livraison et la branche de revue sont indiqués dans le message de livraison ; aucune PR, fusion ou déploiement n'est demandé ou effectué.

## Points à valider avant E.03

1. Revue et acceptation de cette livraison E.02, puis autorisation explicite E.03.
2. Confirmer la granularité des schémas/defaults/politiques et les statuts tous indisponibles jusqu'au renderer qualifié.
3. Examiner les priorités de fusion et de reset, dont l'héritage desktop indépendant de tablet et le maintien des settings lors du changement de paire layout/version.
4. Accepter la stratégie de contraste conservatrice à 4,5:1 et la couche opaque obligatoire derrière le texte pour gradient/glass ; exiger le contrôle post-fusion et la conformité Python/TS en E.03.
5. Examiner le contrat OpenAPI proposé et les erreurs, sans activer la négociation avant le ticket de persistance autorisé.
6. Compléter la recette visuelle C+D et établir la baseline v1 avant acceptation des futures comparaisons visuelles E.03/E.11 ; consigner séparément Windows natif E.02.
7. Maintenir Product Showcase/Bento et les moteurs immersifs hors disponibilité jusqu'à leurs prérequis et tickets approuvés.

Aucun blocage technique constaté pour livrer les contrats. Les contrôles effectifs, le rendu, les migrations et l'activation restent des travaux futurs non autorisés. **Arrêt à la fin d'E.02, en attente de revue.**

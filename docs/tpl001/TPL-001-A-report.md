# TPL-001.A — Rapport de conception

Date : 19 octobre 2026. Branche dédiée : `design/tpl-001-a`, créée depuis `4ce0f6b` (clôture documentaire de PORT-001 ; code accepté `27a0b85`).

**Livré pour revue de conception — validation de A attendue. Aucun développement B/C/D/E commencé.**

## Décision utilisateur appliquée

Le périmètre global est approuvé sous les précisions de la revue : Minimal et Editorial réellement distincts, personnalisation persistante côté serveur, aperçu fidèle, versions et isolation, aucun moteur immersif prématuré. L’autorisation porte uniquement sur la préparation des contrats et de l’architecture. Cette livraison ne constitue pas une bibliothèque fonctionnelle ni une validation de migrations.

## Livrables

| Demande | Proposition livrée |
|---|---|
| Composition versionnée et exemples | Schéma composition v1, deux snapshots complets avec layouts, variantes, ordre et permissions distincts ; descripteurs unavailable, manifeste avec empreintes |
| Contenu et personnalisation | Schémas typés, présentation de base, overrides bornés et exemple ; règles absent/null/false/remise à zéro et invariants serveur documentés |
| Stockage et migration | PortfolioDesign JSONB, compteur Portfolio partagé, requêtes idempotentes ; plan additif sans backfill implicite ni modification des migrations historiques |
| API et erreurs | OpenAPI 3.1 autonome proposé, routes de catalogue/aperçu/création/design ; session/CSRF, If-Match et idempotence 24 h explicités |
| Parcours et inventaire UI | Bibliothèque, aperçu desktop/mobile, sélection, création, personnalisation, sauvegarde et reprise après reconnexion ; composants et responsabilités listés |
| Tests et sécurité | Plan PostgreSQL synthétique, concurrence, duplication, isolation, schémas, navigateur et non-régressions ; Windows distinct |
| Options et décisions | Tableau des alternatives et recommandations dans design.md |

## Vérifications exécutées dans cet environnement Linux

Résultats détaillés : [contract-checks.json](contract-checks.json). Validation statique avec le Python et jsonschema déjà disponibles ; aucune dépendance ajoutée :

- Les cinq schémas proposés passent Draft202012Validator.check_schema ; exemples de snapshots et personnalisation valides, formats explicitement vérifiés.
- Les deux descripteurs restent compatibles avec le schéma template v1 existant et ne sont pas annoncés disponibles.
- Assertions ponctuelles sur cohérence des sections, types/variantes, valeurs par défaut et thèmes des exemples : réussies.
- Cinq exemples négatifs rejetés : champ inconnu, payload d’expérience, null d’override, type de section inconnu, thème non autorisé.
- Cibles des 63 références OpenAPI/JSON Schema résolues. **Pas de validation sémantique complète par un outil OpenAPI spécialisé** ; revue détaillée et tests de contrat futurs requis.
- Vérification des liens locaux et diff de documentation ; fichiers fonctionnels/contrats actifs et preuves PORT inchangés.

Ces vérifications sont des contrôles de conception ponctuels, pas une suite applicative TPL implémentée. Les invariants transversaux restants sont spécifiés, pas présentés comme déjà exécutés par un service. Les 88 tests Linux PORT antérieurs restent des preuves historiques acceptées ; ils ne sont pas réexécutés pour ce dossier.

**Non exécutés : migrations, tests PostgreSQL, renderer, serveur d’API TPL, parcours navigateur TPL, Windows natif.** Aucun test Windows PORT supplémentaire n’est revendiqué et sa réserve non bloquante reste ouverte.

## Fichiers de cette livraison

Modification :

- `docs/tickets/TPL-001.md` : statut du périmètre et autorisation A uniquement, lien vers le dossier.

Créations :

- `docs/tpl001/README.md`
- `docs/tpl001/TPL-001-A-report.md`
- `docs/tpl001/design.md`
- `docs/tpl001/test-plan.md`
- `docs/tpl001/contract-checks.json`
- `docs/tpl001/contracts/openapi.proposed.json`
- `docs/tpl001/contracts/schemas/composition.v1.json`
- `docs/tpl001/contracts/schemas/content.v1.json`
- `docs/tpl001/contracts/schemas/presentation.v1.json`
- `docs/tpl001/contracts/schemas/customization.v1.json`
- `docs/tpl001/contracts/schemas/snapshot.v1.json`
- `docs/tpl001/examples/minimal.descriptor.v1.json`
- `docs/tpl001/examples/minimal.snapshot.v1.json`
- `docs/tpl001/examples/editorial.descriptor.v1.json`
- `docs/tpl001/examples/editorial.snapshot.v1.json`
- `docs/tpl001/examples/customization.v1.json`
- `docs/tpl001/examples/bundle-manifest.proposed.json`

## Décisions restant à valider

1. Catalogue Git immuable, manifeste/digests et deux variantes de composition proposées ; stratégie ultérieure de catégories Creative/Experimental par version de contrat.
2. Stockage PortfolioDesign et documents JSONB distincts, base figée + overrides typés, ancrages de sections, contenu de case studies réduit à des cartes sans modèle métier Projet.
3. API proposée et compteur Portfolio/ETag commun ; extension contrôlée de la duplication existante pour ses futures ressources locales.
4. Idempotence de la nouvelle création uniquement, rétention 24 h, replay de réponse originale et arbitrage après expiration.
5. Plan additif, absence de conversion automatique des portfolios vierges et politique de retour arrière après nouvelles écritures.

Les options, avantages, limites et recommandations sont développés dans [design.md](design.md). Pas de blocage d’accès ou d’environnement pour cette livraison documentaire ; la validation des choix ci-dessus constitue le point d’arrêt demandé avant B/C/D/E. Aucun merge, aucune base réelle, aucun CMS historique ni `.local/` modifié.

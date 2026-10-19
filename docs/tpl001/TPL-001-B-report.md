# TPL-001.B — Rapport d’exécution pour revue

Date : 19 octobre 2026. Branche dédiée **`feature/tpl-001-b`**, issue de la conception approuvée `b151719`.

**Statut : livré pour revue, non encore accepté. C/D/E restent non autorisées.**

Implémentation : `deaf73e`. Durcissement des versions : `6645c9f`. Tests de versions renforcés : `a001b48`. Référence source finale, avec refus des références médias/documents/thèmes non disponibles : **`943b9cc64f3c2ecd28162b1d84876605b4def465`**. Le commit documentaire de livraison vient ensuite et ne remplace pas ces références de code.

**Suivi Windows du 19 octobre 2026 :** sur `730384b`, l’utilisateur rapporte 72 réussites, 1 erreur d’encodage et 1 test symlink ignoré parmi 74 tests Django. [Correctif UTF-8 et relance](TPL-001-B-windows-encoding-fix.md) ; la validation Windows du correctif reste en attente. Les preuves Linux ci-dessous conservent leur contexte initial.

## 1. Ajustements de la revue A intégrés

[design.md, §9](design.md#9-ajustements-de-revue-a--intégrés-avant-tpl-001b) explicite les extensions futures aux palettes, polices, images, vidéos, animations et expériences immersives, avec évolution de schémas et préservation des overrides. La stratégie future MediaAsset/PortfolioAsset traite propriété canonique, références opaques, originaux immuables, dérivés, sécurité, accès privé/public, duplication, rétention et purge. **Aucune table, stockage ou fonction d’upload n’est implémenté.**

Les contenus sont fictifs : Camille Exemple, trois études UX/UI synthétiques et visuels CSS originaux. Aucun client réel, média personnel ou résultat utilisateur n’est revendiqué. Les deux templates sont réellement rendus, pas des captures utilisées comme aperçu.

Les contrats proposés A restent conservés à part. Seules les lectures B ont été activées après contrôle de leurs réponses et erreurs. available est une projection du manifeste versionné, conditionnée aux bundles et capacités de renderer valides ; ce n’est pas une publication ou une création de portfolio.

## 2. Fonctionnement livré

- **Registre Python sans modèle** : fichiers bornés à 256 Kio, UTF-8, clés JSON uniques, chemins locaux/symlinks confinés aux contrats, SHA-256 exact, références et formats validés avec JSON Schema 2020-12. Refus des versions non canoniques ASCII ou dépassant les 30 caractères de la référence PORT.
- Cohérence entre composition, contenu, présentation, source, thème et politiques de personnalisation. Doublons, sections/références absentes, types/variantes incompatibles, expérience non nulle et URL dangereuse refusés. Les variantes disponibles sont limitées aux combinaisons réellement implémentées du renderer.
- Registre sans cache persistant ni réparation : erreur → **503 générique**, aucune entrée partiellement utilisable, pas de chemin privé divulgué. Retours copiés pour éviter de modifier le bundle en mémoire.
- **Minimal** : hero centré, flux vertical et grille de projets. **Editorial** : titres asymétriques, repères marginaux, projet principal puis liste de récits et panneau contact. Même thème `studio-neutral@1.0.0`, différences de composition et hiérarchie vérifiables.
- **PortfolioRenderer partagé** : reçoit un snapshot validé, résout ordre/visibilité/réglages locaux sans modifier la source et rend via une liste fermée de sections. React échappe les textes ; aucune insertion HTML, CSS libre ou récupération distante. Le même composant est testé avec un snapshot local indépendant en mémoire ; **aucune instance persistée n’est revendiquée**.
- Aperçus desktop/mobile via largeur réelle du conteneur et container queries ; mêmes composants et données. Fonctionne aussi sur une fenêtre mobile réelle. Focus et boutons utilisables au clavier. Aucun moteur d’animation ni nouvelle dépendance.

### Routes actives et accès

API authentifiée : GET `/api/v1/templates`, GET `/api/v1/templates/{template_id}/versions/{template_version}`, GET `.../preview`. Catalogue paginé/filtrable côté API ; interface B limitée à l’entrée des deux aperçus, sans le parcours de sélection/création de D.

Studio : `/templates`, `/templates/minimal/1.0.0`, `/templates/editorial/1.0.0`, sous le garde de session AUTH existant. Accès anonyme ou session expirée → connexion. Erreur de service → message générique. Aucun portfolio créé pendant une consultation.

Toutes les écritures de catalogue sont refusées. Les routes from-template/design proposées pour C ne sont pas activées. La bibliothèque complète de sélection, la sauvegarde des personnalisations, l’idempotence de création et les migrations PortfolioDesign restent **à développer en C/D après autorisation**.

## 3. Cohérence OpenAPI vérifiée avant activation

[Contrat B actif](../../contracts/api/templates.v1.json), référencé par l’OpenAPI racine ; contrat session, routes et schémas PORT existants préservés.

Les tests comparent les réponses réelles catalogue/détail/aperçu, filtres/pagination, formats et erreurs 400/401/404/405/409/503 aux schémas et vérifient no-store. Le navigateur vérifie aussi le refus 403 d’une écriture sans CSRF. Les paramètres de version désignent une version exacte, jamais latest ; une version inconnue renvoie 404. Les statuts de disponibilité correspondent à la projection du manifeste et les aperçus indisponibles renvoient 409. Les 29 références locales de contrats B sont résolues sans accès réseau.

Aucun validateur OpenAPI externe n’a été ajouté ; ce sont des contrôles sémantiques et de réponses de l’implémentation B, pas une certification exhaustive de l’ensemble des propositions C. Les réponses streaming de Next peuvent afficher la page « 404 » avec un statut HTML 200 ; le contrat JSON backend renvoie bien 404, et les deux comportements sont vérifiés séparément.

## 4. Résultats exécutés sous Linux

Preuve synthétique : [validation-summary.json](evidence/validation-summary.json).

| Vérification | Résultat |
|---|---|
| Suite Django entière sur PostgreSQL 17.11 synthétique | **74/74** : 57 historiques + 17 TPL, aucun échec/skip |
| Registre/API TPL après durcissement des versions | **17/17**, sous-ensemble déjà compté, pas 17 tests additionnels |
| Intégrité BASE / tests CMS historique | **12/12 + 6/6** |
| Clients health / AUTH / PORT | **3/3 + 4/4 + 6/6** |
| Renderer réel TSX, sécurité et résolution locale | **6/6** |
| Total distinct des tests automatiques | **111 réussis**, sans compter les relances |
| TypeScript et build production Next | Réussis |
| Django check / makemigrations --check --dry-run | Aucun problème / aucun changement |
| PostgreSQL runtime et accès du rôle de tests | 17.11, UTF8, privilèges minimaux vérifiés |
| Sources CMS et preuves PORT | 11 empreintes historiques intactes ; preuves PORT inchangées |
| Chromium desktop/mobile | Deux templates × deux viewports : **4 scénarios réussis**, plus deux captures du mode mobile dans un écran desktop |

Les messages « readiness check failed » du journal Django sont émis par les tests de panne attendue ; la suite termine OK. L’avertissement Node de détection de module TS reste non bloquant ; aucune dépendance ou configuration globale n’a été modifiée pour le masquer.

Les validations portent sur Linux Python 3.13.5, Node 24.19/npm 11.9, PostgreSQL 17.11 réel et Chromium 154.0.8037.57. Le build et les captures concernent le renderer livré ; les contrôles de versions et de références non disponibles ont ensuite été renforcés et leur suite ciblée relancée avec succès.

### Preuves conservées

- [Django complet](evidence/django-tests.txt), [registre/API final](evidence/registry-tests.txt), [renderer](evidence/renderer-tests.txt).
- [Build](evidence/build.txt), [TypeScript](evidence/typecheck.txt), [BASE](evidence/base-tests.txt), [CMS](evidence/legacy-tests.txt).
- [Résultats navigateur](evidence/browser-results.json) et [sortie](evidence/browser.txt).
- [Minimal desktop](evidence/minimal-1365.png), [Minimal mobile](evidence/minimal-390.png), [Editorial desktop](evidence/editorial-1365.png), [Editorial mobile](evidence/editorial-390.png).
- Captures des conteneurs mobile sur desktop : [Minimal](evidence/minimal-container-mobile.png), [Editorial](evidence/editorial-container-mobile.png).

Les retours chariot/espaces de progression du journal de build sont normalisés pour Git, sans modifier les résultats. Captures issues du moteur réel et inspectées visuellement. Vérifiés : cinq sections, trois projets fictifs, absence de débordement, aucune requête externe/erreur de page, commandes au clavier, session et CSRF, connexion/déconnexion, absence de création de portfolio. Aucun audit lecteur d’écran complet revendiqué.

Les comptes de navigateur étaient créés uniquement dans la base de validation synthétique séparée PORT, sans nouvelles migrations, puis les trois comptes de test et leurs ressources de compte/session liées ont été retirés. Aucun compte ou fichier d’authentification livré dans les fixtures/commits.

## 5. Critères de B

| Critère utilisateur | Statut |
|---|---|
| Ajustements documentaires A intégrés avant développement | Fait : extensibilité, médias, rendu réel, démonstration et activation |
| Registre versionné strict et deux bundles | Vérifié, tests positifs et négatifs |
| Deux templates visuellement distincts et professionnels | Rendus réels desktop/mobile, captures inspectées ; appréciation finale soumise à revue |
| Renderer sécurisé partagé et aperçus fidèles | Vérifié par tests TSX et Chromium |
| Références, thème, versions et contenu stricts | Vérifiés par schémas, invariants et tests API sans écriture |
| available uniquement avec bundles et capacités validés | Révision 1 activée après tests ; erreur de registre fermée en 503 |
| Tests et rapport, branche dédiée | Livrés avec références et inventaire |
| Aucun C/D/E, moteur immersif, stockage média ou nouvelle migration | Respecté |
| CMS, `.local/`, bases réelles et absence de merge | Respecté |
| Windows natif | Exécution utilisateur partielle sur `730384b` : **72 réussis, 1 erreur, 1 ignoré** ; correctif UTF-8 à revalider sur Windows |
| Acceptation de B | **En attente de revue utilisateur** |

## 6. Fichiers, démarrage et réserves

[Inventaire exhaustif relatif à `b151719`](TPL-001-B-files.txt). Les changements existants sont limités au raccordement URL/API du SaaS, à OpenAPI, aux commandes de tests npm/CI/PowerShell et à la documentation. Aucun fichier fonctionnel du CMS historique, module métier AUTH/PORT/accounts ou migration existante modifié. Nouveaux fichiers : module stateless templates, schemas/bundles versionnés, renderer, routes d’aperçu, tests et preuves synthétiques. Aucun lockfile ni dépendance ajouté/modifié.

[Commandes Windows et Linux](TPL-001-B-runbook.md). **Windows natif exécuté partiellement par l’utilisateur sur `730384b`, validation du correctif en attente**. L’arrêt à la suite Django ne valide pas les contrôles npm/renderer/typecheck/build suivants ; le test symlink ignoré reste une limitation de l’environnement. CI GitHub ajoutée/étendue mais son exécution distante n’est pas revendiquée.

Aucun blocage Linux restant. Aucun merge ni changement de base réelle. Cette livraison n’autorise ni C/D/E, ni éditeur visuel libre, ni déploiement/publication. Attendre la revue de B avant la phase suivante.

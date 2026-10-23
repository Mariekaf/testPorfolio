# TPL-001.E.05 — Quatre layouts Hero modulaires

**Statut : livré pour revue, non validé par cette livraison.**

Date : 19 octobre 2026. Branche : `feature/tpl-001-e05`.
Base vérifiée : E.04 `2cfbbf53417630ef540c26ffa70b50c8b78daaef`, directement
ancêtre de cette livraison. Le SHA du commit E.05 est fourni lors de la remise ;
les empreintes de sources et preuves sont dans `e05/evidence/manifest.json`.

## Périmètre livré

L'autorisation révisée porte sur quatre layouts : **Centered, Split Screen,
Fullscreen et Typographic**, version `1.0.0`. Chacun possède une composition
visuellement distincte et responsive. Palette, typographie système et ses trois
échelles, fond uni/dégradé et surfaces flat/glass sont combinables indépendamment
du choix de layout, dans les limites des contrats acceptés.

Le nouveau composant React serveur valide le **snapshot v2 complet** avec les
vrais schémas E.02 et le résolveur E.03, puis vérifie ses capacités implémentées.
Il ne reçoit pas une configuration effective non vérifiée, ne modifie pas les
entrées et n'invente aucun fallback. Le rendu est fermé sans `enabled={true}`.
Aucune route Studio/public ne l'importe : l'interface existante et les deux
renderers v1 restent inchangés.

Deux nouveaux tests Python convertissent explicitement en mémoire les snapshots
Minimal/Editorial avec le convertisseur pur E.04, puis vérifient les quatre rendus
réels via Node. Ils démontrent la compatibilité des documents, **sans persistance
ni accès SQL**. Les sessions, permissions, verrouillages, If-Match et révisions
E.04 n'ont pas été modifiés. Aucune migration n'a été créée ou exécutée.

Le registre déclaratif E.02 reste figé. Un registre renderer additif distingue
quatre implémentations des trois layouts futurs et n'annonce aucune sélection
éditeur disponible. Asymmetric, Product Showcase, Bento Grid, versions inconnues
et comportements autres que `none` sont refusés explicitement.

## Validation Linux exécutée

Environnement : Python backend 3.13.5, Node 24.19.0, npm 11.9.0, TypeScript 5.9.3,
Next 16.4.2 et React 19.3.1 déjà verrouillés ; aucune dépendance applicative ajoutée.
Navigateur : Chromium 154.0.8037.57, Playwright 1.62.0 déjà installé dans l'outillage
Python 3.12 du cloud, uniquement pour les tests navigateur.

| Vérification exécutée | Résultat | Preuve |
|---|---|---|
| Contrats/résolution/conversion pure Python et compatibilité E.05 | **158/158** | `e05/evidence/python-tests.log` |
| Tests Node existants + E.05 | **99/99** | `e05/evidence/node-tests.log` |
| Tests de contrôle d'intégrité BASE | **12/12** | `e05/evidence/integrity-tests.log` |
| Tests CMS historique sur données temporaires synthétiques | **6/6** | `e05/evidence/legacy-tests.log` |
| Références historiques et fixture BASE | **11 sources inchangées, 4 empreintes vérifiées** | `e05/evidence/historical-reference.log` |
| Typecheck Next/TypeScript | Réussi | `e05/evidence/typecheck.log` |
| Build Next production, sans déploiement | Réussi | `e05/evidence/build.log` |
| Chromium : quatre layouts × six largeurs | **24 réussis**, contraste et clavier inclus | `e05/evidence/browser-results.json` |
| Textes maximaux et zoom CSS 200 % | **24 réussis**, sans débordement horizontal | même preuve |
| Forced-colors / clavier | **4 réussis** | même preuve |
| Captures réelles desktop/tablette/mobile | **12 PNG** examinés | `e05/evidence/*-{1440,768,375}.png` |

Total unittest/Node : **275 réussis, zéro échec, zéro ignoré**. Les 158 tests Python
incluent les 55 vecteurs de parité réellement exécutés avec Node. Les 99 tests
Node incluent les **deux empreintes HTML v1 exactes** Minimal/Editorial, ainsi que
13 tests E.05 ; un test E.05 couvre les 96 combinaisons de quatre layouts, trois
échelles, deux surfaces, deux palettes et deux types de fond.

Les largeurs navigateur sont 320, 375, 640, 768, 1024 et 1440 px. Vérifications :
contrastes calculés sur les couleurs CSS effectives ≥4,5:1 pour texte et CTA,
surfaces de lecture opaques même avec glass, alignements aux breakpoints,
Tab/focus visible/Entrée vers une vraie section, absence d'erreur JavaScript et
de mouvement avec reduced-motion. Les titres à 160 caractères et CTA à 60
caractères ne débordent pas à zoom 200 %.

Les captures utilisent le vrai renderer et son CSS, sans route applicative
nouvelle. Les pages statiques sont générées dans un dossier temporaire neuf et
servies uniquement sur 127.0.0.1 pendant le test. La politique du navigateur cloud
refuse file:// ; le harness utilise donc ce serveur éphémère de fichiers fictifs.

## Critères et garde-fous

| Critère | Statut |
|---|---|
| Quatre compositions effectivement distinctes | Réalisé, SSR et captures |
| Contrats E.02 / résolution E.03 | Réutilisés sans modification |
| Compatibilité documents E.04 | Conversion pure explicite des deux bundles testée ; aucune écriture |
| Couleurs indépendantes du layout, gradients, typographie, surfaces | Réalisé et combinaisons testées |
| Mobile/tablette/desktop, zoom et contenus longs | Réalisé dans Chromium Linux |
| Contrastes, clavier, reduced-motion, forced-colors | Contrôles exécutés ; pas de certification globale WCAG |
| Fonctionnalité modulaire désactivée par défaut | Prop fermée et absence d'intégration dans les routes |
| Capacités non implémentées refusées | Réalisé, sans fallback |
| v1, sources historiques et bundles immuables | Inchangés ; tests et empreintes réussis |
| Aucune migration / base existante / `.local/` | Aucune opération effectuée |
| AUTH, API, dépendances et lockfile | Inchangés |
| E.06+, éditeur, animations, médias, 3D | Non développés |
| PR, fusion, déploiement | Aucun |
| Validation Windows native E.05 | **Non exécutée, ouverte** |
| Approbation technique de cette livraison | **En attente du demandeur** |

## Fichiers et intégration

La liste exhaustive est dans [e05/files.txt](e05/files.txt). Deux fichiers existants
sont modifiés : `apps/studio/tsconfig.json` ajoute uniquement
`allowImportingTsExtensions` (avec noEmit déjà actif, pour importer le résolveur
accepté sans en changer les imports), et l'index documentaire `docs/tpl001/README.md`.
Les autres fichiers sont nouveaux : composant/CSS, modules de contrats, manifeste,
fixtures synthétiques, tests, harness, documentation et preuves.

[Contrat détaillé de rendu](e05/rendering.md) : intégration future, cible du CTA,
règles de capacité, surfaces opaques, responsive et limites de performance.
[Commandes Windows exactes, sans SQL](e05/windows.md).

## Limites et éléments à revoir

- Windows natif non exécuté. Les succès E.02/E.03 et des tickets antérieurs ne
  valent pas validation E.05 ; commandes reproductibles fournies.
- Pas de validation Safari/Firefox, lecteur d'écran ni appareil mobile physique.
  CSS zoom Chromium est testé ; le changement d'échelle du système Windows ne l'est pas.
- Pas de nouvel essai des transactions/concurrence PostgreSQL E.04 : ces preuves
  acceptées restent dans E.04. Aucun ancien cluster de validation n'a été interrogé.
- Pas de page publique v2, écran Studio modulaire ou sélecteur de layout activé.
  Les quatre rendus sont disponibles au niveau du composant opt-in et du harness.
- Aucun upload/média, police personnalisée, vidéo, parallaxe, animation ou 3D.
  La décoration Split est du CSS ; le Hero Fullscreen ne signifie pas une vidéo.
- Le flou glass reste borné et décoratif ; ses performances sur GPU mobile réel
  devront être évaluées avant activation à grande échelle.
- La recette visuelle manuelle C+D reste séparée. Les PNG E.05 sont des références
  de revue, pas une approbation anticipée ni une capture du Studio en mode v2.

La prochaine décision attendue est la revue d'E.05, notamment ses quatre rendus,
la séparation entre déclarations et implémentations et la frontière d'intégration
opt-in. Aucun ticket suivant n'est commencé.

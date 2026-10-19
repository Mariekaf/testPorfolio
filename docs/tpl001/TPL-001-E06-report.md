# TPL-001.E.06 — Trois nouveaux layouts Hero

**Livraison pour revue — non validée par ce rapport.**

Branche : `feature/tpl-001-e06`. Base acceptée et vérifiée avant modification :
`a3e6e9011d09e72c8f9ca48ce6331eae99a24f1b` (E.05). Date : 19 octobre 2026.
Le SHA de livraison est communiqué à la remise et vérifiable par `git rev-parse HEAD`.
Aucune PR, fusion, mise en production ou opération SQL.

## Résultat fonctionnel

| Layout | Version rendue | Composition réelle |
|---|---|---|
| Asymmetric | 1.0.0 | Texte décalé verticalement, hiérarchie décentrée et illustration latérale étroite ; pile lisible sur mobile |
| Product Showcase | 1.1.0 | Présentation textuelle et panneau graphique évoquant une interface produit, sans média ou donnée inventée |
| Bento Grid | 1.1.0 | Cellule principale de lecture et trois cellules géométriques ; grilles à deux, trois ou quatre colonnes selon largeur |

Les sept layouts sont implémentés dans le composant modulaire opt-in. Les quatre
rendus E.05 conservent leur version 1.0.0 et leur HTML exact. Les nouveaux panneaux
et cellules sont décoratifs/aria-hidden ; seuls les champs existants title,
subtitle et cta_label représentent le contenu utilisateur. Les démonstrations
sont explicitement fictives. Aucun nouveau champ de données utilisateur.

Palettes indépendantes du layout, trois échelles typographiques system-sans,
fonds unis/dégradés et surfaces flat/glass restent disponibles selon les contrats
acceptés. Le texte et le CTA ont toujours une surface opaque dont les contrastes
sont validés à 4,5:1 ; le glass n'est qu'une couche décorative bornée.

## Évolution de contrat explicitement approuvée

L'audit initial a révélé que les anciennes références Product Showcase/Bento
1.0.0 exigeaient des données content-v2 et, pour Product, des médias. Elles étaient
explicitement refusées par E.02/E.03. L'utilisateur a autorisé **« Oui, variante
textuelle versionnée »** après présentation de ce problème.

La solution ajoute le profil de confiance fermé `text-layouts` v1 et les deux
références **1.1.0**. Elle conserve les anciennes références et leurs refus,
sans conversion ou substitution silencieuse. Aucun schéma de document E.02,
bundle immuable ou digest historique n'est changé. Les trois nouveaux layouts
utilisent toujours Design2/composition2/content1/presentation2/customization2,
HeroConfig1 et experience null.

Le résolveur E.03 et les validateurs Python/TypeScript partagent cette extension
via une sélection explicite du profil. Leurs appels par défaut gardent le contrat
historique. Le composant isolé utilise le nouveau profil ; les APIs, le convertisseur
et la validation de sauvegarde E.04 restent inchangés. Les nouvelles références
**ne sont donc pas sauvegardables par les APIs actuelles**. Une intégration
applicative future devra sélectionner explicitement ce contrat et préserver les
contrôles E.04 ; E.06 ne le fait pas. Aucune politique locale de portfolio stocké
n'est élargie. Les fixtures n'accordent ces références qu'à des copies synthétiques.

[Détails et décision](e06/contract-decision.md).

## Preuves Linux exécutées

Environnement : Python backend 3.13.5, Node 24.19.0, npm 11.9.0, TypeScript 5.9.3,
React 19.3.1, Next 16.4.2. Chromium 154.0.8037.57 et Playwright 1.62.0 pour les
vérifications navigateur (outillage Python 3.12 du cloud). Dépendances et lockfiles
applicatifs inchangés ; aucun moteur tiers ajouté.

| Vérification | Résultat final | Preuve sous `e06/evidence/` |
|---|---|---|
| Python : contrats, résolution, conversion pure, rendu, nouveau profil | **163/163** | `python-tests.log` |
| Node : tests existants, sept layouts et références HTML | **116/116** | `node-tests.log` |
| Contrôles BASE : tests du vérificateur | **12/12** | `integrity-tests.log` |
| Tests CMS sur serveur et données synthétiques temporaires | **6/6** | `legacy-tests.log` |
| Empreintes historiques BASE | **11 fichiers inchangés, 4 empreintes de fixture vérifiées** | `historical-reference.log` |
| TypeScript strict des contrats | Réussi | `strict-types.log` |
| Typecheck Next | Réussi après relance séquentielle | `typecheck.log` |
| Build Next production sans déploiement | Réussi | `build.log` |
| Nouveaux layouts × six largeurs | **18 réussis**, clavier/contraste/reduced-motion inclus | `browser-results.json` |
| Nouveaux layouts, textes longs + zoom CSS 200 % | **18 réussis** | même preuve |
| Nouveaux layouts, forced-colors et clavier | **3 réussis** | même preuve |
| Régression navigateur E.05 | **24 largeurs + 24 zoom/textes + 4 forced-colors réussis** | `e05-browser-results.json` |
| Comparaison aux PNG E.05 acceptés | **12 identiques pixel par pixel** | `e05-pixel-regression.json` |
| Références visuelles nouvelles | **9 PNG**, mobile/tablette/desktop | `*-375.png`, `*-768.png`, `*-1440.png` |
| Mesures SSR des sept layouts | 700 rendus chronométrés après chauffe | `performance.json` |

Total final unittest/Node : **297 tests réussis, aucun ignoré**. Les cinq tests
Python E.06 incluent **28 vecteurs communs** avec véritable exécution Node et
comparaison complète des résultats/reset ; ils ne sont pas comptés comme 28 tests
unittest supplémentaires. Les 55 vecteurs historiques E.03 restent exécutés.
Les 17 tests Node E.06 comprennent **168 combinaisons** (sept layouts × trois
échelles × deux palettes × deux surfaces × deux fonds), les quatre références
HTML E.05 exactes et les erreurs de contrat/capacités. Les deux références HTML
v1 Minimal/Editorial restent également vérifiées.

Les tests purs E.04/E.06 couvrent les copies des deux snapshots Minimal/Editorial,
leur conversion explicite en mémoire et le rendu Node des variantes ; aucune
sauvegarde, connexion SQL ou migration n'est effectuée. Les entrées restent
inchangées ; les resets suppriment les clés sans écrire null. Versions inconnues,
propriétés arbitraires, profils altérés, référence hors politique, comportement
futur et contrastes insuffisants échouent explicitement.

Les tests navigateur utilisent le vrai composant SSR et son CSS, dans un harness
statique hors dépôt, servi temporairement sur 127.0.0.1. Largeurs : 320, 375, 640,
768, 1024 et 1440 px. Ils contrôlent aussi la géométrie distincte : décalage
Asymmetric, alignement central du panneau Product, cellules Bento sur plusieurs
lignes. Au total : **91 cas navigateur** (42 largeurs, 42 textes/zoom, 7 forced-colors).
Le zoom utilise les limites title160/subtitle500/CTA60 ; aucune troncature ou
barre de défilement horizontale. Tab, focus visible et Entrée vers une vraie
section sont vérifiés. Les figures décoratives n'ajoutent aucun arrêt clavier.
Les captures desktop et mobile ont été examinées visuellement.

### Incident de vérification résolu

Un premier typecheck a été lancé en parallèle du build : Next remplaçait
`.next/types`, d'où des TS6053 de fichiers générés absents. Le log initial est
conservé dans `typecheck-initial-concurrent-failure.log`. Après achèvement du build,
la même commande séquentielle a réussi, ainsi que le contrôle TypeScript strict.
Aucun test, type ou garde n'a été désactivé et aucun fichier fonctionnel n'a été
modifié pour contourner cet incident. Le guide Windows prescrit la séquence correcte.

## Performance et limites

Mesures indicatives du cloud partagé : médianes SSR **0,495–0,749 ms**, p95
**0,840–1,110 ms** sur les sept fixtures après chauffe. Initialisation du harness
**577,9 ms**, incluant transpilation TSX et imports ; premier rendu **58,7 ms**
avec préparation des validateurs. Ce ne sont pas des cold starts de déploiement.

CSS source commun : **9 548 octets**, gzip indicatif **2 236 octets**, contre
4 769 / 1 500 pour E.05. Aucun client JavaScript, téléchargement média ou moteur
animé ajouté. Ces tailles ne représentent pas un chunk Next effectivement servi :
aucune route n'importe le composant. Pas de mesure Core Web Vitals, GPU mobile,
mémoire sous charge ou débit HTTP. [Rapport détaillé](e06/performance.md).

## Périmètre des fichiers et garde-fous

[Liste exhaustive](e06/files.txt), incluant preuves et captures. Modifications
fonctionnelles limitées au renderer modulaire/CSS, registre renderer et extension
explicite des validateurs/résolveurs ; tests et documentation associés.
Les schémas et bundles existants, renderers v1, AUTH, CMS historique, `.local/`,
modèles, migrations, routes et API sont préservés. Aucune dépendance applicative.
Le registre garde `enabled_by_default: false` et sept `selectable: false`.

## Réserves de revue et suite

- **Windows natif E.06 non exécuté par l'agent** ; commandes sans base fournies
  dans [e06/windows.md](e06/windows.md). La validation Windows E.05 confirmée par
  l'utilisateur ne vaut pas validation E.06.
- Safari, Firefox, lecteur d'écran et appareils physiques non vérifiés. Pas de
  certification WCAG globale ; zoom CSS et forced-colors émulés dans Chromium Linux.
- Pas de nouveaux tests PostgreSQL E.04, ni de sauvegarde/édition de données réelles.
- Nouveaux layouts disponibles uniquement dans le renderer opt-in/harness, sans
  écran, sélecteur, publication ou écriture de ces références via l'API actuelle.
- Pas de média réel dans Product/Bento, ni de contenu structuré supplémentaire.
  Leurs figures ne constituent pas des captures des travaux utilisateur.
- Pas d'éditeur visuel, animation, parallaxe, vidéo, carrousel, scrollytelling ou 3D.
- La recette visuelle manuelle C+D reste un suivi distinct.

E.06 s'arrête à cette livraison. **E.07 n'est pas commencée.** La revue technique et
l'acceptation de ce code restent à la décision du demandeur.

# E.02 — Contrats Hero et registre, règles de conformité

Cette livraison implémente exclusivement les contrats approuvés par E.01 (`fc2f2b3`). Elle ne les branche ni au renderer, ni aux endpoints, ni au stockage. Un document reconnu par ce validateur hors application n'est **pas** un document sauvegardable ou un layout fonctionnel.

## Versions et fichiers

Les contrats exécutables sont sous `contracts/schemas/hero/` et `contracts/schemas/templates/documents/*.v2.json`. La matrice fermée est snapshot2/composition2/content1/presentation2/customization2/experience=null. Les trois textes Hero et leurs limites restent ceux de content v1. Les objets sont fermés ; les versions inconnues, clés inconnues et null explicites sont rejetés.

`composition.v2` impose les defaults Hero et une politique sur chaque section hero et les interdit aux autres types. `presentation.v2` porte les defaults complets d'apparence. Le validateur sémantique exige leur présence sur les seules sections Hero. `customization.v2.sections[].hero` accepte les overrides partiels HeroConfig v1. Les politiques peuvent déclarer les sept layouts ; l'usage effectif de Product Showcase/Bento dans un design de cette matrice est refusé car content v2/médias sont absents. Leur HeroConfig isolée reste reconnaissable comme déclaration future, sans disponibilité.

Les palettes sont indépendantes du layout : modifier uniquement `appearance.palette.accent` ne demande ni nouvelle identité de template ni champ layout. Le thème reste studio-neutral 1.0.0 ; il s'agit de tokens locaux, pas d'une nouvelle ressource thème.

## Déclaration, implémentation et sélection

`contracts/hero/capabilities.v1.json` et `HeroCapabilities` déclarent exactement sept layouts : centered, split-screen, fullscreen, typographic, asymmetric, product-showcase, bento-grid. Toutes les entrées ont declared=true, implemented=false et selectable=false ; runtime_enabled=false. Ces statuts concernent le **renderer modulaire v2**. Les deux variantes du renderer historique restent fonctionnelles et inchangées ; elles ne constituent pas une implémentation de HeroConfig v1.

Les capacités d'apparence sont palette, solid, gradient, system-sans, flat, glass ; le seul comportement contractuel est none. Aucun moteur, URL de plugin ou import dynamique dans le registre. `selectable_layouts()` est vide ; `require_selectable()` refuse même une déclaration connue. Une capacité/version inconnue échoue explicitement, sans fallback Centered. Les lectures renvoient des copies indépendantes.

La version de fichier définit le contrat du registre. Une future qualification fera évoluer explicitement le registre et son lecteur dans un ticket autorisé ; elle ne modifiera pas les paramètres d'une identité/version déjà copiée dans un design. L'état de disponibilité ne doit jamais remplacer une preuve d'implémentation. Les anciens bundles/snapshots et leurs digests ne changent pas.

## Paramètres et limites

| Dimension | Contrat exact |
|---|---|
| layout | id déclaré + version semver ASCII exacte ≤30 caractères ; version connue 1.0.0 dans E.02. Pas de CSS ni composant libre. |
| settings | spacing compact/normal/airy ; alignment start/center ; emphasis quiet/strong. Défauts complets, overrides partiels. Valeurs également limitées par presentation_policy de la section. |
| responsive | Deux maps optionnelles tablet/desktop, uniquement les trois settings. Base mobile-first ; pas de changement structurel de layout par breakpoint. |
| palette | text/surface/accent, hex RGB exact #RRGGBB, longueur 7 ; overrides partiels, defaults complets. Ni alpha, var(), url(), couleur CSS libre ou saut de ligne. |
| typography | system-sans uniquement ; scale compact/balanced/display. Aucun téléchargement de police. Defaults family/scale obligatoires. |
| solid | kind=solid + color hex obligatoire, aucune autre clé. |
| gradient | kind=gradient, angle entier 0..359, 2..4 stops, position entière 0..100 et couleur hex ; positions strictement croissantes vérifiées sémantiquement. Les couleurs des extrémités s'étendent jusqu'aux bords si les positions ne sont pas 0/100. |
| surface | flat sans paramètre ; ou glass avec opacity entière 85..100, blur entier 0..12. Pas d'effet activé maintenant. |
| behavior | Exactement `{ "kind": "none" }`, sans params, callback, timeline ou référence exécutable. |

Le plafond par document reste 262144 octets UTF-8, JSON sans NaN/Infinity ou clé dupliquée. Aucun média, HTML, JavaScript, sélecteur, shader ou propriété CSS arbitraire n'est admis. Les chaînes de contenu existantes restent du texte brut échappé ; elles ne deviennent pas du HTML.

## Fusion et reset — spécification pour E.03, aucun résolveur livré

1. Utiliser uniquement les defaults **locaux** des documents copiés ; ne jamais relire le template source pour remplacer un default existant.
2. Réglages de section : presentation.settings → override presentation historique → hero.layout.settings → override du breakpoint applicable. Clé absente = hériter. Le Studio devra n'exposer qu'un contrôle pour chaque valeur effective.
3. Mobile utilise la base ; tablette utilise base+tablet ; desktop utilise base+desktop, sans reprendre tablet. Seuils futurs de conteneur : <640, 640..1023, ≥1024 px. Le seuil v1 à 650 px reste inchangé.
4. Palette et typography fusionnent par clé autorisée. Le Hero de base est réparti entre composition (layout) et presentation (appearance) ; behavior absent signifie none.
5. Background et surface sont des unions : remplacement complet, sans mélange des branches. Layout id/version se remplace comme une paire ; settings/responsive absents héritent des defaults locaux tant qu'ils restent compatibles avec cette paire. Changer le layout ne supprime ni le contenu ni les overrides d'apparence.
6. Supprimer une clé remet à l'héritage ; supprimer hero restaure tout le Hero local ; null est invalide. Supprimer les conteneurs devenus vides est facultatif, sauf schema_version qui reste obligatoire si hero existe. Cette règle ne supprime aucune donnée de contenu.
7. Si une nouvelle combinaison contredit une politique, refuser avec champ concerné ; ne pas nettoyer silencieusement. Vérifier le document **effectif complet** après fusion avant toute écriture/rendu v2 futur.

La fusion, le reset effectif et les adaptations v1→v2 ne sont pas implémentés en E.02. Les fonctions de validation ne mutent ni ne convertissent leur entrée.

## Contraste, combinaisons et limites de validation

Le calcul applique la luminance relative sRGB WCAG avec seuil 0,04045 et ratio (Lclair+0,05)/(Lsombre+0,05), sans arrondir avant comparaison. Text/surface et accent/surface doivent atteindre **4,5:1** ; ce seuil conservateur couvre le texte des CTA même si certains contrôles ou grands textes peuvent se satisfaire de 3:1. Aucun abaissement implicite dépendant de la taille d'un titre.

Le validateur contrôle les paires de couleurs présentes ensemble et les defaults complets. Une palette partielle n'a pas toujours les deux couleurs à comparer : sa validité contractuelle ne prouve pas son contraste une fois héritée. **E.03 devra résoudre les valeurs puis appeler `validate_appearance(..., complete=True)` sur le résultat complet**, côté serveur et avec conformité TS. Le présent validateur de design est une prévalidation contractuelle, pas une autorisation de sauvegarde. Rien n'est exposé au runtime tant que cette étape manque.

Pour éviter toute fausse garantie sur les gradients/glass, le contrat impose conceptuellement une couche opaque de couleur palette.surface derrière tous les textes/CTA ; glass reste décoratif autour de cette couche. Le futur renderer devra démontrer cette séparation, les états hover/focus et le fallback opaque avant sélection. Ni la couleur d'un stop ni l'opacité d'un effet ne servent de preuve de contraste d'un texte sur arrière-plan variable. Sans cette couche, la combinaison doit rester indisponible jusqu'à une validation de contraste plus complète.

Le validateur de design réutilise les invariants de sections v1 : références exactes, types, ordre, visibilité protégée, projets uniques/liens HTTPS, réglages autorisés. Il ajoute defaults Hero, politique de layout, version déclarée, prérequis de contenu, gradients et contraste explicite. La validation de toutes les valeurs **après fusion** appartient à E.03 ; aucune disponibilité ne peut être déduite de cette seule prévalidation.

## Accessibilité, extensions et performance

Le premier comportement est none ; prefers-reduced-motion doit conserver ce rendu sans déplacement. La future activation de tout moteur exige contenu lisible sans JS, fallback statique, prise en compte des changements de préférence, contrôle pause/clavier et aucun scroll capturé. Vidéo, 3D, parallaxe, carrousel et scrollytelling sont refusés par les schémas actuels.

Les apparences restent scoped au Hero, sans effet sur les contrôles du Studio. Glass/gradient devront être qualifiés avec zoom, focus, mobile et contraste ; aucun rendu ni mesure visuelle n'est livré ici. Les cibles E.01 restent ≤15 Kio gzip de CSS Hero additionnel mutualisé, CLS ≤0,1 et LCP ≤2,5 s sur un profil documenté. Aucun chiffre de performance visuelle n'est présenté comme mesuré en E.02. Le registre n'importe aucun moteur ; aucune dépendance ajoutée.

## OpenAPI inactif

`openapi.v2.proposed.json` est autonome et **absent** de `contracts/api/openapi.yaml` et du routeur. GET/PUT design proposés négocient `Accept-Design-Schema` (absent=1), sans conversion ; 406 design_schema_not_acceptable si le client ne supporte pas l'enveloppe. Les corps sont fermés, PUT accepte content1 avec customization1 ou customization2 ; la version doit correspondre au document stocké, invariant sémantique futur. Un ancien ETag reçoit 412 ; If-Match absent 428. Propriété avant préconditions/négociation, source/permissions protégées, AUTH inchangé, no-store et ETag canonique conservés.

L'API v1 active n'adopte **aucune** de ces nouvelles réponses ou règles en E.02. La route upgrade et son implémentation sont différées à E.04 ; aucun endpoint proposé supplémentaire enregistré. Les tests vérifient les références du document OpenAPI, ses corps/réponses et le maintien du schéma de session existant. Ce sont des tests de contrat, pas des tests HTTP du protocole futur.

## Fixtures communes et commandes sans base

`contracts/fixtures/hero/cases.v1.json` contient 81 cas synthétiques UTF-8, positifs/négatifs, avec target, stage=semantic, valid et document. valid signifie « déclaration contractuelle reconnue », jamais « capacité disponible ». Les cas selection sont tous négatifs. Le fichier est lisible sans transformation par Python et TypeScript ; les deux consomment les mêmes octets. Les tests Python appliquent schémas et contrôles sémantiques ; les tests TypeScript vérifient la consommation du corpus et les types, **sans prétendre fournir un validateur JSON Schema TS**. La conformité des futurs résolveurs des deux langages sera testée en E.03.

Depuis la racine, dans Windows PowerShell, environnement backend et node_modules déjà installés :

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend')
& .\backend\.venv\Scripts\python.exe -B -m unittest backend.tests.test_hero_contracts -v
if ($LASTEXITCODE -ne 0) { throw 'E02 Python contract tests failed.' }
node --test packages/content-contracts/test/hero-contracts.test.ts
if ($LASTEXITCODE -ne 0) { throw 'E02 shared corpus tests failed.' }
node node_modules/typescript/bin/tsc --noEmit --strict --module nodenext --target es2022 --allowImportingTsExtensions --types node packages/content-contracts/src/hero-contracts.ts packages/content-contracts/test/hero-contracts.test.ts
if ($LASTEXITCODE -ne 0) { throw 'E02 TypeScript contract check failed.' }
```

Sauvegarder/restaurer au besoin la précédente valeur de PYTHONPATH dans la session. Ces commandes ne chargent pas config.settings, ne lisent pas de configuration privée et ne connectent aucune base. Ne pas lancer Test-Foundations.ps1 pour ce ticket : il contient des vérifications PostgreSQL et une suite Django avec base. Windows natif reste à exécuter et à consigner séparément.

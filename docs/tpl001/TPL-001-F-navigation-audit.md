# TPL-001.F — Audit et proposition de navigation du Studio

**Statut à la rédaction : conception pour validation.**

Décision utilisateur du 23 octobre 2026 : architecture approuvée et implémentation
F.04 → F.01 → F.02 → F.03 autorisée, sans push automatique. La validation du code
et de la recette reste distincte ; voir le rapport de livraison `f/report.md`.
Référence examinée : `41aaffd73d166ab0cbf6525a8df6d27465d8f7fa`, branche source
`feature/media-001`. Arbre initial propre. Branche documentaire dédiée :
`design/tpl-001-f-navigation`. Aucun push, PR, merge, déploiement ou PUB-001.

## 1. Conclusion de l’audit

Les trois boutons « Bientôt » sont dans **l’espace d’un portfolio identifié**, pas
un menu global du Studio. Ils ne correspondent pas à trois modules métier absents :
des fonctions existent dans deux éditeurs distincts, sans navigation commune.

Proposition : conserver cet ancrage au portfolio, partager la navigation entre sa
vue d’ensemble, ses paramètres et son éditeur, remplacer **Pages par Sections**,
et ouvrir une vue ciblée du même éditeur. Aucune nouvelle API, table, conversion,
fonction de publication ou activation des Hero modulaires n’est nécessaire.

Il ne faut pas promettre les mêmes réglages aux trois templates : les capacités
réellement disponibles diffèrent. Cette proposition ne transforme ni les listes
de projets en entités globales, ni les sections en pages indépendantes.

## 2. Preuves dans le dépôt

| Sujet | Fichier / constat |
| --- | --- |
| Menu « Bientôt » | [`portfolio-manager.tsx`](../../apps/studio/src/components/portfolio-manager.tsx#L88), ligne 88 : boutons désactivés Projets, Pages, Apparence, Publication ; portfolio nommé dans la sidebar. Présent en modes `overview` et `settings`. |
| Routage des éditeurs déjà connu | Même fichier, `actions()` et cartes : `creative-editorial` → `/ready`, autres templates actuels → `/edit`. Ce routage actuel ne doit pas devenir un fallback universel pour un template inconnu. |
| Shell authentifié | [`session-shell.tsx`](../../apps/studio/src/components/session-shell.tsx) : session vérifiée, expiration/déconnexion et thème clair/sombre du Studio. Pas de module global Projets/Pages/Apparence. |
| Protection des routes | [`portfolios/layout.tsx`](../../apps/studio/src/app/portfolios/layout.tsx) : cookie puis `/auth/me`, redirection sans session et en cas d’expiration. Ce contrôle ne remplace pas les permissions par portfolio du backend. |
| Minimal / Editorial | [`template-editor.tsx`](../../apps/studio/src/components/templates/template-editor.tsx) : état `selected`, contenu typé, ordre/visibilité autorisés, présentation locale et aperçu commun. |
| Creative Editorial | [`ready-editor.tsx`](../../apps/studio/src/components/templates/ready-editor.tsx) : groupes de slots, champs de projets, `MediaPicker`, `style_overrides`, palette/police/couleurs et aperçu ; pas de sélection libre de layout. |
| Renderers | `components/templates/portfolio-renderer.tsx`, `creative-editorial-view.tsx`, `ready-preview.tsx` : réutiliser les renderers, ne pas créer un rendu de navigation parallèle. |
| Schémas / provenance v1 | `contracts/templates/{minimal,editorial}/1.0.0/{descriptor,snapshot}.json` ; `PortfolioDesign`, validation Python et contrats TypeScript. |
| Schémas / provenance v3 | `contracts/ready-templates/creative-editorial/1.0.0/` ; `contracts/schemas/ready/snapshot.v3.json` ; `ReadyPortfolioDesign`. Composition verrouillée. |
| Propriété | `modules/portfolios/models.py`, `modules/accounts/services.py`, `modules/portfolios/views.py` : `Portfolio.account`, compte personnel actif, propriétaire et Membership cohérents, suppression logique filtrée. |
| Contrats API | `contracts/api/{portfolios,template-instances,ready-instances,media}.v1.json` ; `backend/config/urls.py`, `modules/portfolios/urls.py`. |

Les chemins backend abrégés ci-dessus sont relatifs à `backend/` ; les composants
sont relatifs à `apps/studio/src/`. Les références concernent la source, pas une
recette navigateur exécutée dans cette intervention.

### Routes Studio réellement présentes

- `/dashboard` : liste des portfolios, sélection par carte/action ; liens vers les
  templates complets et la bibliothèque de médias.
- `/portfolios/new` : création d’un portfolio vierge avec métadonnées.
- `/portfolios/{id}` : vue d’ensemble et menu provisoire.
- `/portfolios/{id}/settings` : informations du portfolio, même menu provisoire.
- `/portfolios/{id}/edit` : éditeur Minimal/Editorial historique.
- `/portfolios/{id}/ready` : éditeur Creative Editorial.
- `/portfolios/ready` : choix/création Creative Editorial, **pas un UUID actif**.
- `/portfolios/media` : bibliothèque privée au niveau du compte, pas par page.
- `/templates`, `/templates/{templateId}/{version}`, `/templates/{templateId}/{version}/use` :
  galerie, aperçu et création Minimal/Editorial.

Il n’existe aucune route Studio autonome `/projects`, `/pages` ou `/appearance`,
ni écran de publication publique. Ne pas fabriquer de liens vers ces URL.

## 3. Matrice demandée

| Rubrique | Fonctionnalités existantes | Fonctionnalités manquantes | Réutilisation possible | Action recommandée |
| --- | --- | --- | --- | --- |
| Projets | Liste locale à chaque design ; ajout, édition, retrait et lien HTTPS. Creative Editorial : couverture média privée, alt/cadrage. | Module global Project, pages de case study et tri des projets par interface. Aucun bouton de réorganisation des éléments de projet dans les deux éditeurs. | Éditeur v1 `case 'projects'` ; v3 slot `selected_projects` ; sauvegarde du document existant. | Ouvrir la rubrique Projets du bon éditeur, sans nouvelle entité, sans ajout de tri. |
| Pages | Sections typées v1 ; groupes de slots et sections fixes v3. Contenu éditable ; visibilité/ordre de certaines sections en v1. | Multipage, routes par page, ajout libre de sections/blocs ; réorganisation/masquage de sections Creative Editorial. | Liste de sections v1 et groupes de champs v3 déjà implémentés. | Renommer **Sections** ; exposer les contrôles existants, structure v3 explicitement conservée. |
| Apparence | v1 : espacement, alignement, emphase par section. v3 : palettes, quatre couleurs, polices autorisées, reset et contraintes de contraste. Hero : contenu et présentation selon template. | Réglages globaux palette/police v1 dans l’UI, thème universel, CSS libre, sélection des sept layouts, effets immersifs. | Contrôles actuels, validateur et même renderer d’aperçu. | Ouvrir une vue Apparence adaptée à la famille ; accès au Hero contextuel, aucune nouvelle capacité activée. |

### Différences par template à conserver

| Capacité | Minimal 1.0.0 | Editorial 1.0.0 | Creative Editorial 1.0.0 |
| --- | --- | --- | --- |
| Famille de document courante de l’éditeur | Design v1 | Design v1 | Document v3, slots de contenu v2 |
| Hero initial | `hero-centered` | `hero-split` | Composition Creative Editorial verrouillée |
| Projets dans l’UI | Jusqu’à 24 ; titre 160, résumé 1 000, URL HTTPS facultative | Identique | Jusqu’à 6 ; titre 120, résumé 300, lien externe facultatif et couverture privée |
| Ordre initial des sections | Hero, projets, présentation, compétences, contact | Hero, présentation, compétences, projets, contact | Navigation, Hero, présentation, projets, contact, pied de page |
| Ordre modifiable | Projets/présentation/compétences selon positions autorisées | Présentation/compétences/projets selon positions autorisées | Non exposé ni permis par cette composition |
| Visibilité | Hero obligatoire ; autres sections toggleables ; contact non déplaçable | Identique | Pas de contrôle de visibilité de section dans cet éditeur |
| Projets réordonnables par UI | Non | Non | Non |
| Réglages d’apparence existants | Présentation par section, valeurs selon `presentation_policy` | Identique, rendu distinct | `ink-lime` / `paper-cobalt`, couleurs background/surface/text/accent, `system-sans` / `system-serif` versionnées, reset |
| Médias dans cet éditeur | Pas de champs d’images projet/Hero | Pas de champs d’images projet/Hero | Logo, portrait, couvertures via MEDIA-001 |

Le déplacement de **sections** v1 ne signifie pas réorganisation des **projets**.
Un tableau JSON conservant un ordre ne suffit pas à déclarer un contrôle de tri
existant. De même, les références couleur/typo d’un snapshot ne constituent pas
une UI de personnalisation globale v1.

## 4. Données, API et permissions

### Aucun modèle métier nouveau

`PortfolioDesign` contient `composition`, `content`, `presentation`, `customization`
et la version de schéma 1/2 ; les projets sont des éléments de `content.sections`.
`ReadyPortfolioDesign` contient un document JSON v3 ; les projets sont dans
`content.slots.selected_projects.items`. `ReadyDesignRevision` conserve les révisions.
L’audit ne trouve pas de modèle métier Project ou Page autonome dans les modules
SaaS présents. Les paragraphes/blocs de texte riche v3 ne sont pas un éditeur libre.

Propriété canonique inchangée : User → Account personnel autorisé → Portfolio →
design. Pas de nouvelle propriété dupliquée dans une navigation ou un état local.

| Usage | Endpoint existant à réutiliser |
| --- | --- |
| Métadonnées / sélection | `GET /api/v1/portfolios`, `GET /api/v1/portfolios/{id}` |
| Design Minimal / Editorial | `GET/PUT /api/v1/portfolios/{id}/design` |
| Creative Editorial | `GET/PUT /api/v1/ready-portfolios/{id}` |
| Validation / révisions v3, si nécessaire à l’éditeur existant | `POST .../{id}/validate`, `GET .../{id}/revisions` |
| Images | Endpoints MEDIA-001 existants et `POST /api/v1/ready-portfolios/{id}/media` pour leur résolution privée |

Les préfixes abrégés des deux endpoints v3 sont `/api/v1/ready-portfolios`.
Les PUT restent strictement `{content, customization}` avec ETag/`If-Match` et
compteur `Portfolio.version` canonique. Ne pas envoyer composition, thème, source,
compte ou présentation immuable depuis les nouvelles vues de navigation.

`PortfolioBase` applique IsAuthenticated/session, CSRF, compte autorisé et filtre
`deleted_at`. Les autres comptes reçoivent un 404 ; un menu client ne vaut jamais
permission. `DesignDetail` vérifie le schéma négocié ; les écritures v2 restent
gardées. `ReadyDetail` verrouille, contrôle la version, refuse l’archive, valide
le document et les médias du compte, puis crée une révision. Aucun de ces flux
ne change avec la proposition.

Les pages actuelles `/edit` utilisent par défaut Design v1. Une ancienne conversion
v2 ne doit pas être présentée comme éditable en v1 : négociation 406/écriture gardée
restent des contraintes réelles. Ne pas forcer `Accept-Design-Schema`, un flag ou
une conversion pour rendre un lien apparemment fonctionnel.

## 5. Proposition UX/UI à approuver

### Organisation contextuelle unique

Au niveau global : conserver Dashboard, choix des templates et médias ; pas de
module global Projets/Sections/Apparence ni de sélection automatique du premier
portfolio. Une action globale éventuelle renvoie à la liste « Choisissez un portfolio ».

Au niveau d’un portfolio : une seule sidebar partagée, avec **nom, template et
état** clairement visibles, puis :

1. Vue d’ensemble.
2. Projets.
3. Sections (remplace Pages).
4. Apparence.
5. Paramètres.

« Mes portfolios » permet de changer de contexte sans inventer un état global
persisté. Ne pas stocker le « portfolio actif » dans localStorage/session entre
utilisateurs. L’UUID de l’URL et les réponses autorisées sont la source du contexte.
Le thème clair/sombre du Studio reste distinct de l’apparence du portfolio.

La publication reste une information non interactive « Publication publique
indisponible », sans faux lien ou bouton « Bientôt ». Cela ne supprime ni ne change
les états métier de publication/visibilité.

### Cibles proposées, non encore implémentées

| Intention | Minimal / Editorial | Creative Editorial |
| --- | --- | --- |
| Projets | `/portfolios/{id}/edit?panel=projects` | `/portfolios/{id}/ready?panel=projects` |
| Sections | `/portfolios/{id}/edit?panel=sections` | `/portfolios/{id}/ready?panel=sections` |
| Apparence | `/portfolios/{id}/edit?panel=appearance` | `/portfolios/{id}/ready?panel=appearance` |

Ces paramètres sont une **proposition d’état UI**, pas des URL déjà fonctionnelles.
Aucune route API ni page métier supplémentaire. `panel` est une enum locale fermée ;
une valeur inconnue affiche la vue par défaut de l’éditeur autorisé, sans modifier
le document. Ce défaut UI n’est jamais un fallback de template/layout inconnu.
Les URL `/edit` et `/ready` actuelles sans paramètres gardent leur comportement.

- **Projets** : afficher les champs et actions existants de la liste de projets,
  avec aperçu et bouton Enregistrer communs. État vide utile « Aucun projet —
  Ajouter un projet » ; pas de lien vers une case study inexistante.
- **Sections v1** : liste actuelle, sélection d’une section, champs de contenu,
  afficher/masquer et monter/descendre strictement selon le snapshot. Section
  masquée toujours retrouvable pour la réactiver.
- **Sections v3** : groupes actuels dans l’ordre de la composition, ouverture du
  groupe choisi ; pas de plus/drag-and-drop pour modifier cette composition.
  Texte discret « La structure de ce template est conservée ».
- **Apparence v1** : section sélectionnée, espacement/alignement/emphase autorisés,
  reset existant. Accès explicite au Hero pour sa présentation ou ses textes dans
  Sections ; pas de palette ni sélecteur de polices v3 injecté en v1.
- **Apparence v3** : contrôles `style_overrides` existants et aperçu ; raccourci
  vers le groupe Hero de Sections pour portrait/titre/CTA. Pas de nouveau layout,
  gradient, surface ou animation ajouté à ce ticket.

### Conserver le brouillon et la sauvegarde

Une seule instance d’éditeur, un seul `draft`, une seule version/ETag, un seul
bouton Enregistrer pour le portfolio. Changer de rubrique ne doit provoquer ni
unmount/remount, ni rechargement du snapshot, ni perte des saisies ou médias locaux.
La navigation de panneau ne déclenche aucune sauvegarde et aucun PUT.

Les changements de panneau (y compris retour/avance navigateur dans le même
éditeur) ne quittent pas ce brouillon. Les protections existantes de départ doivent
être ajustées uniquement pour reconnaître cette navigation interne : quitter le
portfolio, changer de portfolio, se déconnecter ou recharger conserve la confirmation
existante. Ne pas supprimer globalement les intercepts de liens/popstate.

Un panneau n’est pas un enregistrement indépendant : Enregistrer sauvegarde le
document courant complet, y compris les changements effectués dans les autres
rubriques. Les erreurs de validation et conflits 412 restent visibles ; aucun
écrasement automatique, retry de PUT ou perte du brouillon en cas de changement
rapide de panneau. Pendant une mutation, conserver les règles actuelles de l’éditeur.

### États contextuels

| État | Comportement proposé |
| --- | --- |
| Dashboard sans sélection | Liste actuelle ; état vide et actions de création/choix de template. Pas de faux UUID ni écran Projets vide. |
| Portfolio sans design | Vue d’ensemble/paramètres utilisables ; message « Aucun template associé », liens vers les parcours de création existants. **Ne pas appliquer un template en place** : ce flux n’existe pas. |
| Portfolio archivé | Accès à l’aperçu et panneaux en lecture seule lorsqu’un design est disponible ; restauration depuis la vue d’ensemble. Ne pas réactiver les mutations. |
| Portfolio supprimé / autre compte | Erreur contrôlée issue de l’API, sans nom/cache du précédent portfolio ; retour Dashboard. |
| Source/version/schéma non pris en charge | Message clair et retour Vue d’ensemble ; aucune substitution par Minimal, Editorial ou Centered. |
| API indisponible / chargement | État explicite et Réessayer ; pas de contenu ou de liens dérivés d’un ancien UUID. |
| Session expirée | Flux AUTH actuel ; pas de sauvegarde anonyme ou de contournement. |

### Accessibilité et responsive

Sidebar gauche sur desktop, navigation horizontale compacte et retour au portfolio
sur mobile, sans deuxième arborescence concurrente. En-tête nom/template/statut
sur chaque vue ; noms longs qui reviennent à la ligne, sans débordement à 320 px.
`aria-current` sur la rubrique active, libellés explicites, focus visible, ordre DOM
logique. À l’activation d’un panneau, déplacer le focus vers son titre de façon
prévisible sans voler le focus lors d’une saisie. Fonctionner au clavier, zoom
200 %, forced-colors et reduced-motion ; pas d’animation nécessaire.

## 6. Découpage recommandé après validation

Estimations indicatives pour développement + tests ciblés, hors revue et recette
Windows ; incertitude principale : partage de layout sans réinitialiser les éditeurs.

| Tâche | Complexité / effort indicatif | Dépendances | Critères d’acceptation principaux |
| --- | --- | --- | --- |
| F.04 — Contexte et navigation partagée | Moyenne à élevée, 2–3 j | Validation de cette proposition | Contexte UUID validé ; mapping des trois templates connus ; sidebar dans overview/settings/edit/ready ; paramètres UI fermés ; états vierge/archive/erreur ; identité sans fuite entre comptes ; maintien des drafts au changement de panneau. |
| F.01 — Accès aux projets | Moyenne, 1–2 j | F.04 | Les deux familles ouvrent la bonne liste ; ajout/édition/retrait uniquement ; sauvegarde/réouverture ; limites respectées ; aucun tri ou modèle Project inventé. |
| F.02 — Sections plutôt que Pages | Moyenne, 1–2 j | F.04 | Libellé Sections ; sélection de contenu v1/v3 ; ordre/visibilité v1 contraints ; composition v3 inchangée ; pas de multipage implicite. |
| F.03 — Accès à l’apparence | Moyenne, 1–2 j | F.04 ; cohérence de sélection avec F.02 | Contrôles v1 locaux et v3 globaux existants ; AA/typo/reset inchangés ; accès Hero contextuel sans activation modulaire. |
| Recette transversale | Moyenne, 1–2 j | F.01–F.04 | Cas multi-template/multi-portfolio, responsive/clavier, conflits, persistance et non-régression validés et documentés. |

Ordre : F.04, F.01/F.02, F.03, recette consolidée. Aucun parallélisme ou démarrage
n’est autorisé par ce document. Un composant partagé de navigation et un petit
adaptateur de capacités UI sont préférables à trois écrans réimplémentant les champs.
L’éventuel `app/portfolios/[id]/layout.tsx` et les hooks de panneaux sont **à concevoir
pendant F.04**, pas des fichiers créés par cet audit. Lire les guides Next locaux
requis par `apps/studio/AGENTS.md` avant toute implémentation future.

### Fichiers concernés par l’implémentation future

- `apps/studio/src/components/portfolio-manager.tsx` : remplacer les placeholders.
- `components/templates/template-editor.tsx`, `ready-editor.tsx` : cibler les
  contrôles existants, partager les panneaux sans dupliquer `draft` ou `save`.
- `app/portfolios/[id]/{page,settings/page,edit/page,ready/page}.tsx` et éventuel
  layout contextuel partagé, sous réserve du fonctionnement Next 16.
- `app/style.css`, modules CSS des deux éditeurs : navigation et responsive.
- Composant de navigation et adaptateur UI proposés, sans persistance ni API.
- Tests Node/TypeScript et scripts de recette navigateur dédiés.

Aucune modification nécessaire identifiée des modèles, migrations, API, bundles
immuables, AUTH ou CMS. Toute nécessité nouvelle de ce type doit être expliquée
et soumise avant élargissement du périmètre.

## 7. Plan de tests et preuves attendues

| Niveau | Cas à couvrir | Critère |
| --- | --- | --- |
| Tests UI/unitaires | Mapping template/version, `panel`, UUID/contextes, états vierges/archives ; template inconnu ; v2 non éditable par v1 | Aucun fallback de métier et aucune destination fabriquée. |
| Navigateur, chaque template | Vue d’ensemble → Projets/Sections/Apparence → Paramètres ; ouverture directe des URL ; retour/avance | Bonne instance, bonne rubrique, état actif, aucun 404 pour un contexte supporté. |
| Modification | Ajouter/modifier/retirer un projet ; champs de sections ; réglages d’apparence ; enregistrer, reload et rouvrir | Même contrat de données, persistance réelle ; projet/portfolio distincts jamais confondus. |
| Brouillon transversal | Modifier dans Projets, aller vers Apparence puis Sections ; retour navigateur ; annuler un départ ; changer de portfolio | Saisies/aperçu conservés dans le même brouillon ; confirmation seulement aux sorties effectives. |
| Concurrence / erreurs | Deux onglets, ETag obsolète, 412 ; échec réseau et validation ; clics rapides | Ni double sauvegarde ni écrasement ; saisies conservées, erreur compréhensible. |
| Permissions | Session absente/expirée, UUID d’autre compte, suppression/archivage depuis un autre onglet | Contrôles backend maintenus ; refus et absence de fuite même avec URL directe. |
| Aucun contexte | Dashboard vide, plusieurs portfolios, portfolio vierge | Choix explicite ou état utile ; jamais de premier portfolio sélectionné silencieusement. |
| Spécificités | v1 sections fixes/obligatoires ; v3 palette AA, média privé, structure verrouillée ; limites 24/6 projets | Aucun contrôle nouveau hors contrat ni capacité masquée exposée par navigation. |
| A11y / visuel | Clavier, focus, 320/390/768/1280 px, zoom 200 %, forced-colors, reduced-motion | Pas de débordement horizontal global ou focus perdu ; état actif lisible sans dépendre de la couleur seule. |
| Non-régression | Suites existantes, TypeScript strict/build Next, renderer/snapshots/digests, sauvegarde et téléchargement média | Rendus et contrats conservés ; nouvelles captures des trois templates aux largeurs utiles. |

Les tests Node actuels de `apps/studio/test/` couvrent surtout les helpers/API,
pas une preuve de navigation visuelle : compléter avec navigateur réel. Réutiliser
les scénarios `browser_tpl001_cd.py`, `browser_ready_e0704.py`, `browser_media001.py`
comme références, sans lancer un runner touchant à une configuration habituelle.

Pour les futurs tests nécessitant PostgreSQL : uniquement **cluster PostgreSQL 17
natif neuf**, comptes et médias synthétiques, port/stockage nouveaux et détruits
après preuve ; jamais la base habituelle ni la démo persistante. Windows natif,
Python 3.13 et Node 24, sans Docker. Aucun test SQL n’est exécuté dans cet audit.
Si l’environnement de réalisation ne permet pas cette vérification, consigner
la limite et les commandes Windows ; ne pas déclarer une recette native réussie.

## 8. Risques et décisions à valider

1. **Valider le renommage Pages → Sections**, cohérent avec les données actuelles.
2. **Valider le contexte exclusivement par portfolio** et l’absence de module global.
3. **Valider les panneaux d’un seul éditeur**, sans nouvel écran métier/API ;
   préciser que la sauvegarde inclut tout le brouillon, pas seulement le panneau.
4. **Valider les limites différentes par template**, notamment palette/typo v3
   seulement, pas d’images v1, pas de réorganisation de projets ajoutée ici.
5. **Valider Publication comme information indisponible**, sans lien actif.
6. Risque principal : navigation Next/rechargement des composants et interception
   des sorties. Preuve navigateur requise avant d’annoncer l’absence de perte de saisie.
7. Risque de confondre édition des informations et changement de template d’un
   portfolio vierge : ce dernier reste une capacité absente et n’est pas inventé.
8. Source/version inconnue ou design v2 : incapacité d’édition explicite, pas une
   exception silencieusement contournée par la nouvelle navigation.

## 9. Tickets ultérieurs réellement nécessaires, hors TPL-001.F

- Modèle Project global et réutilisation inter-portfolios, pages dédiées de projets,
  UX Case Study Builder et multipage : nouvelles spécifications/contracts/permissions.
- Réorganisation des éléments de projets par UI : petit ticket distinct à cadrer
  si souhaité ; ne pas la présenter comme déjà développée.
- Sélection libre des sept Hero, extension de styles/surfaces/gradients, animations
  et 3D : tickets d’intégration dédiés ; conserver les flags et renderers actuels.
- Application/changement de template sur un portfolio vierge/existant : stratégie
  de compatibilité, récupération et approbation séparées.
- Publication publique, domaines et versions publiées : PUB-001 non démarré.

## 10. Périmètre de cette intervention

Lecture du dépôt et des contrats ; extraction hors ligne des sections des bundles
pour comparer leurs capacités. Aucun serveur, test navigateur, migration, compte,
stockage ou connexion PostgreSQL lancé. Aucun accès à `.local/` ou aux bases de
recette persistantes. Les tests listés sont **un plan**, pas des résultats acquis.

Seul ce document est ajouté, sur une branche dédiée issue de la référence vérifiée.
Aucun composant, route, contrat, bundle, permission ou fichier fonctionnel n’est
modifié. **À la rédaction, attente de validation avant F.01–F.04 ; autorisation ultérieure consignée en tête.**

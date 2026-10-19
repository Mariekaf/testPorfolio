# TPL-001.E.01 — Architecture proposée des Hero modulaires

Statut : **proposition pour revue, aucune implémentation autorisée par ce document**.

Audit du 19 octobre 2026, dépôt `Mariekaf/testPorfolio`, référence `feature/tpl-001-cd`, commit `f95da77`. Branche documentaire locale : `design/tpl-001-e01-hero`. Aucun push, accès aux bases, changement de dépendance ou migration dans cette étape.

Le demandeur rapporte les tests automatisés Windows C+D réussis ; leur exécution n'a pas été reproduite dans cet audit. La recette visuelle manuelle C+D reste ouverte. Les preuves historiques conservent leur statut à leur date. La nouvelle définition de E comme éditeur de Hero remplace, pour cette proposition, l'ancien libellé de validation globale : seule **E.01** est actuellement autorisée.

## 1. Conclusion et décisions à examiner

Un template reste une composition initiale de portfolio. Un Hero devient une section composée par un résolveur de capacités : **layout + apparence + comportement**, avec contenu indépendant. Il n'y aura pas de template distinct pour chaque combinaison.

| Proposition | Conséquence |
|---|---|
| H01 : conserver intégralement le chemin de rendu v1 | Aucun remplacement implicite de `hero-centered` ou `hero-split`, ni changement des anciens bundles. |
| H02 : introduire une enveloppe de design v2 et un contrat Hero v1 distinct | Validation et dispatch explicites ; changement contrôlé futur de la contrainte SQL qui impose actuellement v1. |
| H03 : porter les overrides locaux dans `customization.v2` | La sauvegarde reste un remplacement atomique du contenu et de la personnalisation ; les documents source ne deviennent pas modifiables par l'éditeur. |
| H04 : autoriser les combinaisons via capacités versionnées | Les sept layouts sont des cibles de conception ; seuls les layouts réellement implémentés et testés seront sélectionnables. |
| H05 : commencer avec comportement `none`, sans ressource distante | Aucun moteur d'animation, upload, vidéo ou 3D activé par anticipation. |
| H06 : conversion explicite avec précondition et révision de récupération | Pas de conversion à la lecture, au déploiement ou pendant une migration de structure. |
| H07 : appliquer les seuils responsive au conteneur du portfolio | L'aperçu et l'instance ont le même rendu à largeur égale, indépendamment des panneaux du Studio. |

Ces choix sont nouveaux et soumis à validation. La séparation des documents, l'immuabilité des sources, la propriété par Account et le compteur `Portfolio.version` sont déjà implémentés ; les propositions ne constituent pas une approbation du futur code.

## 2. Audit vérifiable de l'existant

Chemins ci-dessous relatifs à la racine du dépôt.

| Fichier / contrat actuel | Constat | Évolution future concernée |
|---|---|---|
| `backend/modules/templates/registry.py` | Vérifie empreintes, chemins, thème, versions, invariants ; `LAYOUT_VARIANTS` lie les variantes au layout global. Le manifeste exige renderer `1.0.0`. | Ajouter un registre de capacités et un dispatch de contrats ; conserver les validations v1. |
| `contracts/templates/manifest.v1.json`, `minimal/1.0.0/`, `editorial/1.0.0/` sous `contracts/templates/` | Bundles chargés et copiés, empreintes SHA-256 des octets. | Ne rien réécrire ; publier de nouvelles versions seulement après réalisation et validation. |
| `contracts/schemas/templates/documents/{snapshot,composition,content,presentation,customization}.v1.json` | Objets fermés ; Hero = trois textes ; réglages = spacing, alignment, emphasis ; expérience exclusivement null. | Nouveaux schémas, sans élargir rétroactivement v1. |
| `backend/modules/templates/models.py` | JSONB existants ; contraintes `tpl_design_schema_v1` et `tpl_no_experience_v1` ; pas d'owner dupliqué. | Réutiliser JSONB ; permettre explicitement v2 dans une future migration additive contrôlée. Garder expérience null au premier lot. |
| `backend/modules/templates/validation.py` | Valide exclusivement snapshot v1, puis invariants du registre ; plafond 256 Kio. | Sélection de schéma par version, erreurs fermées, validation indépendante de la disponibilité actuelle du catalogue. |
| `backend/modules/templates/instance_views.py` | PUT accepte exactement content/customization ; autorisation, If-Match et verrou avant écriture ; composition/presentation/experience protégées. | PUT v2 typé, sans ouvrir ces champs ; conversion séparée. |
| `backend/modules/templates/instance_services.py` | Copie profonde, contenu initial neutre, duplication indépendante, provenance et digest conservés. | Étendre la copie aux nouveaux documents/références autorisées ; aucune référence mutable au template. |
| `apps/studio/src/lib/template-render.ts` | Types et résolveur v1 ; calcul des overrides, ordre et visibilité protégés. | Union discriminée v1/v2 et résolution Hero pure/déterministe. |
| `apps/studio/src/components/templates/portfolio-renderer.tsx` et `.module.css` | Même renderer catalogue/instance ; Hero textuel, thème light fixe, style piloté par layout global ; container query actuelle à 650 px. | Déléguer les seuls Hero v2 à des composants scoped, sans modifier les sélecteurs v1. |
| `template-editor.tsx`, `template-preview.tsx`, `template-thumbnail.tsx` dans ce même dossier | Édition typée, brouillon local, conflit conservé ; aperçu réel desktop/mobile ; vignette rendue et réduite. | Contrôles progressifs, aperçu tablette, capacités et états indisponibles ; aucun moteur lourd dans les cartes. |
| `apps/studio/src/lib/template-instances.ts` | Session/CSRF AUTH, ETag, erreurs ; pas de contenu stocké dans localStorage. | Transport versionné, sans modifier le contrat d'authentification. |
| `contracts/api/{openapi.yaml,templates.v1.json,template-instances.v1.json}` | Contrats actifs catalogue et instances. | Ajouter le contrat v2 et tester sa cohérence avant activation ; ne pas modifier ces fichiers en E.01. |

Le contenu n'accepte actuellement ni image, ni carte Hero, ni lien CTA libre. Le renderer ne comporte pas d'animation. Les sept layouts ne sont donc pas déjà disponibles. Le stockage JSONB ne permet pas d'ajouter librement une propriété : schémas, validation sémantique, types TS, SQL et clients doivent évoluer ensemble.

Réutilisables : registre immuable et ses contrôles de chemins/empreintes, résolution des sections, primitives typographiques/thème, renderer partagé, protections de visibilité et d'ordre, API atomique/ETag, duplication, isolation PORT et session AUTH. Les sélecteurs CSS du Hero v1 doivent rester isolés plutôt qu'être généralisés au risque de modifier les anciens portfolios.

## 3. Architecture cible et responsabilités

```text
Bundle Git versionné ── copie initiale ──> PortfolioDesign privé
                                             │
                        validation JSON + invariants + capacités
                                             │
                    résolveur pur : defaults locaux + overrides
                                             │
                     HeroResolved (non persisté, versionné)
                         │             │                │
                      layout       apparence       comportement
                         └──────── renderer partagé ─────┘
                            catalogue / aperçu / instance
```

Trois identifiants différents : `composition.layout` organise tout le portfolio ; `section.variant` identifie le rendu historique ; `hero.layout.id` choisit seulement la composition interne du Hero v2. Un Hero Split pourra appartenir à un portfolio Minimal, sous réserve de capacité déclarée. Aucun changement des autres sections.

Le registre de capacités est livré avec le code, immuable par version, sans plugins exécutables téléchargés. Une entrée décrit id/version, schémas reconnus, slots et types acceptés, paramètres bornés, layouts responsive compatibles, besoins en médias, comportement autorisé, fallback et statut de disponibilité. Les documents copiés embarquent leurs références et politiques nécessaires ; un retrait du catalogue n'invalide pas une instance existante. Les implémentations historiques restent installées tant que des documents les référencent.

Un résolveur Python et un résolveur TypeScript appliqueront le même contrat et les mêmes fixtures de conformité ; il ne s'agit pas de prétendre partager directement un module entre ces deux langages. Le serveur fait autorité. Le résultat effectif n'écrase jamais les valeurs héritées sauvegardées.

### Répartition des documents proposée pour le premier lot v2

| Document | Version / rôle |
|---|---|
| snapshot | v2 : enveloppe avec références de versions explicites. |
| composition | v2 : reprend les sections, garde le layout global ; ajoute pour chaque Hero des defaults de layout et une politique de capacités bornée. Aucun composant arbitraire. |
| content | v1 conservé dans le premier lot : title, subtitle, cta_label, mêmes limites et ancre interne vers projets. Un futur content v2 ajoutera explicitement les slots médias/cartes. |
| presentation | v2 : conserve thème et réglages existants ; ajoute les defaults d'apparence Hero par section. |
| customization | v2 : conserve ordre, visibilité et overrides existants ; ajoute `sections[].hero` décrit ci-dessous. |
| experience | null dans le premier lot ; un futur document versionné portera timelines, scènes et interactions. |

Une matrice de versions autorisées remplace toute combinaison libre : le premier snapshot v2 admet exactement composition2/content1/presentation2/customization2/experience null. Le marqueur Hero v1 est un quatrième niveau de versionnement, distinct du semver du bundle et de `Portfolio.version`.

## 4. Proposition de configuration Hero

Exemple **documentaire non accepté par les contrats actuels**, extrait de customization v2 :

```json
{
  "schema_version": 2,
  "sections": [{
    "section_id": "hero",
    "hero": {
      "schema_version": 1,
      "layout": {
        "id": "split-screen",
        "version": "1.0.0",
        "settings": {"spacing": "normal", "alignment": "start", "emphasis": "quiet"},
        "responsive": {"tablet": {"alignment": "center"}}
      },
      "appearance": {
        "palette": {"text": "#182F25", "surface": "#F6F8F1", "accent": "#294438"},
        "typography": {"family": "system-sans", "scale": "balanced"},
        "background": {"kind": "solid", "color": "#F6F8F1"},
        "surface": {"kind": "flat"}
      },
      "behavior": {"kind": "none"}
    }
  }]
}
```

### Contrat normatif proposé pour HeroConfig v1

Tous les objets sont fermés (`additionalProperties:false`). `schema_version` est obligatoire et constant 1. Les trois dimensions sont optionnelles dans un override ; leurs defaults sont complets dans les documents locaux de base. Les objets vides inutiles peuvent être omis. `null` n'est pas un mécanisme de remise à zéro.

| Champ | Forme et limites proposées |
|---|---|
| layout | Objet avec id/version obligatoires si présent. id parmi les sept identifiants du tableau suivant ; version semver ASCII exacte, longueur ≤30, paire connue obligatoire. settings et responsive optionnels. Aucun import de composant. |
| layout.settings | Partial des trois réglages existants : spacing compact/normal/airy, alignment start/center, emphasis quiet/strong. |
| layout.responsive | Seulement tablet et desktop ; mêmes clés de settings, sans changement de layout structurel entre breakpoints dans le premier lot. Les valeurs de base sont mobile-first. |
| appearance.palette | Partial text/surface/accent, couleurs `^#[0-9A-Fa-f]{6}$`. Tokens strictement locaux au Hero ; pas de changement de l'identité du thème. |
| appearance.typography | family parmi les polices d'un registre local ; uniquement system-sans initialement. scale compact/balanced/display ; valeurs CSS générées par le renderer, jamais fournies par l'utilisateur. |
| appearance.background | Union fermée : solid {color} ; gradient {angle entier 0..359, stops de 2 à 4 {color, position entier 0..100}}. Positions strictement croissantes. Aucun `url()`, SVG ou chaîne CSS. |
| appearance.surface | Union fermée flat ; glass {opacity entier 85..100, blur entier 0..12}. Fallback opaque et contraste vérifié ; glass sélectionnable uniquement après tests sur backgrounds autorisés. |
| behavior | Exactement {kind: none} dans le premier contrat activable. Aucun champ params libre. |

Pour les réglages existants d'une section Hero v2 : defaults presentation.settings → override presentation existant → layout.settings → override du breakpoint applicable. Cette priorité permet de conserver les contrôles historiques ; l'éditeur présente ensuite une seule source de contrôle Hero et n'écrit pas deux valeurs concurrentes. Les autres sections gardent leur résolution actuelle.

Pour les dimensions Hero : defaults composition/presentation → override local. Les maps de tokens et réglages fusionnent par clé autorisée ; les unions background/surface et la paire layout id/version sont remplacées atomiquement. Le changement de layout n'efface pas le contenu. Retirer une clé restaure l'héritage local, jamais le bundle distant. Si un changement rend un réglage incompatible, le serveur refuse avec erreur de champ ; l'éditeur propose une remise à zéro explicite, sans nettoyage silencieux.

Defaults sûrs des nouveaux bundles : Centered pour Minimal et Split pour Editorial, spacing normal, alignment center pour Centered/start pour Split, emphasis quiet, palette du thème studio-neutral light copiée localement, system-sans/balanced, background solid sur la couleur de fond du thème, surface flat, behavior none. Aucun média requis, autoplay ou effet glass par défaut. Les valeurs responsive absentes héritent de la base ; desktop n'hérite pas d'un override tablette. La conversion d'un ancien document conserve d'abord ses valeurs effectives plutôt que de lui appliquer ces defaults de nouveaux bundles. Le résolveur considère behavior absent comme none ; une configuration future nécessitant experience non null devra utiliser une nouvelle matrice de versions et une évolution SQL séparée.

Invariants : un seul override par section existante ; `hero` uniquement sur type hero ; toute paire de capacité doit être installée et autorisée par la politique locale ; aucun élargissement des permissions via le client ; tableaux et textes bornés ; limite actuelle de 256 Kio conservée. Le serveur valide après fusion, notamment contraste, slots requis et référence de section. Le frontend valide pour l'ergonomie mais ne remplace pas le serveur.

### Sept layouts et règles de disponibilité

| ID cible | Composition / responsive | Condition de disponibilité |
|---|---|---|
| centered | Texte centré ; largeur de lecture bornée. | Première cible statique. |
| split-screen | Deux zones, empilées sur mobile, texte avant visuel dans le DOM. | Première cible statique ; zone décorative optionnelle, aucune image fictive inventée. |
| fullscreen | Min-height adaptée au viewport, contenu extensible, aucun scroll capturé. | Validation du zoom, petits écrans et chrome mobile. |
| typographic | Hiérarchie typographique forte, tailles bornées. | Titres longs, accents, zoom et overflow testés. |
| asymmetric | Grille asymétrique visuelle, ordre de lecture stable. | Réduction à une colonne ; pas de réordonnancement sémantique CSS. |
| product-showcase | Texte + visuel produit explicite. | Contrat média/contenu futur requis ; indisponible tant que le slot produit n'existe pas. |
| bento-grid | Texte + 2 à 6 cartes structurées. | Content v2 et schéma de cartes requis, indépendants d'un moteur d'animation. Aucune collection JSON libre. |

Les layouts deviennent disponibles individuellement après validation, pas après simple ajout à un enum. Aucun fallback silencieux d'un ID inconnu vers Centered : erreur explicite. L'absence facultative d'un visuel peut utiliser un rendu textuel déclaré dans la capacité ; une ressource obligatoire manquante interdit la sélection/sauvegarde.

### Extensions préparées, non admises par HeroConfig v1 initial

Un futur contrat versionné pourra ajouter background image/video et slots visuels via des **UUID MediaAsset**, jamais des URLs ou chemins client. La frontière média déjà proposée dans `design.md` §9 est conservée : propriétaire Account, association autorisée au portfolio, état prêt/quarantaine, MIME détecté, empreinte, dimensions, variantes, alt ou rôle décoratif et point focal. Aucun upload, stockage ou endpoint média créé ici. Dérivés publics uniquement à la publication explicite ; pas de fuite d'un média privé dans une miniature.

Un futur behavior référencera une entrée d'un document experience versionné par section/slot stables. Les types carousel, parallax, scroll-sequence et scene-3d auront chacun un schéma fermé, un moteur/version, des paramètres bornés et un rendu statique de secours. Les timelines ne contiendront ni sélecteurs CSS arbitraires, ni fonctions, expressions ou shaders fournis par l'utilisateur. Un événement pourra cibler une action déclarée, pas appeler du JavaScript libre. Les coordonnées temporelles et spatiales ne seront pas intégrées au contenu textuel.

GSAP pourra devenir un adaptateur de timeline après choix de licence, budget et tests ; Three.js un adaptateur de scène distinct chargé à la demande. Aucune de ces dépendances n'est justifiée pour les Hero statiques. Une future expérience ne doit pas changer l'URL, intercepter le scroll ou masquer un contenu essentiel sans contrat d'accessibilité spécifique.

## 5. Responsive, accessibilité et performance

Pour v2, seuils de **conteneur** proposés : mobile <640 px, tablette 640–1023 px, desktop ≥1024 px. Le renderer utilise des container queries CSS, pas un calcul de viewport au montage ; SSR et hydratation restent déterministes. v1 conserve son seuil actuel à 650 px et ses styles. Tester notamment 320, 375, 639, 640, 768, 1023, 1024 et 1440 px avec les panneaux ouverts/fermés.

Une structure sémantique conserve un H1, les titres et liens réels, un ordre DOM logique et le focus visible. CTA actuel vers projets conservé ; pas de faux bouton vide. Pas de texte tronqué pour tenir dans un layout ; zoom 200/400 %, navigation clavier, textes longs et absence de débordement horizontal à 320 px. Contraste WCAG AA : 4,5:1 texte normal, 3:1 grand texte et contrôles pertinents. Sur gradient, tester le contraste du texte sur toute sa zone ; au premier lot, imposer une surface opaque validée derrière le texte si une preuve de contraste n'est pas possible. Pas de texte directement sur média sans surface contrôlée.

`prefers-reduced-motion: reduce` est prioritaire : contenu complet immédiatement visible, aucun déplacement décoratif, parallaxe, autoplay ou scroll forcé. Le futur moteur écoutera aussi les changements de préférence en cours de session. Le mode sans JS doit conserver contenu et CTA. Carrousel futur : contrôle pause, clavier, état accessible et aucune annonce continue ; vidéo future : poster et contrôle, pas d'autoplay sonore. Une erreur WebGL doit laisser une présentation statique lisible.

Objectifs à mesurer, **non mesurés en E.01** : aucune dépendance JS supplémentaire pour les layouts statiques ; CSS Hero additionnel mutualisé cible ≤15 Kio gzip ; CLS ≤0,1 ; LCP cible ≤2,5 s selon profil mobile documenté, puis p75 terrain après publication future. Réserver les dimensions des médias ; ne pas lazy-loader le visuel LCP ; ne charger les moteurs lourds ni dans les cartes de catalogue ni dans les aperçus inactifs. Réduire blur et couches transparentes sur mobile. Tout dépassement de budget doit être rapporté avant activation, avec protocole reproductible réseau/CPU.

## 6. Compatibilité, sauvegarde et API proposées

### Matrice de compatibilité

| Situation | Règle proposée |
|---|---|
| Bundle Minimal/Editorial 1.0.0 | Octets et empreintes inchangés ; rendu v1 conservé. |
| Design v1 existant | GET, édition et duplication v1 continuent ; aucun ajout JSON à la lecture. |
| Nouveau client lisant v1 | Dispatch vers le renderer historique ; accès aux Hero modulaires via action explicite uniquement. |
| Nouveau design v2 | Références de contrats/capacités exactes et renderer v2 installés ; pas d'accès par client ne déclarant que v1. |
| Catalogue retiré | Instance toujours validée et rendue depuis ses documents locaux et capacités conservées. |
| Ancien serveur ou client devant du v2 | Échec explicite, jamais suppression des champs ou écriture partielle par interprétation v1. |

Les futurs bundles compatibles v2 auront de **nouvelles versions explicites**, choisies lors de la livraison, et de nouvelles empreintes. Leurs valeurs initiales peuvent reproduire les deux identités visuelles sans coupler Hero et template. Le digest d'une instance reste celui de son bundle source : ce n'est pas le hash du design personnalisé. Une conversion ne change ni source_template ni source_digest pour simuler une nouvelle provenance.

### API : proposition non active

Conserver les routes et le contrat AUTH. Les endpoints design/catalogue-preview recevront une négociation explicite `Accept-Design-Schema: 1,2` ; absence = 1 pour les anciens clients. Une réponse expose sa version. Sur GET d'un document non supporté par le client : 406 `design_schema_not_acceptable`, après contrôle de propriété. Aucun downgrade silencieux. Il faudra ajouter cet en-tête aux contrats et à la configuration cross-origin si utilisée, sans modifier les cookies/session. Réponses privées no-store.

PUT design reste `{content, customization}`, avec versions embarquées correspondant au design courant ; version incohérente/inconnue = 400 `invalid_design`. Un client ayant conservé un ancien ETag reçoit d'abord le conflit 412 après autorisation ; même avec un ETag récent, un corps v1 ne peut écraser un design v2. Conserver 428 sans If-Match, 404 pour cible étrangère/supprimée, archive en lecture seule, compteur canonique incrémenté une seule fois.

Une conversion future sera une action distincte, proposée `POST /api/v1/portfolios/{id}/design/upgrade`, CSRF + If-Match, corps fermé avec `target_schema_version:2` et version du convertisseur. Une prévisualisation de conversion est sans effet de bord. L'API de conversion, ses schémas et erreurs doivent être revus avant développement ; rien n'est enregistré actuellement. L'éditeur doit expliquer qu'enregistrer reste privé et ne publie pas ; le système de publication n'est pas ajouté dans E.

### Plan de migration futur, sans exécution dans ce ticket

1. Ajouter les schémas et dispatch v1/v2, puis le renderer capable de lire les deux, avant toute écriture v2. Conserver tous les anciens fichiers de migration et bundles.
2. Proposer une migration de structure qui remplace la contrainte schema_version=1 par l'ensemble explicite {1,2}. Elle n'altère aucun document ; experience reste SQL NULL. Tester sur PostgreSQL 17 synthétique depuis AUTH/PORT/C+D et depuis les designs v1. Ne pas lancer sur une ancienne base de validation.
3. Pour permettre une conversion en place récupérable, proposer une table append-only `PortfolioDesignRevision` liée au design, contenant ancien snapshot complet, version Portfolio d'origine, hash, version du convertisseur et date. Propriété dérivée du portfolio, mêmes protections d'accès, jamais publique. Cette nouvelle table exige une validation préalable ; elle ne remplace pas les JSONB courants. Pas de simple journal contenant les données privées en clair dans les logs.
4. Après sauvegarde autorisée, conversion utilisateur explicite : verrou Portfolio puis Design, vérification If-Match/état/propriété, capture de révision et écriture v2 dans une même transaction. Même UUID portfolio/design, mêmes contenus/états/provenance ; version Portfolio +1. La conversion inclut les anciennes valeurs effectives de réglages et des defaults locaux déterministes. Aucun retrait de champ inconnu ou réparation de propriété.
5. Conserver le rendu v1 jusqu'au choix explicite ; montrer les différences avant conversion, sans promettre un rendu pixel-identique du v2. Une restauration est une nouvelle mutation versionnée, jamais une décrémentation de compteur. Si la révision de récupération n'est pas approuvée, **bloquer la conversion en place** et proposer seulement une copie explicitement demandée (nouveaux UUID, original intact).
6. Déploiement futur : désactiver les écritures v2 par défaut, vérifier les deux lectures puis activer progressivement. Après données v2, ne pas rétrograder vers un serveur ne lisant que v1 et ne pas supprimer la contrainte/tables pour forcer le rollback. Préférer arrêt des écritures et correction en avant ; restauration d'une sauvegarde seulement sur décision explicite.

Ni sauvegarde ni migration réelle n'est autorisée par E.01. Le protocole BASE de sauvegarde des données locales reste applicable, notamment aux fichiers absents de Git ; aucune inspection de `.local/` n'est nécessaire pour ce plan.

## 7. Découpage proposé de TPL-001.E

**Tous les tickets après E.01 restent non autorisés.** Les sous-lots de cette proposition pourront être ajustés à la revue ; leur présence ne déclenche pas leur développement.

| Ticket | Dépendances | Périmètre et critères d'acceptation |
|---|---|---|
| E.01 — Architecture Hero | C+D implémenté | Audit sourcé, schéma proposé, règles de compatibilité, backlog et risques soumis ; décisions H01–H07 et récupération examinées. Statut : présent document, à revoir. |
| E.02 — Contrats et capacités | Approbation E.01 | Nouveaux schémas fermés et matrice des versions ; registre layouts/apparence ; behavior none seulement ; fixtures valides/invalides communes Python/TS ; OpenAPI cohérent ; aucun bundle v1 modifié, aucune migration réelle. |
| E.03 — Résolution et compatibilité | E.02 | Résolveurs purs conformes, priorité explicite et refus des valeurs inconnues ; dispatch v1 inchangé ; tests golden DOM/styles/captures Minimal/Editorial ; titres/CTA/ordre et hash des sources préservés. |
| E.04 — Persistance et conversion contrôlée | E.02, E.03 ; validation de la révision | Migrations additives testées uniquement sur DB synthétiques neuves PostgreSQL 17 ; GET sans mutation ; négociation client, PUT v1/v2, If-Match, rollback transactionnel, restauration et duplication testés ; aucune conversion implicite. |
| E.05 — Renderer statique, lot 1 | E.03 | Centered/Split réels et distincts, scoped CSS ; palette, gradient, typographie et glass validés ou indisponibles ; même moteur catalogue/instance/aperçu ; aucune dépendance d'animation ; tests SSR/XSS/contraste. |
| E.06 — Studio Hero progressif | E.04, E.05 | Layout/Apparence/Comportement séparés ; réglages avancés progressifs ; unavailable expliqué ; reset par clé, conflits conservés, brouillon non perdu ; aperçus desktop/tablette/mobile ; sauvegarde privée sans publication. |
| E.07 — Autres layouts textuels | E.05 | Fullscreen, Typographic, Asymmetric activés individuellement après tests clavier/zoom/overflow/DOM ; combinaisons validées sans nouvelles versions de template pour chaque variante. |
| E.08 — Contrats de contenu et médias | E.02 ; spécification média séparée approuvée | Proposition content v2/slots et frontière MediaAsset/PortfolioAsset, alt/crops, ownership et duplication ; aucune URL arbitraire. Stockage/upload nécessitent ticket et autorisation propres, pas implicites ici. |
| E.09 — Product Showcase et Bento | E.07, E.08 et résolution média réelle si nécessaire | Rendu responsive opérationnel ; carte 2..6 et médias prêts autorisés ; absence/étranger/quarantaine refusés ; pas de maquette annoncée disponible. |
| E.10 — Contrat Experience | E.02 ; revue distincte | Document versionné et cibles stables, paramètres typés, fallback/reduced-motion, budget et modèle d'exécution validés ; aucun GSAP/Three.js, parallaxe, vidéo ou carrousel activé par ce seul ticket de contrat. |
| E.11 — Qualification du lot statique | E.04, E.06, E.07 ; E.09 si inclus | Matrice sécurité/responsive/visuelle/performance, preuves Linux + Windows distinctes, revue manuelle et rapport ; seuls les composants qualifiés sont available. Peut clore un premier lot sans E.08–E.10. |

La recette visuelle C+D peut continuer en parallèle de la conception. Sa clôture et une baseline visuelle approuvée sont requises avant d'accepter les comparaisons de non-régression E.03/E.11. Les moteurs d'expérience, scènes 3D, vidéo et parallaxe feront l'objet de tickets ultérieurs séparément approuvés ; ils ne sont pas une dépendance de l'éditeur statique.

### Preuves attendues lors de l'implémentation future

- Schémas : propriétés inconnues, null, versions incohérentes, dimensions extrêmes, doublons, couleurs/gradients invalides, ID/semver Unicode trompeurs et surcharge JSON refusés.
- Conformité : mêmes fixtures de fusion et mêmes refus en Python/TS ; modifications des seules dimensions choisies ; reset et duplication indépendants ; sources immuables.
- Sécurité : isolation inter-comptes, session/CSRF inchangés, aucun HTML/CSS/JS interprété, ressource étrangère invisible, absence de fuite via erreurs et thumbnails ; précondition et archive inchangées.
- Migrations : aller depuis schéma actuel avec documents synthétiques, préservation UUID/données/états, rollback transactionnel d'une conversion invalide, reprise/conflits, lecture v1 après ajout v2, comportement explicite d'un client ancien.
- Rendu : v1 de référence, sept layouts seulement lorsqu'implémentés, largeurs frontières, mobile/tablette/desktop, zoom/clavier/lecteur d'écran, reduced-motion et sans JS ; Firefox/Chromium et Windows natif distingués.
- Performance : profils réseau/CPU et versions navigateur consignés ; coût initial/mémoire/CLS/LCP mesurés ; aucune scène active dans la grille de bibliothèque.

## 8. Risques et mesures

| Risque | Mesure et limite |
|---|---|
| Régression CSS des anciens Hero | Chemin v1 isolé, captures avant changements ; ne pas renommer des sélecteurs partagés sans preuve. |
| Explosion combinatoire des variantes | Registre de capacités, paramètres bornés, tests pairwise plus cas critiques exhaustifs, refus des combinaisons non qualifiées. L'indépendance conceptuelle n'impose pas toutes les combinaisons. |
| Deux implémentations de validation divergentes | Schémas et corpus communs, invariants testés des deux côtés ; serveur autoritaire. |
| Ancien client écrasant v2 | Négociation explicite, version de corps stricte et ETag ; jamais de conversion descendante automatique. |
| Publication accidentelle | Documents privés, aucune publication dans E ; future publication par snapshot validé séparé, manuelle. |
| Perte lors de conversion ou rollback | Révision atomique et sauvegarde autorisée ; mise à niveau en place bloquée sans récupération validée. |
| Glass/gradient illisible ou coûteux | Surfaces contrastées, blur borné, fallback opaque, activation après mesures. |
| Médias privés, SSRF, fichiers dangereux | Références opaques et contrôle Account/Portfolio ; pas de fetch URL arbitraire ni upload anticipé. |
| Animation provoquant inconfort ou charge GPU | none par défaut, reduced-motion prioritaire ; adaptateurs isolés et chargement différé futur, fallback statique. |
| Dérive de provenance / bundles réécrits | Digest du bundle conservé, capacité versionnée, nouveaux fichiers plutôt que modification d'anciens snapshots. |
| Coût de conservation des anciens renderers/révisions | Politique de rétention et de support à valider avant activation, pas de purge implicite ; une référence existante reste lisible. |

## 9. Périmètre livré et validation de cette étape

Livraison documentaire uniquement : ce rapport et son lien dans l'index TPL. Aucune dépendance, API active, schéma actif, application, migration ou fixture modifiée. Aucun test d'application ou de base exécuté dans E.01 ; les résultats C+D ne sont pas présentés comme de nouveaux résultats. Contrôles de livraison : liens locaux, exemple JSON et whitespace Git, puis vérification des seuls fichiers documentaires modifiés.

Décisions demandées à la revue : H01–H07 ; première livraison limitée aux layouts statiques qualifiés ; convention de versions imbriquées ; négociation de contrat ; priorité des overrides ; ajout futur d'une révision de récupération avant conversion en place. Après validation seulement, E.02 pourra être autorisé explicitement. Rien dans ce document ne vaut fusion, déploiement ou accord d'accès à une base réelle.

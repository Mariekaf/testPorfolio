# TPL-001.E.07.01 — Templates de portfolios prêts à l'emploi

Version 0.1 — **PROPOSITION POUR REVUE, NON APPROUVÉE**. 19 octobre 2026,
Africa/Douala. Branche `design/tpl-001-e0701-ready-templates`, issue du commit E.06
`f579f0dd3af147316115ae366dc2bcc798721db8`. E.05/E.06 sont validées selon la décision
utilisateur, y compris les tests Windows rapportés ; aucune nouvelle exécution
Windows n'est revendiquée ici.

Cette livraison est documentaire. Les JSON sous `e0701/` sont des propositions
non chargées par l'application ; aucun contrat approuvé n'est élargi. Aucun accès
SQL, migration, média réel, route nouvelle ou implémentation E.07.02.

## 1. Décision produit proposée

Une bibliothèque propose des **portfolios complets**, chacun avec une direction
artistique conservée. Le propriétaire remplace les contenus et, facultativement,
les couleurs/polices autorisées ; il ne doit pas reconstruire une mise en page.

La référence « Form & Play » est décrite dans la demande mais son image n'est pas
présente dans le contexte accessible. Cette étude retient la typographie ample,
le portrait, les blocs projets, la navigation et l'asymétrie décrits ; elle ne
prétend ni avoir inspecté le visuel ni en copier les ressources. Une maquette
originale de Creative Editorial devra faire l'objet d'une revue visuelle avant
son statut available. Aucune image ni police protégée n'est récupérée ici.

| Notion | Responsabilité | Modifiable par le propriétaire |
|---|---|---|
| Layout | Primitive structurelle, notamment les sept Hero E.05/E.06 | Seulement si une politique de template l'autorise ; verrouillé dans le premier template |
| Template complet | Sections, rythme, proportions, superpositions, variantes responsive, politique de styles, démonstration et ressources sous licence | Pas de déplacement, z-index, CSS ou suppression structurelle libre |
| Slot | Contenu typé lié à un emplacement sémantique stable | Valeur et métadonnées expressément permises, dont alt/cadrage |
| Personnalisation | Ensemble borné de tokens et options approuvés pour ce template | Couleurs autorisées et paire typographique reconnue |
| Instance | Copie de la composition/politique versionnée, contenu privé, références médias et version canonique Portfolio.version | Contenu et overrides, via contrôle de propriété et préconditions |

Un Hero n'est pas un template de portfolio : sept layouts Hero ne représentent
pas sept portfolios complets disponibles. L'éditeur libre reste hors périmètre.

## 2. Audit vérifié de l'existant

| Fichiers lus au commit de référence | Fait observé / conséquence |
|---|---|
| `contracts/templates/manifest.v1.json`, `backend/modules/templates/registry.py` | Catalogue Git, deux bundles, SHA-256, limites et références locales. Le loader est explicitement limité aux snapshots v1 et aux deux layouts de portfolio. Nouveau contrat requis pour Creative Editorial. |
| `minimal/1.0.0/descriptor.json`, `editorial/1.0.0/descriptor.json` | Le statut enregistré peut être unavailable ; le manifeste est l'autorité et le loader écrase le statut retourné. Le manifeste actuel annonce les deux available. Ne pas déduire l'état effectif du seul descriptor. |
| `contracts/schemas/templates/documents/*.v1.json`, `snapshot.v2.json` | v1/v2 fermés ; content v1 contient hero/about/projects/skills/contact textuels, projets embarqués. Ni portrait, média, navigation configurable ni slots génériques. |
| `apps/studio/src/components/templates/portfolio-renderer.tsx` et `.module.css` | Renderer v1 partagé catalogue/instance, masthead/footer codés, faux visuels géométriques pour projets ; aucun média utilisateur. Ne pas les présenter comme une gestion d'images. |
| `template-preview.tsx`, `template-editor.tsx`, `template-thumbnail.tsx` | Aperçus/édition C+D disponibles pour le chemin existant. Pas d'éditeur de templates complets riches ; recette visuelle manuelle C+D suivie séparément. |
| `hero_contracts.py`, `hero_resolution.py`, `packages/content-contracts/src/hero-resolution.ts` | Contrats E.02 et résolution E.03, contraste et reset ; dépendance aux invariants de snapshot v2. Pas d'acceptation native d'un document v3. |
| `modular-hero-renderer.tsx`, `contracts/hero/renderer.v1.json` | Sept Hero isolés et testés ; registre renderer 1.1.0, tout selectable false, activation par défaut false. Pas de routage Studio/public. |
| `contracts/hero/text-layouts.v1.json`, `e06/contract-decision.md` | Product Showcase/Bento 1.1.0 textuels via profil explicite ; les versions 1.0.0 gardent leurs refus. Pas de champs médias. Le profil n'est pas activé dans la validation de sauvegarde E.04. |
| `backend/modules/templates/models.py` | PortfolioDesign JSONB CHECK schema_version IN (1,2), experience null ; source_digest. DesignTransition autorise seulement upgrade1→2 et restore2→1. Aucune révision générique v3. |
| `instance_services.py`, `instance_views.py` | Création idempotente 24 h, copie indépendante, ETag/If-Match ; PUT ne reçoit que content/customization. Initialisation actuelle neutralise les données de démonstration. Ne pas contourner ces règles. |
| `backend/modules/portfolios/models.py` | Propriété via Account ; Portfolio.version canonique. CHECK status=draft, visibility=private et thème initial studio-neutral1.0.0. Publication non implémentée ; nouveaux thèmes/pubs ne passent pas ces contraintes. |
| `transitions.py`, `hero_conversion.py`, `validation.py` | E.04 conversion explicite, récupérable et atomique ; validation persistante reste sur les profils acceptés v1/v2. Ne pas réutiliser DesignTransition comme journal v3 sans nouveau contrat. |

### Capacités disponibles et manquantes

| Capacité | Disponible aujourd'hui | Extension nécessaire |
|---|---|---|
| Comptes, isolation et version canonique | AUTH/PORT, compte personnel, propriété Account | Conserver ; aucune collaboration activée |
| Galerie et choix de template | Deux templates textuels v1, copies idempotentes | Catalogue versionné de templates complets, statuts/capacités étendus |
| Hero | Sept rendus isolés, apparence bornée et responsive | Intégration contrôlée dans documents complets ; portrait non fourni par HeroConfig1 |
| Navigation/footer | Chrome fixe du renderer v1 | Variantes complètes, liens dérivés des sections réellement visibles |
| Projets | Cartes textuelles embarquées, liens HTTPS | Covers, slots et états vides ; vraies pages de case study non fournies par ce ticket |
| Médias SaaS | Aucun module d'import/stockage utilisateur opérationnel identifié | Pipeline sûr, propriété, références, dérivés, droits, quotas et rétention |
| Personnalisation | Réglages v1, Hero palettes/gradient/glass, police système | Politique globale du template, contrastes de toutes les surfaces, polices sous licence |
| Prévisualisation | V1 catalogue/instance, harness Hero | Même renderer complet pour démo, brouillon, aperçu exact et publication |
| Publication manuelle | Non implémentée ; contraintes SQL draft/private | Révisions de publication immuables, pointeur actif, serveur public isolé |
| Mise à jour de template | Provenance copiée ; aucune mise à niveau silencieuse | Comparaison explicite, mapping slots, récupération et conservation des médias |

## 3. Architecture proposée : trois documents et un catalogue immuable

```text
Bundle Git versionné (composition + politique + démo + ressources licenciées)
       │ vérification complète du manifeste et des capacités
       ▼
Copie dans une instance privée : composition figée + slots utilisateur + overrides
       │ validation et résolution pures ──> aperçu brouillon privé
       │ validation de publication + confirmation explicite
       ▼
Publication immuable (document résolu + références médias + versions de renderer)
       │ remplacement atomique du pointeur actif du portfolio
       ▼
Site public de CE portfolio (aucune lecture de son brouillon)
```

Le catalogue est versionné indépendamment du Hero : identifiant stable
`creative-editorial`, semver `1.0.0`, renderer `ready-portfolio@1.0.0`, contrats
et capacité responsive reconnus. Le premier état est draft. Aucun bundle
Creative Editorial disponible n'est créé par cette étude.

### Manifeste et statuts

Un futur manifeste v2 référencera descriptor, composition, style-policy,
content-demo, responsive-profile et assets licenciés, avec taille et SHA-256
par fichier. Un bundle_digest est calculé sur la liste triée des chemins,
tailles et hashes des payloads, en JSON canonique UTF-8 selon algorithme versionné ;
le manifeste porteur de ce digest est exclu du calcul pour éviter l'autoréférence.
Les binaires sont hashés octet par octet ; le JSON a une politique LF explicite,
jamais une normalisation opaque des contenus. Traversée de chemins, symlinks
sortant du bundle, doublons, collisions de casse Windows, propriétés inconnues
ou dépendance non reconnue : refus fermé. Limites proposées : 64 versions au
catalogue paginé, 256 Kio par JSON, 128 assets et 25 Mio de payload par bundle.

| Statut proposé | Découverte / création / instances |
|---|---|
| draft | Interne, aucune création utilisateur |
| preview | Démonstration interne autorisée, création bloquée |
| available | Galerie, vrai aperçu et création autorisés si toutes les capacités sont opérationnelles |
| deprecated | Nouvelles créations bloquées, versions existantes conservées ; remplacement conseillé |
| retired | Masqué de la galerie, aucune création ; historique et instances encore rendables |
| quarantined | Nouvelle création et nouvelle publication bloquées ; traitement de sécurité explicite des releases affectées |

Le statut appartient au manifeste de découverte, pas au snapshot utilisateur.
Une indisponibilité de catalogue n'invalide pas une instance déjà créée. Une
quarantaine de sécurité n'est pas un moyen de supprimer silencieusement son
contenu : conserver la révision, informer, proposer une version sûre, et prévoir
la suspension publique motivée si la faille l'impose. La décision de suspension
nécessite une procédure produit/sécurité distincte.

Critère available : bundle et droits vérifiés, renderer réel, slots et politiques
validés, états vides acceptables, import et médias sûrs, aperçu/instance/public
paritaires, création et publication opérationnelles, références desktop/tablette/
mobile revues. Une vignette ou une liste JSON ne suffit pas.

## 4. Matrice de versions proposée — rupture explicite, pas élargissement de v2

| Famille | Enveloppe | Composition | Contenu | Présentation / customisation | Expérience | Chemin |
|---|---:|---:|---:|---|---|---|
| Minimal/Editorial actuels | 1 | 1 | 1 | 1 / 1 | null | Renderer v1 inchangé |
| Hero modulaires acceptés | 2 | 2 | 1 | 2 / 2 | null | E.03/E.04 ; renderer isolé E.05/E.06 |
| Templates complets proposés | **3** | **3** | **2** | **3 / 3** | null | Nouveau dispatch explicite, à approuver |

Cette proposition v3 est justifiée par les nouveaux types de slots, sections
navigation/footer et médias ; les schémas fermés v2 ne permettent pas de les
ajouter honnêtement. Aucun numéro proposé n'est enregistré dans les contrats
actifs. Les variantes de Hero gardent leurs propres versions ; une version de
layout ne doit pas être confondue avec celle d'un template ou d'un document.

Les exemples et schémas sont dans [e0701/examples](e0701/examples/) et
[e0701/schemas](e0701/schemas/). Ils ne constituent pas un moteur de validation
métier complet : validation sémantique, droits et états sont obligatoires en plus.
Les champs inconnus sont fermés, les sections/bindings spécifiques du template
seront comparés à leur manifeste de confiance.

## 5. Slots typés, limites et états vides

Les IDs de slots sont stables, distincts de leurs libellés traduits. Chaque
valeur est discriminée par type ; le template fixe ses contraintes et ses
liaisons. Le propriétaire ne peut pas changer le type, ajouter un slot exécutable,
modifier les bindings ou fournir son propre schéma. Les contraintes de template
ne peuvent que resserrer les plafonds globaux ci-dessous.

| Type proposé | Forme / plafond | Null et vide |
|---|---|---|
| text | Texte brut, max 500 caractères ; limites par slot plus strictes | String vide conservée au brouillon, jamais transformée en faux contenu |
| rich_text | AST fermé : 8 paragraphes × 30 segments, 1 000 caractères/segment ; plafond global AST 12 Kio et 6 000 caractères cumulés | blocks=[] = vide ; pas de HTML/Markdown libre, iframe, style, lien imbriqué ou code |
| image | UUID asset, alt≤240, decorative bool, focal_point normalisé [0,1]² | value=null = absence explicite ; pas d'URL ni de chemin disque |
| logo | Même référence sûre, politique de cadrage contain | value=null : identité textuelle utilisée si non vide |
| link | Libellé≤60 et union section/external/email | target=null désactive et omet le contrôle ; pas de lien factice vers # |
| project_list | 0–12 cartes embarquées : UUID, titre≤120, résumé≤300, cover optionnelle et cible optionnelle | [] : section et entrée de navigation omises, rythme alternatif prévu |
| social_links | 0–8 entrées d'un réseau énuméré, label et lien validé | [] : pas de groupe vide ni icône cliquable sans nom |

Pour les nouveaux slots : borne de texte définie en points de code Unicode,
UTF-8 strict, aucun surrogate isolé ; équivalence Python/TypeScript à tester,
notamment emoji et accents. Pas de normalisation silencieuse ni de trim à la
sauvegarde ; trim sert seulement à détecter le vide. Limite globale du document
256 Kio et profondeur 32 pour cette famille. Ces propositions ne réécrivent pas
les limites ou fixtures historiques E.02/E.03.

Liens : HTTPS externe uniquement, sans identifiants, contrôle ou backslash,
validation après parsing canonique ; sections référencent un ID visible appartenant
à l'instance ; email devient un mailto généré depuis une adresse validée. Pas de
javascript/data/file, SVG-lien, query CSS ou lien administratif. Réseaux nommés :
allowlist de domaine attendue, label accessible, rel noopener/noreferrer ; `other`
reste HTTPS validé. Aucune récupération serveur du site cible.

Différencier **validité du brouillon** et **aptitude à publier** : champs requis
pour publier peuvent être vides dans un brouillon sauvegardable. État invalide
de type, d'ACL ou de contraste : sauvegarde refusée. Erreurs de préparation à
publier : liste de chemins/codes sûrs, publication refusée, brouillon conservé.
Un exemple JSON avec asset UUID synthétique valide la structure, pas l'existence
ni les droits de l'asset.

### Inventaire Creative Editorial

| Slot | Type / limite locale | Publication | État absent |
|---|---|---|---|
| identity_name | text 80 | Requis non blanc | Publication bloquée |
| brand_logo | logo | Facultatif, contain | Identité textuelle, sans changer la navigation |
| hero_title | text 160 | Requis non blanc | Publication bloquée |
| hero_subtitle | text 300 | Facultatif | Espacement secondaire retiré selon variante prévue |
| hero_portrait | image, crop 4:5 desktop / 1:1 mobile | Facultatif | Zone d'art abstrait propriétaire, non présentée comme portrait réel |
| hero_cta | link, libellé 60 | Facultatif | Bouton omis ; lien section refusé si sa destination est absente |
| about_heading | text 120 | Facultatif | Titre de section omis, pas de h2 vide |
| about_body | rich_text, 3 000 caractères cumulés | Facultatif | Section et lien de navigation omis |
| projects_heading | text 120 | Facultatif | Liste peut rester sous label de section du template, traduit et non trompeur |
| selected_projects | project_list, 0–6 cartes | Facultatif | Section omise avec variante de composition de vide revue |
| contact_heading | text 120 | Facultatif | Titre omis |
| contact_link | link | Au moins contact_link ou un social valide requis pour publier | Pas de CTA vide |
| socials | social_links, max 6 | Peut satisfaire l'exigence de contact | Groupe omis si vide |
| footer_note | text 160 | Facultatif | Footer garde seulement les éléments disponibles ; aucun copyright nominatif inventé |

Navigation : dérivée des sections réellement présentes, labels de traduction
versionnés dans le template, ordre fixe. Pas de tableau de liens utilisateur qui
permettrait de fabriquer une section inexistante. L'architecture laisse un futur
slot navigation typé possible, sans le déclarer nécessaire au premier template.

Les cartes projets sont **des données embarquées de cette instance**, pas de
faux modèles Project prétendument présents aujourd'hui. L'éventuelle migration
vers un module Project/Case Study fera l'objet d'un contrat dédié. Les liens
locaux vers des pages projet ne sont disponibles que si le module fournit une
page publiée ; en première étape, lien externe HTTPS ou carte sans lien. Aucune
promesse de case study builder livré par E.07.01.

## 6. Composition, direction artistique et responsive

Le bundle fige les six sections navigation, Hero, présentation, projets, contact,
footer ; slots facultatifs contrôlent des états prévus, jamais des coordonnées
libres. Superpositions, ratios, taille de titre, grille de cartes et espacements
sont du code renderer versionné. Les contenus utilisateur n'apportent pas de CSS,
HTML, position, z-index, classe, shader ou JS.

Creative Editorial propose un Hero à titre ample, portrait cadré et couche
abstraite originale, cartes projets avec covers, navigation lisible et contact
fort. Ce Hero complet ne peut pas être annoncé comme une simple activation du
Hero E.06 : le portrait et l'art direction de page nécessitent une nouvelle
variante de section du renderer complet. Aucun huitième identifiant de layout
Hero n'est requis ; une variante de template compose des primitives connues,
avec un assemblage médial explicite et testé. Si HeroConfig1 ne peut exprimer une
propriété nécessaire, ne pas la glisser dans ses overrides : la conserver dans
le contrat de section v3, ou demander ultérieurement un HeroConfig versionné.

Breakpoints proposés : container queries mobile <640, tablette 640–1023,
desktop≥1024 px, cohérents avec E.03. Pas d'héritage desktop depuis tablette.
Desktop : composition décentrée à chevauchements bornés ; tablette : réduction
des couches ; mobile : ordre de lecture linéaire et grille unique. Cadrage image
fourni par politique et point focal ; propriétaire ne modifie pas les ratios.
Les variantes mobiles sont des branches de composition fiables du même contenu,
pas des copies indépendantes susceptibles de diverger.

Revue visuelle requise à 320, 375, 640, 768, 1024, 1440, 1920 px, texte long,
200 % et 400 % de zoom, orientation paysage et état sans portrait/projet/logo.
Ordre DOM logique, un h1, headings sans sauts fabriqués, navigation nommée,
lien d'évitement, clavier/focus visible ; aucune réorganisation CSS qui inverse
un parcours interactif. Contraste texte 4,5:1 y compris grands titres (choix plus
strict), contrôles/focus et pictogrammes pertinents ≥3:1, cibles ≥44×44 CSS px.
Le texte ne repose jamais directement sur un portrait ou un dégradé non maîtrisé.
Reduced-motion/forced-colors sont obligatoires ; pas d'animation dans ce lot.

## 7. Personnalisation contrôlée

Politique `creative-editorial-style@1.0.0` : palettes originales `ink-lime` et
`paper-cobalt`, overrides de quatre couleurs hex6 (background, surface, text,
accent), aucune propriété CSS libre. Le bundle définit les valeurs et les
relations de contraste pour chaque zone, y compris navigation, liens et focus.
Une couleur bien formée peut être refusée pour incompatibilité ; aucun fallback
silencieux de palette. Pour image/gradient, texte sur couche opaque validée.

Ordre : defaults du template → palette sélectionnée → overrides par couleur.
Changer de palette ne supprime pas silencieusement les overrides existants ;
prévisualiser et expliquer le reset explicite. Reset par suppression de clé,
pas null ; tableaux/unions remplacés atomiquement. Ne pas réinterpréter les règles
E.03 de Hero dans le reste de la page sans contrat et fixtures de parité.

Police initiale : **system-sans uniquement**, permettant de livrer sans police
protégée ni chargement distant. Le sélecteur ne montre pas de seconde police
fictive. Le modèle prévoit `font_pair_id` immuable ; ajouter une paire nécessite
licence redistribuable, fallback métrique, budget WOFF2, tests Windows et validation
de la direction artistique. Famille, graisses et métriques sont allowlistées,
pas d'upload de police ou de requête Google Fonts utilisateur. Une telle paire
n'est pas transmise à HeroConfig1 qui n'accepte que system-sans ; son éventuelle
extension doit être versionnée et approuvée. Les proportions ne deviennent pas
paramétrables par l'utilisateur sous couvert de personnalisation.

## 8. Médias sûrs : architecture proposée, rien importé ici

### Entités et propriété

`MediaAsset(id UUID, account FK, state, mime, byte_size, width, height,
checksum, private_object_key, rights_declaration, created_by, created_at)` ;
`MediaVariant(asset, recipe_version, role, width, height, checksum, object_key)`.
Une référence de slot contient seulement UUID, alt, decorative et focal_point.
L'asset appartient à Account pour réutilisation entre portfolios du même compte ;
chaque résolution de référence vérifie design.portfolio.account == asset.account.
Un UUID inconnu/étranger renvoie une erreur uniforme, pas ses métadonnées.
Pas de nouvelle propriété dupliquée dans PortfolioDesign. Les assets du bundle
sont distincts des assets utilisateur et identifiés par référence de bundle+hash,
jamais par un faux UUID utilisateur.

### Import et validation

1. Action authentifiée/CSRF, quota compte et intention d'upload à clé idempotente ;
   stockage staging privé et nom de clé généré serveur, sans chemin fourni par le client.
2. Format réel identifié par signature puis décodage complet en worker isolé,
   timeout et plafond mémoire. MIME/extension déclarés ne font pas autorité.
3. Proposition initiale : JPEG/PNG/WebP statiques, ≤10 Mio, ≤20 mégapixels et
   ≤8192 px par dimension ; refuser SVG utilisateur, GIF/animation, PDF, vidéo,
   archives, fichiers polyglottes et formats inconnus. Limites appliquées au flux
   avant décodage puis aux dimensions avant allocation complète. WebP animé refusé.
4. Réencoder, retirer EXIF/GPS et métadonnées privées, générer dérivés bornés
   (portrait, cover, logo), calculer hashes et marquer ready. Antivirus éventuel
   ne remplace pas décodage/réencodage et isolation. Dépendance de traitement
   à choisir/versionner après revue sécurité, aucune ajoutée ici.
5. Original privé jamais rendu tel quel ; seuls dérivés validés sont accessibles.
   Échec ⇒ rejected, staging expiré nettoyé. Aucun remote URL import (SSRF évité).

États : initiated → uploaded → processing → ready, ou rejected ; suppression
logique explicite. Aucun objet processing/rejected ne peut être publié. Proposition
quota initial à valider : 500 Mio stockés/compte, 200 assets, 10 intentions d'upload
par minute ; inclure originaux+dérivés, réserver/restituer atomiquement les octets.
Des uploads parallèles ne doivent pas contourner le quota.

Droits : attestation d'autorisation avant ready, provenance/licence si disponible,
assets de démonstration originaux ou dûment redistribuables avec auteur/notice.
Une simple case cochée n'établit pas les droits ; politique de retrait dédiée.
Alt non blanc requis pour un portrait/cover informatif ; decorative=true autorise
alt vide seulement dans un emplacement déclaré décoratif. Logo identifiant a un
nom accessible ; pas de retrait silencieux de l'alt. Point focal n'altère jamais
le fichier original. Déduplication par hash seulement à l'intérieur du compte,
jamais une preuve de possession inter-comptes.

### Stockage, accès, rétention

Interface de stockage indépendante : adaptateur filesystem privé sous un dossier
SaaS explicite hors racine servie pour Windows natif, puis stockage objet privé
compatible S3 pour production (choix fournisseur à valider). Aucun Docker requis,
aucune lecture/réutilisation du `.local/` historique. Clés générées, chemin résolu
strictement sous racine, anti-symlink/ACL Windows ; aucun fichier de credential
ou secret dans une fixture/commit.

Brouillon : URLs de dérivés autorisées et courtes, Cache-Control private/no-store,
pas de lien réutilisable d'un autre compte. Public : URLs de dérivés immuables
liés à une release ; les rendre publics doit être une action explicite associée
à la publication. Servir sur origine médias sans cookies d'auth, Content-Type
correct, nosniff, CSP adaptée. Pas de permission publique sur tout le bucket.

Une suppression de slot n'efface pas le média. Les références de brouillon,
révisions de récupération et releases sont conservées et empêchent le GC. Le
même fichier peut être partagé entre deux portfolios du même compte ; dupliquer
l'instance duplique les références et métadonnées locales, pas nécessairement
les octets de l'asset immuable. Modifier/cadrer une copie n'affecte pas l'autre.

Rétention proposée : staging abandonné 24 h, objets non référencés 30 jours,
révisions récupérables au moins 30 jours ; une référence de release conservée
bloque le GC au-delà. Unpublish et révocation ont une politique de purge/CDN
explicite : une URL publique déjà copiée ne redevient pas secrète par magie.
Obligation de retrait peut suspendre les releases concernées, sans supprimer
silencieusement leur journal. Sauvegarde : manifestes objets+hashes, DB et clés de
chiffrement gérées séparément ; restauration vérifie les références et les hashes.

## 9. Persistance et publication proposées

### Instance et concurrence

Réutiliser PortfolioDesign pour l'enveloppe v3 après **nouvelle migration additive
explicitement autorisée** : CHECK (1,2,3), toujours experience null ; aucun défaut
passé automatiquement à 3, aucun backfill. Le couple initial_theme actuel est
bloqué sur studio-neutral : avant tout nouveau thème global, proposer séparément
la contrainte et sa signification. Pour le premier lot, conserver ce marqueur
historique et stocker la politique de style propre au template dans presentation3 ;
ne pas faire croire que PORT connaît un nouveau thème déjà valide.

Copie profonde à la création : provenance template id/version, bundle_digest,
composition et politique épinglées ; contenu utilisateur neutre distinct des
valeurs de démo. Les exemples fictifs ne sont pas copiés dans une instance réelle
sans action explicite et marquage. La première création doit néanmoins produire
une composition attractive avec états vides, sans publier une identité fictive.
L'initialiseur v1 actuel devra avoir un équivalent distinct pour v3, pas être
élargi silencieusement. Création idempotente conserve la rétention 24 h.

Toutes mutations privées : compte autorisé, portfolio actif, ETag/If-Match sur
Portfolio.version, transaction et ordre de verrous portefeuille puis design.
Changer content/customization incrémente ce seul compteur, sans publier. Gestion,
visibilité et publication restent des dimensions indépendantes ; archived bloque
les éditions/publications selon politique, sans supprimer une release implicitement.

Prévoir `DesignRevision` immuable avec before/after, hash, auteur, action et
version pour les mises à niveau de template v3 et récupération. Ne pas relâcher
la contrainte de DesignTransition E.04, qui reste spécifique à 1↔2. Une restauration
est une nouvelle mutation avec nouvelle version, jamais un décrément du compteur.
Ces nouvelles tables demandent un plan de migrations spécifique avant exécution.

### Prévisualiser sans publier

Quatre contextes utilisent le **même renderer versionné** : démo (contenus fictifs
explicitement marqués), aperçu local non enregistré, aperçu privé d'une révision
sauvegardée, release publique. Pas de vignette peinte à la main ni d'aperçu ignorant
les règles responsive réelles. Vignettes générées à partir du vrai bundle.

Aperçu local du contenu non enregistré peut rendre client-side la partie pure,
avec le même validateur TS ; tout rendu serveur et toute publication sont revalidés
Python. Un payload client n'est jamais une autorisation de médias ou de publication.
Un aperçu de révision persistée porte Portfolio.version et son hash ; changement
du brouillon ⇒ avertissement et nouvel aperçu requis pour publier cette version.
Pas de stockage du contenu dans localStorage. Aperçu authentifié no-store/noindex,
iframe de même origine ou origine contrôlée avec CSP/sandbox appropriés ; pas de
partage public par token dans le premier lot.

### Publication manuelle et indépendante

Proposer `PortfolioRelease` immuable : portfolio FK, UUID, source_portfolio_version,
template/bundle/renderer/schema versions, document résolu figé, manifestes de
médias validés et hashes, auteur/date. `PortfolioPublication` unique par portfolio
avec active_release FK nullable et publication_version. Contraintes : active_release
appartient au même portfolio, aucune release d'un autre compte acceptée.
Le pointeur publication_version sert à invalider les caches, sans concurrencer
le compteur d'édition canonique Portfolio.version.

Action Publish explicite, If-Match, clé d'idempotence 24 h et hash de l'intention :
verrou, vérification exacte de la version prévisualisée, validation de tous slots,
droits médias et droits de diffusion, création release + swap du pointeur dans
une transaction SQL. Ne pas ouvrir une transaction longue pendant les uploads
ou conversions de fichiers : seuls assets ready entrent dans la transaction.
Le serveur public lit uniquement active_release et ses dérivés, jamais le design
mutable. Brouillon modifié après publication ⇒ ancienne release publique intacte.
Un portfolio A publié ne change aucun pointeur/cache de B.

Les fichiers dérivés sont préparés avant le swap ; une panne ne remplace jamais
le site par une release incomplète. Invalidation cache via outbox transactionnel
ou traitement réessayable après commit, clé incluant release_id ; ancien cache
peut rester brièvement visible, mais aucun brouillon. Publish répété restitue la
même release. Unpublish explicite efface le pointeur, rollback explicite désigne
une release sûre compatible : chacun versionné, autorisé et idempotent.

**Blocage actuel explicite :** les CHECK Portfolio.status=draft et visibility=private
et la sérialisation publication_state interdisent de prétendre que ce flux existe.
Leur évolution doit être décidée avec le ticket Publication : proposer un état
public dérivé du pointeur (unpublished/published), une visibilité private/public
indépendante, et une modification coordonnée des CHECK/DTO. Ne pas publier avec
un DTO affirmant toujours draft ; ne pas réutiliser management_state. E.07.04
ne peut activer Publish sans cette dépendance validée et son autorisation DDL.

Domaine initial proposé : chemin public unique dérivé d'un identifiant de
publication ou handle global réservé, pas le slug seul qui n'est unique que par
compte. Domaines personnalisés et certificats hors premier lot. Les changements
de slug privé ne redirigent pas silencieusement une adresse publique ; politique
d'alias explicite à valider. Contenu privé et API restent sur leurs ACL AUTH.

## 10. Compatibilité, mises à jour et récupération

1. Dispatcher par schema_version exact. V1 garde son renderer et ses bundles ;
   v2 garde ses validateurs/profils et versions Hero. Aucun document v3 envoyé à
   E.03 comme s'il était v2, aucune composition Minimal fictive fabriquée pour
   contourner ses invariants.
2. Pour v3, extraire ultérieurement un noyau pur de résolution Hero réutilisable
   sans changer les façades E.03 ; adaptateur v3 validant d'abord le document
   complet. Fixtures de parité et références exactes E.03/v1/E.05 obligatoires.
   Les propriétés médias/art direction restent dans la composition de section
   v3, jamais dans des propriétés inconnues HeroConfig1.
3. Les politiques locales copiées et références renderer restent immuables par
   version, même si le catalogue change. Les nouveaux templates n'élargissent
   pas les politiques des instances existantes.
4. Installation de v3 n'est pas migration de portfolio : nouvelles instances
   seulement, après autorisation. Aucune conversion automatique Minimal ou
   Editorial, ni remplacement de bundle/digest par un identifiant créatif.
5. Une future mise à niveau explicite compare version source/cible, présente
   mapping de slots et pertes éventuelles. Créer une révision de récupération
   complète avant écriture, conserver médias/références, validation puis commit
   atomique avec If-Match et idempotence. Changement de type/slot non mappable ⇒
   conflit demandant arbitrage ; aucun contenu jeté. Publication existante intacte.
6. Premier lot recommandé : création de nouvelles instances Creative Editorial ;
   mise à niveau inter-template et conversion v1/v2→v3 reportées. Leur contrat
   doit être conçu mais pas livré sous couvert d'un formulaire de remplacement.
7. Retrait de template ne supprime pas son renderer historique. Patch de sécurité
   explicite par nouvelle version ; tout retrait de runtime exige inventaire des
   références et procédure de récupération, jamais un fallback silencieux.

Tests de futures migrations : PostgreSQL 17 neuf et jetable, données synthétiques
v1/v2/compte double/UUID/medias absents, comparaison avant/après et restauration,
Windows natif et Linux. Toute base réelle exige sauvegarde vérifiée et autorisation
explicite ; aucune commande migrate n'est fournie ni exécutée dans cette phase.

## 11. Sécurité, qualité et performance : critères futurs

- Contrats : positifs/négatifs communs Python/TS, versions inconnues, références
  manquantes, type/slot inattendu, AST malformé et budget UTF-8 ; comparaison
  sémantique des futures API/DTO/erreurs/ETag avec les schémas avant activation.
- Isolation : lecture/édition/upload/preview/publication d'un autre compte,
  IDOR des assets/revisions, usages simultanés de quotas, course delete/publish,
  appariement release-portefeuille en base et service.
- Médias : MIME mensonger, bombes de décompression, dimensions extrêmes,
  EXIF/GPS, SVG/polyglotte/animation, timeout, objet non ready, path traversal,
  symlink et ACL Windows ; aucune désactivation de TLS/signatures pour les outils.
- Concurrence : deux onglets, version périmée, mêmes clés avec intentions
  différentes, interruption worker, reprise upload, publication et restauration.
- Rendu : screenshots vrais sur trois appareils logiques, textes longs et vides,
  largeur 320–1920, clavier, focus, contrastes calculés, lecteurs d'écran,
  reduced-motion, forced-colors, CLS. Les snapshots E.05/E.06 sont un socle,
  pas une preuve que le nouveau template complet est accessible.
- Budget proposé : portrait above-fold optimisé ≤250 Kio, cover ≤300 Kio,
  logo ≤64 Kio ; initial page ≤750 Kio transférés sur fixture type, images hors
  viewport lazy, sizes/srcset et width/height connus. Aucun moteur d'animation.
  Polices additionnelles futures ≤150 Kio WOFF2 et licences vérifiées.
- Cibles à mesurer sur environnement fixé : LCP≤2,5 s, CLS≤0,1 ; pas de promesse
  fondée sur les seuls timings SSR Node. Revue GPU/glass réelle si utilisé.

## 12. Découpage recommandé — après approbation seulement

| Ticket | Périmètre et dépendances | Critères d'acceptation / arrêt |
|---|---|---|
| **E.07.02 — Contrats des templates complets et registre hors ligne** | Approbation des décisions ci-dessous ; finaliser schémas v3/slots/politiques/manifestes, profil responsive et inventaire Creative Editorial ; nouveau loader hors ligne et fixtures synthétiques. Garder loader v1. | Parité Python/TS, schémas fermés + validation sémantique, digests/licences/capacités vérifiés ; sections/bindings immuables ; matrice versions testée ; statut draft/preview seulement, aucun endpoint/DDL/stockage/éditeur/publication. Arrêt pour revue. |
| **E.07.03 — Premier template complet, médias et aperçus isolés** | E.07.02 acceptée ; maquette originale approuvée ; choix média/stockage et menaces validés. Sous-lots séparés : renderer complet + états vides, adaptateur Hero/parité, pipeline médias privé et vérification d'ACL sur environnement synthétique autorisé. | Vrai Creative Editorial responsive, démo licenciée, même moteur aperçu/instance, images sûres, budgets et recette visuelle ; Windows filesystem natif documenté. Toute table média exige plan DDL et autorisation spécifique avant exécution, même cluster de test. Aucune route catalogue disponible ni publication réelle. Revue avant intégration. |
| **E.07.04 — Instances contrôlées, remplacement de contenu et publication manuelle** | E.07.03 acceptée ; contrats/API de persistance v3, révisions, contraintes PORT et **dépendance Publication** validés ; DDL autorisé séparément. Sous-lots revus : création/idempotence, formulaire de slots+aperçu, publish/unpublish et récupération. | Propriété Account, If-Match, drafts indépendants du public, médias/revisions conservés, publication atomique par portfolio ; aucun contenu démo réel implicite. available seulement après preuve de bout en bout Linux/Windows et recette visuelle. Aucun éditeur libre ni mise à jour inter-template automatique. |

Ces tickets sont des lots recommandés, pas une autorisation de développement.
E.07.03 médias et E.07.04 Publication sont des dépendances importantes, à découper
en sous-tickets ou tickets MEDIA/PUB dédiés plutôt que déclarer E.07.04 terminé
avec un bouton désactivé. En l'absence d'autorisation Publication, la livraison
reste explicitement « preview privée », jamais « prêt à publier ». Chacun des
sous-lots s'arrête pour sa propre revue ; cette étude n'autorise aucun DDL.

## 13. Décisions structurantes à valider

| Décision proposée | Conséquence / arbitrage |
|---|---|
| R01 — Nouvelle famille Design v3, content v2, sans élargir v1/v2 | Nouveaux contrats/dispatch et future contrainte SQL ; isolation propre des versions |
| R02 — Composition et art direction verrouillées, slots remplaçables | Simplicité et fidélité ; pas de changement de layout ni drag/drop au premier lot |
| R03 — Projets embarqués, liens externes ou sans lien d'abord | Pas de faux module Case Study ; futur modèle projet explicitement séparé |
| R04 — Portrait/projets facultatifs avec états artistiques de vide | Portfolio élégant même incomplet ; contact + identité/titre restent requis pour publier |
| R05 — Premier template system-sans ; palettes + quatre couleurs bornées | Police géante possible sans assets protégés ; variantes de police après licences/tests |
| R06 — MediaAsset par Account, dérivés privés et pipeline local/S3 | Réutilisation intra-compte, ACL sur toutes les références, quotas/rétention à approuver |
| R07 — Nouvelle révision générique, E.04 inchangée | Préserve récupération v1↔v2 ; nécessite nouvelles tables pour v3 |
| R08 — Publication immuable avec pointeur par portfolio | Vrai brouillon séparé du public ; travail PUB/contraintes/API indispensable |
| R09 — Première livraison v3 pour nouvelles instances seulement | Pas de risque de conversion implicite ; migrations de contenu/report inter-template reportées |
| R10 — Trois lots à portes de revue et statut available strict | Un catalogue visuellement crédible n'est déclaré prêt qu'après intégration réelle |

Questions de produit à trancher pendant la revue : portrait facultatif retenu ?
Publication autorisée avec zéro projet si contact réel disponible ? Palettes et
polices système suffisantes pour une première maquette originale ? Quotas et
délais de conservation acceptables ? Adresse publique initiale par handle global
ou identifiant opaque ? Périmètre E.07.04 incluant PUB, ou ticket PUB distinct ?

Risques majeurs : surestimer les capacités Hero textuelles, gonfler le dernier
lot avec médias/publication, perdre l'art direction avec des slots trop libres,
exposer un original ou une preview privée, changer un thème incompatible avec
les CHECK existants, retirer un renderer encore référencé, confondre démo et
contenu utilisateur, perdre le média d'une release lors d'un GC, ou promettre
une ressemblance visuelle sans revue d'une maquette originale. Les portes de
validation ci-dessus répondent à ces risques sans supposer les extensions déjà
acceptées.

**Arrêt : attendre la revue E.07.01 et l'approbation des décisions/contrats avant
E.07.02.** Aucune implémentation n'est engagée par les exemples proposés.

# E.07.03 — Creative Editorial, renderer isolé

Livraison pour revue, 20 octobre 2026 (Africa/Douala). Base acceptée E.07.02 :
`0268f8054906a93f5ec62638111a5037c6968207`. Les preuves Windows E.07.02 sont celles
transmises par l'utilisateur : 449 réussites, 1 symlink ignoré, zéro échec ; elles
ne constituent pas une exécution Windows E.07.03.

## Direction artistique originale

Le template associe un fond encre et un accent citron, une typographie expressive,
un portrait illustré légèrement décalé, une présentation en colonnes, une grille
projets asymétrique et un contact de grande taille. La seconde palette et la
référence serif autorisées sont également prises en charge. Les proportions,
chevauchements décoratifs, ratios et breakpoints appartiennent au renderer, pas
au document utilisateur. Aucun positionnement libre ou nouvel override.

Les huit SVG sont des illustrations vectorielles **originales et synthétiques** :
deux portraits stylisés de personnages fictifs, deux symboles et quatre abstractions
d'interfaces. Aucun portrait réel, logo tiers, screenshot de produit, marque ou
police protégée des références n'est repris. Les sources et la notice CC0 sont
sous `contracts/fixtures/ready-rendering/assets/`. Il ne s'agit ni d'uploads SVG
utilisateur ni d'un élargissement de la future politique média : ce sont des
ressources Git de confiance avec nom, taille, dimensions et SHA-256 vérifiés.

## Entrée et composition

`creative-editorial-renderer.tsx` est un composant React serveur, sans use client,
hook, gestionnaire de scroll, appel API, authentification, écriture ou accès SQL.
Exemple d'appel futur, uniquement dans un contexte explicitement autorisé :

```tsx
<CreativeEditorialRenderer
  document={snapshotV3}
  media={trustedSyntheticContext}
  enabled={true}
  scope="preview-a"
  demonstration={true}
/>
```

L'option est fermée par défaut ; le renderer refuse sans enabled strictement true.
Le scope est un préfixe d'ID borné et contrôlé, unique par instance dans une page.
Le document complet est validé par le vrai registre/validateur E.07.02 avant rendu.
Aucune transformation v1/v2→v3, aucun faux snapshot Minimal ni élargissement de
contrat. Le renderer respecte la variante creative-hero.v1 et ne prétend pas
ajouter des images à HeroConfig1 ou remplacer les sept Hero historiques.

Le DOM respecte les six IDs et l'ordre navigation/Hero/about/projects/contact/
footer. Les 14 slots correspondent aux bindings canoniques E.07.02. Les deux
fixtures remplacent **tous** ces slots, gardent composition/presentation identiques,
et produisent des textes, logos, portraits et cartes différents. Le rythme se
réorganise naturellement avec la longueur du texte ; la stabilité ne signifie
pas imposer des hauteurs qui coupent le contenu.

Le registre E.07.02, ses capacités conservatrices et son bundle restent intacts,
au statut **draft**. Aucun template disponible, selectable ou route active.
L'implémentation de ce composant de preview n'active pas le profil catalogue,
les médias réels ou la publication. Aucune valeur historique n'est changée.

## Brouillons et données hostiles

Les valeurs vides/null/[] prévues par E.07.02 ont un rendu déterministe : identité
et h1 portent des indications explicites « à compléter » / « brouillon », pas
une personne fictive ; portrait absent réserve une zone d'art clairement signalée.
About/projets/contact sans contenu utile et leurs liens de navigation sont omis.
Les cartes sans titre et les liens sans libellé utilisable ne deviennent pas des
arrêts clavier vides. La navigation vide est omise, le header structurel conservé.
Les titres secondaires manquants utilisent des libellés de section neutres.

Les **clés obligatoires** manquantes ou les types/versions inconnus restent des
documents invalides selon E.07.02 : refus explicite du rendu entier. « Absence »
signifie ici valeurs facultatives/null ou textes vides dans les 14 slots fermés,
pas réparation silencieuse d'un document structurellement invalide.

React échappe les textes ; l'AST rich text fermé produit uniquement paragraphes,
strong et em. Aucun dangerouslySetInnerHTML, CSS arbitraire, HTML libre, lien
non validé ou donnée personnelle codée en dur. Les libellés de navigation et de
structure sont du texte de template ; toutes les informations de profil viennent
des slots. Les annotations de démo sont une option explicite du harness synthétique.

## Médias contrôlés

`ready-fixture-media.ts` reçoit les références UUID existantes et un contexte
**séparé du document**, fourni par le harness de confiance. Ce contexte n'est pas
une nouvelle propriété de snapshot ni une permission accordée à un utilisateur.
Pour l'instant il ne sait sélectionner que des ressources du manifeste synthétique
Git. Il n'ouvre aucun chemin disque, URL distante, original privé ou ancien média.

Une image n'est rendue que si l'UUID est connu du contexte, son compte correspond,
les droits sont confirmés, l'état vaut ready, l'alt n'est pas vide et sourceId
est reconnu. Le src est construit depuis un nom local fermé, jamais depuis une
URL ou un chemin client. Les props width/height sont fixes, loading eager pour
portrait/logo et lazy pour covers, decoding async ; cadrage cover et focal_point
validé. Le logo utilise contain.

| État | Rendu |
|---|---|
| Disponible et autorisé | img avec dimensions et alt du slot |
| Référence absente, inconnue ou alt incomplet | Zone « Image à compléter ou indisponible », aucun fetch |
| processing | Zone « Image en préparation », aucun fetch |
| rejected | Zone générique indisponible, aucun fetch |
| Compte étranger ou droits absents | Zone générique indisponible, aucun fetch |
| Source inconnue ou état non implémenté | Zone générique indisponible, aucun fallback |

Le logo indisponible est omis ; l'identité textuelle reste lisible. Le contexte
synthétique n'est pas un service d'autorisation média réel : un futur service
MEDIA devra construire ses décisions depuis le compte authentifié. E.07.03 ne
livre aucun upload, fournisseur, quota, rétention, réencodage ou accès à des images
privées réelles. Les SVG authored ne changent pas les restrictions d'upload futures.

## Responsive, apparence et accessibilité

Container queries mobile<640, tablette640–1023, desktop≥1024. Portrait carré sur
mobile, 4:5 sur tablette/desktop ; grille projets une colonne sur mobile, asymétrie
et décalages bornés dès tablette. Le contenu n'est ni tronqué ni limité par une
hauteur fixe. La surface de lecture reste opaque, sans texte sur portrait.

Les couleurs proviennent exclusivement de la palette effective E.07.02. Le CTA
utilise accent/surface ; le contact accent sur surface ; texte et focus héritent
des couples contrôlés à 4,5:1. Le petit symbole synthétique est une ressource image
sur fond clair fixe ; aucun calcul de contraste automatique sur des pixels de
portrait ou de logo n'est revendiqué. Les références system-sans/system-serif
contrôlent les titres ; la paire éditoriale conserve un corps système lisible.
Aucun téléchargement de police et aucun nouveau token de document.

Un h1, trois h2 et trois h3 pour la démo complète ; nav nommée, header/main/footer,
sections nommées via aria-labelledby, images alt et décorations aria-hidden.
Skip-link natif et ancres internes de section focalisables ; pas de tabindex
positif. Focus visible et noms de liens présents. Cibles principales ≥44px.
Reduced-motion et forced-colors prévus, aucun mouvement implémenté.

Les tests inspectent structure/labels/alt/clavier dans Chromium ; **aucune session
NVDA/VoiceOver/JAWS n'a été exécutée**. Cela prépare le lecteur d'écran sans
prétendre à une certification WCAG globale. Windows/Safari/Firefox et appareil
physique restent à vérifier, ainsi que le scaling système (zoom CSS200% seulement).

## Prévisualisation indépendante

`render_ready_e0703.mjs` exporte le vrai composant SSR et son vrai CSS dans un
**dossier temporaire neuf hors dépôt**, avec assets vérifiés. CSS Modules : seul le
nom haché des classes est remplacé par le nom local dans le loader de vérification,
pas le renderer ni son style. Le build Next et le typage sont vérifiés séparément ;
aucune route n'est activée pour bundler/servir ce composant.

Quatre pages : studio-a, studio-b, paper-serif et empty-draft. Le premier couple
démontre la substitution, la troisième les personnalisations autorisées et la
quatrième les états de brouillon.

`serve_ready_e0703.py` sert exclusivement ces pages et les huit SVG connus sur
127.0.0.1, sans auth, API ou cookies. Il refuse racine Git, fichiers non prévus,
chemins encodés sortants et symlinks des ressources. CSP bloque scripts, objets,
formulaires et frames ; images self, styles inline nécessaires au vrai SSR.
Le contrôle navigateur respecte la CSP, sans unsafe-eval ni bypassCSP. Aucun
prétexte pour servir le dépôt ou `.local/` avec python -m http.server.

## Revue visuelle et limites

Douze PNG réels sous evidence/ : quatre pages × mobile375, tablette768 et
desktop1440. Les deux portfolios complets ont été examinés en planche comparative :
hiérarchie, portrait, rythme projets, contact et ordre mobile conservés. La police
système et les sauts de ligne peuvent différer sur Windows ; les comparaisons de
composition concernent grilles/ratios/fontes, pas une identité pixel de textes différents.

Les 24 cas layout/largeur, 24 cas textes/zoom, 4 forced-colors et6 comparaisons
de substitution réussissent. Aucun débordement horizontal, erreur JS ou requête
média distante. Les captures sont des preuves de preview synthétique, pas un site
publié ou une approbation utilisateur anticipée.

Aucun budget Core Web Vitals, comportement sous charge, pipeline d'images réelles
ou GPU mobile n'est certifié. Les ressources SVG sont légères et les dimensions
réservées ; mesures de publication/production restent au futur ticket dédié.

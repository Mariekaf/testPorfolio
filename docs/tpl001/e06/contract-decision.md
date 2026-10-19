# E.06 — Variantes textuelles versionnées approuvées

## Constat préalable et autorisation

Au commit E.05 accepté `a3e6e9011d09e72c8f9ca48ce6331eae99a24f1b`, Product
Showcase 1.0.0 exige content-v2/media-assets ; Bento Grid 1.0.0 exige content-v2.
Les validateurs Python/TypeScript les refusent dans les documents content v1.
Le simple passage de `implemented` à true aurait donc annoncé un rendu inutilisable.

Une autorisation spécifique a été demandée avant cette évolution : permettre une
« évolution versionnée de ces prérequis, partagée par les validateurs
Python/TypeScript, pour permettre des compositions fondées uniquement sur les
textes content v1 existants, sans nouveau champ ni média », en préservant les
anciens contrats. **Réponse utilisateur : « Oui, variante textuelle versionnée ».**
Cette autorisation ne vaut pas acceptation anticipée du code E.06.

## Décision implémentée

- Le manifeste déclaratif E.02 et tous les schémas de documents existants sont inchangés.
- Asymmetric 1.0.0 devient rendable avec les contrats existants.
- Product Showcase et Bento Grid **1.1.0** sont les variantes textuelles nouvelles.
  Leurs versions 1.0.0 et leurs prérequis historiques restent refusés, sans remapping.
- `contracts/hero/text-layouts.v1.json`, validé par son schéma fermé homonyme,
  est un profil de confiance `text-layouts` version 1.0.0. Il reconnaît exactement
  ces deux couples id/version et `requires: ["content-v1"]`.
- Aucun champ n'est ajouté aux documents utilisateurs : matrice Design2,
  composition2, content1, presentation2, customization2, HeroConfig1, experience null.
- La politique locale du document doit autoriser explicitement le couple id/version.
  Sa limite de sept entrées est conservée. Les snapshots, defaults et overrides
  existants ne sont jamais modifiés pour ajouter ce droit.

## Sélection explicite du profil, aucune activation de parcours

Python : `HeroCapabilities(text_layouts=True)` et
`resolve_heroes(document, text_layouts=True)` ; même option pour reset.
Sans option, le comportement accepté E.02/E.03 reste inchangé.

TypeScript : `createHeroResolver` accepte le manifeste via une nouvelle option
**d'initialisation de confiance**, `textLayouts`. Ce n'est pas un champ du portfolio.
`hero-runtime.ts` conserve `heroResolver` historique et expose `textHeroResolver`
au composant modulaire isolé. La validation du profil est fermée ; il est copié
avant usage. Aucun profil n'est chargé depuis un document utilisateur.

Le registre renderer passe à 1.1.0 et annonce sept implémentations : cinq couples
1.0.0 et deux couples 1.1.0. Chaque entrée reste `selectable: false`, et
`enabled_by_default` reste false. Les versions 1.0.0 des deux layouts futurs ne
sont pas annoncées comme rendables.

Les APIs, la validation de sauvegarde E.04, le convertisseur, les modèles et les
migrations restent inchangés. Les nouveaux couples ne sont **pas acceptés par les
APIs de persistance actuelles** : leur activation sera une intégration future
explicite, hors E.06. E.06 démontre leur compatibilité structurelle JSON et la
résolution des copies synthétiques issues d'E.04, sans modifier les politiques
ou documents stockés. Cela préserve aussi l'interdiction d'activer ces Hero dans
les routes Studio/publiques.

## Contenu et accessibilité

Seuls title, subtitle et cta_label sont affichés comme contenu. Le panneau
Product est une abstraction CSS, pas une capture réelle de produit. Les trois
cellules décoratives Bento et l'illustration Asymmetric sont `aria-hidden` et
n'affichent aucune statistique, marque ou projet inventé comme donnée utilisateur.
Les démonstrations nomment explicitement leur caractère fictif.

Les règles de fusion/reset/contraste ne sont pas remplacées : le profil ajoute
uniquement des références compatibles. Texte/CTA restent sur une surface opaque,
même avec glass ou gradient. Aucune injection CSS/HTML/JS, aucun moteur externe.

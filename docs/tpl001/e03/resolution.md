# TPL-001.E.03 — Résolution déterministe des Hero

Livraison hors application, issue d'E.02 `76e8af02159ccc237a1f7e83f41d2b6d66db1aab`. Aucun endpoint, renderer, modèle ou stockage ne consomme ces résolveurs. Les schémas, bundles, digests et capacités d'E.02 sont inchangés.

## Entrées et sortie

Python : `resolve_heroes(document)` dans `backend/modules/templates/hero_resolution.py`.

TypeScript : `createHeroResolver(contracts).resolve(document)` dans `packages/content-contracts/src/hero-resolution.ts`. `contracts` contient une map de schémas publics approuvés et le registre de capacités ; ce sont des **entrées de confiance du build**, jamais des documents fournis par un utilisateur. Le helper de lecture de fichiers sous test/ est exclusivement un outil de test, sans accès aux configurations locales. La factory clone les contrats, compile les schémas en mémoire une fois, puis n'en modifie ni les objets ni les statuts. Aucun téléchargement de schéma, plugin ou catalogue.

Seule l'enveloppe Design v2 est acceptée : composition2/content1/presentation2/customization2/experience null. Un snapshot v1 est refusé, jamais converti. Une section non Hero reste dans le document d'entrée et n'est pas modifiée.

Résultat transitoire, non persisté :

```json
{
  "schema_version": 1,
  "design_schema_version": 2,
  "heroes": [{
    "section_id": "hero",
    "visible": true,
    "content": {"title": "Designer fictif", "subtitle": "", "cta_label": "Voir les projets"},
    "layout": {
      "id": "centered", "version": "1.0.0",
      "settings": {
        "mobile": {"spacing": "normal", "alignment": "center", "emphasis": "quiet"},
        "tablet": {"spacing": "normal", "alignment": "center", "emphasis": "quiet"},
        "desktop": {"spacing": "normal", "alignment": "center", "emphasis": "quiet"}
      }
    },
    "appearance": {
      "palette": {"text": "#111111", "surface": "#FFFFFF", "accent": "#222222"},
      "typography": {"family": "system-sans", "scale": "balanced"},
      "background": {"kind": "solid", "color": "#FFFFFF"},
      "surface": {"kind": "flat"}
    },
    "behavior": {"kind": "none"}
  }]
}
```

schema_version=1 décrit cette sortie normalisée, pas un retour à snapshot v1. Aucun identifiant de propriétaire, ETag ou état de publication n'est créé. Les Hero sont retournés dans l'ordre effectif des sections, y compris ceux masqués ; visible explicite évite de perdre leur configuration. Le contenu est copié, jamais interprété comme HTML.

## Algorithme et priorités

1. Valider l'enveloppe et les invariants E.02 : références exactes, types, variantes historiques, ordre, visibilité, politiques, versions, valeurs explicites et prérequis. Aucun default du catalogue source n'est relu.
2. Pour chaque Hero, copier les defaults locaux composition.hero.layout et presentation.hero.appearance, retrouver les overrides par section_id.
3. Remplacer layout id/version comme une paire ; conserver les settings et responsive locaux non remplacés. Une paire inconnue ou absente de la politique est refusée. Product Showcase/Bento restent refusés faute de leurs prérequis ; les cinq autres layouts sont calculables sans être sélectionnables dans un renderer.
4. Base des réglages = presentation.settings → override presentation historique → layout.settings local → layout.settings de l'override Hero. Chaque couche remplace uniquement les clés présentes. Les defaults layout.settings étant complets, ils ont volontairement priorité sur les anciens contrôles de présentation, conformément au contrat E.02.
5. Mobile = base. Tablette = base + responsive.tablet local + override responsive.tablet. Desktop = base + responsive.desktop local + override responsive.desktop. Jamais d'héritage tablette → desktop. Maps fusionnées par clé. Les seuils <640 / 640–1023 / ≥1024 px restent une convention pour les futurs consommateurs ; aucun viewport, DOM ou écran n'est lu par ces fonctions.
6. Palette et typography fusionnent par clé. Background et surface sont remplacés intégralement comme unions typées ; aucune clé d'une ancienne branche n'est conservée. Le comportement absent devient none, seule valeur admise.
7. Valider à nouveau le Hero complet, ses paramètres et chaque breakpoint contre la politique ; vérifier le contraste final complet. Retourner exclusivement de nouveaux objets, sans alias entre entrées, sorties ou maps de breakpoints.

La couche opaque palette.surface derrière textes/CTA reste une exigence de rendu future : le résolveur ne dessine rien et ne transforme pas glass en garantie d'accessibilité visuelle. Les ratios text/surface et accent/surface doivent atteindre 4,5:1, luminance sRGB WCAG sans arrondi préalable. Une couleur partielle acceptée structurellement en E.02 peut être refusée ici après héritage. #767676 sur blanc passe ; #777777 échoue. Un échec ne remplace jamais le layout par Centered ni les couleurs par un preset.

## Reset sans null

Python : `reset_hero_override(document, section_id, path=())`.

TypeScript : `resolver.reset(document, sectionId, path=[])`.

Ces helpers renvoient une **copie** de Design v2 avec la clé d'override supprimée. Ils valident la structure initiale puis la résolution finale complète ; un reset qui restaure une combinaison sans contraste suffisant échoue explicitement. Ils n'écrivent jamais null. Ils peuvent réparer une palette partielle invalide après fusion en retirant la clé responsable.

Les chemins sont relatifs à sections[].hero et strictement autorisés :

- Chemin vide : retirer tout hero, conserver section_id, visible et presentation de l'entrée.
- layout, appearance, behavior : retirer cette dimension.
- layout/settings et ses clés spacing/alignment/emphasis ; layout/responsive, ses entrées tablet/desktop et leurs trois clés.
- appearance/palette et ses clés text/surface/accent ; appearance/typography et ses clés family/scale.
- appearance/background et appearance/surface uniquement en entier, car unions atomiques.

Une paire id/version ne se réinitialise qu'en retirant layout. schema_version, chemins inconnus, chemin null et retrait d'une clé interne d'union sont refusés. Réinitialiser une clé autorisée déjà absente est idempotent ; les conteneurs vides sont retirés, le marqueur hero.schema_version reste présent si hero n'est pas supprimé. L'absence restaure toujours le default local, pas celui du template publié ailleurs.

## Validation TypeScript et dépendance

Ajv **8.20.0**, licence MIT, est ajouté au seul package content-contracts, version exacte et dépendances transitives verrouillées avec intégrités npm. Justification : appliquer Draft 2020-12 et les schémas fermés déjà approuvés, sans maintenir un validateur de schémas artisanal. Aucun coerceTypes, useDefaults ou removeAdditional ; aucune mutation ni correction silencieuse. Aucune dépendance d'animation/3D. Le point d'entrée existant du package et le Studio n'importent pas ce nouveau module.

Le validateur TS reprend les contrôles sémantiques de sections nécessaires au document complet. Les formats reproduisent la configuration jsonschema verrouillée : UUID canonique ; email contenant @ ; la sûreté des liens HTTPS est contrôlée séparément. Le format uri n'étant pas enregistré dans l'environnement Python verrouillé, il n'ajoute pas de restriction JSON Schema différente côté TS. Les validations de production existantes ne sont pas modifiées.

La limite reste 262144 octets UTF-8 avec le comptage des séparateurs Python ; les valeurs JS non JSON, non finies, cycliques et les chaînes contenant des surrogates isolés sont refusées. Les entrées usuelles sont des objets JSON déjà parsés ; ces fonctions ne remplacent pas le parseur HTTP strict qui refuse les clés dupliquées. Les erreurs publiques ne contiennent pas le document.

Ajv compile du code à partir des seuls schémas de confiance. Avant une intégration future au navigateur, il faudra examiner une génération standalone au build et la CSP ; aucune compilation de schéma utilisateur ou activation dans le navigateur n'est livrée ici.

## Preuves communes et limites

`contracts/fixtures/hero/resolution.v1.json` contient un design synthétique de base et **55 cas** avec changements explicites et résultats attendus écrits indépendamment des résolveurs. Ils couvrent héritage, priorités, palettes, contraste final, seuils, unions, responsive, resets idempotents/refusés, versions/politiques inconnues, comportement futur refusé et plusieurs Hero dont un masqué.

Les tests Python et TS appliquent les mêmes cas et vérifient les résultats attendus. Le test de parité Python lance réellement Node et compare tous les résultats, erreurs et documents de reset, sans ignorer le test si Node manque. Les tests TS gèlent profondément leurs entrées et vérifient l'absence d'alias. Aucun test de parité n'est un simple contrôle de présence des fixtures.

`v1-reference.v1.json` épingle 12 sources/snapshots/schémas approuvés et les empreintes du HTML statique Minimal/Editorial. Les sources texte autorisent uniquement l'équivalence de checkout LF/CRLF, sans autre normalisation ; les bundles conservent aussi leurs digests réels contrôlés par les tests E.02. Les classes CSS sont simulées comme dans les tests renderer existants : ce sont des références DOM et de sources CSS, **pas des captures navigateur ni une recette visuelle**.

Les capacités restent runtime_enabled=false, implemented=false, selectable=false. La résolution prouve une configuration calculable et validée, pas un renderer disponible. Aucun stockage, conversion, publication ou ticket E.04+ n'est activé.

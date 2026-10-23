# E.05 — Rendu modulaire isolé, version 1.0.0

Les quatre dispositions autorisées sont `centered`, `split-screen`, `fullscreen`
et `typographic`, version `1.0.0`. Le composant serveur React est
`apps/studio/src/components/templates/modular-hero-renderer.tsx`.
Il ne remplace pas le renderer v1. Aucun écran, endpoint, sélecteur de layout,
conversion, écriture ou drapeau backend n'est ajouté ou activé.

## Frontière d'intégration

Un appelant explicitement autorisé pourra utiliser :

```tsx
<ModularHeroRenderer
  snapshot={snapshotV2}
  sectionId="hero"
  scope="portfolio-example"
  continuationId="portfolio-projects"
  enabled={true}
/>
```

`snapshot` est le document complet v2, tel que sauvegardé par E.04, sans projection,
réécriture ou conversion. Le composant appelle le résolveur E.03 sur ce document
avant de lire son contenu. Le chargement et le contrôle d'accès restent la
responsabilité du serveur existant ; le renderer ne reçoit aucun identifiant de
compte et n'effectue aucune requête. Les transitions, révisions, idempotence,
ETag/If-Match et permissions E.04 restent inchangées.

Sans `enabled={true}`, le composant lève `HeroRenderingError` avant résolution.
Il n'existe aucun fallback v1 ou Centered. Les routes actuelles continuent à
utiliser exclusivement le renderer v1. L'activation dans un parcours Studio ou
public nécessitera un ticket ultérieur autorisé : la prop n'est pas une préférence
utilisateur persistée ni un nouveau mécanisme d'autorisation.

L'appelant choisit un `scope` unique par instance de Hero dans un même document,
et doit fournir la vraie section suivante portant l'ID `continuationId` s'il veut
un CTA. Le composant valide le format des IDs, utilise uniquement des fragments
locaux, et omet le CTA si sa cible n'est pas fournie ou son libellé est vide.
Il ne fabrique pas de destination factice. Le harness de vérification fournit une
section de projets synthétique. Un titre vide est refusé explicitement ; aucun
texte utilisateur n'est inventé pour le remplacer. Le Hero porte l'unique h1 de
la page ; l'intégrateur doit éviter plusieurs titres principaux.

## Registres et validation

`contracts/hero/capabilities.v1.json` et les schémas E.02 restent inchangés : ils
forment le registre déclaratif figé dont dépend le résolveur accepté. Le registre
additif `contracts/hero/renderer.v1.json` décrit cette implémentation E.05 :

- Quatre layouts implémentés ; aucun n'est sélectionnable dans un éditeur.
- Trois layouts non implémentés : Asymmetric, Product Showcase, Bento Grid.
- Apparence : palette, solid, gradient, system-sans, flat, glass.
- Comportement : `none` uniquement. Activation par défaut : false.

`hero-runtime.ts` assemble les vrais schémas JSON comme entrées de confiance du
résolveur E.03. Aucun schéma ni registre n'est accepté depuis les données du
portfolio. `hero-rendering.ts` vérifie ensuite les capacités et versions rendables.
Un layout déclarable/résolvable n'est pas nécessairement rendable : Asymmetric
est rejeté au rendu ; Product/Bento restent également interdits et leur absence
de prérequis est déjà contrôlée par E.03. Versions inconnues, dimensions
incompatibles, propriétés arbitraires et comportements futurs échouent.

Les overrides, suppressions de clés/reset, atomicité des unions et règles de
fusion ne sont pas réimplémentés : c'est le résolveur accepté qui les applique.
Les deux contrastes texte/surface et accent/surface doivent atteindre 4,5:1,
sans arrondi avant décision. Un document invalide ne produit aucun rendu partiel.

## Composition et apparence

| Layout | Composition effective |
|---|---|
| Centered | Panneau de lecture centré et arrondi, largeur de lecture limitée |
| Split Screen | Texte et illustration géométrique CSS pure en deux colonnes dès 640 px ; une colonne sur mobile |
| Fullscreen | Hauteur minimale 100svh, panneau opaque et repère de portfolio ; aucun blocage du scroll |
| Typographic | Titre surdimensionné, règles et signature décorative ; composition asymétrique du texte dès 1024 px |

La signature décorative de Typographic n'active pas le layout futur `asymmetric`.
Ces éléments sont `aria-hidden` et ne prétendent pas représenter une image ou
un projet réel. Aucun média, téléchargement de police ou moteur tiers n'est ajouté.

La palette est indépendante du layout. La famille autorisée reste `system-sans`,
avec les trois échelles compact/balanced/display. Le fond solid ou gradient est
construit uniquement depuis des couleurs hex et nombres validés : ni CSS, HTML,
URL, JavaScript ni balisage arbitraire. React échappe les contenus textuels.
Les variables CSS sont une sortie interne de valeurs bornées, jamais un langage
fourni par l'utilisateur.

Une surface `glass` est **décorative**, derrière les panneaux opaques de lecture.
Le texte, les CTA et le repère restent sur `palette.surface` opaque. Opacité
85–100 et flou 0–12 px respectent le contrat ; l'absence de backdrop-filter laisse
la couche colorée décorative. Une surface flat n'ajoute aucun flou. Les gradients
peuvent comporter 2–4 stops strictement ordonnés selon E.03. Le contraste n'est
jamais justifié par une moyenne de gradient ou une transparence supposée.

## Responsive, accessibilité et performance

Les container queries prennent la largeur réelle du Hero : mobile <640 px,
tablette 640–1023 px, desktop ≥1024 px. Le CSS reçoit séparément les trois
réglages effectifs E.03, notamment desktop sans héritage implicite de tablette.
Sur très petite largeur, les marges sont plafonnées pour préserver la lisibilité.
Les titres, sous-titres et libellés longs reviennent à la ligne. Fullscreen utilise
une hauteur minimale extensible, jamais un cadre de hauteur fixe qui coupe le texte.

CTA natif clavier, cible réelle, focus visible contrasté et hauteur ≥48 px ;
aucun tabindex positif, capture de scroll, mouvement ou lecture automatique.
`prefers-reduced-motion` neutralise aussi les animations/transitions qui seraient
héritées. Le mode forced-colors utilise les couleurs système. Aucune garantie de
certification WCAG globale du portfolio ne découle des seuls tests de ce composant.

Aucun composant client, effet, mesure JS de viewport, média distant ni moteur
GSAP/Three.js. Le rendu produit uniquement du HTML et du CSS ; Ajv s'exécute côté
serveur/harness et valide les contrats une fois par instance de module. Les bornes
de taille/profondeur de document d'E.03 restent appliquées. Le coût d'un flou borné
peut néanmoins varier selon le GPU ; aucune mesure sur mobile physique n'est revendiquée.

## Références visuelles

Les 12 PNG sous `evidence/` proviennent du vrai composant React SSR et de son vrai
CSS, aux largeurs 375, 768 et 1440 px. Le loader de test remplace uniquement les
noms hachés CSS Modules par leurs noms locaux ; il ne redessine aucun composant.
Les pages sont générées hors dépôt, puis servies temporairement sur 127.0.0.1
par le script navigateur, sans application, API ou base. Elles utilisent les
quatre documents fictifs UTF-8 de `contracts/fixtures/hero/rendering.v1.json`.

Ces captures sont des références de revue E.05, pas une recette utilisateur
Windows, un test de publication v2, ni un nouveau bundle immuable Minimal/Editorial.
La chaîne de build Next et le typage sont contrôlés séparément ; aucune route
Next modulaire n'est activée pour produire les captures.

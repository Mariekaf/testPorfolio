# E.06 — Mesures de performance et limites

Mesure exécutée sous Linux, Node 24.19.0, avec le vrai composant React SSR et le résolveur complet. Aucune base, requête API ou route active. La commande reproductible est :

```sh
node scripts/verification/benchmark_hero_e06.mjs /tmp/hero-e06-performance-NEW.json
```

Le fichier doit être nouveau : le script refuse un écrasement. Après dix passages de chauffe, cent rendus sont chronométrés par layout. Les quantiles sont des observations du cloud partagé, sans seuil de SLA ni promesse sur le PC utilisateur.

| Layout | Médiane SSR (ms) | p95 SSR (ms) | HTML (octets UTF-8) |
|---|---:|---:|---:|
| centered | 0.722 | 1.110 | 1119 |
| split-screen | 0.501 | 0.840 | 1172 |
| fullscreen | 0.504 | 0.913 | 1230 |
| typographic | 0.495 | 0.867 | 1189 |
| asymmetric | 0.596 | 0.960 | 1215 |
| product-showcase | 0.749 | 1.085 | 1377 |
| bento-grid | 0.718 | 1.086 | 1438 |

Initialisation mesurée du harness : **577.9 ms**. Elle inclut les hooks TSX/CSS de test, les imports et les deux profils Ajv ; ce n'est pas le cold start d'une application déployée. Le premier rendu de la série vaut **58.7 ms**, avec compilation initiale des validateurs. Les premiers rendus suivants bénéficient déjà de ce travail partagé : ils ne constituent pas sept cold starts indépendants.

Le CSS source commun passe de **4769 à 9548 octets** ; sa compression gzip indicative de **1500 à 2236 octets**. Ces tailles ne sont ni les chunks minifiés Next publiés ni une mesure de transfert HTTP. Aucun paquet ou lockfile applicatif ne change.

Le composant reste serveur, sans hook client, timer, gestionnaire de scroll ou média distant. Les figures sont du CSS statique et aria-hidden ; aucun réseau ou décodage de média supplémentaire. Glass conserve un flou décoratif borné à 12 px et un panneau de texte opaque. Les documents restent limités à 256 Kio et les références sont validées avant tout rendu.

## Limites et risques à suivre

- Pas de mesure de Core Web Vitals, LCP/CLS/INP, mémoire serveur sous charge ou débit HTTP ; aucune route modulaire activée.
- Les deux profils Ajv partagent le contrat mais ont chacun leur instance de validation ; le coût froid est visible dans la mesure du harness. Ne pas reconstruire le résolveur à chaque requête lors d’une future intégration.
- Pas de mesure GPU/mobile physique ; backdrop-filter peut coûter davantage sur un appareil ancien. Le fallback conserve une couche colorée décorative, sans supprimer la surface de lecture opaque.
- Les titres longs agrandissent volontairement le Hero : pas de hauteur fixe ni de troncature silencieuse. La vérification 200 % est un zoom CSS Chromium ; le scaling système Windows n’est pas mesuré.
- Les douze comparaisons pixel E.05 ne sont valables qu’à environnement graphique identique. Les différences de polices Windows/Linux doivent être examinées séparément.
- Pas de certification lecteur d’écran, Safari ou Firefox. Le fonctionnement clavier, forced-colors et reduced-motion est vérifié dans Chromium Linux.

Résultats bruts : [evidence/performance.json](evidence/performance.json). E.07 et l’activation applicative restent hors périmètre.

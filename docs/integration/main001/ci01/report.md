# MAIN-001.CI.01 — Installer les dépendances Node avant Django

## Diagnostic et limites des sources

Base : `412bcccab714dd993f9b42539ce3e9a950795c23`, branche
`integration/main-001-saas`. L’utilisateur rapporte 393 tests Django et 33 erreurs
sur le run GitHub `39974616727`, PostgreSQL/privilèges validés.

L’API GitHub refuse toujours le téléchargement de l’artefact et la lecture du run
(`Forbidden`). Aucun fichier joint n’est disponible dans cette session. Les traces
ci-dessous sont donc des **preuves locales reproduites**, pas des journaux distants
prétendument récupérés. La CI distante n’est pas déclarée réussie.

Dans une archive Git neuve sous `/tmp`, sans `node_modules`, les mêmes drivers
appelés par les tests Python sont exécutés avec Node 24 et leur stderr capturé :

- `hero-rendering-driver.mjs` : exit 1,
  `Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'react'`.
- `ready-rendering-driver.mjs` : exit 1, même erreur pour `react`.
- `ready-e0702-driver.mjs` : exit 1,
  `Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'ajv'` depuis
  `packages/content-contracts/src/ready-contracts.ts`.

Les tests Python de parité et rendu SSR appellent ces drivers via `subprocess.run`
avec `capture_output=True, check=True`. L’erreur Python `CalledProcessError` est
une conséquence : les imports Node échouent avant leur traitement du document.
React, Ajv et les outils de compilation nécessaires sont déjà présents dans les
manifestes et le lockfile ; ils manquent seulement dans le checkout CI au moment
incorrectement choisi pour les tests Django.

## Correctif minimal

Déplacer l’unique étape **`npm ci --ignore-scripts`** immédiatement après
l’installation Python et avant le runner de migrations/tests Django. Aucun paquet,
version, lockfile, script applicatif, test ou garde de migration n’est modifié.
L’option `--ignore-scripts`, les contrôles d’intégrité, permissions, rôles et suites
existants restent inchangés. Les autres fichiers ajoutés sont uniquement ce
rapport et ses preuves.

## Protocole de reproduction

1. Archiver le commit de base dans un nouveau dossier sans dépendances Node.
2. Capturer les stderr des drivers et exécuter les 393 tests via le runner existant,
   avec PostgreSQL 17.11 natif neuf et stockage privé jetable.
3. Attendre la fin du run défaillant ; ne pas installer npm pendant son exécution.
4. Exécuter `npm ci --ignore-scripts` dans cette même copie, sans changer les sources.
5. Relancer les drivers avec exactement les mêmes entrées et toute la suite Django,
   sur un **autre** cluster neuf ; exécuter Node complet, TypeScript et build Next.
6. Vérifier le YAML : une seule installation npm, placée avant Django, permissions
   `contents: read` inchangées.

Les instances PostgreSQL et leurs stockages sont supprimés par le runner. Aucun
accès à une base persistante, `.local/`, une démo ou au CMS historique. Docker/CI
GitHub ne sont pas revendiqués comme exécutés localement : Linux natif est utilisé.

## Résultats avant correction

Copie neuve sans dépendances Node : **393 tests exécutés, 33 erreurs**, 103,263 s.
Cette reproduction rejoint exactement le nombre d’erreurs rapporté pour GitHub.
Les 33 entrées d’erreur sont toutes des `CalledProcessError` de processus Node,
réparties dans `test_hero_rendering`, `test_hero_resolution`,
`test_hero_text_layouts`, `test_ready_rendering` et `test_ready_templates`.
Les trois drivers ci-dessus retournent exit 1 avant installation. Voir les fichiers
`before-*.stderr` et `before-django.log` dans [evidence](evidence/).

Après installation des dépendances, ces mêmes appels retournent exit 0, sans
`ERR_MODULE_NOT_FOUND` (`after-*.stderr` et `after-*.stdout`). Deux stderr sont
vides ; le driver de rendu ready émet un avertissement Node
`MODULE_TYPELESS_PACKAGE_JSON` non bloquant. Il est conservé dans les preuves,
sans changement de package.json hors périmètre. Le driver de registre valide le digest et
le statut draft ; les deux drivers de rendu acceptent une liste vide. La suite
Django complète après installation vérifie les vrais documents et rendus.

Le cache npm par défaut sous `/home/agent` était inaccessible dans cet environnement
cloud. L’installation a été rejouée avec un cache temporaire sous `/tmp` ; aucune
modification du workflow pour ce détail local. Ce problème de cache ne doit pas
être confondu avec la cause démontrée du run CI.

## Résultats après installation

- **393 tests Django réussis**, zéro erreur/skip, 111.509 s ; même archive de
  sources, autre cluster PostgreSQL 17.11 natif neuf et stockage privé neuf.
- Schéma : aucune modification détectée ; privilèges minimaux runtime/test validés.
- 226 tests Node réussis, aucun échec/skip ; TypeScript strict et build Next réussis.
- Intégrité/ACL : 25 exécutés, 22 réussis et 3 ignorés Windows, sans les compter
  comme réussites ; CMS historique : 6 réussis ; 11 empreintes historiques et
  4 empreintes de fixture intactes.
- YAML parsé et ordre vérifié : une seule étape npm avant le runner Django.

La reproduction native Windows et le runner Docker GitHub ne sont pas exécutés
localement ; les preuves sont Linux natif. Aucun changement des tests pour obtenir
ces résultats.

## Livraison et CI distante

Le correctif est destiné à `integration/main-001-saas`, sans force-push.
La publication Git et les tentatives de consultation de la PR #3/CI sont rapportées
avec le SHA final dans le message de livraison. Une réponse `Forbidden` interdit
de confirmer les checks et donc de fusionner. Aucun bypass ou push direct vers
main. TPL-002 reste en attente ; aucun déploiement ni publication de portfolio.

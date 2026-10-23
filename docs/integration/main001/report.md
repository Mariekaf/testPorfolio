# MAIN-001 — Consolidation SaaS pour main

## Historique et méthode

- Main distant examiné : `59f4e5ca9ef345fdf581d7056ec52868db8b550c`.
- Source SaaS : `ffbd17953167aea16311b06ea6e43602fa979d59`.
- Ancêtre commun : `f2f8e5d27ceb9b8df1dce008ecda62e6e903460a` (BASE-001).
- Divergence initiale : 60 commits SaaS et un commit propre à main.
- Le commit propre à main est la fusion de BASE-001, parents `bf8952534bf8a17e7eb4521fee91d62409edc62a` et `f2f8e5d27ceb9b8df1dce008ecda62e6e903460a`.
  Son arbre est identique à BASE-001 : aucun changement de contenu propre à main
  ne reste à reporter ou arbitrer.
- Branche d’intégration créée depuis main : `integration/main-001-saas`.
- Fusion non fast-forward, sans réécriture ni squash :
  `80f0e4ab801c0e1cad01154139dbef12e336b135`.
  Ses parents sont main puis la source SaaS. Aucun conflit.
  Son arbre est identique au commit SaaS source, vérifié avec `git diff --quiet`.

Cette consolidation conserve les deux historiques. Le correctif CI et les preuves
ci-dessous sont ajoutés dans un commit de suivi ; aucun commit déjà publié n’est
modifié. La comparaison globale initiale comporte 685 fichiers : elle regroupe les
livraisons CORE, AUTH, PORT, TPL et MEDIA, et pas seulement les 34 fichiers de F.

## Préservation et sécurité

Aucun changement de code métier pendant MAIN-001. Aucun changement du CMS
historique, d’AUTH, des contrats, renderers, snapshots/bundles ou migrations par
rapport à la source SaaS. Les fichiers historiques sont aussi vérifiés contre la
référence BASE-001. Aucune nouvelle migration, migration destructive, conversion
ou écriture sur une base existante. Les tests de migrations existantes utilisent
uniquement un cluster PostgreSQL 17 neuf, synthétique et jetable.

Aucun accès à `.local/`, à une configuration habituelle ou à la démonstration
persistante. Le scan des chemins et signatures de secrets du delta complet ne
signale aucun fichier sensible ni clé connue ; cela ne constitue pas un audit
exhaustif de sécurité. Les preuves ne contiennent pas de configuration privée,
credential, cookie ou mot de passe. Dépendances applicatives et lockfiles inchangés.

Les tests vérifient notamment l’isolation des comptes, les permissions, CSRF,
sessions, ETag, quotas médias, intégrité des images, révisions, concurrence et
restauration. Aucun élargissement de permissions ni activation de PUB-001.

## Adaptation de la CI

Le workflow CORE initial provisionnait directement une base standard puis exécutait
les migrations. Les migrations E.04/E.07.04/MEDIA exigent désormais une autorisation
et une identité synthétique explicites : cette ancienne séquence n’est plus adaptée.

Le workflow conserve le nom et le job `linux-foundations`, les permissions
`contents: read`, les versions Python 3.13 / Node 24 et les contrôles historiques.
Il utilise le runner isolé existant, qui vérifie l’identité du cluster PostgreSQL 17,
provisionne les rôles minimaux, vérifie les migrations et le schéma, exécute la suite
Django puis détruit son propre stockage. Les flags de migration sont limités au
processus synthétique, sans désactiver les gardes applicatives. Le runner n’accepte
aucune base ou configuration existante.

La CI utilise Docker sur son runner GitHub éphémère, avec l’image 17 par digest déjà
verrouillée dans le runner. Les vérifications locales utilisent PostgreSQL **natif**,
sans Docker. Cette différence est explicite : le passage CI Docker ne peut pas être
déclaré réussi avant son exécution distante. La suite Node couvre maintenant tous
les contrats/Studio (226 tests), plutôt que les seuls scripts historiques. Les
pushes main/intégration et les PR déclenchent le workflow ; aucun filtre de contrôle
bloquant n’est supprimé. Les artefacts autorisés sont une liste fermée de journaux
sans secrets, pas les fichiers de configuration temporaires.

Le YAML a été parsé, ses déclencheurs, l’identité du job et les permissions vérifiés.
Ce contrôle ne remplace ni actionlint ni l’exécution GitHub Actions.

## Validation locale

Voir les journaux dans [evidence](evidence/). Python 3.13.5, Node 24, PostgreSQL
17.11 natif neuf et Chromium Linux. Aucun test ne vise une base persistante.

- Suite Django complète : **393 réussis**, 120,634 s, zéro échec/skip ; `django-tests.log`.
- Migrations existantes, `makemigrations --check --dry-run`, rôles runtime/test :
  réussis dans le cluster neuf ; preuves `schema-check.log`, `runtime-privileges.log`.
- Node : 226 tests réussis, zéro échec/skip.
- TypeScript strict et build Next : réussis, aucune mise en service de production.
- Vérifications intégrité/ACL : 25 exécutés, 22 réussis, 3 ignorés Windows.
- CMS historique : 6 tests réussis ; syntaxe `script.js` et `admin.js` valide.
- Référence BASE : 11 empreintes historiques et 4 empreintes de fixture préservées.
- Dépendances Python : 12 paquets vérifiés compatibles via `uv pip check`.
  Le venv n’embarque pas pip ; `python -m pip check` y est indisponible, pas réussi.
- Audit npm production : zéro vulnérabilité signalée à cette exécution.
- Parcours navigateur F : voir `navigation-results.json` ; trois templates, panneaux,
  brouillons, sauvegarde/réouverture, sorties/historique, conflits réels, archive,
  suppression, isolation, médias et session révoquée.

## GitHub, fusion et déploiement

L’accès Git permet fetch/push. L’API GitHub retourne `Forbidden` et `gh auth status`
signale que le jeton GH_TOKEN est invalide. Aucun contournement n’est tenté. Sans
création/inspection de PR et accès aux contrôles requis, aucune fusion directe par
push sur main ne doit être utilisée pour contourner la revue/CI.

Comparaison prévue :
https://github.com/Mariekaf/testPorfolio/compare/main...integration/main-001-saas

Pour débloquer : fournir au client GitHub une authentification valide avec accès au
dépôt, création de PR, lecture des checks/protections et droits de fusion autorisés.
Sur un poste personnel, remplacer le GH_TOKEN invalide ou, si approprié, le retirer
de cette session et effectuer `gh auth login --hostname github.com --web`. Ne jamais
copier le jeton dans Git, un journal ou une conversation. Ensuite :

```powershell
gh auth status
gh pr create --repo Mariekaf/testPorfolio --base main --head integration/main-001-saas --title "MAIN-001 — Consolidation du SaaS Portfolio" --body-file docs/integration/main001/report.md
# Utiliser le numéro réel retourné, sans supposer qu’une PR existe déjà.
gh pr checks NUMERO --repo Mariekaf/testPorfolio --watch
```

Vérifier aussi les protections de main, approbations exigées, absence de conflit et
SHA exact de tête, puis seulement fusionner si tous les contrôles requis sont
réussis. Ne pas utiliser `--admin`, force-push, un remplacement de main ou le bypass
des contrôles. Si main évolue entre-temps, le fusionner normalement dans la branche
d’intégration puis refaire les contrôles concernés.

Aucune cible de production opérationnelle et documentée :
`backend/config/settings/production.py` refuse volontairement de démarrer. Aucun
déploiement, aucune URL de production, aucune publication de portfolio.

## Réserves

Windows natif non exécuté dans cet environnement ; les skips Windows ne sont pas
des réussites. Réserves F conservées : lecteur d’écran, zoom navigateur réel et
sauts multi-entrées de l’historique sur certains moteurs. Pas de certification WCAG
exhaustive ni de validation charge/production. L’état distant final et les SHA de
livraison sont communiqués dans le rapport final de session.

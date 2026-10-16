# BASE-001 — Rapport d'exécution

- Date : 16 octobre 2026.
- Branche dédiée : `arch/base-001`.
- Référence historique : `bf8952534bf8a17e7eb4521fee91d62409edc62a`.
- État Git initial : propre.
- Autorisation : ARCH-002 validé ; BASE-001 seulement.
- Résultat : référence de compatibilité établie ; aucun changement du CMS historique ; CORE-001 non commencé.

## Travail réalisé

1. Création de la branche sans worktree ni déplacement de checkout.
2. Inventaire du serveur, du rendu public, de l'administration, des paramètres, des données et des tests.
3. Matrice de 41 capacités/scénarios avec preuves exécutées ou lecture des sources explicitement distinguées.
4. Carte complète du JSON historique, références médias, invariants et cas de futur import à traiter.
5. Fixture créée de zéro : identité fictive, adresses example.test, trois projets dont un brouillon, Unicode/paragraphes, deux sections par projet et trois PNG générés dont un orphelin.
6. Manifeste SHA-256 des 11 fichiers historiques, manifeste des quatre fichiers de données synthétiques et vérificateur sans dépendance.
7. Exécution des six tests existants, des contrôles syntaxiques et de douze scénarios navigateur supplémentaires.
8. Protocole PowerShell de sauvegarde privée à froid, vérification des empreintes et restauration dans une copie isolée.
9. Préparation documentaire des options Docker et PostgreSQL natif Windows pour CORE-001. Aucune commande de ce futur ticket exécutée.

## Résultats des vérifications

Environnement courant : Linux, Python 3.12.14, Node.js v24.19.0, Git 2.52.0. Playwright et Chromium sont préinstallés. Aucune dépendance installée. Le choix Python 3.13 du futur socle SaaS n'est pas implémenté par ce ticket.

| Vérification | Exécutée | Résultat | Preuve |
|---|---|---|---|
| Suite historique standard | Oui | 3 réussites | evidence/existing-tests.txt |
| Même suite avec encodage cp1252 simulé | Oui | 3 réussites | evidence/existing-tests.txt |
| Total historique | Oui | 6 tests, 0 échec, 0 erreur, aucun skip annoncé ; 2,176 s | evidence/existing-tests.txt |
| Syntaxe script.js | Oui | Code de sortie 0 | evidence/javascript-syntax.txt |
| Syntaxe admin.js | Oui | Code de sortie 0 | evidence/javascript-syntax.txt |
| Référence des sources | Oui | 11 empreintes identiques | evidence/reference-check.txt |
| Fixture/manifestes | Oui | 4 empreintes ; validation sans troncature ; ordre, brouillon, Unicode et médias vérifiés | evidence/reference-check.txt |
| Navigateur | Oui | B01–B12 réussis ; aucune erreur JavaScript collectée | evidence/browser-tests.txt |
| Sauvegarde/restauration du PC utilisateur | Non | Procédure livrée ; données réelles non accessibles/non utilisées | ../runbooks/legacy-backup-windows.md |
| PostgreSQL natif Windows ou Docker | Non | Préparation documentaire uniquement ; CORE-001 non commencé | ../runbooks/core001-windows-postgresql-options.md |
| Audit complet accessibilité, charge et sécurité | Non | Hors BASE-001 ; cas sources signalés S dans la matrice | feature-matrix.md |

Les tests historiques créent leurs propres dossiers temporaires ; leur exemple suivi historique reste inchangé. Aucun contenu personnel de cet exemple n'est copié dans les nouveaux livrables. Les vérifications supplémentaires utilisent uniquement la fixture synthétique. Les identifiants nécessaires aux tests sont générés dans leurs répertoires temporaires et ne sont pas enregistrés dans les preuves ou commits.

### Détail navigateur

- B01 : accueil, portrait, ordre des publiés, à propos et contact.
- B02 : page dédiée rechargeable, métadonnées/liens, texte littéral, Unicode, sections et comportement introuvable historique HTTP 200.
- B03 : connexion et liste complète des projets en administration.
- B04 : création, image, brouillon, publication et mise à jour immédiate actuelle après sauvegarde.
- B05 : sections, ordre, suppression, liens et retrait de référence de couverture.
- B06 : duplication avec brouillon/nouveau slug, suppression et ordre des projets.
- B07 : aperçu refusé à l'invité, brouillon accessible en session et navigation conservant le mode aperçu.
- B08 : modification du profil, mailto, liens externes protégés et contact masqué sans e-mail.
- B09 : aperçu palette et options de thème appliquées au portfolio.
- B10 : JSON des modifications en mémoire, ZIP du disque avec orphelin et sans auth, import annulé/confirmé puis sauvegardé.
- B11 : indicateur dirty et avertissement beforeunload.
- B12 : absence de débordement horizontal à 390 px du public/admin/éditeur et déconnexion.

Un premier passage du nouveau script navigateur s'est arrêté à B09 : le sélecteur du harnais exigeait un libellé exact alors que le label du select contient aussi ses options. Le sélecteur du seul script BASE-001 a été corrigé ; le passage complet suivant a réussi. Aucun correctif du CMS n'a été nécessaire. La présence de reduced-motion dans les styles ne vaut pas audit exhaustif des mouvements ou de l'accessibilité.

## Limites conservées sans modification

La matrice sépare dix groupes de limites des capacités à préserver : médias publics par URL, publication immédiate, troncatures de listes, mémoire non partagée, validation d'image partielle, shell HTTP 200/SEO client, aperçu partiellement propagé, export/restauration limités, contenu codé en dur et absence de fonctionnalités SaaS avancées.

La publication manuelle, les snapshots et la confidentialité médias sont des changements approuvés pour les tickets suivants, pas des modifications à faire dans BASE-001.

## Statut des critères d'acceptation

| Critère ARCH-002 / consigne | Statut | Preuve / limite |
|---|---|---|
| Chaque fonctionnalité identifiée et associée à une vérification | Conforme | Inventaire + C01–C41 ; tests exécutés distincts des scénarios par lecture |
| Limites connues séparées des comportements à conserver | Conforme | L01–L10 dans la matrice |
| Six tests existants exécutés et résultat consigné | Conforme | Preuve brute, 6 réussites |
| Exports/imports, brouillons, images et paramètres couverts | Conforme | H1–H3, B01–B12, carte des données |
| Différence sauvegarde/publication cible documentée | Conforme | C29/L02 et invariants ; manuel par défaut dans le SaaS |
| Sources locales absentes de Git incluses dans la conservation | Conforme | Inventaire par installation, variable DATA et protocole privé |
| Aucune donnée personnelle/auth dans les nouvelles fixtures ou preuves | Conforme | Création synthétique, example.test, PNG générés ; aucun fichier privé copié |
| Aucun fichier historique modifié | Conforme | 11 SHA-256 identiques et comparaison Git avec le commit de référence |
| Aucun média ou fichier .local supprimé/déplacé/réécrit | Conforme | Tests sur dossiers temporaires ; aucun accès à la source privée réelle |
| Branche Git dédiée et liste des fichiers | Conforme | arch/base-001 ; liste ci-dessous |
| Alternative PostgreSQL natif Windows prévue | Conforme documentaire | Runbook dédié, non exécuté ; validation native future |
| CORE-001 non commencé | Conforme | Aucun backend SaaS, package, service DB ou dépendance ajouté |

## Fichiers créés

Aucun fichier préexistant modifié. Vingt fichiers nouveaux :

1. docs/compatibility/README.md
2. docs/compatibility/BASE-001-report.md
3. docs/compatibility/feature-inventory.md
4. docs/compatibility/feature-matrix.md
5. docs/compatibility/legacy-data-map.md
6. docs/compatibility/legacy-source-manifest.json
7. docs/compatibility/evidence/existing-tests.txt
8. docs/compatibility/evidence/javascript-syntax.txt
9. docs/compatibility/evidence/reference-check.txt
10. docs/compatibility/evidence/browser-tests.txt
11. docs/runbooks/legacy-backup-windows.md
12. docs/runbooks/core001-windows-postgresql-options.md
13. scripts/verification/check_base001.py
14. scripts/verification/browser_base001.py
15. tests/fixtures/base001/README.md
16. tests/fixtures/base001/legacy-content.json
17. tests/fixtures/base001/manifest.json
18. tests/fixtures/base001/uploads/11111111111111111111111111111111.png
19. tests/fixtures/base001/uploads/22222222222222222222222222222222.png
20. tests/fixtures/base001/uploads/33333333333333333333333333333333.png

## Blocages et réserves

Aucun blocage pour achever BASE-001. La sauvegarde réelle sur le PC et les parcours Windows natifs ne sont pas exécutables depuis cet environnement ; ils ne sont pas présentés comme validés. Leur exécution sera requise avant une migration réelle / pour la validation Windows de CORE-001.

Le rapport ne vaut pas validation automatique de CORE-001. Attendre l'accord utilisateur avant toute création de socle Django/Next.js/PostgreSQL, toute nouvelle dépendance ou migration.

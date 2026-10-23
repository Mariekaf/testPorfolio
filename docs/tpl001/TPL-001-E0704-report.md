# Livraison de revue — TPL-001.E.07.04

**Livrée pour revue, non déclarée validée.** 20 octobre2026.
Branche `feature/tpl-001-e0704`, parent approuvé
`144043b67c96b7869c714e79a0b1b66c536ad5f5` ; SHA de livraison communiqué à la remise.
Une seule branche et une seule livraison E.07.04, aucune PR/fusion/déploiement.

## Parcours livré

Depuis le dashboard authentifié, **Choisir Creative Editorial** ouvre une sélection
privée avec miniature, description et aperçu réel du brouillon vide. La création
explicite produit un portfolio neuf privé, sans conversion ni identité fictive par
défaut. Les 14 slots disposent de contrôles structurés, y compris paragraphes et
fragments gras/emphase, projets, liens, réseaux et références média.

Palettes et références de police autorisées, couleurs hexadécimales sous contraintes
AA4,5:1 et reset par suppression des overrides. La composition n'est pas éditable.
Le véritable composant visuel E.07.03 est partagé entre wrapper serveur et aperçu
client privé, avec validation E.07.02 ; aucun moteur de rendu parallèle.
Les styles sont isolés des règles globales du Studio et le contenu embarqué n'ajoute
pas un deuxième landmark main imbriqué. Le renderer synthétique E.07.03 reste disponible.

Sauvegarde atomique avec ETag/If-Match, reprise par dashboard/vue d'ensemble,
révisions complètes append-only, brouillons incomplets valides, erreurs réseau et
conflits conservant la saisie. Une réponse de chargement périmée est ignorée pour
éviter l'écrasement des premières saisies (vérifié dans le parcours navigateur).
Confirmation avant abandon/recharge destructive ; aucun cache personnel durable.
Sessions, déconnexion et expiration restent celles d'AUTH-001, sans modification.

MEDIA-001 absent : UUID/alt/cadrage peuvent être conservés, **aucune propriété ou
permission média n'est inventée, aucune source image utilisateur n'est chargée**.
Les placeholders sont explicites ; pas d'upload/stockage/traitement réel.
Les projets sont des contenus privés locaux et non des preuves de projet réel
vérifié pour la publication. Aucun PUB, catalogue public ou route publique ajouté.

[Architecture et récupération](e0704/architecture.md) ·
[Utilisation et limites](e0704/usage.md) ·
[Commandes Windows sûres](e0704/windows.md) ·
[Inventaire des fichiers](e0704/files.txt) ·
[Contrat API](../../contracts/api/ready-instances.v1.json).

## Persistance et sécurité

Migration additive `templates.0003` : ReadyPortfolioDesign v3 séparé et
ReadyDesignRevision. Ownership exclusivement via Portfolio.account ; aucun champ
propriétaire dupliqué. Source digest et composition comparés au bundle immuable.
Portfolio.version demeure canonique, même pour les mutations de métadonnées.
Révisions design versionnées (éventuels sauts si seules les métadonnées changent),
clé unique design/version, trigger SQL anti-update/delete. Pas de backfill.

POST création idempotent24h via intention UUID, atomique avec le portfolio, le design
et sa première révision. PUT sous verrou portfolio, validation complète avant save
et révision dans la même transaction. 428 sans If-Match, 412 si périmé ; pas de
retry PUT aveugle. Une interruption annule document/version/révision ensemble.
404 hors compte/supprimé ; refus archivé et provenance incohérente. CSRF réel et
sessions existantes, payload JSON strict borné256Kio uniquement sur les nouvelles
routes ; limite AUTH16Kio inchangée. Verrous saturés : 503 temporaire.

Les données complètes de chaque sauvegarde restent récupérables dans les révisions.
L'API privée expose les50 dernières métadonnées, pas un endpoint de restauration
ou une purge. En cas de problème : conserver tables/révisions, désactiver le parcours,
fixer en avant. Le reverse SQL refuse si des instances v3 existent. Une éventuelle
application future sur données réelles nécessite sauvegarde et autorisation distinctes.
La migration reste volontairement bloquée hors du contexte isolé autorisé.

La duplication v3 via l'ancienne action est refusée explicitement pour éviter une
copie sans design. Les duplications v1/v2 et leurs contrôles sont inchangés et testés.
Les manifestes/bundles/schémas historiques ne sont pas promus ou réécrits :
Creative Editorial reste **draft** ; l'offre MVP privée est un contrat distinct.

## Validation Linux exécutée

Environnement : Python backend3.13.5, Node24.19.0/npm11.9.0, TypeScript5.9.3,
React19.3.1/Next16.4.2, PostgreSQL17.11 (image17 épinglée par digest),
Chromium154.0.8037.57 et Playwright1.62.0 (outillage Python3.12 existant séparé).
Aucune dépendance applicative ni lockfile ajouté/modifié.

| Contrôle | Résultat | Preuve dans e0704/evidence |
|---|---|---|
| Suite Django complète PostgreSQL, contrats et AUTH compris | 367 réussis, dont18 E.07.04 | django-tests.log |
| Node contrats/renderers/clients Studio | 212 réussis, dont4 E.07.04 | node-tests.log |
| Vérifications d'intégrité BASE | 12 réussis | integrity-tests.log |
| CMS historique sur données synthétiques temporaires | 6 réussis | legacy-tests.log |
| Référence historique | 11 fichiers inchangés,4 hashes de fixture | historical-reference.log |
| TypeScript strict Studio/TSX | Réussi | typecheck.log |
| Build Next production | Réussi, aucune publication | build.log |
| SQL et migrations additives, contrôle de dérive | Réussi dans cluster neuf uniquement | migrations.log, schema-check.log |
| Rôle runtime et accès maintenance de test | Moindres privilèges vérifiés | runtime-privileges.log |
| Parcours navigateur authentifié | 8 groupes de vérification réussis | browser-results.json, browser.log |
| Captures desktop/mobile Studio/portfolio + sélection | 5 PNG réels | selection-desktop,studio-*,portfolio-* |

Total : **597 tests automatiques réussis, aucun ignoré sous Linux**, auxquels
s'ajoutent les8 groupes de recette navigateur. Les18 tests E.07.04 sont inclus dans
les367, pas ajoutés une deuxième fois. Le navigateur n'est pas compté comme un
nombre artificiel de tests unitaires. Les références HTML v1 et tests Hero E.05/E.06,
les70 vecteurs de parité E.07.02, le renderer E.07.03 et les sessions AUTH sont
réexécutés dans les suites ; les résultats des tickets précédents ne sont pas
présentés comme une exécution nouvelle.

Les nouveaux tests couvrent création/réouverture, remplacement des14 slots, styles,
révisions SQL immuables, isolation/CSRF/anonymat, préconditions, provenance, limites,
archivage/suppression, idempotence, erreurs et rollback, deux véritables écritures
PostgreSQL simultanées (200/412), migration depuis v1/v2 avec snapshots, transitions
et session conservés, garde anti-base existante et réponses OpenAPI réelles.

La recette navigateur crée un compte **synthétique neuf**, choisit le template,
modifie les14 slots, valide les états invalides/médias indisponibles, provoque une
panne réseau contrôlée puis réessaie, sauvegarde, quitte et reprend via le dashboard,
ouvre deux éditeurs et vérifie le conflit sans écrasement, refuse un abandon avant
recharge explicite, capture1440/375px sans débordement, puis se déconnecte et vérifie
la fermeture de la route privée. Zéro erreur JavaScript non gérée.

## Isolation vérifiée

Le runner refuse toute configuration/DSN de base existante : nouveau conteneur
étiqueté E.07.04, stockage tmpfs, configuration/credentials aléatoires privés dans
TEMP, vérification server_version et data_directory/identité du conteneur avant
provisioning. Les préfixes e04_ servent uniquement à conserver la garde historique,
le cluster est neuf E.07.04. Rôles distincts runtime/migration/test. Les migrations
et tests n'ont jamais visé la base locale habituelle ou une ancienne base de recette.
Django/Next sur ports loopback temporaires, navigateur sans cookies existants.
Cluster et processus créés sont supprimés/arrêtés dans finally ; les services déjà
présents sont préservés. [Attestation de la dernière exécution](e0704/evidence/isolated-environment.json).

## Critères et points restant ouverts

| Critère | Statut de livraison |
|---|---|
| Sélection privée, création explicite,14 slots, styles autorisés | Réalisé, testé |
| Vrai aperçu privé, brouillons et état média honnête | Réalisé, testé |
| Sauvegarde/reprise, concurrence, permissions et révisions | Réalisé, testé |
| Migration additive et conservation v1/v2/AUTH | Réalisé dans cluster synthétique17 uniquement |
| Non-régression CMS, bundles et contrats historiques | Vérifiée |
| Captures desktop/mobile et recette complète | Produites et examinées |
| Windows natif E.07.04 | **Non exécuté** ; commandes fournies |
| Windows E.07.03 et vraie session lecteur d'écran | **Toujours ouverts**, aucune validation inventée |
| Application SQL réelle / environnement persistant de l'utilisateur | **Non autorisée et non effectuée** |
| MEDIA/PUB, upload, restauration UI, duplication v3 | Hors périmètre, indisponibles explicitement |
| Validation de livraison E.07.04 | **En attente de la revue utilisateur** |

Le symlink peut être ignoré sous Windows faute de privilège : le consigner et ne
pas le déclarer réussi. Safari/Firefox, appareil physique, scaling OS et vraie session
NVDA/VoiceOver non exécutés. Les captures montrent un parcours fonctionnel MVP ;
l'amélioration esthétique reste reportée comme demandé. Pas de certification WCAG
globale ou de Core Web Vitals de production. Une fermeture forcée/expiration sans
sauvegarde ne bénéficie pas d'une récupération locale persistante (contrat AUTH intact).
La rétention de révisions, les quotas et MEDIA/PUB nécessitent une décision future.

**Arrêt après cette livraison. Aucun ticket ultérieur, PR, fusion, publication,
déploiement ou manipulation de données existantes.**

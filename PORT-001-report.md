# PORT-001 — Rapport d’exécution

Date : 18 octobre 2026 (Africa/Douala). Branche : **`feature/port-001`**.
Commit d’implémentation : **`34d78fe`** ; le commit final documentaire est indiqué dans le message de livraison et obtenu par `git rev-parse HEAD`.

**Statut : implémentation et validation Linux livrées pour revue technique. Validation Windows native PORT-001 non exécutée. Aucun merge, déploiement public, TPL-001 ou éditeur visuel commencé.** L’approbation de P01–P10 ne vaut pas acceptation anticipée de ce code.

## 1. Références et périmètre

- Référence AUTH-001 : `2ff4fc1`, également tête de la référence Git PR nº 1 vérifiée.
- Ancienne branche PORT-001 : `669d573`, conservée sans réécriture ; son modèle propriétaire User et son slug global étaient provisoires.
- Proposition ARCH-002 : `6237710`, suivie de l’approbation explicite P01–P10 par l’utilisateur sous dix conditions. Décision consignée dans [ARCH-002](docs/architecture/ARCH-002.md).
- API et plan détaillé établis avant les modifications métier : [OpenAPI](contracts/api/portfolios.v1.json), [plan de migration](docs/architecture/PORT-001-migration-plan.md).

## 2. Implémentation

### Propriété, provisioning et autorisation

Account personnel unique par User, propriétaire canonique `Account.owner`, Membership admin active unique. Les rôles collaboratifs sont réservés et aucun endpoint de comptes collaboratifs, invitations ou transferts n’existe.

Portfolio appartient désormais à Account. La liste, le détail et toutes les mutations appliquent le même périmètre personnel et les contrôles d’adhésion. Une cible étrangère, inconnue ou supprimée est introuvable. Un identifiant client ne peut assigner/changer le propriétaire ; un Membership forgé ne supplante pas le propriétaire canonique.

Inscription atomique User/Account/Membership sans connexion automatique ; rattrapage des utilisateurs existants dans la migration et service idempotent pour les identités administratives non provisionnées. Aucun signal caché, aucune modification du manager historique ou du modèle User. Une incohérence existante est refusée, pas réparée. Le schéma de session AUTH-001 et ses champs restent strictement inchangés.

### Gestion multi-portfolios et workspace

- Dashboard actif/archives, compteurs réels, pagination 12, cartes avec visuel neutre, date et actions.
- Création vierge : nom, slug généré/modifiable, description, référence de thème initial réellement validée. Option template visible et indisponible, sans faux catalogue.
- Workspace par UUID, vue d’ensemble et paramètres actifs ; Projets/Pages/Apparence/Publication explicitement indisponibles.
- Modification conditionnelle, duplication avec nouvel UUID/slug, archivage/restauration, suppression logique confirmée côté UI **et API**.
- Conflits de version avec ETag/If-Match, refus 428/412 ; slug réservé par compte y compris supprimés, collision 409 ; unicité réelle PostgreSQL.
- Gestion, publication, visibilité et suppression séparées. Le champ SQL historique `status` est conservé et exposé comme `publication_state`. SQL impose toujours draft/private ; aucun endpoint ni URL publique de portfolio.
- Clair/sombre cohérent, préférence UI seule persistée, responsive, reduced-motion, labels/erreurs de champ, dialogue natif avec focus initial, confinement Tab/Maj+Tab et Escape.

### Thèmes et templates préparés

`studio-neutral@1.0.0` est un descripteur JSON concret, validé par schéma avant création. Ses tokens neutres correspondent au studio ; aucun moteur de changement de thème n’est prétendu. Références template facultatives appariées/versionnées, rejetées en entrée dans le MVP vierge ; schéma futur avec catégories, disponibilité, miniature optionnelle, thèmes compatibles et références de documents séparant contenu, présentation et expérience. Aucun template n’est instancié, aucun projet/page/média/animation créé.

## 3. Migrations et conservation

| Étape nouvelle | Rôle |
|---|---|
| accounts.0001 | Schéma Account/Membership, FK protégées, unicités et domaines |
| accounts.0002 | Provisioning des identités existantes ; incohérence bloquante |
| portfolios.0002 | Expansion : compte nullable, gestion, version, références |
| portfolios.0003 | Contrôle complet des sources, rattachement des supprimés inclus, contraintes puis compte obligatoire et fin de l’unicité globale |
| portfolios.0004 | Contraction : retrait de l’ancienne FK owner seulement après rattachement |

Migrations identity historiques et portfolios.0001 inchangées. UUID, contenus, états SQL, dates, type historique, deleted_at et sessions préservés. Les vérifications de Membership/propriété/slug précèdent le rattachement ; aucune correction silencieuse. Les contraintes différables sont vérifiées avant les opérations DDL suivant le backfill. La contraction ne promet pas un retour automatique à l’unicité globale ; une restauration de sauvegarde cohérente doit être planifiée pour une base à conserver.

**Aucune migration sur une base contenant des données réelles n’a été exécutée.** Les tests utilisent la base de test PostgreSQL ; les parcours navigateur ont une autre base, des rôles, une configuration et une boîte temporaires dédiés. Le générateur de validation fournit également une base native séparée pour le PC Windows, sans copier les utilisateurs de développement. Après les parcours, la base navigateur temporaire, ses rôles, sa configuration et ses e-mails reset ont été supprimés ; la base de validation séparée et vide reste disponible dans le cloud. Les instructions de démarrage réutilisables ont été enregistrées dans le brouillon de configuration d’environnement, sans publication de site.

## 4. Résultats réellement exécutés

Linux, Python 3.13.5, Node 24.19.0/npm 11.9.0, PostgreSQL **17.11 réel** via image CORE épinglée. Dépendances verrouillées réutilisées ; aucune dépendance ajoutée.

| Vérification | Résultat |
|---|---|
| Django AUTH/CORE/PORT | **57/57** |
| Dont migrations historiques avec données | **5/5**, départ AUTH seul et PORT provisoire ; hash/session/UUID/dates/supprimés conservés ; incohérences bloquées |
| Dont concurrence réelle entre connexions | **4/4**, provisioning idempotent, collision SQL, collision API 201/409 et écritures 200/412 |
| Intégrité BASE | **12/12** |
| CMS historique | **6/6** |
| Contrats santé frontend | **3/3** |
| Client auth | **4/4** |
| Client portfolios | **6/6** |
| Total suites | **88 tests réussis** |
| TypeScript et build Next.js | Réussis, nouvelles routes privées générées |
| Modèles/migrations | `makemigrations --check --dry-run` : aucun écart |
| OpenAPI et schémas | YAML et références externes résolus ; schémas thème/template et descripteur réel validés |
| PostgreSQL et rôles | UTF8, maintenance du rôle de test, runtime sans DDL/CREATEDB/superuser/BYPASSRLS vérifiés |
| Référence historique | 11 sources et 4 empreintes conformes ; JS historiques acceptés |
| Parcours PORT navigateur | 1365 px et 390 px, réussite complète |
| Régression AUTH navigateur | 1280 px et 390 px, réussite complète |
| Windows natif PORT-001 | **Non exécuté** ; guide et scripts fournis, aucun succès hérité d’AUTH revendiqué |

Le test d’atomicité d’inscription a aussi été renforcé avec une erreur injectée après insertion d’Account, lors de la création de Membership : aucun User/Account/Membership partiel ne reste. Ce même cas de la suite Django a été réexécuté isolément avec succès (1/1) après renforcement ; il n’est pas ajouté une seconde fois au total de 88.

Les parcours PORT couvrent : état vide, création vierge, template indisponible, édition, erreur de slug, conflit de version avec rechargement explicite, duplication, archives/restauration, confirmation de suppression au clavier et Escape, pagination, erreur réseau/réessai, isolation avec deuxième compte, sombre conservé, reduced-motion et absence de débordement horizontal.

Les parcours AUTH couvrent : inscription, connexion, logout, reset via boîte privée, refus de réutilisation, cookies, absence de jetons localStorage, inter-onglets, absence de token dans les URL HTTP, réponse d’identité tardive et logout sans BroadcastChannel. Seul le sélecteur d’affichage du prénom dans le script a été adapté au nouveau dashboard ; les contrôles de sécurité sont conservés.

[Résumé machine](docs/portfolios/evidence/validation-summary.json), [résultats navigateur](docs/portfolios/evidence/browser-results.json), [journal PORT](docs/portfolios/evidence/portfolio-browser.txt), [journal AUTH](docs/portfolios/evidence/auth-browser.txt).

Captures synthétiques : [dashboard clair desktop](docs/portfolios/evidence/dashboard-light-1365.png), [dashboard sombre desktop](docs/portfolios/evidence/dashboard-dark-1365.png), [dashboard mobile](docs/portfolios/evidence/dashboard-dark-390.png), [workspace mobile](docs/portfolios/evidence/workspace-dark-390.png), plus états vides et autres formats dans le même dossier. Les captures ont été inspectées ; elles ne présentent ni compte réel, ni cookie, ni mot de passe ou lien reset.

### Corrections apportées pendant la vérification

- L’outil de test de migrations tentait de reconstruire un état pour la cible de désinstallation `(app, None)` ; corrigé pour lire l’état identity restant et restaurer le schéma entre scénarios. Les tests initiaux en erreur ont ensuite été réexécutés avec succès ; ils ne sont pas masqués ou ignorés.
- Confinement du focus ajouté après constat navigateur de sortie du dialogue avec Maj+Tab.
- Chargement de pagination synchronisé pour éviter une nouvelle étiquette de page avec les anciennes cartes ; assertions navigateur attendent le nombre effectif de cartes.
- Normalisation des slugs automatiques avec underscores corrigée avant le dernier passage backend : un nom valide ne doit pas produire une erreur SQL. Cas `My__Name` ajouté.
- Flèches remplacées par SVG inline pour éviter des glyphes manquants dans les captures, sans dépendance d’icônes.

## 5. Critères de livraison et conditions utilisateur

| Critère | État |
|---|---|
| Plusieurs portfolios indépendants avec UUID stable et Account | Vérifié Linux |
| Dashboard limité au propriétaire ; accès inter-utilisateurs refusés | API et navigateur vérifiés |
| Création vierge et template indisponible | Vérifiés navigateur |
| Références thème/template versionnées et validables | Schémas, descripteur et contraintes vérifiés |
| Modifier/dupliquer/archiver/restaurer/supprimer logiquement | API et navigateur vérifiés |
| Slugs par compte, réservation des supprimés, concurrence | PostgreSQL/API vérifiés |
| Préconditions de version et absence d’écrasement | Deux connexions et parcours navigateur vérifiés |
| Aucune publication automatique | Contraintes SQL/API et assertions vérifiées |
| Desktop/mobile, clavier/dialogue et sombre | Chromium Linux vérifiés ; aucun audit lecteur d’écran revendiqué |
| Non-régression AUTH/CORE/BASE | Suites, contrat session et parcours AUTH vérifiés |
| Sources historiques, `.local/`, migrations historiques | Intacts, aucune lecture de données historiques |
| Absence de secret/fichier privé publié | Exclusions et scan des valeurs générées avant commit ; preuves synthétiques uniquement |
| Réserves Windows explicites | Scripts/guide fournis ; exécution native à effectuer |
| Approbation du code et migrations | **À réaliser par la revue technique de l’utilisateur** |

Les dix conditions d’approbation architecturale sont appliquées : évolution contrôlée de l’historique, conservation testée, refus d’incohérence, thème concret et contrats TPL futurs, session inchangée, deux points d’entrée de migration réels testés sur PostgreSQL 17 synthétique, absence de migration réelle, historique intact et aucune fusion.

## 6. Démarrage et vérification Windows

Suivre [le guide PowerShell natif](docs/runbooks/port001-windows-development.md). Il commence par préparer la configuration privée **`port001.validation.local.json`** et une base distincte. Ne pas appliquer les nouvelles migrations à la configuration de développement réelle sans sauvegarde et autorisation.

Après préparation de cette base séparée, terminal Django :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
$env:SAAS_CONFIG_FILE = Join-Path (Get-Location) 'infra\env\port001.validation.local.json'
& .\scripts\windows\Start-Backend.ps1
```

Autre terminal, studio :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
$env:NEXT_TELEMETRY_DISABLED = '1'
npm.cmd run dev --workspace @portfolio/studio
```

La suite `Test-Foundations.ps1` doit être lancée avec SAAS_CONFIG_FILE de validation et Next arrêté. Elle inclut désormais les tests du client portfolios. Les deux nouveaux scripts PowerShell n’ont pas été exécutés sur Windows ici ; leur fonctionnement natif reste à confirmer.

## 7. Réserves et décisions différées

- Livré pour revue, pas approuvé ni fusionné. PORT-001 Windows doit être exécuté sur le PC ; les preuves AUTH anciennes ne suffisent pas.
- Pas de catalogue TPL opérationnel, éditeur, moteur de thèmes, collaboration, import du CMS, média, publication ou 3D.
- API provisoire avec slash final remplacée par les chemins canoniques documentés ; pas de promesse de rétrocompatibilité d’un contrat provisoire non validé.
- Pas de restauration des portfolios supprimés, purge automatique ou transfert de compte. Slugs supprimés restent réservés ; politique de rétention/récupération à définir.
- La duplication n’est pas une API d’import ni une copie de futures ressources. Une demande répétée indépendante peut créer une autre copie ; pas de clé d’idempotence promise.
- Provisioning et invariants de Membership sont transactionnels ; l’accès normal ne répare pas les incohérences. Pas de garantie SQL inter-table fictive ni de triggers supposés existants.
- Le contexte natif Windows reste ouvert. La production HTTPS, SMTP externe, politique de proxy de confiance et ouverture publique restent hors livraison.
- Avertissement Node de détection de module lors des tests TS : non bloquant ; aucune mise à niveau de dépendance imposée pour le masquer.

## 8. Fichiers et revue Git

Liste exhaustive relative à AUTH-001 `2ff4fc1` : [files.txt](docs/portfolios/files.txt). Elle inclut les documents de proposition/préparation conservés dans la branche et les preuves, pas les configurations privées, bases, dépendances ou builds.

La branche distante est publiée sans réécriture et sans fusion de PR. La tentative réelle de création de PR brouillon via `gh pr create`, base `feature/auth-001`, a échoué : `Post https://api.github.com/graphql: Forbidden`. La branche est publiée, mais aucune nouvelle PR automatique n’a été créée ni approuvée. Aucun numéro ou statut GitHub n’est inventé. Comparaison de revue : https://github.com/Mariekaf/testPorfolio/compare/feature/auth-001...feature/port-001

**Attendre la revue technique et la validation utilisateur avant fusion ou ticket suivant.**

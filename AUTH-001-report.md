# AUTH-001 — Rapport d’implémentation

Date : 16 octobre 2026. Branche : `feature/auth-001`, créée depuis `7331e5b` (`fix/core-001-windows`, socle validé avec corrections Windows). Aucun merge dans `main`.

**Statut : AUTH-001 clôturé techniquement le 16 octobre 2026 sur instruction utilisateur, après revue et confirmation des contrôles Windows. PR non fusionnée.**

Décision finale et preuves par version : [revue technique](docs/reviews/AUTH-001-technical-review.md). Les sections datées ci-dessous conservent l’historique des blocages et de leur résolution ; elles ne constituent pas le statut courant.

## Réalisation

- Inscription sans connexion automatique ; e-mail normalisé et unique jusque dans PostgreSQL ; mot de passe haché/validé par Django ; UUID utilisateur préservé.
- Sessions Django, rotation à la connexion, révocation à la déconnexion et révocation de toutes les sessions suivies après réinitialisation. Durée absolue configurable.
- CSRF sur toutes les mutations anonymes/authentifiées ; cookies distincts du CMS, HttpOnly, SameSite Strict et Secure en HTTPS.
- Limites partagées PostgreSQL par IP/e-mail, clés HMAC ; commande de purge sans journal de données personnelles.
- Reset temporaire à usage unique, réponse générique, liens dans un fragment URL effacé côté navigateur, boîte mail privée par défaut et SMTP configurable par variables d’environnement.
- Formulaires accessibles, afficher/masquer le mot de passe, erreurs par champ, chargement, tableau de bord vide protégé côté serveur et API. Revalidation au focus/retour de page, expiration et notification entre onglets.
- Aucun module portfolio, publication, éditeur ou migration des données réelles ajouté. Aucune nouvelle dépendance ; fichiers de verrouillage conservés.

Migration `identity.0002` atomique : contrôle préalable des identités SaaS éventuelles, normalisation si compatible, remplacement du champ technique username par l’e-mail, ajout des contraintes et tables de suivi/limitation. Elle ne lit pas le CMS historique. Des identités ambiguës bloquent sans correction automatique. Une restauration de sauvegarde SaaS est nécessaire pour revenir à l’ancien schéma si nécessaire ; aucune migration inverse aveugle n’est recommandée.

Les tests du socle ont été adaptés uniquement pour créer un utilisateur synthétique par e-mail et retirer l’ancienne assertion « route login absente ». Les tests historiques restent intacts.

## Résultats réellement exécutés sous Linux

Environnement : Python 3.13.5, Node 24.19.0, npm 11.9.0, PostgreSQL **17.11 réellement connecté**. Dépendances verrouillées CORE-001 réutilisées. Chromium installé dans l’environnement, Playwright utilisé uniquement comme outil de vérification existant.

| Vérification | Résultat |
|---|---|
| `check_base001.py` | 11 sources historiques et 4 empreintes de fixture vérifiées |
| Tests d’intégrité BASE | 12/12 réussis |
| Tests historiques `tests/` | 6/6 réussis, dont scénarios d’encodage Windows simulés sous Linux |
| Django `manage.py test tests --settings=config.settings.test --noinput` depuis `backend/` | 33/33 réussis, base de test PostgreSQL créée puis supprimée |
| Contrats santé frontend | 3/3 réussis |
| Client API auth `npm run test:auth` | 4/4 réussis |
| TypeScript | réussi |
| Build Next.js | réussi ; dashboard dynamique, écrans auth générés |
| Migrations | migration complète depuis zéro sur base jetable réussie ; aucun écart de modèles non migré |
| Vérification PostgreSQL/rôles | UTF8, table utilisateur, maintenance du rôle de test et absence de privilèges DDL/superuser du runtime vérifiées |
| Chromium desktop 1280 px et mobile 390 px | parcours inscription/connexion/déconnexion/reset/rejet réutilisation, déconnexion entre onglets et absence de jeton dans les URL HTTP réussis |
| `git diff --check` | réussi |

Total des suites unitaires/contrats : **58 tests réussis**, plus les parcours navigateur. Aucun résultat Windows réel n’est déduit de ces tests.

Les parcours navigateur utilisent une base PostgreSQL, des rôles et une boîte privés jetables distincts de la configuration de développement. Aucun compte réel ou contenu historique n’est utilisé. Les fichiers d’e-mail et de configuration restent hors Git. Tests backend supplémentaires : origine CSRF non autorisée, absence de fuite de mot de passe/privilèges, profil lié à la session, fixation de session, cookie HTTPS, erreurs SMTP expurgées, permissions Linux de la boîte, garde de migration et purge des compteurs.

Un premier passage navigateur a révélé une double redirection de déconnexion causée par le BroadcastChannel reçu dans l’onglet émetteur. Correction : ignorer le signal local pendant la déconnexion volontaire ; parcours relancé avec succès. Le lecteur du mail dans l’outil de test a aussi été corrigé pour décoder le message MIME depuis ses octets UTF-8.

## Statut des critères

| Critère | Statut et preuve |
|---|---|
| AC01 inscription | Validé Linux : backend + navigateur |
| AC02 doublons | Validé Linux : API normalisation + contrainte PostgreSQL contournant le manager |
| AC03 mot de passe invalide | Validé Linux : validation et messages de champ |
| AC04 connexion | Validé Linux : backend + navigateur |
| AC05 erreurs génériques | Validé Linux : comptes absent/inactif/mauvais mot de passe |
| AC06 accès dashboard | Validé Linux : session, protection serveur et navigateur |
| AC07 ressources privées | Validé Linux : API 401 et redirection dashboard anonyme ; profil lié à la session |
| AC08 déconnexion | Validé Linux : suppression de session et navigateur |
| AC09 reset | Validé Linux : boîte privée et parcours réel navigateur ; SMTP externe non utilisé |
| AC10 liens invalides/expirés/réutilisés | Validé Linux : backend pour les trois cas, navigateur pour la réutilisation |
| AC11 limitation | Validé Linux : deux clients partagent les compteurs PostgreSQL, 429 + Retry-After |
| AC12 CSRF/cookies | Validé Linux : mutations anonymes, origine refusée, cookies et option Secure HTTPS |
| AC13 responsive | Validé Chromium Linux desktop/mobile ; revue humaine et lecteur d’écran non exécutés |
| AC14 Windows natif | **Validé sur preuves utilisateur** : 58 tests, TypeScript/build et PostgreSQL 17.6 sur `ffc015b` ; contrôle Test-Mailbox et parcours principaux confirmés sur `466d87c`. Correctifs frontend finaux testés Linux, non réexécutés sur Windows ; voir la revue pour la portée exacte |
| AC15 historique | Validé Linux : empreintes inchangées et 6 tests historiques réussis ; `.local/` non consulté/modifié |
| AC16 secrets | Validé sur les chemins testés : réponses limitées, liens absents des URL HTTP, pas de journal SMTP sensible, boîte privée, configuration ignorée et contrôle des fichiers livrés |

## Reproduction et limites

API : [docs/api/auth-v1.md](docs/api/auth-v1.md). Installation et commandes PowerShell exactes : [docs/runbooks/auth001-windows-development.md](docs/runbooks/auth001-windows-development.md). Ce guide complète CORE-001 sans Docker et conserve la configuration native existante.

Dans deux terminaux Windows à la racine du clone :

```powershell
& .\scripts\windows\Start-Backend.ps1
```

```powershell
$env:NEXT_TELEMETRY_DISABLED = '1'
npm.cmd run dev --workspace @portfolio/studio
```

Dans un troisième : `& .\scripts\windows\Test-Foundations.ps1`. Suivre auparavant la migration et l’initialisation de boîte décrites dans le guide. Ne jamais partager les fichiers mail, cookies ou configuration locale.

Le navigateur automatisé est optionnel et requiert un Playwright/Chromium déjà installé, sans dépendance ajoutée au projet. Il écrit des comptes synthétiques : exclusivement sur une base et boîte jetables. Le script refuse les origines non locales. Les conditions de création de cette instance de test doivent être explicites avant son exécution.

Le profil production reste fermé. La politique de proxy de confiance, les limites réseau et la vérification d’e-mail avant ouverture publique restent des travaux de déploiement ultérieurs. La limite IP est agrégée derrière le proxy local Next ; la limite e-mail reste indépendante. Aucun déploiement public, test SMTP externe ou validation Windows n’est revendiqué. Node émet un avertissement non bloquant de détection de module lors des tests TypeScript natifs ; les quatre tests passent sans configuration expérimentale.

## Livraison Git et PR

Branche dédiée `feature/auth-001`. La [PR nº 1](https://github.com/Mariekaf/testPorfolio/pull/1) a été créée par l’utilisateur et est en brouillon, selon sa confirmation du 16 octobre 2026. La création de PR n’est plus un blocage. La revue et la validation Windows native restent ouvertes.

Vérification indépendante : `git ls-remote origin refs/heads/feature/auth-001 refs/pull/1/head` a confirmé les deux références au commit `bbbd4dd` au début de cette vérification. L’accès GraphQL pour consulter les métadonnées reste refusé (`Forbidden`) ; le statut brouillon provient de la confirmation utilisateur, pas d’une lecture API. Aucun merge ni modification de la PR via l’API n’est effectué.

Ne pas commencer le ticket suivant ni fusionner avant revue et validation Windows.

### Préparation des vérifications encore ouvertes

Le 16 octobre 2026, relecture ciblée des sessions/CSRF, de la révocation des sessions lors du reset, de la migration, des ACL PowerShell et de la protection du dashboard. Cette relecture ne remplace pas l’approbation de la PR. Réexécution Linux : 33 tests Django et 4 tests du client auth réussis ; les 11 empreintes historiques et les 4 empreintes de fixture sont conformes. Les autres résultats du tableau précédent restent ceux de la livraison initiale.

Correction documentaire : arrêter Next.js avant `Test-Foundations.ps1`, qui exécute un build dans le même `.next`, puis relancer le studio pour les parcours manuels. Aucun changement fonctionnel ni modification du CMS historique pour cette préparation.

Vérifications à recueillir sur le PC Windows : branche/commit testés, versions Python/Node/npm/PostgreSQL, migration SaaS, ACL effectives de la boîte, résultat complet de `Test-Foundations.ps1`, parcours auth, expiration, onglets et retour arrière. Cette liste correspond aux éléments attendus avant réception du transcript Windows décrit ci-dessous. PORT-001 reste suspendu ; PR nº 1 conservée en brouillon selon la consigne utilisateur.


## Fichiers créés et modifiés

La liste exhaustive ci-dessous exclut les dépendances installées, builds, configurations privées et messages de test.

Fichiers modifiés :

- `apps/studio/next.config.mjs`
- `apps/studio/src/app/layout.tsx`
- `apps/studio/src/app/page.tsx`
- `apps/studio/src/app/style.css`
- `backend/config/settings/base.py`
- `backend/config/settings/development.py`
- `backend/config/urls.py`
- `backend/modules/identity/models.py`
- `backend/tests/test_foundations.py`
- `package.json`
- `scripts/windows/Start-Backend.ps1`
- `scripts/windows/Test-Foundations.ps1`

Fichiers créés :

- `AUTH-001-report.md`
- `apps/studio/src/app/auth-form.tsx`
- `apps/studio/src/app/dashboard/dashboard.tsx`
- `apps/studio/src/app/dashboard/page.tsx`
- `apps/studio/src/app/forgot-password/page.tsx`
- `apps/studio/src/app/login/page.tsx`
- `apps/studio/src/app/register/page.tsx`
- `apps/studio/src/app/reset-password/page.tsx`
- `apps/studio/src/lib/auth.ts`
- `apps/studio/test/auth.test.mjs`
- `backend/modules/identity/mailbox.py`
- `backend/modules/identity/management/__init__.py`
- `backend/modules/identity/management/commands/__init__.py`
- `backend/modules/identity/management/commands/cleanup_auth_limits.py`
- `backend/modules/identity/managers.py`
- `backend/modules/identity/migrations/0002_authenticationlimit_authsession_alter_user_options_and_more.py`
- `backend/modules/identity/rate_limits.py`
- `backend/modules/identity/serializers.py`
- `backend/modules/identity/views.py`
- `backend/tests/test_authentication.py`
- `contracts/schemas/auth/session.v1.json`
- `docs/api/auth-v1.md`
- `docs/runbooks/auth001-windows-development.md`
- `infra/mailbox/.gitignore`
- `scripts/verification/browser_auth001.py`
- `scripts/windows/Initialize-Mailbox.ps1`

## Preuves Windows natives reçues le 16 octobre 2026

Source : sortie de `Test-Foundations.ps1` exécuté par l’utilisateur sur son PC, fournie dans le chat. Il ne s’agit pas d’une exécution distante par l’agent. Aucun transcript brut, chemin personnel, message mail ou configuration privée n’est commité.

- Référence historique : 11 fichiers inchangés, 4 empreintes de fixture conformes.
- Tests : intégrité 12/12, CMS historique 6/6, Django 33/33, contrats santé 3/3, client auth 4/4, soit **58/58**.
- PostgreSQL natif **17.6** : UTF8, accès de maintenance du rôle de test, rôle runtime sans DDL/CREATEDB/superuser/BYPASSRLS vérifiés.
- Base de test créée, migration `identity.0002` appliquée avec succès puis base de test supprimée. Le transcript ne constitue pas une preuve séparée de migration de la base de développement.
- Django check, absence d’écart de migrations, TypeScript et build Next.js réussis. Message final du script réussi.
- Les avertissements PostgreSQL proviennent des scénarios de panne simulée qui passent. Avertissement Node `MODULE_TYPELESS_PACKAGE_JSON` non bloquant, sans changement de dépendance requis.
- Initialisation des ACL de la boîte signalée réussie dans le précédent retour utilisateur ; contrôle des permissions effectives sur un message Windows encore à effectuer. Le test Python de permissions POSIX ne vérifie pas les ACL Windows.

Versions préalablement fournies sur ce PC : Python 3.13.5, Node 24.22.0, npm 11.14.0, PowerShell 5.1. Le commit testé a ensuite été confirmé par l’utilisateur : `ffc015b`. `showmigrations identity` confirme également `[X]` sur `0001` et `0002` dans la base de développement.

Restent à valider : démarrage Django/studio Windows et santé de la base de développement, parcours inscription/connexion/déconnexion/reset, expiration, onglets/retour arrière, responsive/clavier et ACL effectives de la boîte. La revue/approbation de la PR nº 1 reste distincte. Aucun merge et aucun démarrage de PORT-001.

## Correctif Windows de la boîte privée — exécution encore à valider

Après réussite des 58 tests sur `ffc015b`, le démarrage Django a été interrompu par `Set-Acl` dans `Initialize-Mailbox.ps1` : privilège `SeSecurityPrivilege` manquant. La première initialisation avait réussi ; le second passage devait donc être couvert explicitement. Ce blocage ne modifie pas les résultats de tests antérieurs mais empêche de déclarer le démarrage et les parcours Windows validés.

Correction : remplacement des deux appels `Set-Acl` de la boîte par les setters .NET Framework `DirectoryInfo.SetAccessControl` et `FileInfo.SetAccessControl`. Seules les règles DACL modifiées sont enregistrées ; propriétaire/groupe/audit restent inchangés. Les deux identités autorisées restent l’utilisateur courant et SYSTEM, sans élévation.

Nouveau contrôle `scripts/windows/Test-Mailbox.ps1`, intégré à `Test-Foundations.ps1` : première initialisation, héritage vers un fichier synthétique, initialisation répétée, protection des DACL et présence exclusive des deux règles FullControl attendues, contenu conservé, nettoyage et restauration de la variable d’environnement. Ce contrôle n’ouvre aucun vrai message.

Vérifications Linux de cette correction : intégrité de référence et `git diff --check`. Aucun PowerShell Windows n’est disponible dans cet environnement ; **le contrôle ACL et la relance Django ne sont pas encore déclarés réussis**. Le nouveau passage complet de la suite Windows reste attendu. PORT-001 reste bloqué, aucune fusion ni modification du CMS historique.

Fichiers concernés par ce correctif : `scripts/windows/Initialize-Mailbox.ps1`, `scripts/windows/Test-Mailbox.ps1` (créé), `scripts/windows/Test-Foundations.ps1`, ce rapport et le guide Windows AUTH-001.

## Clôture après revue technique

L’utilisateur a demandé la revue de la PR puis la clôture d’AUTH-001, et confirmé par « oui » la réussite sur le correctif Windows 466d87c de Test-Mailbox, du démarrage Django et des parcours inscription/connexion/déconnexion/reset/expiration. Cette déclaration lève le blocage Windows précédemment ouvert ; elle est distinguée du transcript automatisé antérieur.

Revue effectuée et deux défauts frontend corrigés : réponse d’identité tardive pendant la déconnexion et absence de BroadcastChannel empêchant la redirection. Scénarios de régression avec délais simulés vérifiés dans Chromium desktop/mobile. Suite de 58 tests Linux, TypeScript/build, migration complète et rôles PostgreSQL vérifiés lors de la revue. Les derniers ajustements frontend n’ont pas été réexécutés sur le PC Windows ; aucune validation de cette version exacte sous Windows n’est prétendue.

**AUTH-001 clôturé dans le suivi documentaire.** La PR nº 1 reste sans fusion ; aucune approbation formelle ou clôture GitHub n’a été envoyée, l’API étant inaccessible. Aucun démarrage de PORT-001, aucun déploiement et aucun changement des sources historiques.

Livrables complémentaires de clôture : `docs/reviews/AUTH-001-technical-review.md` (créé), `apps/studio/src/app/dashboard/dashboard.tsx` et `scripts/verification/browser_auth001.py` (corrigés), ce rapport et le guide Windows (statuts actualisés).

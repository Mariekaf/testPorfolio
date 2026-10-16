# AUTH-001 — Rapport d’implémentation

Date : 16 octobre 2026. Branche : `feature/auth-001`, créée depuis `7331e5b` (`fix/core-001-windows`, socle validé avec corrections Windows). Aucun merge dans `main`.

**Statut : implémentation et vérifications Linux réalisées ; ticket non terminé tant que la validation Windows native AC14 et la PR ne sont pas acquises.**

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
| Chromium desktop 1280 px et mobile 390 px | parcours inscription/connexion/déconnexion/reset/rejet réutilisation réussis |
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
| AC14 Windows natif | **OUVERT** : PowerShell 5.1, PostgreSQL natif, ACL et parcours PC à exécuter |
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

Branche dédiée `feature/auth-001`, base de revue recommandée `fix/core-001-windows` pour isoler AUTH-001 du socle non encore fusionné dans main. L’accès Git est vérifié séparément de l’API GitHub. L’API GitHub renvoie actuellement `Forbidden` pour ce dépôt : la PR automatique est bloquée, aucun numéro de PR n’est annoncé. Aucun secret/token n’est demandé dans le chat.

Le lien de comparaison après publication de la branche permet de créer la PR :
https://github.com/Mariekaf/testPorfolio/compare/fix/core-001-windows...feature/auth-001

Ne pas commencer le ticket suivant ni fusionner avant revue et validation Windows.

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

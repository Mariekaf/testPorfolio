# PORT-001 — Vérification Windows native isolée (sans Docker)

Statut : **guide préparé, exécution Windows PORT-001 non effectuée par l’agent**. Ne pas réutiliser les succès Windows AUTH-001 comme preuve des nouvelles migrations. La livraison `27a0b85` est acceptée et PORT-001 clôturé depuis le 19 octobre 2026 ; Windows reste une réserve non bloquante [suivie séparément](../portfolios/windows-follow-up.md).

## Préconditions et données réelles

PowerShell 5.1, Python 3.13 x64, Node 24/npm 11 et PostgreSQL 17 natif sur le port déjà configuré. Utiliser le clone SaaS, préserver `.local/` et les fichiers historiques. Arrêter les terminaux Django et Next avec Ctrl+C avant de changer de branche.

**Ne pas lancer migrate avec la configuration de développement réelle par défaut.** Les commandes suivantes génèrent une configuration privée distincte, une nouvelle base et des rôles séparés pour des essais synthétiques. Aucune donnée AUTH ou CMS réelle n’est copiée. Vos comptes de développement habituels ne seront donc pas présents dans cette base de validation.

Si une migration de la base réelle est souhaitée ultérieurement : plan de sauvegarde PostgreSQL, vérification de restauration sur une base séparée et autorisation explicite préalable. Aucun pg_dump ou export privé ne doit être commité ou envoyé dans le chat. Aucun script de cette livraison ne purge votre base réelle.

## 1. Branche et dépendances

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
git status --short
git fetch origin
git switch feature/port-001
# Si la branche n’existe pas localement : git switch --track origin/feature/port-001
git pull --ff-only origin feature/port-001
git log -1 --format="%h %s"
py -3.13 --version
node --version
npm.cmd --version
& .\backend\.venv\Scripts\python.exe -m pip install --require-hashes -r .\backend\requirements\development.txt
& .\backend\.venv\Scripts\python.exe -m pip check
npm.cmd ci --ignore-scripts
```

S’arrêter si le dépôt contient des changements à préserver ou si une commande échoue. Aucune dépendance métier nouvelle n’est introduite.

## 2. Base native synthétique séparée

Dans un nouveau terminal qui utilise encore la configuration SaaS native habituelle (pas une ancienne variable SAAS_CONFIG_FILE de test) :

```powershell
& .\scripts\windows\Initialize-PortfolioValidation.ps1
git check-ignore infra/env/port001.validation.local.json
$env:SAAS_CONFIG_FILE = Join-Path (Get-Location) 'infra\env\port001.validation.local.json'
& .\backend\.venv\Scripts\python.exe -B scripts/development/provision_database.py --admin-user postgres
& .\backend\.venv\Scripts\python.exe -B backend/manage.py migrate --plan --settings=config.settings.migration
& .\backend\.venv\Scripts\python.exe -B backend/manage.py migrate --settings=config.settings.migration --noinput
& .\backend\.venv\Scripts\python.exe -B scripts/verification/verify_core_database.py --check-test-access
```

Le mot de passe administrateur PostgreSQL est demandé masqué et n’est pas enregistré. Le générateur crée seulement `infra/env/port001.validation.local.json`, ignoré Git et protégé par ACL utilisateur/SYSTEM. Réexécution : conserver la même configuration, ne pas régénérer des identifiants ni changer les mots de passe de rôles existants.

Les migrations de comptes et portfolios créent/provisionnent les données de **cette base séparée**. La migration historique Portfolio reste conservée et les nouvelles étapes expansion/rattachement/contraintes/contraction lui succèdent. Une incohérence doit provoquer un arrêt, jamais une réparation silencieuse. Aucun catalogue/template/publication n’est activé.

## 3. Suite automatisée

Garder Next.js arrêté pendant le build de la suite. Dans le même terminal avec SAAS_CONFIG_FILE défini :

```powershell
& .\scripts\windows\Test-Foundations.ps1
```

Résultats attendus dans cette livraison : 12 tests d’intégrité, 6 historiques, 57 Django, 3 contrats santé, 4 client auth et 6 client portfolios, soit **88 tests**, puis TypeScript/build. Le contrôle ACL PowerShell `Test-Mailbox.ps1` est distinct de ce total. Les tests de migration et de concurrence sont dans les 57 Django ; leur base `test_…` est séparée de la base de validation elle-même.

Les tests de migration restaurent leur schéma après chaque scénario et ne s’exécutent que si le nom de base commence par `test_`. Scénarios : départ AUTH seul, départ PORT provisoire avec données synthétiques et supprimés, incohérence Membership, slug incompatible et mauvais rattachement bloqués. Les avertissements de panne de santé simulée sont attendus uniquement dans les tests correspondants.

## 4. Deux terminaux de services

Terminal Django — **réappliquer la configuration de validation dans ce terminal** :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
$env:SAAS_CONFIG_FILE = Join-Path (Get-Location) 'infra\env\port001.validation.local.json'
& .\scripts\windows\Start-Backend.ps1
```

Terminal studio :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
$env:NEXT_TELEMETRY_DISABLED = '1'
npm.cmd run dev --workspace @portfolio/studio
```

Sur votre PC, ouvrir `http://127.0.0.1:3000/register`. Toujours utiliser 127.0.0.1 pour les cookies ; Django reste sur 8001. Les comptes de cette nouvelle base sont indépendants de la base AUTH habituelle.

## 5. Parcours de vérification

1. Créer un utilisateur synthétique `@example.test`, vérifier l’absence de connexion automatique puis se connecter. Dashboard vide et compteur actif 0.
2. « Créer un portfolio » : option vierge fonctionnelle, option template visiblement indisponible, aucune fausse bibliothèque. Saisir nom/description, vérifier le slug généré, créer et vérifier la redirection workspace.
3. Modifier nom/slug/description ; confirmer que l’UUID du workspace reste identique et les erreurs sont proches du champ. Un slug déjà utilisé dans le même compte doit être refusé.
4. Créer plusieurs portfolios. Vérifier les compteurs et, au-delà de 12, la pagination et le filtre d’archives.
5. Dupliquer : nouvelle instance et slug distinct, brouillon/privé, thème Studio Neutral version 1.0.0. Aucune page ni ressource publique.
6. Archiver : disparition des actifs, présence dans Archives, détail consultable mais pas de modification/duplication. Restaurer : actif à nouveau, toujours brouillon/privé.
7. Supprimer : dialogue, focus sur Annuler, Tab/Maj+Tab confinés, Escape annule ; confirmer ensuite et vérifier la disparition des listes et le refus du détail. Aucune interface de récupération n’est prétendue.
8. Deux onglets de paramètres sur la même instance : enregistrer dans l’un puis dans l’autre. Le second doit afficher un conflit et demander un rechargement explicite, sans écraser les changements.
9. Deuxième compte synthétique dans une fenêtre privée : aucun portfolio du premier visible. Accès direct au premier UUID : introuvable ; créer un même slug dans son propre compte est autorisé.
10. Vérifier desktop, mobile 390 px, clavier, clair/sombre (préférence conservée), absence de débordement horizontal et mode reduced-motion. Projets/Pages/Apparence/Publication doivent rester indisponibles.
11. Refaire les parcours AUTH-001, dont reset dans la boîte privée, expiration et déconnexion inter-onglets. Ne transmettre ni mots de passe, ni cookies, ni messages mail, ni liens reset.

## Résultats à transmettre

Branche/commit, versions, résumé final des tests, étapes réussies/échouées et messages techniques expurgés uniquement. Les captures Linux de référence sont dans `docs/portfolios/evidence/`. Aucun succès Windows de PORT-001 n’est acquis sans ces exécutions réelles.

Arrêter les services à la fin. Retirer la variable dans les terminaux concernés avec `Remove-Item Env:SAAS_CONFIG_FILE` seulement quand ils sont arrêtés. Revenir à la configuration de développement réelle **ne doit pas déclencher de migration**. La suppression des bases/rôles de validation et la politique de rétention restent des actions explicites ; aucune purge automatique n’est fournie.

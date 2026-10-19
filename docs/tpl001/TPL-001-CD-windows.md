# TPL-001.C+D — Validation Windows native, sans Docker

**Guide préparé ; Windows C+D NON EXÉCUTÉ par l’agent.** PostgreSQL 17 natif, Python 3.13 x64, Node 24/npm 11, PowerShell 5.1. Le correctif d’encodage `99b2269` est inclus. Conserver le résultat symlink ignoré comme limitation de l’environnement si cette capacité reste indisponible ; ne pas le compter parmi les réussites.

Aucune commande ci-dessous ne doit viser une base réelle. La préparation crée une nouvelle configuration privée, un nouveau nom de base et trois nouveaux rôles. Aucune donnée, compte, média ou session de l’ancien CMS/SaaS n’est copié. Ne pas changer `.local/`. Arrêter Django/Next et préserver les modifications locales avant de changer de branche.

## 1. Récupérer et installer

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
git status --short
git fetch origin
git switch feature/tpl-001-cd
git log -1 --format="%h %s"
py -3.13 --version
node --version
npm.cmd --version
& .\backend\.venv\Scripts\python.exe -m pip install --require-hashes -r .\backend\requirements\development.txt
& .\backend\.venv\Scripts\python.exe -m pip check
npm.cmd ci --ignore-scripts
```

Ne pas forcer Git ni écraser un fichier local si la commande refuse. Les dépendances et lockfiles restent ceux du socle ; aucun nouveau paquet requis.

## 2. Préparer une base C+D séparée

Le premier SAAS_CONFIG_FILE ci-dessous est une **source de métadonnées de connexion uniquement** (instance native locale déjà installée). Il n’est pas utilisé pour exécuter des migrations. Le helper ne génère que le nouveau fichier privé.

```powershell
$env:SAAS_CONFIG_FILE = Join-Path (Get-Location) 'infra\env\port001.validation.local.json'
& .\scripts\windows\Initialize-TemplateValidation.ps1
if ($LASTEXITCODE -ne 0) { throw 'Préparation interrompue.' }

git check-ignore infra/env/tpl001-cd.validation.local.json
$env:SAAS_CONFIG_FILE = Join-Path (Get-Location) 'infra\env\tpl001-cd.validation.local.json'
$config = Get-Content -LiteralPath $env:SAAS_CONFIG_FILE -Raw | ConvertFrom-Json
if (-not $config.database.name.StartsWith('tpl001_cd_')) { throw 'Configuration inattendue : arrêt.' }
if ($config.database_mode -ne 'native') { throw 'Ce guide exige PostgreSQL Windows natif.' }
& .\backend\.venv\Scripts\python.exe -B scripts/development/provision_database.py --admin-user postgres
if ($LASTEXITCODE -ne 0) { throw 'Création de la base interrompue.' }
& .\backend\.venv\Scripts\python.exe -B backend/manage.py migrate --settings=config.settings.migration --noinput
if ($LASTEXITCODE -ne 0) { throw 'Migration synthétique interrompue.' }
& .\backend\.venv\Scripts\python.exe -B scripts/verification/verify_core_database.py --check-test-access
```

Le mot de passe administrateur est demandé localement, jamais enregistré ni communiqué. Ne pas afficher `$config` et ne pas publier le fichier privé. Le script Initialize-Database.ps1 historique lit une autre configuration pour certaines vérifications ; utiliser les commandes explicites ci-dessus pour C+D.

Une provenance de template existante sans design bloque la nouvelle migration, avec message explicite. Ne pas la corriger ou effacer silencieusement. La base C+D fraîche ne contient normalement aucune telle donnée. Toute migration future de données réelles nécessite sauvegarde, restauration vérifiée et autorisation distincte.

## 3. Tests automatiques

Next doit être arrêté pendant typecheck/build. Même terminal, après la préparation de la base :

```powershell
$env:SAAS_MAILBOX_PATH = Join-Path (Get-Location) 'infra\mailbox\tpl001-cd'
& .\scripts\windows\Initialize-Mailbox.ps1
& .\scripts\windows\Test-Foundations.ps1
```

La suite utilise les rôles de tests et une base temporaire de tests, pas les données réelles. Elle inclut AUTH, PORT, registre B, instances, migrations et concurrence C+D, clients et renderer. Reporter les résultats réellement exécutés, sans déduire les étapes suivantes d’un arrêt préalable. Un test symlink ignoré reste un skip.

## 4. Démarrer Django et Next

Terminal Django :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
$env:SAAS_CONFIG_FILE = Join-Path (Get-Location) 'infra\env\tpl001-cd.validation.local.json'
$env:SAAS_MAILBOX_PATH = Join-Path (Get-Location) 'infra\mailbox\tpl001-cd'
& .\scripts\windows\Start-Backend.ps1
```

Terminal Studio :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
$env:NEXT_TELEMETRY_DISABLED = '1'
npm.cmd run dev --workspace @portfolio/studio
```

Navigateur du PC : studio local port 3000. Vérification depuis un troisième terminal :

```powershell
Invoke-RestMethod 'http://127.0.0.1:8001/health/ready'
```

Créer un compte **synthétique neuf dans cette base** via l’inscription, puis se connecter. Les anciens comptes n’ont pas été copiés.

## 5. Parcours manuel à consigner pour chacun des deux templates

1. Dashboard → Créer un portfolio → Utiliser un template. Filtrer Minimal puis Editorial, consulter les aperçus desktop/mobile, puis « Utiliser ce template ».
2. Saisir nom et slug distincts, cliquer « Créer et personnaliser ». Tester le double clic : un seul portfolio doit apparaître. Le portfolio reste brouillon privé ; aucune adresse publique n’est créée. Les données initiales sont neutres, les exemples fictifs réservés aux démonstrations.
3. Introduction : modifier titre, sous-titre et CTA. À propos : titre/description. Projets : ajouter/retirer, modifier titre/résumé/lien HTTPS. Compétences : ajouter/retirer/modifier. Contact : titre, texte et e-mail. Tester un lien non HTTPS ou un e-mail invalide : sauvegarde refusée avec message, brouillon local conservé.
4. Masquer une section facultative ; déplacer les sections autorisées. Hero obligatoire reste visible et ancré ; contact reste ancré. Modifier espacement/alignement/emphase proposés ; réinitialiser la présentation pour retrouver la base du template. Vérifier l’aperçu immédiat, sans données perdues lors d’un masquage.
5. Enregistrer explicitement, recharger la page, se déconnecter et se reconnecter : le contenu, l’ordre, la visibilité et les réglages doivent être identiques à la dernière sauvegarde.
6. Modifier sans sauvegarder puis utiliser un lien, Retour navigateur ou fermer/recharger : une confirmation doit prévenir la perte. Annuler conserve le brouillon. Aucun contenu privé n’est stocké dans localStorage ; la préférence clair/sombre du Studio peut y rester.
7. Ouvrir le même portfolio dans deux onglets. Modifier/enregistrer dans A, puis enregistrer une modification dans B. B reçoit un conflit 412 et conserve son brouillon. Le rechargement serveur exige confirmation de remplacement ; aucune fusion automatique ou écriture forcée.
8. Dashboard : identifier le badge du template, « Modifier le portfolio », dupliquer, modifier la copie et vérifier l’original inchangé. Archiver puis restaurer ; l’archive est en lecture seule et la restauration reste privée. Vérifier aussi un portfolio vierge existant : informations et actions PORT conservées, aucun design inventé.
9. Second compte synthétique dans une fenêtre privée : l’URL d’édition ou l’API design du premier compte doit refuser l’accès, sans contenu du propriétaire.
10. Desktop, tablette et mobile : champs, navigation, boutons et aperçu utilisables au clavier, aucun débordement horizontal. Studio sombre : panneaux et cartes suivent les tokens sombres ; le rendu du portfolio reste celui du thème neutre clair de ce lot.

## 6. Durée de l’idempotence et limites

La clé est conservée pour les réessais de la même intention et du même contenu tant que le formulaire reste ouvert. Elle expire après 24 h ; l’interface ne relance pas automatiquement une intention expirée. Après rechargement du formulaire ou réponse réseau incertaine, consulter le dashboard avant une nouvelle intention. Les clés ne dédupliquent pas deux créations volontairement distinctes.

Les enregistrements expirés ne sont plus rejouables. Le nettoyage physique s’effectue par la commande ci-dessous ; sa planification quotidienne devra être configurée lors d’une future exploitation, sans déploiement dans cette livraison :

```powershell
# Toujours avec la configuration synthétique C+D pour ces essais.
& .\backend\.venv\Scripts\python.exe -B backend/manage.py prune_template_requests
& .\backend\.venv\Scripts\python.exe -B backend/manage.py prune_template_requests --execute
```

La première commande compte seulement ; la seconde supprime les réponses d’idempotence expirées, jamais les portfolios. Pas de publication, upload, palette libre, HTML/CSS libre, paiement, moteur 3D ou phase E dans cette livraison.

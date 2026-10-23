# Recette manuelle du SaaS complet — Windows natif

Référence examinée : `feature/media-001`, `fd6b6aedcf543069d0322b6dc739a9b0e18278bf`.
Guide documentaire autorisé à être publié sur la branche de travail. Aucun
changement du SaaS, migration de base existante, publication publique de portfolio,
PR ou PUB-001. **Les commandes Windows ci-dessous n’ont pas
été exécutées par l’agent Linux.** Elles doivent être suivies par étapes.

## 1. Ce qui est réellement accessible

| Fonction | Accès / limites à cette référence |
| --- | --- |
| Inscription, connexion, déconnexion, récupération du mot de passe | UI normale, sessions/CSRF inchangées, e-mails dans une boîte privée locale. |
| Dashboard et plusieurs portfolios | Création, informations, duplication, archive/restauration, suppression logique. |
| Minimal et Editorial historiques | Galerie `/templates`, éditeur historique et aperçu ; documents v1 conservés. |
| Creative Editorial complet | Sélection distincte `/portfolios/ready`, instance privée et éditeur `/portfolios/{id}/ready`. |
| Personnalisation | Identité, navigation, Hero, présentation, projets, contact, pied de page ; palettes, couleurs validées, polices autorisées. |
| Hero Creative Editorial | Textes, portrait, CTA, apparence dans sa composition verrouillée. **Pas de sélecteur libre des sept layouts modulaires.** |
| Médias | Bibliothèque privée, import JPEG/PNG/WebP, sélection, alt, cadrage, remplacement et retrait ; pas de vidéo/SVG. |
| Aperçu et sauvegarde | Aperçu réel privé desktop/mobile dans l’éditeur, sauvegarde explicite, réouverture et conflits de version. |
| Hero modulaires E.05/E.06 | Renderers implémentés/testés, **non activés dans le parcours Studio**. Ne pas forcer les flags ou convertir un document. |
| Publication publique | **Non développée/activée**. Ni URL publique, domaine personnalisé, bouton de publication fonctionnel, ni visite anonyme du portfolio. |
| UX Case Study Builder, édition libre, collaboration, 3D/animations immersives | Pas de parcours complet disponible ; ne pas les assimiler à la liste de projets du template. |

Le résultat est un brouillon privé utilisable pour la recette, pas un site publié.
Les aperçus ne constituent pas un lien à partager avec un visiteur anonyme.

## 2. Scripts examinés et stratégie retenue

- `run_media001_isolated.py` fournit les garde-fous : cluster natif neuf, SCRAM,
  rôles séparés, contrôle `data_directory`, stockage privé et environnement dédié.
  **Ne pas le lancer pour cette recette** : il arrête les services et détruit ses
  données dans `finally`.
- `initialize_private_media.py` initialise uniquement un stockage neuf, hors dépôt.
- `provision_database.py` et `verify_core_database.py` préparent et vérifient les
  rôles minimaux. Ils sont réutilisés, exclusivement sur le cluster créé ici.
- `Initialize-Mailbox.ps1` est réutilisé avec un chemin explicitement isolé.
- `Initialize-Development.ps1` écrit la configuration habituelle : **non utilisé**.
- `Start-Backend.ps1` impose le port 8001 : lancement direct de Django sur **8011**.
- Next utilise `SAAS_API_ORIGIN` ; lancement direct de son binaire comme le runner,
  pour choisir **3011** au lieu du port 3000 du script npm habituel.

On utilise une **copie Git séparée** et un venv séparé. Rien n’est installé dans
le venv/node_modules de votre copie habituelle. Toutes les ressources résident
sous `%LOCALAPPDATA%\PortfolioSaaS-Demos\demo-<identifiant>` : source, configuration
privée, PostgreSQL, médias, boîte mail et logs. Le dossier ne sera pas effacé à
l’arrêt ; il permet de reprendre la recette et de vérifier la persistance.

Trois ports fixes, uniquement loopback : PostgreSQL **55441**, Django **8011**,
Studio **3011**. Si l’un est occupé, arrêter la procédure : ne pas tuer le service
existant ni changer un seul port sans adapter toutes les références du guide.

## 3. Terminal A — prérequis et copie isolée

Ouvrir **un nouveau PowerShell normal**, sans élévation administrateur. Ne pas
réutiliser un terminal contenant un travail de maintenance en cours. Ne pas lancer
`Start-Transcript` ni afficher les fichiers de configuration/secrets.

```powershell
$ErrorActionPreference = 'Stop'
Set-Location "$env:USERPROFILE\testPorfolio-saas"
$sourceRepo = (Get-Location).Path
$pgBin = 'C:\Program Files\PostgreSQL\17\bin'
Get-ChildItem Env:SAAS_*, Env:PG* | ForEach-Object { Remove-Item -LiteralPath ('Env:' + $_.Name) }
py -3.13 --version
if ($LASTEXITCODE -ne 0) { throw 'Python 3.13 requis.' }
node --version
if ($LASTEXITCODE -ne 0) { throw 'Node 24 requis.' }
if ((node --version) -notmatch '^v24\.') { throw 'Installer Node 24 avant de continuer.' }
npm.cmd --version
if ($LASTEXITCODE -ne 0) { throw 'npm indisponible.' }
& "$pgBin\initdb.exe" --version
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL 17 natif requis.' }

$demoHome = Join-Path $env:LOCALAPPDATA ('PortfolioSaaS-Demos\demo-' + [guid]::NewGuid().ToString('N'))
$env:PORTFOLIO_DEMO_HOME = $demoHome
$env:PORTFOLIO_DEMO_SOURCE_REPO = $sourceRepo
@'
import os, sys
from pathlib import Path
root=Path(os.environ['PORTFOLIO_DEMO_HOME'])
if (root.exists() or not root.is_absolute() or any(p.lower()=='.local' for p in root.parts)
    or root.resolve().is_relative_to(Path(os.environ['PORTFOLIO_DEMO_SOURCE_REPO']).resolve())):
    raise SystemExit('Choisir un dossier demo neuf.')
for parent in root.parents:
    if parent.is_symlink() or parent.is_junction():
        raise SystemExit('Chemin de demo avec junction/symlink refuse.')
sys.path.insert(0,str(Path(os.environ['PORTFOLIO_DEMO_SOURCE_REPO'])/'scripts/verification'))
from run_media001_isolated import private_directory
root.mkdir(mode=0o700,parents=True,exist_ok=False)
private_directory(root)
print('Dossier demo neuf, DACL restreinte configuree.')
'@ | py -3.13 -B -
if ($LASTEXITCODE -ne 0) { throw 'Preparation du dossier prive echouee.' }

$demoRepo = Join-Path $demoHome 'source'
git clone --branch feature/media-001 https://github.com/Mariekaf/testPorfolio.git $demoRepo
if ($LASTEXITCODE -ne 0) { throw 'Clone echoue ; ne pas continuer.' }
if ((git -C $demoRepo rev-parse HEAD) -ne 'fd6b6aedcf543069d0322b6dc739a9b0e18278bf') {
    throw 'La branche distante a change : faire examiner la reference avant de continuer.'
}
Set-Location $demoRepo
py -3.13 -m venv .\backend\.venv
if ($LASTEXITCODE -ne 0) { throw 'Creation du venv echouee.' }
$demoPython = Join-Path $demoRepo 'backend\.venv\Scripts\python.exe'
& $demoPython -m pip install --require-hashes -r .\backend\requirements\development.txt
if ($LASTEXITCODE -ne 0) { throw 'Installation verrouillee Python echouee.' }
& $demoPython -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependances Python incoherentes.' }
npm.cmd ci --ignore-scripts
if ($LASTEXITCODE -ne 0) { throw 'Installation verrouillee npm echouee.' }
$env:PORTFOLIO_DEMO_REPO = $demoRepo
$env:PORTFOLIO_DEMO_PG_BIN = $pgBin
Write-Host "Dossier a conserver pour reprendre la recette : $demoHome"
```

Attendu : Python 3.13, Node 24, `initdb (PostgreSQL) 17.x`, installation sans erreur.
Le service PostgreSQL habituel sur 5432 n’est ni interrogé, ni arrêté, ni modifié.

## 4. Terminal A — environnement persistant de la démonstration

Ce fichier ne contient aucun mot de passe. Les fenêtres lancées plus loin héritent
de `PORTFOLIO_DEMO_HOME`, puis rechargent cet environnement explicitement.

```powershell
@'
$ErrorActionPreference = 'Stop'
$env:PORTFOLIO_DEMO_HOME = $PSScriptRoot
$meta = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'demo.json') -Raw | ConvertFrom-Json
$demoHome = $PSScriptRoot
$demoRepo = $meta.repo
$env:PORTFOLIO_DEMO_REPO = $meta.repo
$env:PORTFOLIO_DEMO_PG_BIN = $meta.pg_bin
# Seulement l'environnement de ce terminal, pas les variables Windows persistantes.
Get-ChildItem Env:SAAS_*, Env:PG* | ForEach-Object { Remove-Item -LiteralPath ('Env:' + $_.Name) }
$env:SAAS_CONFIG_FILE = Join-Path $PSScriptRoot 'config.json'
$env:SAAS_MEDIA_ROOT = Join-Path $PSScriptRoot 'media'
$env:SAAS_MAILBOX_PATH = Join-Path $PSScriptRoot 'mailbox'
$env:SAAS_STUDIO_ORIGIN = 'http://127.0.0.1:3011'
$env:SAAS_API_ORIGIN = 'http://127.0.0.1:8011'
$env:SAAS_HERO_TRANSITIONS_ENABLED = '0'
$env:SAAS_HTTPS = '0'
$env:NEXT_TELEMETRY_DISABLED = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONPATH = Join-Path $meta.repo 'backend'
$env:DJANGO_SETTINGS_MODULE = 'config.settings.development'
Set-Location $meta.repo
'@ | Set-Content -LiteralPath (Join-Path $demoHome 'session.ps1') -Encoding UTF8
```

`SAAS_HTTPS=0` correspond au mode de développement HTTP loopback déjà prévu par
AUTH-001 ; sessions, contrôle d’origine, CSRF, mots de passe et permissions restent
actifs. Aucun SMTP hérité n’est utilisé. Ne pas remplacer les URL par une IP LAN,
`0.0.0.0` ou un tunnel ; ne pas modifier les durées de session pour cette recette.

## 5. Terminal A — créer uniquement le cluster neuf et sa base de démonstration

Le bloc suivant reprend le provisioning du runner. Il génère des secrets aléatoires
dans le dossier privé, ne demande **aucun mot de passe PostgreSQL habituel**, et
n’affiche aucune valeur secrète. Les migrations déjà présentes sont autorisées
uniquement après identification du nouveau cluster ; aucun schéma n’est modifié
sur une ancienne base. Le préfixe `e04_` respecte les gardes historiques, il ne
réutilise pas un ancien cluster de validation.

```powershell
@'
import json, os, secrets, socket, subprocess, sys, uuid
from pathlib import Path
import psycopg
root=Path(os.environ['PORTFOLIO_DEMO_HOME'])
repo=Path(os.environ['PORTFOLIO_DEMO_REPO'])
pg=Path(os.environ['PORTFOLIO_DEMO_PG_BIN'])
data=root/'pgdata'
created_here=False
try:
    if (root/'demo.json').exists() or (root/'config.json').exists() or data.exists():
        raise ValueError('Initialisation non repetable sur un dossier existant.')
    version=subprocess.check_output([str(pg/'initdb.exe'),'--version'],text=True)
    if not version.startswith('initdb (PostgreSQL) 17.'):
        raise ValueError('PostgreSQL 17 requis.')
    for port in (55441,8011,3011):
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',port))
    sys.path.insert(0,str(repo/'scripts/development'))
    from initialize_private_media import initialize
    initialize(root/'media')
    password=secrets.token_hex(32)
    name='e04_demo_'+uuid.uuid4().hex[:10]
    config={'database_mode':'native','secret_key':secrets.token_hex(48),
            'bootstrap_user':'manual_demo_bootstrap','bootstrap_password':password,
            'database':{'host':'127.0.0.1','port':55441,'name':name}}
    for kind,suffix in (('runtime','app'),('migration','ddl'),('test','test')):
        config['database'][kind+'_user']=name+'_'+suffix
        config['database'][kind+'_password']=secrets.token_hex(32)
    config_path=root/'config.json'
    with config_path.open('x',encoding='utf-8') as file:json.dump(config,file)
    pwfile=root/'init-password'
    with pwfile.open('x',encoding='utf-8') as file:file.write(password+'\n')
    created_here=True
    with (root/'setup.log').open('x',encoding='utf-8') as log:
        subprocess.run([str(pg/'initdb.exe'),'-D',str(data),'-U','manual_demo_bootstrap',
          '--pwfile',str(pwfile),'--auth-host=scram-sha-256','--auth-local=scram-sha-256',
          '--encoding=UTF8','--locale=C'],check=True,stdout=log,stderr=subprocess.STDOUT)
    pwfile.unlink()
    with (data/'postgresql.conf').open('a',encoding='utf-8') as file:
        file.write("\nlisten_addresses='127.0.0.1'\nport=55441\npassword_encryption='scram-sha-256'\n"
                   "log_statement='none'\nlog_min_error_statement='panic'\nlog_min_duration_statement=-1\n")
    subprocess.run([str(pg/'pg_ctl.exe'),'start','-D',str(data),'-l',str(root/'cluster.log'),'-w','-t','30'],
                   check=True,stdout=subprocess.DEVNULL)
    with psycopg.connect(host='127.0.0.1',port=55441,dbname='postgres',
                         user='manual_demo_bootstrap',password=password,connect_timeout=3) as conn:
        directory=conn.execute('SHOW data_directory').fetchone()[0]
        server=conn.execute('SHOW server_version').fetchone()[0]
        if Path(directory).resolve()!=data.resolve() or not server.startswith('17.'):
            raise ValueError('Identite du cluster neuf incorrecte.')
    os.environ['SAAS_CONFIG_FILE']=str(config_path)
    os.environ['SAAS_MEDIA_ROOT']=str(root/'media')
    os.environ['SAAS_MAILBOX_PATH']=str(root/'mailbox')
    for key in list(os.environ):
        if key.startswith('SAAS_EMAIL_'):os.environ.pop(key)
    import provision_database
    provision_database.getpass.getpass=lambda _:password
    provision_database.provision('manual_demo_bootstrap')
    env=os.environ.copy()
    env.update(PYTHONPATH=str(repo/'backend'),PYTHONUTF8='1',PYTHONIOENCODING='utf-8',
               SAAS_E04_ISOLATED_MIGRATIONS='1',SAAS_E0704_ISOLATED_MIGRATIONS='1',
               SAAS_MEDIA001_ISOLATED_MIGRATIONS='1',SAAS_HERO_TRANSITIONS_ENABLED='0',
               SAAS_STUDIO_ORIGIN='http://127.0.0.1:3011',SAAS_HTTPS='0')
    with (root/'migrations.log').open('x',encoding='utf-8') as log:
        subprocess.run([sys.executable,'-B','backend/manage.py','migrate',
          '--settings=config.settings.migration','--noinput'],cwd=repo,env=env,check=True,
          stdout=log,stderr=subprocess.STDOUT)
    subprocess.run([sys.executable,'-B','scripts/verification/verify_core_database.py',
                    '--check-test-access'],cwd=repo,env=env,check=True)
    meta={'kind':'portfolio-manual-demo-v1','repo':str(repo),'pg_bin':str(pg)}
    with (root/'demo.json').open('x',encoding='utf-8') as file:json.dump(meta,file)
    print('Cluster demo identifie, base neuve initialisee, roles minimaux verifies. Secrets omis.')
except Exception:
    if created_here and (data/'postmaster.pid').exists():
        subprocess.run([str(pg/'pg_ctl.exe'),'stop','-D',str(data),'-m','fast','-w'],
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    raise SystemExit('Preparation demo echouee. Ne pas relancer sur ce dossier ni afficher config.json. Conserver les logs prives.') from None
'@ | & $demoPython -B -
if ($LASTEXITCODE -ne 0) { throw 'Arret : preparation de demonstration echouee.' }
. (Join-Path $demoHome 'session.ps1')
& .\scripts\windows\Initialize-Mailbox.ps1
if ($LASTEXITCODE -ne 0) { throw 'Initialisation boite privee echouee.' }
```

Attendu : PostgreSQL 17/UTF8, rôle runtime sans DDL/superuser/BYPASSRLS, migrations
terminées et boîte privée configurée. **Ne pas relancer l’initialisation** pour
reprendre demain : utiliser la section reprise. En cas d’échec, conserver le
répertoire pour diagnostic ; ne pas y remplacer les valeurs par la configuration
habituelle et ne pas envoyer `config.json`, `init-password`, `pgdata` ou les e-mails.

## 6. Vérification d’identité avant tout redémarrage

Créer une fois ce vérificateur, sans secret dans son code. Il ne lit que la
configuration du dossier de démonstration ; toute erreur est générique.

```powershell
@'
import json, os
from pathlib import Path
import psycopg
try:
    root=Path(os.environ['PORTFOLIO_DEMO_HOME']).resolve()
    meta=json.loads((root/'demo.json').read_text(encoding='utf-8'))
    config=json.loads((root/'config.json').read_text(encoding='utf-8'))
    db=config['database']
    if (meta['kind']!='portfolio-manual-demo-v1' or db['host']!='127.0.0.1'
        or db['port']!=55441 or not db['name'].startswith('e04_demo_')
        or config['bootstrap_user']!='manual_demo_bootstrap'):
        raise ValueError()
    with psycopg.connect(host='127.0.0.1',port=55441,dbname='postgres',
                         user=config['bootstrap_user'],password=config['bootstrap_password'],connect_timeout=3) as conn:
        directory=conn.execute('SHOW data_directory').fetchone()[0]
        version=conn.execute('SHOW server_version').fetchone()[0]
        if Path(directory).resolve()!=(root/'pgdata').resolve() or not version.startswith('17.'):
            raise ValueError()
    print('Identite du cluster de demonstration verifiee.')
except Exception:
    raise SystemExit('Verification demo refusee. Aucun service existant ne doit etre adopte.') from None
'@ | Set-Content -LiteralPath (Join-Path $demoHome 'verify-demo.py') -Encoding UTF8
& $demoPython -B (Join-Path $demoHome 'verify-demo.py')
if ($LASTEXITCODE -ne 0) { throw 'Identite de demonstration incorrecte.' }
```

## 7. Deux fenêtres pour laisser les serveurs accessibles

Toujours depuis A, créer deux scripts **dans le dossier de démonstration**, pas
dans le dépôt. Ils resteront au premier plan de leur fenêtre ; pas de timer,
runner de test, fermeture automatique ou suppression de la base.

```powershell
@'
. (Join-Path $PSScriptRoot 'session.ps1')
$python = Join-Path $env:PORTFOLIO_DEMO_REPO 'backend\.venv\Scripts\python.exe'
& $python -B (Join-Path $PSScriptRoot 'verify-demo.py')
if ($LASTEXITCODE -ne 0) { throw 'Cluster demo incorrect.' }
& .\scripts\windows\Initialize-Mailbox.ps1
& $python -B backend/manage.py runserver 127.0.0.1:8011 --noreload
if ($LASTEXITCODE -ne 0) { throw 'Django arrete avec erreur.' }
'@ | Set-Content -LiteralPath (Join-Path $demoHome 'backend.ps1') -Encoding UTF8
@'
. (Join-Path $PSScriptRoot 'session.ps1')
$python = Join-Path $env:PORTFOLIO_DEMO_REPO 'backend\.venv\Scripts\python.exe'
& $python -B (Join-Path $PSScriptRoot 'verify-demo.py')
if ($LASTEXITCODE -ne 0) { throw 'Cluster demo incorrect.' }
Set-Location (Join-Path $env:PORTFOLIO_DEMO_REPO 'apps\studio')
& node.exe ..\..\node_modules\next\dist\bin\next dev --hostname 127.0.0.1 --port 3011
if ($LASTEXITCODE -ne 0) { throw 'Studio arrete avec erreur.' }
'@ | Set-Content -LiteralPath (Join-Path $demoHome 'studio.ps1') -Encoding UTF8

foreach ($demoPort in @(8011,3011)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $demoPort -ErrorAction SilentlyContinue) {
        throw "Port $demoPort occupe : ne pas reutiliser un serveur existant."
    }
}
Start-Process powershell.exe -ArgumentList @('-NoProfile','-NoExit','-File',('"{0}"' -f (Join-Path $demoHome 'backend.ps1')))
Start-Process powershell.exe -ArgumentList @('-NoProfile','-NoExit','-File',('"{0}"' -f (Join-Path $demoHome 'studio.ps1')))
```

**Fenêtre B = Django** : attendre `Starting development server at http://127.0.0.1:8011/`.
**Fenêtre C = Studio Next.js** : attendre `Ready` et `http://127.0.0.1:3011`.
Les laisser ouvertes pendant toute la recette. `--noreload` évite un second
processus Django ; aucun serveur habituel ne sera stoppé pour libérer un port.

Dans A :

```powershell
Invoke-RestMethod 'http://127.0.0.1:8011/health/live'
Invoke-RestMethod 'http://127.0.0.1:8011/health/ready'
Start-Process 'http://127.0.0.1:3011'
```

Les deux contrôles doivent retourner `status: ok`. Sur la page d’accueil, cliquer **Vérifier la connexion** : elle doit confirmer
la disponibilité du backend/PostgreSQL. Ne pas exposer le port PostgreSQL dans le
navigateur et ne pas ouvrir le CMS historique (`server.py`, port 8000).

| Écran | URL exacte |
| --- | --- |
| Accueil SaaS | http://127.0.0.1:3011/ |
| Inscription | http://127.0.0.1:3011/register |
| Connexion | http://127.0.0.1:3011/login |
| Mot de passe oublié | http://127.0.0.1:3011/forgot-password |
| Dashboard | http://127.0.0.1:3011/dashboard |
| Creative Editorial | http://127.0.0.1:3011/portfolios/ready |
| Médias privés | http://127.0.0.1:3011/portfolios/media |
| Minimal / Editorial | http://127.0.0.1:3011/templates |
| Portfolio vierge / métadonnées | http://127.0.0.1:3011/portfolios/new |

La page d’accueil porte encore les textes historiques CORE-001 annonçant des
fonctions futures : ce texte n’est pas à jour avec les routes implémentées. Utiliser
les liens du tableau et le dashboard ; aucun texte applicatif n’est modifié ici.

L’URL de l’éditeur Creative Editorial est
`http://127.0.0.1:3011/portfolios/<UUID-créé>/ready` : conserver l’adresse réellement
obtenue à la création. Aucun UUID préexistant n’est injecté dans la démonstration.

## 8. Compte de démonstration et récupération

Ouvrir le Studio dans une nouvelle fenêtre privée/Invité, pour éviter de remplacer
les cookies d’une session habituelle : les cookies sont liés à l’hôte, pas au port.

1. Sur `/register`, créer **Camille Martin**, `camille.martin@example.test`.
   Identité fictive réservée à cette recette. Choisir dans le formulaire un mot
   de passe inédit d’au moins 12 caractères, validé normalement ; le conserver
   dans votre gestionnaire. Aucun compte/mot de passe par défaut, superuser,
   désactivation de CSRF ou accès admin n’est nécessaire.
2. Se connecter sur `/login`. Le compte personnel est provisionné par le SaaS,
   pas manuellement par SQL. Créer plusieurs portfolios depuis ce compte.
3. À la reprise, utiliser le même compte : la base n’est pas recréée.
4. Pour récupérer ce compte : `/forgot-password`, même adresse, puis ouvrir le
   dernier e-mail **localement**, sans l’imprimer dans le terminal :

```powershell
$mail = Get-ChildItem -LiteralPath (Join-Path $demoHome 'mailbox') -File |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $mail) { throw 'Aucun e-mail : verifier le compte et la demande dans le Studio.' }
Start-Process notepad.exe -ArgumentList ('"{0}"' -f $mail.FullName)
```

Copier le lien complet dans le navigateur, **y compris le fragment `#uid=…&token=…`**.
Le lien ne représente pas un site public. Il est à usage unique et expire selon
AUTH-001 (30 min par défaut). Choisir un nouveau mot de passe puis se reconnecter.
L’adresse `example.test` ne nécessite pas de SMTP. Ne partager aucun contenu de
boîte, lien de récupération, fichier secret ou export de cookies.

## 9. Jeu de démonstration fictif, sans import de données personnelles

Pour tester réellement l’éditeur, remplir les champs par l’UI normale, puis importer
les images existantes via le sélecteur : aucun fixture SQL, média UUID inventé,
bypass de validation ou compte préchargé.

```powershell
$demoAssets = Join-Path $demoHome 'assets'
New-Item -ItemType Directory -Path $demoAssets -ErrorAction Stop | Out-Null
Copy-Item (Join-Path $demoRepo 'docs\media001\evidence\portrait-synthetique.png') $demoAssets
Copy-Item (Join-Path $demoRepo 'docs\media001\evidence\logo-synthetique.png') $demoAssets
Copy-Item (Join-Path $demoRepo 'docs\media001\evidence\couverture-synthetique.png') $demoAssets
Start-Process explorer.exe -ArgumentList ('"{0}"' -f $demoAssets)
```

Ces visuels sont synthétiques, pas le portrait d’une personne ni les ressources
« Form & Play ». Le texte suivant est fictif ; les projets et résultats ne doivent
pas être présentés comme des références clients réelles.

| Champ | Contenu proposé |
| --- | --- |
| Nom du portfolio | Camille — UX/UI & produits utiles |
| Identité | Camille Martin |
| Titre principal Hero | Des interfaces claires, des usages plus simples. |
| Sous-titre | Designer UX/UI, je transforme les parcours complexes en expériences accessibles, du premier entretien au prototype. |
| CTA Hero | « Voir mes projets », type `section`, cible `projects`. |
| Présentation | Je conçois des services numériques utiles avec des équipes produit. Ma démarche associe recherche, architecture de l’information, prototypage et tests d’utilisabilité. Ce portfolio de démonstration rassemble des études fictives. |
| Projet 1 | **Clair Budget** — Simplifier le suivi des dépenses : entretiens exploratoires, hiérarchisation des besoins et prototype mobile accessible. Étude fictive. |
| Projet 2 | **Agora Culture** — Repenser la recherche d’événements et la réservation : parcours comparés, tests de navigation et composants UI cohérents. Étude fictive. |
| Liens des projets | Type externe, `https://example.com/clair-budget` et `https://example.com/agora-culture`. Liens de démonstration, pas de case study hébergée. Ou laisser le lien facultatif vide. |
| Contact | « Parlons de votre projet », type `email`, adresse `camille.martin@example.test`. |
| Pied de page | Portfolio de démonstration — contenus et projets fictifs. |
| Texte alternatif | « Illustration abstraite de démonstration » ; pour la couverture, « Composition graphique du projet fictif Clair Budget ». |

Importer les trois images avec confirmation des droits via l’UI. Associer le
portrait, le logo, puis la couverture aux slots correspondants. Ajouter des
paragraphes/fragments et projets avec les boutons de l’éditeur, sans coller du HTML.
La politique de publication future ne rend pas ces projets fictifs « publiables » :
aucune publication publique n’est exécutée dans cette recette.

## 10. Parcours de recette et résultats attendus

Cocher chaque étape réellement exécutée ; conserver une capture sans mot de passe,
e-mail de récupération, cookie ou configuration secrète.

1. **AUTH** : inscription valide, mot de passe trop faible refusé, connexion,
   déconnexion, dashboard protégé après déconnexion, récupération via boîte locale.
   Éviter les dizaines de tentatives invalides : les limites anti-abus sont actives.
2. **Dashboard** : créer deux portfolios indépendants, vérifier leurs noms ; tester
   modification des informations, duplication, archive puis restauration. Utiliser
   un portfolio jetable distinct pour la suppression logique avec confirmation.
3. **Creative Editorial** : bouton « Choisir Creative Editorial », nom du portfolio,
   « Créer mon portfolio privé ». Vérifier l’accès à son éditeur `/ready`.
4. **Contenu** : remplir toutes les sections du jeu proposé. Le Hero permet titre,
   sous-titre, portrait et CTA ; ne pas chercher un sélecteur des sept layouts.
5. **Apparence** : changer la palette puis une couleur valide et une police
   autorisée. Tester un contraste insuffisant : validation/refus attendu ; rétablir
   la palette valide avant sauvegarde. Pas de CSS/JS/HTML arbitraire.
6. **Médias** : bibliothèque, import des images synthétiques, sélection, alt,
   cadrage, remplacement et retrait d’un slot. Import de plus de quatre fichiers,
   d’un format non autorisé ou d’un fichier >8 Mio : refus attendu.
7. **Aperçu** : Desktop/Mobile de l’éditeur, fenêtre réelle étroite, zoom 200 %,
   navigation clavier, titres longs. L’aperçu est privé, avec images résolues
   réellement depuis le backend, pas une capture statique.
8. **Sauvegarde** : cliquer « Enregistrer », attendre la confirmation, actualiser,
   quitter vers le dashboard, se déconnecter/reconnecter, rouvrir le même portfolio.
   Textes, images, alt, cadrages et apparence doivent être conservés. Les changements
   non enregistrés ne sont pas garantis après fermeture de l’onglet.
9. **Conflit** : ouvrir le même brouillon dans deux onglets ; enregistrer A, puis
   tenter d’enregistrer B avec son ancienne version. Conflit attendu, sans
   écrasement silencieux. Comparer les saisies avant de recharger le brouillon.
10. **Isolation** : dans un autre navigateur/profil indépendant, inscrire
    `alex.demo@example.test`. Il ne doit voir ni portfolios ni médias de Camille.
    Ouvrir l’URL d’un portfolio/média de Camille dans ce second profil doit être
    refusé. Sans session, les médias restent également inaccessibles.
11. **Révisions/médias** : retirer une image d’un slot puis enregistrer ne rend pas
    forcément sa suppression possible : une révision peut encore la référencer.
    Refus `asset_in_use` attendu. Tester la suppression avec une image nouvellement
    importée **jamais associée**. Pas de purge forcée pour simplifier la recette.
12. **Templates v1** : `/templates`, vérifier Minimal et Editorial, créer une
    instance de chaque via leur parcours, modifier/enregistrer/réouvrir. Ne pas
    convertir ces instances pour y faire apparaître les Hero modulaires.
13. **Publication** : noter « hors périmètre / indisponible », pas « test réussi ».
    Le statut privé/brouillon est attendu ; aucune URL publique ne doit être créée.
14. **Persistance locale** : arrêter puis reprendre avec la section suivante :
    retrouver le compte et le portfolio sans nouvelle inscription ni nouvelle base.

Limites médias : JPEG/PNG/WebP statiques, 4 fichiers/import, 8 Mio/source,
20 Mpx/8192 px par côté, quota 200 images/200 Mio par compte (variantes conservées,
y compris celles protégées par révisions). Aucun original n’est conservé après
normalisation. La suppression logique reste soumise à la rétention existante.

## 11. Arrêt propre, sans effacer la démonstration

1. Dans **C (Next.js)** : `Ctrl+C`, attendre le retour du prompt. Confirmer si le
   terminal demande l’arrêt ; ne pas fermer brutalement la fenêtre pendant un upload.
2. Dans **B (Django)** : `Ctrl+C`, attendre le retour du prompt.
3. Dans **A**, vérifier l’identité puis arrêter **uniquement ce cluster** :

```powershell
. (Join-Path $demoHome 'session.ps1')
$demoPython = Join-Path $env:PORTFOLIO_DEMO_REPO 'backend\.venv\Scripts\python.exe'
& $demoPython -B (Join-Path $demoHome 'verify-demo.py')
if ($LASTEXITCODE -ne 0) { throw 'Ne pas arreter un service non identifie.' }
& "$env:PORTFOLIO_DEMO_PG_BIN\pg_ctl.exe" stop -D (Join-Path $demoHome 'pgdata') -m fast -w -t 30
if ($LASTEXITCODE -ne 0) { throw 'Arret du seul cluster demo a verifier.' }
```

Ne pas utiliser `Stop-Service postgresql*`, `taskkill /IM python.exe`, ni supprimer
le dossier. Fermer ensuite les terminaux pour retirer leurs variables temporaires.
Les données privées restent sur le PC pour la reprise ; pas d’envoi dans Git.
Ce cluster demeure exclusivement synthetique et jetable : ne pas en faire une base
de travail reelle ni y importer votre base habituelle.

## 12. Reprise le lendemain

Ouvrir un nouveau PowerShell ; remplacer uniquement le chemin de la première ligne
par **le dossier affiché à l’étape 3** (ne pas choisir un ancien dossier de tests).

```powershell
$demoHome = 'C:\CHEMIN\AFFICHE\PortfolioSaaS-Demos\demo-IDENTIFIANT'
. (Join-Path $demoHome 'session.ps1')
$demoPython = Join-Path $env:PORTFOLIO_DEMO_REPO 'backend\.venv\Scripts\python.exe'
& "$env:PORTFOLIO_DEMO_PG_BIN\pg_ctl.exe" status -D (Join-Path $demoHome 'pgdata')
if ($LASTEXITCODE -ne 0) {
    # Refuser un port occupe ; ne jamais adopter le service qui l'utilise.
    if (Get-NetTCPConnection -State Listen -LocalPort 55441 -ErrorAction SilentlyContinue) {
        throw 'Port 55441 occupe : examiner avant de demarrer.'
    }
    & "$env:PORTFOLIO_DEMO_PG_BIN\pg_ctl.exe" start -D (Join-Path $demoHome 'pgdata') -l (Join-Path $demoHome 'cluster.log') -w -t 30
    if ($LASTEXITCODE -ne 0) { throw 'Redemarrage du cluster demo echoue.' }
}
& $demoPython -B (Join-Path $demoHome 'verify-demo.py')
if ($LASTEXITCODE -ne 0) { throw 'Identite du cluster refusee.' }
foreach ($demoPort in @(8011,3011)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $demoPort -ErrorAction SilentlyContinue) {
        throw "Port $demoPort occupe : verifier les fenetres demo existantes, ne pas les doubler."
    }
}
Start-Process powershell.exe -ArgumentList @('-NoProfile','-NoExit','-File',('"{0}"' -f (Join-Path $demoHome 'backend.ps1')))
Start-Process powershell.exe -ArgumentList @('-NoProfile','-NoExit','-File',('"{0}"' -f (Join-Path $demoHome 'studio.ps1')))
Start-Process 'http://127.0.0.1:3011/login'
```

Pas de `initdb`, migration, réinitialisation, npm ci ou nouvel import automatique
à la reprise. Lancer les contrôles de santé lorsque les fenêtres annoncent leur
disponibilité. Les serveurs doivent rester ouverts jusqu’à l’arrêt volontaire.

## 13. Diagnostic et compte rendu

- **ExecutionPolicy** : ne pas appliquer de `Bypass` global. Si Windows bloque
  les scripts, examiner `Get-ExecutionPolicy -List`, l’origine des fichiers et la
  politique du PC avant de poursuivre ; ne pas contourner une politique d’entreprise.
- **401/403** : utiliser uniquement `127.0.0.1:3011`, pas `localhost` ou le port
  Django pour le Studio ; vérifier origine/session et redémarrer les deux fenêtres
  avec `session.ps1`. Ne pas désactiver CSRF ou les cookies de session.
- **Backend/PostgreSQL indisponible** : vérifier le cluster via `verify-demo.py`,
  puis les deux health endpoints. Ne pas basculer vers la configuration habituelle.
- **503 média / ACL** : exécuter les tests ACL existants depuis la copie isolée,
  avec son Python ; ne pas accorder Everyone/Users pour « réparer » le dossier.
- **`asset_in_use` / quota** : protections normales. Noter le scénario ; ne pas
  purger les révisions ou les fichiers à la main.
- **Logs** : `setup.log`, `migrations.log`, `cluster.log` sont privés sous le dossier
  demo ; les sorties Django/Next restent dans B/C. Aucun mot de passe n’est passé
  en argument de commande ou affiché par cette procédure. Ne pas partager les
  e-mails, secrets, URL de récupération, dumps réseau, cookies ou le dossier complet.

Compte rendu recommandé : commit, versions Python/Node/PostgreSQL, étape, résultat
attendu/observé, URL sans secrets, capture et éventuel message d’erreur nettoyé.
Classer chaque fonction « réussie », « échouée », « non exécutée » ou « non disponible ».
Ce guide ne clôture ni la recette manuelle ni la validation Windows du correctif
WinError 32 ; les tests automatisés restent une vérification séparée.

## Vérification documentaire réalisée par l’agent

Lecture des scripts de provisioning, permissions/médias, boîte privée, configuration
Django/Next, migrations gardées et routes/composants réellement accessibles.
Les trois blocs Python embarqués passent `ast.parse` ; les clôtures de blocs du
guide sont équilibrées. Aucun interpréteur PowerShell/Windows n’est disponible ici :
ni les scripts PowerShell ni le parcours Windows complet ne sont annoncés testés.
Aucun cluster, serveur, compte ou média n’a été créé lors de la rédaction. Seul ce
fichier documentaire est ajouté ; la référence applicative reste `fd6b6aed…`.
La publication de ce guide sur la branche ne valide pas la recette Windows.

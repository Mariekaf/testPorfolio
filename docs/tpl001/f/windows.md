# TPL-001.F — Vérification Windows sans base existante

Livraison locale pour revue, sans push automatique. La branche à mettre à
exécution est `design/tpl-001-f-navigation` au commit de livraison communiqué.
**Un git pull ne récupère pas un commit qui n’a pas encore été publié.** Après
transfert ou publication expressément autorisée, vérifier la référence locale
avant de lancer les commandes. Aucune commande ici ne doit viser votre base
habituelle ou votre démonstration persistante.

## Vérifications hors base

Depuis la racine de la copie du ticket, avec Python 3.13, Node 24, PostgreSQL 17 :

```powershell
$ErrorActionPreference = 'Stop'
git branch --show-current
git log -1 --format="%H %s"
git status --short
py -3.13 --version
node --version
& 'C:\Program Files\PostgreSQL\17\bin\initdb.exe' --version
& .\backend\.venv\Scripts\python.exe -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependances Python incoherentes.' }
$tplFNodeTests = @(Get-ChildItem packages/content-contracts/test/*.test.mjs, packages/content-contracts/test/*.test.ts, apps/studio/test/*.test.mjs | ForEach-Object { $_.FullName })
node --test $tplFNodeTests
if ($LASTEXITCODE -ne 0) { throw 'Tests Node echoues.' }
npm.cmd run typecheck
if ($LASTEXITCODE -ne 0) { throw 'TypeScript echoue.' }
$env:NEXT_TELEMETRY_DISABLED = '1'
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Build echoue.' }
& .\backend\.venv\Scripts\python.exe -B scripts/verification/check_base001.py
if ($LASTEXITCODE -ne 0) { throw 'Reference historique modifiee.' }
& .\backend\.venv\Scripts\python.exe -B -m unittest discover -s scripts/verification/tests -v
if ($LASTEXITCODE -ne 0) { throw 'Integrite ou ACL echouee.' }
```

Arrêter votre propre serveur Next avant typecheck/build : le dossier `.next` est
partagé entre ces commandes dans une même copie. Préférer une nouvelle copie pour
cette recette. Ne pas compter un test symlink ignoré comme réussi et ne pas lancer
en administrateur pour masquer une limitation.

## Suite PostgreSQL et navigateur dans un cluster neuf, sans Docker

Installer les outils de recette dans un venv distinct sous TEMP. Ce n’est pas une
dépendance applicative et aucun navigateur n’est ajouté au bundle du Studio.

```powershell
$tplFBrowserVenv = Join-Path $env:TEMP ('tpl-f-browser-' + [guid]::NewGuid().ToString('N'))
py -3.13 -m venv $tplFBrowserVenv
$tplFBrowserPython = Join-Path $tplFBrowserVenv 'Scripts\python.exe'
& $tplFBrowserPython -m pip install 'playwright==1.62.0' 'Pillow==13.0.0'
if ($LASTEXITCODE -ne 0) { throw 'Outils navigateur indisponibles.' }
$env:SAAS_TEST_CHROMIUM = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if (-not (Test-Path -LiteralPath $env:SAAS_TEST_CHROMIUM)) { throw 'Indiquer le chemin reel du navigateur Edge/Chromium installe.' }
$tplFEvidence = Join-Path $env:TEMP ('tpl-f-recipe-' + [guid]::NewGuid().ToString('N'))
try {
    & .\backend\.venv\Scripts\python.exe -B scripts/verification/run_media001_isolated.py `
        --engine native --pg-bin 'C:\Program Files\PostgreSQL\17\bin' `
        --output $tplFEvidence --execute-isolated-migrations `
        --browser --browser-script scripts/verification/browser_tpl001_f.py `
        --browser-python $tplFBrowserPython
    $tplFResult = $LASTEXITCODE
    if (Test-Path (Join-Path $tplFEvidence 'django-tests.log')) {
        Get-Content (Join-Path $tplFEvidence 'django-tests.log') -Encoding UTF8 -Tail 35
    }
    if ($tplFResult -ne 0) { throw "Recette echouee : consulter $tplFEvidence" }
    Get-Content (Join-Path $tplFEvidence 'navigation-results.json') -Encoding UTF8
    Get-Content (Join-Path $tplFEvidence 'isolated-environment.json') -Encoding UTF8
} finally {
    Remove-Item Env:\SAAS_TEST_CHROMIUM -ErrorAction SilentlyContinue
}
```

Le nom historique du runner est conservé pour réutiliser ses protections et ses
rôles. Il crée lui-même un cluster 17 natif neuf, un port loopback aléatoire, des
secrets synthétiques et un stockage privé temporaire, vérifie `data_directory`,
provisionne les rôles minimaux et n’exécute les migrations existantes que sur cette
base neuve. Aucun nouveau fichier de migration. Les flags historiques sont locaux
au processus du runner pour autoriser cette initialisation synthétique ; les Hero
modulaires et transitions d’édition restent désactivés.

Django et Next prennent leurs propres ports puis sont arrêtés avec le cluster et
le stockage dans `finally`. Les preuves restent dans `$tplFEvidence`, sans mot de
passe ni cookie. Ce runner **ne convient pas** pour garder les serveurs ouverts
pendant une recette manuelle.

Le parcours couvre les trois templates, les changements de panneau sans PUT ni
relecture de snapshot, le retour/avance, les sorties annulées, la sauvegarde et
réouverture, les conflits réels 412, l’archive, le portfolio vierge/supprimé,
l’isolation réelle entre comptes et la session révoquée. Les versions inconnues
et le 406 v2 utilisent des réponses de test injectées dans le navigateur, sans
corrompre une base ni activer v2. Le fallback sans Navigation API est simulé sous
Chromium ; cela ne constitue pas une recette Firefox/Safari native.

Pour répéter le parcours MEDIA-001 existant dans un autre cluster neuf : reprendre
le même appel avec un nouveau dossier `$tplFEvidence`, en omettant
`--browser-script` (le défaut reste `browser_media001.py`). Ne jamais réutiliser un
dossier de preuves non vide.

## Recette manuelle durable, dans une NOUVELLE démonstration

Réutiliser [le guide de démonstration Windows](../../runbooks/manual-saas-windows-demo.md)
avec deux adaptations de référence **avant le clone**, sans réutiliser le dossier
ni la base de votre ancienne démo :

1. Suivre son étape 3 jusqu’à la création du dossier privé, avant `git clone`.
2. À la place du clone de `feature/media-001` et de son contrôle `fd6b6aed…`, utiliser :

```powershell
# Copier ici le SHA de livraison valide fourni dans le rapport final.
$tplFExpectedCommit = 'REMPLACER_PAR_LE_SHA_DE_LIVRAISON'
if ($tplFExpectedCommit -notmatch '^[0-9a-f]{40}$') { throw 'Renseigner le SHA avant de poursuivre.' }
git clone --branch design/tpl-001-f-navigation https://github.com/Mariekaf/testPorfolio.git $demoRepo
if ($LASTEXITCODE -ne 0) { throw 'Branche non publiee ou clone echoue : ne pas utiliser une autre branche.' }
if ((git -C $demoRepo rev-parse HEAD) -ne $tplFExpectedCommit) { throw 'Reference differente : arreter avant toute initialisation.' }
```

3. Reprendre le guide à `Set-Location $demoRepo` (création du venv et installation),
   puis ses étapes 4 à 12. Les scripts sont générés uniquement dans le nouveau
   dossier privé. Le nouveau cluster utilise 55441, Django 8011, Studio 3011 :
   arrêter d’abord votre ancienne démo par ses commandes propres si elle occupe
   ces ports. Ne pas changer sa configuration ou supprimer ses données.
4. Conserver les deux serveurs ouverts. Studio : **http://127.0.0.1:3011** ;
   santé backend : **http://127.0.0.1:8011/health/ready**. Créer un compte fictif
   via l’inscription normale, puis un portfolio de chaque template.

### Checklist de navigation à exécuter

- Depuis la vue d’ensemble, vérifier le nom/template/état dans la sidebar.
- Projets : ouvrir le bon portfolio ; ajouter/modifier/retirer selon le template.
  Pas de contrôle de tri ajouté. Vérifier les limites distinctes 24/6.
- Saisir un projet sans enregistrer ; passer à Apparence puis Sections, revenir
  avec Précédent/Suivant : contenu et styles doivent rester présents, sans PUT
  de design dans l’onglet Réseau. Un POST de résolution privée de médias n’est
  pas une sauvegarde et peut survenir dans l’aperçu Creative Editorial.
- Sections : ordre/visibilité contraints en v1 ; groupes fixes en Creative
  Editorial. Pas de nouvelle page ou section libre.
- Apparence : réglages par section en v1 ; palettes/couleurs/polices/reset en v3.
  Tester le raccourci Hero, une couleur au contraste insuffisant puis la corriger.
- Annuler une sortie vers la vue d’ensemble, le dashboard et la déconnexion ;
  retrouver les saisies. Tester aussi le bouton Précédent qui quitterait l’éditeur.
- Enregistrer une fois puis actualiser, quitter/revenir, déconnecter/reconnecter :
  vérifier la persistance. La sauvegarde porte sur le brouillon complet.
- Deux onglets : provoquer un conflit de version ; B doit garder sa saisie,
  afficher le conflit et ne jamais écraser A automatiquement.
- Archive : lecture seule et retour à la vue d’ensemble pour restaurer.
- Portfolio vierge : explication utile et parcours de création d’un autre
  portfolio ; aucun template appliqué automatiquement à l’instance vierge.
- UUID supprimé/étranger et session absente : refus contrôlé, pas de contexte
  d’un autre portfolio. Ne pas modifier les métadonnées en SQL pour tester une
  version inconnue : le test automatisé utilise une réponse navigateur synthétique.
- Tester Tab/Entrée, focus et rubrique active, largeur 320/390/768/1280 px, zoom
  navigateur réel Ctrl+plus à 200 %, couleurs forcées et mouvement réduit Windows.
- Vérifier les médias (import, choix, cadrage, sauvegarde et image réelle après
  réouverture). Ne pas supprimer un média protégé par une révision pour simplifier
  le test.
- La publication publique reste **indisponible**, sans bouton fictif actif.

Consigner les étapes réellement exécutées, versions, skips et erreurs, sans secrets.
Une validation Linux ne remplace pas cette recette Windows/Edge native ni une
recette avec lecteur d’écran. Aucun PUB-001, merge, PR ou déploiement n’est autorisé.

## Réserve historique et zoom

Le hook ajoute une entrée technique à URL identique pour protéger la sortie pas à
pas. Aucun brouillon ou secret n’est enregistré dans history.state. Vérifier aussi
Suivant après une sortie acceptée, puis une nouvelle sortie annulée. Les sauts
multi-entrées via le menu historique ne sont pas garantis sur tous les moteurs.
Le zoom automatisé Linux utilise 720 CSS px et DPR 2 ; valider séparément le zoom
natif 200 % sous Windows. Aucun test Windows ni lecteur d’écran n’est revendiqué.

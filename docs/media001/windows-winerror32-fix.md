# MEDIA-001 — WinError 32 : fermeture des réponses de test

Livraison **locale pour revue**, branche `feature/media-001`, parent
`4ad0e268133e4422c3188c2b8e607d376aa30b7b`. Aucun push, PR, merge, déploiement ou PUB-001.
Aucun changement du code applicatif, des contrats, d’AUTH, des bundles ou du schéma.

## Constat Windows fourni par l’utilisateur

Le correctif ACL précédent a réussi les **25/25 tests**, dont les contrôles natifs
Windows. La suite Django a exécuté 391 tests : une erreur de nettoyage
`PermissionError: [WinError 32]` dans
`MediaTests.test_revisions_retain_used_file_after_slot_removed`, trois tests ignorés,
aucune régression ACL signalée. Ce sont des résultats rapportés par l’utilisateur,
pas des exécutions Windows de l’agent. Les noms/motifs des trois skips ne sont pas
fournis ici ; ils ne sont pas déclarés réussis.

## Cause précise

Le test terminait avec :

```python
self.assertEqual(self.client.get(item['file_url']).status_code, 200)
```

`AssetFile.get` autorise le compte, vérifie taille/empreinte via
`PrivateLocalStorage.open`, puis transfère le fichier ouvert à `FileResponse`.
Django enregistre `file.close` dans les closers de cette réponse : il ne doit pas
fermer le fichier avant son streaming.

Le client de test Django enveloppe le flux dans `closing_iterator_wrapper`.
Son `finally` ferme la réponse lorsque l’itération se termine ou que le générateur
commencé est fermé. Ici, le test ne commence jamais l’itération et ne ferme pas
la réponse. Lire seulement `status_code` ne ferme donc pas `full.webp`.

La réponse et le générateur qui retient sa méthode `close` peuvent former un cycle
de références : abandonner la réponse ne garantit pas une fermeture immédiate.
Windows refuse ensuite la suppression du fichier encore ouvert, contrairement à
Linux qui permet de supprimer un fichier dont un descripteur est toujours ouvert.
Le bon résultat Linux antérieur ne prouvait donc pas l’absence de fuite.

## Audit des chemins de lecture et correction

- **Vue de téléchargement** : transfert du descripteur à `FileResponse` conforme
  au streaming Django ; pas de fermeture anticipée dans la vue.
- **Stockage** : fermeture dans le bloc d’erreur si taille ou SHA-256 incorrects ;
  en cas de succès, propriété transférée à l’appelant.
- **`files_ready`** : les fichiers retournés sont déjà utilisés dans des `with`.
- **Écritures** : `os.fdopen` est déjà entouré d’un context manager.
- **Images** : `Image.open(BytesIO(...))` est déjà entouré de `with`, sans fichier
  disque détenu par Pillow dans ces lectures de test.
- **Autres téléchargements du module de tests** : consommation complète correcte
  dans le cas nominal, mais pas de fermeture explicite si une assertion ou la
  consommation échoue. Ils utilisent maintenant le même contexte de fermeture.

La fuite identifiée est dans le **consommateur de la réponse de test**. La corriger
à cet endroit évite un changement applicatif injustifié ou une fermeture prématurée
du fichier en production.

Un context manager de test `closing_response` :

1. Ferme le générateur du client en premier, y compris en cas d’exception du
   consommateur. Un générateur déjà commencé exécute ainsi son propre `finally`.
2. Ferme ensuite la réponse si elle ne l’est pas déjà. Un générateur jamais
   commencé n’exécute pas son `finally` quand on le ferme : cette seconde étape
   est donc nécessaire.
3. Reprend pour cette fermeture le traitement de `request_finished` du client
   Django : déconnexion temporaire de `close_old_connections`, puis restauration
   dans `finally` si le receiver était connecté. Cela préserve la transaction
   `TestCase`, sans toucher aux hooks de l’application en production.

Le helper dépend de l’itérateur interne du client Django (`response._iterator`),
avec Django verrouillé par le projet. Les tests couvrent ce comportement : une
mise à jour du framework doit les réexécuter. Aucun close n’est confié au GC.
Pas de `ignore_errors`, délai, retry arbitraire, mock de fermeture ou nettoyage
supprimé. Le `TemporaryDirectory.cleanup` original reste strict.

## Régressions ajoutées

Deux tests Django exécutables sous Linux **et** Windows, sans skip de plateforme :

- **Cycle de téléchargement** : vrai stockage et vraies réponses GET/HEAD, pour
  `full` et `thumbnail`, avec flux non commencé, partiel, complet, HEAD et exception
  du consommateur (10 sous-cas). Le spy conserve les vrais fichiers retournés :
  il ne remplace ni l’autorisation, ni le calcul SHA-256, ni la fermeture.
  Après le contexte : `response.closed`, `file.closed`, refus de `file.fileno()`,
  puis renommage aller/retour du fichier sur disque. Windows refuserait ce
  renommage si le handle restait ouvert. L’état fermé est également vérifié sous
  Linux, où un renommage seul ne permettrait pas de détecter cette fuite.
- **Rejet d’intégrité** : taille fausse et SHA-256 faux, pour les deux variantes
  (4 sous-cas). Les vrais descripteurs sont capturés, et leur fermeture effective
  ainsi que le renommage sont vérifiés après le refus.

Le test initial vérifie désormais explicitement la fermeture de sa réponse avant
le contrôle des révisions et le nettoyage. Les protections de cache privé,
`Vary: Cookie`, `nosniff` et CORP restent vérifiées. Les tests existants couvrent
sessions/CSRF, inter-comptes, intégrité, quotas, concurrence, révisions et purge.
Aucun paramètre de ces protections n’est modifié.

## Vérifications Linux

Les essais intermédiaires ont permis d’écarter la fermeture directe d’une réponse
Django dans `TestCase` (signal fermant la connexion transactionnelle), de corriger
une assertion trop restrictive du nouveau test sur `Cache-Control` (les directives
anti-cache supplémentaires existantes doivent rester permises), et de traiter le
close réentrant d’un générateur partiellement lu. Ces essais ont échoué uniquement
dans des clusters jetables ; ils ne sont pas présentés comme preuves réussies.

Les preuves finales sont dans `evidence/winerror32-fix/`. La suite ciblée est
réussie : **24 tests, 21,019 s**, sans échec, erreur ou skip. Elle inclut le test
Windows signalé et les deux nouvelles régressions.

| Vérification finale Linux | Résultat |
| --- | --- |
| Django complet, cluster PostgreSQL 17.11 neuf et stockage neuf | **393 réussis**, 114,540 s, zéro échec/erreur/skip. |
| Média ciblé, autre cluster et autre stockage neufs | **24 réussis**, 21,019 s (sous-ensemble de la suite complète). |
| Intégrité/initialisation/DACL hors base | 25 exécutés : **22 réussis, 3 ignorés Windows uniquement**. |
| CMS historique, données synthétiques | **6 réussis**. |
| Référence BASE-001 | 11 fichiers historiques et 4 empreintes de fixtures inchangés. |
| Provisioning, migrations existantes, schéma et privilèges PostgreSQL | Réussis dans les clusters jetables. |
| Nouveau correctif sur Windows natif | **Non exécuté** par l’agent. |

Total final sans compter deux fois la suite ciblée : **421 réussites et 3 skips**.
Les trois tests DACL ignorés sous Linux ne sont pas les trois skips de la recette
Django Windows : ce sont deux suites et deux environnements distincts.

Les suites frontend/build/navigateur ne sont pas répétées : aucun fichier frontend,
route, vue, renderer ou contrat n’a changé. Aucune base/configuration habituelle
n’est utilisée : le runner crée et détruit son propre cluster PostgreSQL 17 et son
stockage temporaire pour chaque passage. Aucune migration nouvelle n’est ajoutée.

## Commandes Windows après récupération autorisée du correctif

Le commit reste local dans cette livraison : un `git pull` ne le récupère pas
encore. Ne pas lancer ces tests sur l’ancienne référence en pensant tester le
correctif. Après transfert/revue du commit, depuis la racine du dépôt :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
git branch --show-current
git log -1 --format="%H %s"
& .\backend\.venv\Scripts\python.exe --version
& 'C:\Program Files\PostgreSQL\17\bin\initdb.exe' --version

# Ciblé : cluster neuf + stockage neuf, aucun accès à la base habituelle.
$mediaHandleEvidence = Join-Path $env:TEMP ('media001-handles-' + [guid]::NewGuid().ToString('N'))
& .\backend\.venv\Scripts\python.exe -B scripts/verification/run_media001_isolated.py `
    --engine native --pg-bin 'C:\Program Files\PostgreSQL\17\bin' `
    --tests tests.test_media --output $mediaHandleEvidence --execute-isolated-migrations
$mediaHandleResult = $LASTEXITCODE
Get-Content (Join-Path $mediaHandleEvidence 'django-tests.log') -Encoding UTF8 -Tail 35
if ($mediaHandleResult -ne 0) { throw "Échec : conserver le journal complet dans $mediaHandleEvidence" }

# Suite complète : un autre cluster neuf et un autre stockage neuf.
$mediaFullEvidence = Join-Path $env:TEMP ('media001-full-' + [guid]::NewGuid().ToString('N'))
& .\backend\.venv\Scripts\python.exe -B scripts/verification/run_media001_isolated.py `
    --engine native --pg-bin 'C:\Program Files\PostgreSQL\17\bin' `
    --output $mediaFullEvidence --execute-isolated-migrations
$mediaFullResult = $LASTEXITCODE
Get-Content (Join-Path $mediaFullEvidence 'django-tests.log') -Encoding UTF8 -Tail 40
if ($mediaFullResult -ne 0) { throw "Échec : conserver le journal complet dans $mediaFullEvidence" }
```

Attendus structurels : 24 tests ciblés, 393 tests complets. Relever les résultats
réels, les noms/motifs des skips et confirmer l’absence de WinError 32 au nettoyage.
Ne pas élever les privilèges pour transformer un skip symlink en réussite.
Pas de `migrate` ou `Test-Foundations` sur une base existante.

## Réserve

**Windows natif indisponible ici.** La fermeture des vrais descripteurs a été
vérifiée sous Linux ; le comportement de partage/suppression Windows et la recette
PostgreSQL 17 native nécessitent encore l’exécution sur le PC. La réussite Windows
des tests ACL précédents est conservée comme preuve utilisateur distincte.
Livraison à revoir, sans validation anticipée de MEDIA-001.

## Fichiers modifiés/créés

Modifiés :

- `backend/tests/test_media.py` : context manager de fermeture, test corrigé,
  autres lectures sécurisées et deux tests de régression.
- `docs/media001/MEDIA-001-report.md` : suivi ciblé avec lien vers ce rapport.

Créés :

- `docs/media001/windows-winerror32-fix.md` : diagnostic, tests, réserve et commandes.
- `docs/media001/evidence/winerror32-fix/media-targeted.log`.
- `docs/media001/evidence/winerror32-fix/django-tests.log`.
- `docs/media001/evidence/winerror32-fix/integrity.log`.
- `docs/media001/evidence/winerror32-fix/legacy-cms.log`.
- `docs/media001/evidence/winerror32-fix/historical-reference.log`.
- `docs/media001/evidence/winerror32-fix/runtime-privileges.log`.
- `docs/media001/evidence/winerror32-fix/isolated-environment.json`.

Le commit correctif conserve comme parent la référence approuvée `4ad0e268…`.
Aucun fichier de stockage, vue, configuration AUTH ou contrat API n’est modifié.
Les répertoires `.local/`, données usuelles et bundles restent intacts.

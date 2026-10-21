# MEDIA-001 — Correctif DACL Windows pour revue

Statut : **correctif proposé, validation Windows non exécutée par l’agent**.
Branche `feature/media-001`, parent `04746de424280e2308bb846120dc7720d325cb52`.
Aucun push, PR, merge, déploiement ou travail PUB-001.

## Diagnostic et niveau de preuve

La recette Windows rapportée par l’utilisateur a exécuté 389 tests Django en
460,270 s : 10 échecs, 6 erreurs, 3 ignorés. Les tracebacks complets ne sont pas
fournis. Il serait incorrect d’affirmer avoir analysé individuellement ces seize
résultats ou de déclarer que ce correctif les résout tous.

Une incompatibilité précise est démontrable à partir des deux sources :

- CPython 3.13.5, `os_mkdir_impl`, utilise pour `mkdir(mode=0o700)` la DACL
  `D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;OW)`.
  Source : <https://github.com/python/cpython/blob/v3.13.5/Modules/posixmodule.c>.
- `OW` est **OWNER RIGHTS**, SID `S-1-3-4`, et non CREATOR OWNER `S-1-3-0`.
  Source : <https://learn.microsoft.com/en-us/windows/win32/secauthz/well-known-sids>.
- L’ancien `verify_windows_acl` n’autorise que le SID courant, SYSTEM et
  Administrateurs. Il refuse donc cette ACE pourtant privée lorsque son
  propriétaire est autorisé. Le cas CPython est reproduit dans les tests de
  politique, sans prétendre reproduire une DACL native sous Linux.
- `TemporaryDirectory` crée son dossier en mode 0700. Le setup de `MediaMixin`
  l’utilise directement : sa DACL est explicite et protégée, pas simplement
  une copie des permissions héritées du stockage parent.
- L’initialiseur et `private_directory` utilisent également 0700 puis
  `icacls /inheritance:r /grant:r`. Retirer l’héritage et remplacer les grants
  utilisateur/SYSTEM ne retire pas l’ACE **explicite** OWNER RIGHTS. Réinitialiser
  les mêmes grants ne corrigerait donc pas le prédicat erroné du vérificateur.

Cette incompatibilité explique le refus 503 sur un dossier CPython privé typique.
La confirmation de la DACL exacte sur le PC reste à obtenir par les tests natifs.

| Observation | Attribution possible et limite |
| --- | --- |
| 503 `media_unavailable`, message des permissions Windows | Compatible directement avec le rejet de OWNER RIGHTS ; cause démontrée dans les sources, à confirmer sur le PC. |
| Assertions attendant 201 | Cascade attendue si elles utilisent ce stockage ; `MediaMixin.asset()` effectue explicitement cette assertion. |
| Accès à `response.json()['results']` après import | Plusieurs tests le font directement ; un 503 peut produire une erreur secondaire de clé manquante. Ne pas attribuer les six erreurs à ce cas sans leurs traces. |
| Exceptions depuis `import_images` | Le test des slots complets appelle directement ce service ; le contrôle DACL peut lever `PortfolioProblem` avant toute écriture. Attribution individuelle encore ouverte. |
| Total dix échecs/six erreurs | Analyse exhaustive **ouverte**, attente du journal Windows complet demandé. |
| Trois tests ignorés rapportés sous Windows | Noms et motifs non fournis ; ni réussis ni assimilés aux trois nouveaux tests Windows ignorés sous Linux. |

## Correction et invariants

`backend/modules/media/windows_acl.py` sépare l’inspection DACL de sa politique
pure et testable, sans dépendance nouvelle. L’inspection utilise les SID directement
(`GetAccessRules` / `GetOwner`) plutôt que des noms de groupes localisés.

1. La DACL doit être présente et contenir des ACE Allow ; une DACL nulle ou un
   rapport illisible/incomplet est refusé.
2. Le propriétaire doit être le SID courant, SYSTEM ou Administrateurs, même en
   l’absence d’ACE OWNER RIGHTS. Un propriétaire non autorisé pourrait modifier
   la DACL : il n’est jamais accepté.
3. Chaque ACE Allow doit viser une de ces trois autorités, ou OWNER RIGHTS avec
   ce propriétaire préalablement contrôlé. Aucune autre identité n’est autorisée,
   y compris Everyone, Authenticated Users, Users et CREATOR OWNER.
4. Les Allow hérités sont contrôlés comme les explicites. Aucune exception pour
   les ACE InheritOnly ; aucune tentative d’annuler un Allow public avec un Deny.
5. Aucun droit n’est ajouté et aucune DACL n’est réécrite à l’exécution. Les
   autorités SYSTEM/Administrateurs étaient déjà admises par le contrôle initial.
6. Inspection DACL uniquement, aucun accès SACL, aucun `Set-Acl`, privilège
   `SeSecurityPrivilege`, contournement d’ExecutionPolicy ou besoin d’élévation.
7. Transport `-EncodedCommand` UTF-16LE et résultat JSON UTF-8 strict. Le chemin
   passe uniquement par variable d’environnement, jamais interpolé dans le script.
   Ce durcissement n’est pas présenté comme la cause prouvée de la recette.
8. Erreurs d’inspection, délai dépassé et résultats invalides : refus fermé 503
   générique, sans chemin, SID ni erreur PowerShell dans la réponse publique.
   Le cache existant de huit inspections réussies est conservé ; aucun résultat
   négatif n’est mis en cache. Les modifications externes d’ACL en cours de
   processus nécessitent toujours un redémarrage/une invalidation de ce cache.

Le stockage Unix, les quotas, verrous, contrôles des images, révisions, purge,
contrats API, bundles et modèles ne changent pas. Aucune migration n’est ajoutée.
Les bases de recette sont exclusivement des clusters PostgreSQL 17 neufs et
jetables ; les migrations existantes sont exécutées uniquement dans ces clusters.

## Tests ajoutés

Sept tests hors base de politique/transport : OWNER RIGHTS, propriétaires système
admis, propriétaire tiers refusé, principaux publics/inconnus refusés, rapports
nuls/malformés, encodage/chemin non ASCII et erreurs/timeout.

Trois tests **Windows + Python 3.13 uniquement**, sur dossiers temporaires neufs :
création 0700 et héritage, initialisation réelle et sous-dossier `TemporaryDirectory`,
refus d’un grant Everyone explicite puis hérité, refus même accompagné d’un Deny.
Le test négatif ne contient aucune donnée utilisateur ; le grant est supprimé dans
`finally`. Ils ne sont pas annoncés réussis sous Linux.

Deux `SimpleTestCase` Django vérifient le maintien du 503 générique sur toutes les
pannes d’inspection et le contrat existant de cache après succès.

## Résultats Linux

Voir `evidence/windows-acl-fix/` pour les journaux. La suite finale complète inclut
les deux nouveaux tests Django ; les trois tests de DACL natives restent ignorés
sous Linux. Les suites frontend/build/navigateur ne sont pas répétées : aucun
fichier frontend, renderer ou contrat n’est modifié. Cela ne vaut pas recette
navigateur Windows.

| Vérification Linux exécutée | Résultat |
| --- | --- |
| Django complet, cluster PostgreSQL 17.11 neuf, stockage neuf | **391 réussis**, 109,996 s, aucun échec/erreur/skip. |
| Intégrité/initialisation/politique DACL hors base | 25 exécutés : **22 réussis, 3 ignorés Windows uniquement**. |
| CMS historique sur données synthétiques | **6 réussis**. |
| Référence BASE-001 | 11 fichiers historiques et 4 empreintes de fixtures inchangés. |
| Provisioning, migrations existantes, contrôle de schéma et privilèges | Réussis dans le seul cluster jetable du runner. |
| Contrôles DACL natifs Windows et recette PostgreSQL Windows | **Non exécutés** par l’agent. |

Total des suites finales : 419 réussites et 3 tests ignorés, sans compter deux
fois les deux nouveaux tests Django également exécutés hors base pendant la mise
au point. Le premier passage de 389 tests était réussi avant leur découverte ;
la preuve conservée est le passage final de 391 tests. Le conteneur et le
stockage temporaires de chaque passage ont été supprimés par le runner.

## Fichiers livrés

Modifiés :

- `backend/modules/media/storage.py` : délégation à l’inspection privée et mapping
  fermé des erreurs ; aucune autre opération de stockage modifiée.
- `docs/media001/MEDIA-001-report.md` : suivi de la recette et lien vers ce correctif.
- `docs/media001/windows.md` : orientation vers la procédure corrective.

Créés :

- `backend/modules/media/windows_acl.py` : politique DACL et inspection SID/owner.
- `backend/tests/test_media_acl.py` : contrat d’erreur/cache.
- `scripts/verification/tests/test_media_windows_acl.py` : politique, transport et
  intégration native conditionnelle.
- `docs/media001/windows-acl-fix.md` : ce rapport et les commandes PowerShell.
- `docs/media001/evidence/windows-acl-fix/django-tests.log`.
- `docs/media001/evidence/windows-acl-fix/integrity.log`.
- `docs/media001/evidence/windows-acl-fix/legacy-cms.log`.
- `docs/media001/evidence/windows-acl-fix/historical-reference.log`.
- `docs/media001/evidence/windows-acl-fix/runtime-privileges.log`.
- `docs/media001/evidence/windows-acl-fix/isolated-environment.json`.

Aucun initialiseur ne doit supprimer aveuglément OWNER RIGHTS : la correction
est dans son interprétation conditionnelle, pas dans un retrait du contrôle.
Aucun fichier AUTH, CMS, `.local/`, bundle, migration ou dépendance n’est modifié.

## Installation du correctif sans publication GitHub

Le commit est local conformément à l’interdiction de publication. **Un fetch ou
pull ne récupère donc pas ce correctif.** Un patch Git de la livraison est fourni
séparément pour transfert sur le PC. Après téléchargement effectif de ce patch,
avec le nom `media-001-windows-acl.patch`, exécuter :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
if (git status --porcelain) { throw 'Préserver les modifications locales avant de continuer.' }
git switch feature/media-001
if ($LASTEXITCODE -ne 0) { throw 'Changement de branche échoué.' }
if ((git rev-parse HEAD) -ne '04746de424280e2308bb846120dc7720d325cb52') {
    throw 'Référence différente : ne pas appliquer le patch sans revue.'
}
$mediaAclPatch = Join-Path $env:USERPROFILE 'Downloads\media-001-windows-acl.patch'
if (-not (Test-Path -LiteralPath $mediaAclPatch)) { throw 'Transférer le patch avant de continuer.' }
git apply --check $mediaAclPatch
if ($LASTEXITCODE -ne 0) { throw 'Patch incompatible, arrêter sans forcer.' }
git am $mediaAclPatch
if ($LASTEXITCODE -ne 0) { throw 'Application interrompue : examiner git status, ne pas forcer.' }
git log -1 --format="%H %s"
```

`git am` crée le commit local Windows (son SHA peut différer à cause des métadonnées
du committer). Aucun push n’est nécessaire pour tester. Ne pas appliquer deux fois.

## Validation Windows exacte, sans configuration/base habituelle

Depuis cette racine, avec les dépendances MEDIA-001 verrouillées déjà installées :

```powershell
py -3.13 --version
& 'C:\Program Files\PostgreSQL\17\bin\initdb.exe' --version
& .\backend\.venv\Scripts\python.exe -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dépendances Python incohérentes.' }

# Sans base : les trois tests de DACL natives doivent réellement s’exécuter ici.
& .\backend\.venv\Scripts\python.exe -B -m unittest discover `
    -s scripts/verification/tests -v
if ($LASTEXITCODE -ne 0) { throw 'Contrôles DACL/intégrité échoués : conserver le journal.' }

# Cluster PostgreSQL 17 neuf, port dynamique et stockage temporaire neufs.
$mediaAclEvidence = Join-Path $env:TEMP ('media001-acl-' + [guid]::NewGuid().ToString('N'))
& .\backend\.venv\Scripts\python.exe -B scripts/verification/run_media001_isolated.py `
    --engine native --pg-bin 'C:\Program Files\PostgreSQL\17\bin' `
    --output $mediaAclEvidence --execute-isolated-migrations
$mediaAclResult = $LASTEXITCODE
if (Test-Path (Join-Path $mediaAclEvidence 'django-tests.log')) {
    Get-Content (Join-Path $mediaAclEvidence 'django-tests.log') -Encoding UTF8 -Tail 40
}
Write-Host "Résultats de recette : $mediaAclEvidence"
if ($mediaAclResult -ne 0) {
    throw 'Recette échouée : conserver le journal Django complet pour analyse des traces.'
}
Get-Content (Join-Path $mediaAclEvidence 'isolated-environment.json') -Encoding UTF8
```

Pas de `migrate`, `Initialize-Database` ou `Test-Foundations` sur l’environnement
habituel ; pas de service PostgreSQL arrêté/redémarré ; pas de lancement admin pour
masquer un skip symlink. Le runner supprime uniquement ses propres ressources.
Les nouveaux tests Django portent le total attendu à 391, mais le nombre de skips
Windows doit être relevé réellement, avec leurs noms et motifs.

## Réserves et revue

- Windows/PowerShell 5.1 natifs indisponibles dans l’environnement Linux : DACL
  réelle, transport PowerShell, refus publics et recette PostgreSQL native restent
  à exécuter sur le PC. Les mocks Linux ne remplacent pas ces preuves.
- Journal initial complet requis pour classer exhaustivement six erreurs et dix
  échecs. Tout résultat restant après correction doit être analysé séparément.
- Les trois skips natifs de la suite hors base Linux sont des limitations
  d’environnement, pas des réussites. Les skips Windows initiaux restent distincts.
- Livraison pour revue, **pas une validation de MEDIA-001**. Aucune publication
  ni étape PUB-001 n’est entreprise.

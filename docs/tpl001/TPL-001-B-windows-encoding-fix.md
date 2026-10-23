# TPL-001.B — Correctif UTF-8 des tests Windows

Date : 19 octobre 2026 (Africa/Douala). Branche : `fix/tpl-001-b-windows-encoding`, issue de `730384b`.

## Résultat Windows rapporté par l’utilisateur

Sur `730384b`, Test-Foundations.ps1 a atteint la suite Django : **74 tests, 72 réussis, 1 erreur, 1 ignoré**. Les contrôles historiques et PostgreSQL précédents ont réussi. L’erreur UnicodeEncodeError concerne U+0660 dans test_unknown_schema_and_experience_rejected, lors d’une écriture texte utilisant implicitement cp1252.

**Windows n’est pas encore validé sur le correctif.** Les contrôles situés après l’arrêt du script ne sont pas présumés exécutés.

## Correction et périmètre inspecté

- `backend/tests/test_templates.py` : encoding="utf-8" explicite pour les **6 écritures et 8 lectures** texte. Les lectures doivent aussi interpréter correctement les fichiers UTF-8 sous Windows.
- `scripts/verification/browser_tpl001.py` : même encodage explicite pour l’écriture JSON des preuves.
- `apps/studio/test/templates.test.mjs` : lectures Node déjà explicitement utf8 ; aucune correction nécessaire.

Les ensure_ascii=False existants et le caractère Unicode réel dans la version invalide restent présents. Aucune assertion, politique de version, sécurité, logique métier ou condition de skip n’est modifiée. Les écritures modifiées du test portent uniquement sur ses copies temporaires ; les bundles, empreintes, contrats et preuves de livraison existants ne changent pas.

Fichiers documentaires mis à jour : ce suivi et le rapport B. Aucun ajout de dépendance, migration, intervention sur une base réelle, CMS historique, `.local/` ou fusion.

## Vérifications exécutées dans l’environnement Linux

- Suite TPL ciblée : **17/17 réussis**, sans erreur ni skip.
- Reproduction du défaut : exécution du test original de `730384b` en imposant cp1252 aux ouvertures texte Path sans encodage explicite ; UnicodeEncodeError reproduite.
- Même simulation avec la suite TPL corrigée : **17/17 réussis**, sans erreur ni skip. Le patch temporaire de Path.open respecte les encodages explicitement fournis ; aucune variable PYTHONUTF8 n’est utilisée pour contourner le défaut.
- Audit AST : tous les appels read_text/write_text des deux fichiers Python TPL inspectés déclarent UTF-8. Diff de contrôle : runtime, contrats, bundles et preuves historiques inchangés. Vérification Git des espaces réussie.

La simulation cp1252 vérifie le défaut d’encodage ; **elle ne constitue pas une exécution Windows native**. Les deux passages ciblés ne représentent pas 34 tests distincts. La suite complète PostgreSQL/navigateur n’est pas relancée pour ce changement limité aux E/S des tests ; les preuves Linux antérieures restent conservées.

## Symlink : limitation distincte

`test_symlink_outside_bundle_root_rejected` a été **IGNORÉ sur le PC Windows**, car la création de symlinks y est indisponible. Ce résultat n’est pas un succès et ne valide pas le refus d’un symlink sur ce PC. Le test et la protection du registre restent inchangés ; le même test passe sous Linux où les symlinks sont disponibles. Une validation Windows future avec cette capacité restera un suivi séparé ; ne pas supprimer le skip ni déclarer le contrôle réussi artificiellement.

## Récupérer et relancer sur Windows

Conserver toute modification locale et arrêter les terminaux Django/Next avant le changement de branche ; ne pas forcer Git si l’arbre contient des changements incompatibles. Depuis PowerShell :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
git status --short
git fetch origin
git switch fix/tpl-001-b-windows-encoding
git log -1 --format="%h %s"

$env:SAAS_CONFIG_FILE = Join-Path (Get-Location) 'infra\env\port001.validation.local.json'
& .\backend\.venv\Scripts\python.exe -B backend/manage.py test tests.test_templates --settings=config.settings.test --noinput --verbosity 2
& .\scripts\windows\Test-Foundations.ps1
```

La première commande de tests est ciblée ; la seconde relance toute la validation avec la configuration synthétique séparée déjà préparée, sans migration de base réelle. Ne pas substituer une configuration réelle. Le commit à comparer est indiqué dans le message de livraison du correctif.

Si la capacité symlink reste indisponible et qu’aucune autre erreur n’apparaît, on attend **16 réussis + 1 ignoré** pour la suite TPL, puis **73 réussis + 1 ignoré** pour la suite Django complète de 74 tests. Ce sont des résultats attendus, pas encore observés sur le correctif Windows. Consigner séparément le résultat des contrôles npm/typecheck/build exécutés ensuite et tout nouvel échec.

C/D/E restent non autorisées jusqu’à revue de B.

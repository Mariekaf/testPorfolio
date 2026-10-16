# Référence de compatibilité — BASE-001

Point d'entrée des livrables. Le CMS historique n'est pas modifié. CORE-001 nécessite une nouvelle validation et n'est pas commencé.

- [Rapport d'exécution et acceptation](BASE-001-report.md)
- [Inventaire des fonctionnalités et fonctions](feature-inventory.md)
- [Matrice de compatibilité et limites connues](feature-matrix.md)
- [Carte des données et invariants](legacy-data-map.md)
- [Empreintes des 11 fichiers historiques](legacy-source-manifest.json)
- [Sauvegarde privée et restauration isolée Windows](../runbooks/legacy-backup-windows.md)
- [Préparation PostgreSQL Docker ou Windows natif pour CORE-001](../runbooks/core001-windows-postgresql-options.md)
- [Fixtures synthétiques](../../tests/fixtures/base001/README.md)
- [Tests historiques](evidence/existing-tests.txt), [navigateur](evidence/browser-tests.txt), [empreintes/fixtures](evidence/reference-check.txt), [syntaxe JavaScript](evidence/javascript-syntax.txt)

## Reproduire sans dépendance ajoutée

Sous Windows PowerShell, depuis le dépôt :

```powershell
$oldBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
    $env:PYTHONDONTWRITEBYTECODE = '1'
    py -X utf8 -B -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Échec des tests historiques' }
    node --check .\script.js
    if ($LASTEXITCODE -ne 0) { throw 'Échec syntaxe script.js' }
    node --check .\admin.js
    if ($LASTEXITCODE -ne 0) { throw 'Échec syntaxe admin.js' }
    py -X utf8 -B .\scripts\verification\check_base001.py
    if ($LASTEXITCODE -ne 0) { throw 'Échec vérification BASE-001' }
} finally {
    $env:PYTHONDONTWRITEBYTECODE = $oldBytecode
}
```

Le vérificateur compare les fichiers historiques à leurs empreintes, contrôle la fixture et importe les fonctions de validation sans initialiser le CMS. Il échouera volontairement si un fichier historique change après BASE-001 : ne pas recalculer la référence pour masquer cet écart.

## Vérifications navigateur optionnelles

Le script `scripts/verification/browser_base001.py` utilise Playwright et Chromium déjà disponibles dans l'environnement d'exécution de ce ticket. Aucun paquet n'a été installé ni ajouté aux dépendances du CMS. Il ne fait pas partie du démarrage normal de l'application et nécessite ces outils si on souhaite le rejouer ailleurs.

Commande exécutée sur Linux :

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/verification/browser_base001.py --chromium /usr/bin/chromium
```

Sur un poste possédant déjà les outils, fournir le chemin de son exécutable Chromium avec `--chromium`. Le script refuse implicitement les tests sans moteur disponible plutôt que d'annoncer des succès non exécutés. Il utilise une copie des fixtures en répertoire temporaire, un port aléatoire, deux contextes navigateur et des identifiants générés éphémères ; il ne consulte pas les données utilisateur. Il ne contacte pas les URLs externes de démonstration.

Les tests ne constituent pas une migration ni une sauvegarde du poste Windows de l'utilisateur. Aucun résultat Linux ou cp1252 simulé ne doit être présenté comme une validation Windows native.

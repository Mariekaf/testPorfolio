# CORE-001 — Suivi de validation Windows native

Branche de corrections : `fix/core-001-windows`, issue de `51128c6` (`arch/core-001`). AUTH-001 n'a pas commencé. Aucune donnée réelle, aucun secret, aucun média ou fichier d'authentification utilisé dans les tests ou ajouté aux commits.

## Éléments confirmés par les sorties du poste utilisateur

| Étape | Résultat observé |
|---|---|
| PowerShell | 5.1 |
| Git | 2.49.0.windows.1 |
| Python | 3.13.5, 64 bits |
| Node / npm | 24.22.0 / 11.14.0 |
| PostgreSQL natif | Serveur 17.6 Windows x64, port local 5432 |
| Configuration PostgreSQL | listen_addresses=localhost, password_encryption=scram-sha-256 |
| pg_hba_file_rules | Six règles locales/loopback SCRAM, sans erreur ni trust |
| Clone | arch/core-001, commit 51128c6, état Git propre initialement |
| Venv/dépendances | Installation avec --require-hashes réussie ; pip check sans incohérence |
| Initialisation native | Configuration générée, ignorée par Git ; script terminé sans erreur |
| Base et migrations | Rôles provisionnés, toutes migrations initiales OK ; dernière sortie du vérificateur DB fournie partiellement |
| Backend | /health/live et /health/ready retournent status=ok |
| Studio | npm ci réussi ; Next dev répond 200 ; bouton affiche backend et PostgreSQL disponibles |
| Suite Test-Foundations | Arrêt au premier contrôle : Checksum mismatch: .gitignore ; tests suivants non exécutés à ce stade |

Ces observations proviennent de l'utilisateur sur son PC, pas d'une exécution distante par l'agent. Aucun transcript personnel n'est recopié.

## Correction du contrôle d'intégrité

Cause reproduite ici : clone Git propre avec `core.autocrlf=true`, index LF et fichiers de travail CRLF. L'ancien vérificateur comparait leurs octets directement aux empreintes LF enregistrées, ce qui provoque exactement le message reçu, sans modification sémantique des sources.

Correction limitée à l'outillage :

- Comparaison SHA-256 brute en premier.
- En cas d'écart, uniquement pour `.gitignore` et les extensions texte connues `.py/.md/.html/.css/.js/.json` : vérifier UTF-8 strict et remplacer CRLF par LF en mémoire avant comparaison au même hash attendu.
- Aucun autre nettoyage : pas de suppression d'espaces, BOM, CR isolés ou modification de l'encodage.
- Aucune normalisation des PNG ou extensions inconnues.
- Confinement des chemins préservé.
- Manifestes historiques et fixtures existantes inchangés.
- Aucun fichier du CMS historique modifié ; aucune configuration PostgreSQL ou donnée privée changée par le correctif.

La cause exacte sur le poste sera corroborée par `git status --short` et `git ls-files --eol -- .gitignore` lors de la reprise. Si le fichier a réellement été édité, le correctif continuera de le refuser.

## Vérifications de la correction réalisées sous Linux

- 12 tests d'intégrité : LF, CRLF, Unicode, mix LF/CRLF et refus des changements de contenu/espaces/BOM/CR isolé/UTF-8 invalide/binaire/extensions inconnues/chemins sortants.
- Clone propre CRLF : échec de l'ancien vérificateur reproduit, puis succès du vérificateur corrigé pour les 11 sources et 4 fichiers de fixture.
- Même clone avec ajout réel dans `.gitignore` : échec préservé.
- Vérificateur sur les fichiers LF courants : succès.
- Six tests historiques : réussis après correction.

Les tests supplémentaires sont inclus dans Test-Foundations.ps1 et la CI. Aucune installation de dépendance supplémentaire.

## Reste à exécuter sur Windows

1. Conserver les deux serveurs et les fichiers privés ; vérifier l'état Git et les fins de ligne.
2. Récupérer la branche de correction sans reset, clean ni écrasement de modifications locales.
3. Relancer Test-Foundations.ps1 en entier.
4. Examiner chaque résultat : référence, intégrité, six tests historiques, PostgreSQL réel, contrôles Django, douze tests Django, trois tests de contrats, TypeScript et build.
5. Consigner les éventuels nouveaux problèmes spécifiques à Windows sur la même branche.

**Validation Windows globale encore ouverte.** Le succès du navigateur ne remplace pas celui de la suite complète. Ne pas commencer AUTH-001 avant sa validation par l'utilisateur.

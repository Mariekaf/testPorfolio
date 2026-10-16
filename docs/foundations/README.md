# CORE-001 — Socle parallèle

- [Rapport et statut d'acceptation](CORE-001-report.md)
- [Démarrage Windows, PostgreSQL natif ou Docker](../runbooks/core001-windows-development.md)
- [Versions et justification des dépendances](dependency-versions.md)
- [Liste des fichiers du ticket](files.txt)
- Preuves dans `evidence/`.

Le CMS historique et `.local/` ne sont pas modifiés. Le socle n'ajoute que configuration, modèle utilisateur initial, contrôles de santé, studio technique et tests. Pas d'API métier, migration réelle, modèle de portfolio ou animation. AUTH-001 attend une nouvelle validation.

## Parcours Linux équivalent vérifié

Python 3.13 et Node 24 requis. Depuis la racine :

```sh
python3.13 -m venv backend/.venv
backend/.venv/bin/python -m pip install --require-hashes -r backend/requirements/development.txt
backend/.venv/bin/python -B scripts/development/initialize_development.py --mode docker
docker compose --env-file infra/env/development.local.env -f infra/compose.yaml up -d --wait postgres
backend/.venv/bin/python -B scripts/development/provision_database.py
backend/.venv/bin/python -B backend/manage.py migrate --settings=config.settings.migration --noinput
backend/.venv/bin/python -B scripts/verification/verify_core_database.py
npm ci --ignore-scripts
```

Pour un serveur PostgreSQL Linux déjà installé, le mode `native` utilise la même connexion TCP et demande un mot de passe administrateur ; aucune installation de service n'est réalisée par l'outil. Dans l'environnement de validation, un venv Python 3.13 isolé a été placé dans `/tmp` avec uv plutôt que dans backend ; les mêmes fichiers verrouillés ont été utilisés.

Les commandes de tests Django doivent être exécutées depuis `backend/` : lancer `manage.py test tests` depuis la racine peut découvrir à la place les tests historiques homonymes. Cette distinction est appliquée dans le script Windows et la CI.

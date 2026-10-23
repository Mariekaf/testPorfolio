# Versions résolues et justification — CORE-001

Vérification des métadonnées de registres le 16 octobre 2026, puis installations/builds réels. Les versions sont celles disponibles et téléchargées, pas des numéros supposés à partir de la date.

| Élément | Version | Justification / preuve |
|---|---|---|
| Python | 3.13.5 exécuté | Baseline 3.13 d'ARCH-002 ; pyproject refuse les autres mineures |
| Django | 5.2.18 | Correctif LTS 5.2, plutôt que dernier majeur 6.1 ; métadonnée Python >=3.10 incluant 3.13 |
| Django REST Framework | 3.18.3 | Métadonnée Django >=5.2 ; tests avec le couple réel |
| Psycopg + binary | 3.3.6 | Pilote PostgreSQL, roue CPython 3.13 Windows disponible ; pas de compilation C à imposer |
| jsonschema | 4.26.0, développement | Validation des contrats JSON et des exemples dans les tests |
| PostgreSQL | 17.11 exécuté | Image série 17, UTF-8 et connexion/permissions vérifiés |
| Node | 24.19.0 exécuté | Ligne LTS retenue, engine >=24 <25 |
| npm | 11.9.0 exécuté | packageManager et lockfile v3 ; engine >=11 <12 |
| Next.js | 16.4.2 | Node >=20.9 ; peer React 19 accepté ; build et proxy testés |
| React / react-dom | 19.3.1 | Même version ; peer react-dom ^19.3.1 satisfait |
| TypeScript | 5.9.3 | Version stable de la ligne 5, compatible avec Next ; pas d'adoption non nécessaire du majeur 7 |
| @types/react / react-dom | 19.3.0 | Versions correspondantes ; peer respecté |
| @types/node | 24.19.2 | Types de la ligne Node 24 |
| uv | 0.12.23, outil de résolution | Utilisé dans l'environnement, pas dépendance d'exécution du projet |

Sources : `https://pypi.org/pypi/<package>/<version>/json` et `https://registry.npmjs.org/<package>/<version>` ; versions exactes et dépendances transitives conservées dans les locks. LTS Django : https://www.djangoproject.com/download/ ; Node : https://nodejs.org/en/about/previous-releases . Les conditions de compatibilité ont aussi été vérifiées par le test et la compilation, pas seulement les métadonnées.

## Verrouillage

- `backend/requirements/runtime.in` et `development.in` contiennent les dépendances directes exactes.
- Les `.txt` sont compilés avec uv `--python-version 3.13 --universal --generate-hashes`. Ils incluent tzdata sous Windows et les hashes des artefacts compatibles.
- Installer avec `python -m pip install --require-hashes -r ...`, sans désactiver TLS ou les contrôles.
- `package-lock.json` verrouille l'arbre npm et ses intégrités ; `npm ci --ignore-scripts` reproduit l'installation.
- `infra/compose.yaml` utilise `postgres:17@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3`. Le digest verrouille le contenu malgré le tag mobile.
- La disponibilité des roues de développement Windows x64 a été vérifiée par téléchargement ciblé CPython 3.13 et hashes, tzdata inclus. L'évaluation des marqueurs pip dépend aussi de l'hôte : la vérification croisée a utilisé Python 3.13 et rendu le marqueur Windows explicite dans un fichier temporaire. Ce n'est pas une exécution Windows.

Commandes de régénération réservées à une mise à jour intentionnelle, suivie de tous les tests :

```sh
uv pip compile backend/requirements/runtime.in --python-version 3.13 --universal --generate-hashes --output-file backend/requirements/runtime.txt
uv pip compile backend/requirements/development.in --python-version 3.13 --universal --generate-hashes --output-file backend/requirements/development.txt
```

Aucune dépendance GSAP, Three.js, Redis, Celery, drag-and-drop, texte riche ou authentification externe n'est ajoutée. Le serveur public de portfolios, les blocs métier et les rôles multi-tenant ne sont pas simulés dans ce socle.

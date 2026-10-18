# PORT-001 — Préparation du nouveau périmètre

Date : 18 octobre 2026. **Non livré : ARCH-002 à fournir avant la conception des modèles.**

Le nouveau ticket « Gestion multi-portfolios, dashboard designer et préparation des templates » remplace le périmètre provisoire ci-dessous. L’historique distant `feature/port-001` jusqu’à `669d573`, issu d’AUTH-001 `2ff4fc1`, a été conservé. Aucune fusion ni réécriture.

L’[audit préalable et le plan de reprise](docs/reviews/PORT-001-preflight.md) détaillent les écarts, les étapes et le blocage. Le propriétaire direct User et le slug global de l’ancienne implémentation ne sont pas conformes au nouveau ticket. Aucun modèle Account n’a été inventé sans le contrat approuvé.

Vérifications Linux réalisées pendant cette préparation : **64 tests existants réussis**, TypeScript/build, vraie connexion PostgreSQL 17.11, migrations existantes sur base fraîche, rôles, santé backend et accès anonyme contrôlés. Le CMS historique et `.local/` sont préservés. Aucun parcours du nouveau PORT-001 ni test Windows du nouveau périmètre n’est déclaré réussi.

Fichiers de cette préparation : `PORT-001-report.md` (actualisé), `docs/reviews/PORT-001-preflight.md` (créé). Aucun changement fonctionnel.

## Historique — rapport provisoire du 16 octobre 2026

Les déclarations de non-exécution ci-dessous décrivent la session initiale de création de l’ancienne implémentation. Les tests de préparation du 18 octobre sont consignés ci-dessus ; ils ne valent pas acceptation du nouveau ticket.

### Ancien périmètre provisoire

Date : 16 octobre 2026. Branche : `feature/port-001`, dérivée de `feature/auth-001`. Aucun merge effectué.

## Implémenté
- Application Django `modules.portfolios`, migration initiale et modèle propriétaire/slug/type/brouillon/privé/suppression logique.
- API privée `/api/v1/portfolios/` : liste paginée, création, détail, modification, suppression logique et duplication.
- Filtrage par propriétaire et rejet des champs non autorisés. Brouillon et privé imposés par modèle et contraintes SQL.
- Composant React de gestion sur le dashboard existant, appels API avec CSRF et session AUTH-001.
- Tests Django synthétiques pour CRUD, propriétaire, isolation, anonymat et duplication.

## Vérifications NON exécutées
- Aucune commande Django, PostgreSQL, TypeScript, Next.js ni navigateur n'a été exécutée dans cette session : les modifications ont été effectuées directement via l'API GitHub.
- La migration et les nouveaux tests restent à valider sur une base PostgreSQL jetable avant la base de développement.
- La compatibilité Windows native et la non-régression du CMS restent à vérifier.

## Limites et suite
- La liste frontend affiche la première page de 12 portfolios ; navigation de pagination et détails dédiés à compléter.
- Pas de publication publique, d'éditeur visuel, ni de partage entre utilisateurs.
- Vérifier le comportement des erreurs d'API, l'accessibilité, les tests multi-utilisateurs et les collisions concurrentes.
- Ne pas fusionner avant tests, corrections et revue.

## Commandes de validation suggérées
À exécuter dans l'environnement Windows déjà configuré, après mise à jour de la branche, avec une base de test isolée :

```powershell
git fetch origin
git switch feature/port-001
git pull --ff-only origin feature/port-001
& .\backend\.venv\Scripts\python.exe -B backend/manage.py makemigrations --check --dry-run --settings=config.settings.test
& .\backend\.venv\Scripts\python.exe -B backend/manage.py test tests --settings=config.settings.test --noinput
npm.cmd run build --workspace @portfolio/studio
```

Ne pas exécuter une migration sur la base de développement avant vérification de sa sauvegarde et des résultats sur base jetable.

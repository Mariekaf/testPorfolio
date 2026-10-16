# AUTH-001 — Validation Windows native, sans Docker

Statut : **à exécuter sur Windows**. Les résultats Linux ne valident pas les ACL Windows ni PowerShell 5.1. Prérequis CORE-001 conservés : Python 3.13 x64, Node 24, npm 11, PostgreSQL 17 natif en service sur 5432. Utiliser une console PowerShell normale, dans le clone SaaS séparé du CMS historique.

## 1. Récupérer la branche

Arrêter Django/Next avec Ctrl+C dans leurs terminaux. Vérifier que `git status --short` ne contient pas de modifications à écraser.

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
git status --short
git fetch origin
git switch --track origin/feature/auth-001
# Si la branche existe déjà : git switch feature/auth-001
# Puis : git pull --ff-only origin feature/auth-001
py -3.13 --version
node --version
npm.cmd --version
& 'C:\Program Files\PostgreSQL\17\bin\pg_isready.exe' -h 127.0.0.1 -p 5432
```

Ne pas utiliser `reset --hard`, effacer `.local/` ou recopier les données historiques. Le fichier privé `infra/env/development.local.json` existant est conservé. Aucun nouveau secret/dependency n’est nécessaire.

## 2. Dépendances, boîte privée et migration SaaS

```powershell
& .\backend\.venv\Scripts\python.exe -m pip install --require-hashes -r .\backend\requirements\development.txt
& .\backend\.venv\Scripts\python.exe -m pip check
npm.cmd ci --ignore-scripts
& .\scripts\windows\Initialize-Mailbox.ps1
git check-ignore infra/env/development.local.json
& .\backend\.venv\Scripts\python.exe -B backend/manage.py migrate --plan --settings=config.settings.migration
& .\backend\.venv\Scripts\python.exe -B backend/manage.py migrate --settings=config.settings.migration --noinput
& .\backend\.venv\Scripts\python.exe -B scripts/verification/verify_core_database.py --check-test-access
```

La migration ne lit aucune donnée du CMS. Elle contrôle les éventuelles identités SaaS déjà présentes : e-mails vides/doublons normalisés ou noms trop longs bloquent la migration atomiquement, sans afficher de données ni les modifier. En cas de blocage, arrêter et demander une revue ; ne pas corriger automatiquement des comptes réels. Le champ technique `username` est remplacé par l’e-mail. L’UUID et les hachages restent conservés. Le retour à l’ancien schéma nécessite une restauration de sauvegarde SaaS ; ne pas exécuter une migration inverse à l’aveugle.

Si la base n’existe pas encore, suivre d’abord `core001-windows-development.md`, mode natif. Ne pas relancer une initialisation avec un autre mode/port.

## 3. Démarrer dans deux terminaux

Terminal **Django** :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
& .\scripts\windows\Start-Backend.ps1
```

Le script applique les ACL privées de la boîte avant de démarrer Django. Ne pas définir `SAAS_EMAIL_HOST` pour le mode boîte locale. Ne pas afficher les variables ou fichiers de secrets.

Terminal **studio** :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
$env:NEXT_TELEMETRY_DISABLED = '1'
npm.cmd run dev --workspace @portfolio/studio
```

Sur votre PC, ouvrir `http://127.0.0.1:3000/register`. Django utilise 8001 ; le CMS historique reste indépendant sur son port habituel. Utiliser toujours le même hôte.

## 4. Tests automatisés

Arrêter d’abord Next.js avec **Ctrl+C dans le terminal studio**. Le script lance un build Next et ne doit pas partager `.next` avec un serveur de développement en cours. Django peut rester actif : les tests utilisent une base séparée.

Dans le terminal de vérification :

```powershell
Set-Location "$env:USERPROFILE\testPorfolio-saas"
& .\scripts\windows\Test-Foundations.ps1
```

Après réussite du script, relancer `npm.cmd run dev --workspace @portfolio/studio` dans le terminal studio avant les parcours navigateur.

Le script conserve les contrôles historiques et ajoute les tests du client d’authentification. Il doit passer : 12 tests d’intégrité, 6 tests historiques, suite Django (33 tests dans cette livraison), 3 contrats santé, 4 tests du client auth, TypeScript et build. Une réponse 503 simulée dans les tests de santé est attendue ; la commande finale doit néanmoins réussir. Les tests Django créent leur propre base `test_…` avec le rôle de test ; ils n’effacent pas la base de développement.

Le navigateur automatisé est optionnel et nécessite Playwright/Chromium déjà installés ; aucune dépendance supplémentaire n’est ajoutée. `browser_auth001.py` ne doit viser qu’une instance et une boîte temporaires avec une base jetable dédiée, jamais des comptes réels. Le parcours manuel suivant ne demande aucune installation additionnelle.

## 5. Parcours manuel desktop et mobile

1. Créer un compte **synthétique** (`@example.test`), vérifier les validations et le retour à la connexion sans session automatique.
2. Vérifier le refus d’un doublon avec casse différente et l’erreur générique avec mauvais mot de passe.
3. Se connecter ; voir le tableau de bord vide avec le prénom. Vérifier `/dashboard` en fenêtre privée : retour à la connexion.
4. Ouvrir le tableau de bord dans deux onglets, puis se déconnecter : aucun profil ne doit rester visible dans l’autre onglet. Vérifier retour arrière/rechargement.
5. Demander un reset pour le compte synthétique. Ouvrir **localement**, dans l’éditeur de texte, le dernier `.log` de `infra\mailbox`. Copier le lien uniquement dans votre propre navigateur ; ne pas envoyer le fichier ni le lien dans le chat.
6. Choisir un nouveau mot de passe ; vérifier connexion avec le nouveau, refus de l’ancien, refus de réutilisation du lien et déconnexion des autres sessions du même compte (vérification au focus ou dans les 30 s).
7. Tester un lien absent/altéré. Pour l’expiration, définir `$env:SAAS_RESET_SECONDS = '60'` dans le terminal Django, redémarrer, demander un **nouveau** lien et attendre plus de 60 s. Le lien doit être refusé. Restaurer avec `Remove-Item Env:SAAS_RESET_SECONDS`, puis redémarrer.
8. Tester l’expiration de session de la même façon avec `$env:SAAS_SESSION_SECONDS = '60'`, une nouvelle connexion et une attente supérieure à 60 s ; message de session expirée attendu. Restaurer la variable puis redémarrer.
9. Refaire les actions essentielles en vue mobile (390 px) et au clavier. Vérifier labels, erreurs lisibles, indicateur de chargement, absence de défilement horizontal.
10. Inspecter les cookies dans le navigateur : HttpOnly et SameSite Strict. Secure est volontairement absent en HTTP local ; son activation HTTPS est couverte par les tests backend. Vérifier qu’aucun jeton n’est dans `localStorage`.

Ne partager que : version des outils, résumé final des tests, étapes réussies/échouées et messages techniques expurgés. Ne pas partager cookies, config privée, corps de formulaire, fichiers mail, e-mails réels ou liens reset. **AC14 reste ouvert tant que ces résultats Windows ne sont pas réellement fournis.**

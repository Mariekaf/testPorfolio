# Portfolio UX/UI — Marie Roger Fokou Kaffo

Portfolio responsive avec un back-office et des pages d’études de cas. Python 3.10+ suffit ; aucune dépendance d’exécution ni connexion à un service externe n’est nécessaire.

## Démarrer

```sh
cd /workspace/testPorfolio
python3 server.py
```

Le portfolio est à la racine du serveur, le back-office à `/admin`, et chaque projet a une adresse `/projet/son-adresse`. Le port par défaut est 8000 ; `--port` et `--host` permettent de l’adapter. **Ne pas utiliser `python -m http.server`** : le site nécessite les API du serveur et ce serveur statique exposerait les fichiers privés.

Au premier démarrage, un mot de passe aléatoire est créé dans `.local/initial-password.txt`. Consultez ce fichier uniquement sur votre machine pour la première connexion. Aucun mot de passe n’est inclus dans les sources. Pour choisir le vôtre :

```sh
python3 server.py --set-password
```

Saisissez le mot de passe dans le terminal (12 caractères minimum). Le fichier initial est alors supprimé. Redémarrez le serveur pour invalider les anciennes sessions.

## Personnaliser sans coder

- **Mes projets** : créer, modifier, dupliquer, supprimer, réordonner, conserver en brouillon ou publier.
- **Projet** : titre, adresse unique, catégorie, résumé, rôle, durée, année, outils, image de couverture, couleur et liens vers vos prototypes ou sites.
- **UX case story** : ajouter et réordonner des sections contenant titre, récit, image, description accessible et légende. Pour une galerie, ajoutez plusieurs sections d’images. Les textes conservent leurs retours à la ligne ; le HTML n’est pas exécuté.
- **Mon contenu** : nom, métier, disponibilité, portrait, introduction, présentation, compétences, contact, réseaux et pied de page.
- **Apparence** : quatre couleurs, typographie des titres, coins, espacement et grille à une ou deux colonnes.
- **Sauvegardes** : export/import JSON et archive ZIP contenant le contenu enregistré et les images.

Cliquez sur **Enregistrer** pour appliquer les modifications. Les brouillons enregistrés apparaissent dans l’**Aperçu privé**, uniquement pendant votre session d’administration. Enregistrer un projet publié actualise immédiatement le site. Les modifications non enregistrées ne figurent pas dans l’aperçu et un avertissement apparaît si vous quittez la page.

Les trois projets initiaux sont des démonstrations explicitement identifiées : remplacez-les par votre travail réel. Ajoutez votre e-mail pour afficher le bouton de contact ; il ouvre le logiciel de messagerie du visiteur, sans formulaire ni service d’envoi.

## Données et sauvegardes

Le dossier `.local/` contient les données privées et est ignoré par Git :

- `content.json` : contenu et numéro de révision ;
- `content.backup.json` : version enregistrée précédente ;
- `uploads/` : images importées ;
- `auth.json` : empreinte scrypt du mot de passe, jamais le mot de passe lui-même après personnalisation.

Les sessions expirent après huit heures ou un redémarrage. Les sauvegardes concurrentes sont refusées si la révision a changé pour éviter d’écraser le travail d’un autre onglet. Exportez vos modifications avant de recharger dans ce cas.

Pour déplacer le site, arrêtez le serveur, conservez une copie du dossier de données existant, puis restaurez `content.json` et `uploads/` depuis votre archive ZIP dans le dossier de données. Les références d’images du JSON seul ne transfèrent pas les images. Les images retirées d’un projet sont conservées sur disque pour permettre la récupération des anciennes versions. Vous pouvez utiliser `PORTFOLIO_DATA_DIR` pour placer ces données sur un volume persistant distinct.

## Hébergement

Ce projet nécessite un hébergement Python avec **stockage persistant**. Un hébergement statique comme GitHub Pages ne peut pas faire fonctionner ce back-office. En production, placer le serveur derrière un reverse proxy HTTPS, garder le dossier de données privé, définir `PORTFOLIO_HTTPS=1` pour les cookies Secure et utiliser un mot de passe personnel. Les routes de modification exigent une session et un jeton CSRF ; seules les pages, ressources front-end et images sont servies publiquement. La publication de l’environnement cloud ne constitue pas un déploiement public du site.

## Vérifier

```sh
python3 -m unittest discover -s tests -v
node --check script.js
node --check admin.js
```

Les tests Python utilisent un serveur et un dossier temporaire : ils ne modifient pas votre portfolio. Ils couvrent l’authentification, le CSRF, les fichiers privés, les images, les sauvegardes, les brouillons, la publication et les conflits de révision.

# BASE-001 — Inventaire fonctionnel et technique

Référence : `bf8952534bf8a17e7eb4521fee91d62409edc62a`. Branche de travail : `arch/base-001`. Inventaire établi par lecture des sources ; les niveaux de vérification sont détaillés dans la matrice et le rapport. Le CMS historique reste inchangé.

## Application publique (`index.html`, `script.js`, `style.css`)

- Accueil : métier, nom, titre multiligne, présentation, disponibilité, portrait facultatif ou illustration de remplacement.
- Navigation projets/à propos/contact, lien d'évitement, retour en haut.
- Grille ordonnée des seuls projets publiés ; couvertures, couleur, catégorie et illustration de remplacement ; état vide.
- Route propre `/projet/<slug>` : résumé, rôle, durée, année, outils, couverture, liens et sections ordonnées.
- Section : titre, texte avec retours à la ligne, image, texte alternatif et légende ; numéro de section.
- Navigation au projet suivant, métadonnées de titre et description, message de projet introuvable.
- Présentation, compétences séparées par virgules, localisation, réseaux, pied de page ; lien mailto affiché seulement si e-mail renseigné.
- Liens externes avec `noopener noreferrer`, images différées et textes injectés avec `textContent`.
- Palette de quatre couleurs ; titres sans/avec serif ; coins droits/souples/arrondis ; densité compacte/aérée ; une/deux colonnes ; adaptations mobile ; réduction des transitions.
- Aperçu `?preview=1` authentifié incluant les brouillons ; propagation de ce paramètre vers les liens projet et suivant. Les liens retour vers l'accueil ne le propagent pas systématiquement.
- États chargement, erreur et bouton réessayer.

Fonctions : `el`, `link`, `image`, `heading`, `external`, `theme`, `projectURL`, `projectVisual`, `home`, `casePage`, `start`. Les helpers DOM seront remplacés par des composants ; les comportements éditoriaux et de rendu sont la référence fonctionnelle.

## Administration (`admin.html`, `admin.js`, `admin.css`)

- Connexion, déconnexion, affichage des erreurs, reprise après session expirée.
- Projets : liste, ajout, modification, suppression avec confirmation, duplication avec nouvel ID/slug et brouillon, ordre haut/bas, publication par booléen.
- Métadonnées : titre, slug, catégorie, année, résumé, rôle, durée, outils, couleur, couverture et texte alternatif.
- Liens projet ajoutables/supprimables ; sections ajoutables/supprimables/réordonnables avec titre, récit, image, alt et légende.
- Import d'image et URL d'image ; aperçu, retrait de référence, limite client 12 Mio.
- Identité : nom, métier, localisation, disponibilité ; accueil, portrait, sélection projets, à propos, compétences, contact, réseaux et pied de page.
- Apparence : quatre couleurs, typographie, coins, densité et colonnes ; échantillon visuel de palette.
- Sauvegarde explicite avec indicateur dirty, protection contre double envoi, erreurs, version concurrente et avertissement avant fermeture.
- Ouverture du portfolio, aperçu privé et aperçu d'une page enregistrée.
- Export JSON des données en mémoire ; export ZIP du contenu enregistré et de tous les fichiers du dossier uploads ; import JSON remplaçant l'état en mémoire après confirmation, sans sauvegarde automatique.

Fonctions d'interface : `el`, `button`, `toast`, `mark`, `showLogin`, `showStudio`, `field`, `selectField`, `panel`, `grid`, `full`, `title`, `imageField`, `move`, `linkFields`, `newProject`, `projectsView`, `projectView`, `profileView`, `themeView`, `updateThemePreview`, `render`.

Transport et portabilité : `api`, `download`, handlers connexion/sauvegarde/déconnexion, image-picker/import-picker et `beforeunload`. État global : content, csrf, dirty, tab, selected, uploadTarget, saving. Pas de drag-and-drop, texte riche, modèle de page commun ou historique undo/redo aujourd'hui.

## Serveur (`server.py`)

- `password_record` : scrypt n=16384/r=8/p=1, sel aléatoire et comparaison constante à la connexion.
- `write_json` : écriture UTF-8 vers fichier temporaire puis remplacement ; permissions demandées 0600 (ne remplacent pas les ACL Windows).
- `initialize` : crée le dossier de données, uploads, contenu d'exemple si absent et identifiants initiaux si absents.
- `text`, `url`, `validate` : contrôles types/longueurs, protocoles, couleurs, choix de thème, identifiants/slugs, unicité et limites.
- `Handler.log_message` : méthode/chemin sans corps, mot de passe ou query string.
- `respond` : JSON UTF-8, types MIME, no-store, CSP, nosniff, referrer-policy.
- `session` : cookie HttpOnly/SameSite Strict, session en mémoire de huit heures ; Secure activé par `PORTFOLIO_HTTPS=1` à la connexion.
- `same_origin`, `read_body` : origine comparée au Host si fournie ; corps limité à 12 Mio.
- `do_GET`, `do_POST` : routes ci-dessous, filtres publics, auth et CSRF, sauvegarde de révision, upload et sauvegarde ZIP.
- Démarrage : `--host`, `--port`, `--set-password` masqué (12 caractères minimum) ; redémarrage invalide les sessions en mémoire.
- Données : `PORTFOLIO_DATA_DIR` ou `.local` relatif au script ; pas de service externe ni dépendance d'exécution.

## Routes historiques

| Méthode | Route | Contrat observé |
|---|---|---|
| GET | `/`, `/projet/<slug>` | Shell public, contenu chargé côté navigateur |
| GET | `/admin`, `/admin/` | Shell de connexion/administration |
| GET | `/style.css`, `/script.js`, `/admin.css`, `/admin.js` | Ressources explicitement autorisées |
| GET | `/api/content` | Contenu global avec projets publiés uniquement |
| GET | `/api/admin/session` | 200 + csrf ou 401 |
| GET | `/api/admin/content` | Document complet si authentifié |
| GET | `/api/admin/backup` | ZIP authentifié : contenu enregistré + fichiers uploads |
| GET | `/uploads/<nom autorisé>` | Image publique si présente, même liée à un brouillon |
| POST | `/api/login` | Mot de passe, session et CSRF ; limite 10 échecs/5 min/IP |
| POST | `/api/logout` | Session + CSRF, révocation et expiration du cookie |
| POST | `/api/admin/content` | Session + CSRF, validation, contrôle revision, sauvegarde précédente |
| POST | `/api/admin/upload` | Session + CSRF, corps binaire, signature PNG/JPEG/GIF/WebP, nom aléatoire |

Autres chemins : 404. Les erreurs métier POST sont généralement 400 ; sans session 401, CSRF/origine 403, révision obsolète 409, limitation login 429.

## Tests et documentation existants

`PortfolioTest` couvre auth/CSRF/fichiers privés, médias/ZIP/liens/slugs et brouillons/publication/conflit/persistance au redémarrage. `WindowsEncodingTest` répète ces trois tests avec une ouverture texte cp1252 implicite simulée. Ce n'est pas une exécution sur Windows.

`README.md` documente démarrage, personnalisation, stockage, hébergement et encodage Windows. `.gitignore` exclut `.local/`, `__pycache__/` et `*.pyc`. Aucun de ces fichiers n'a été modifié par BASE-001.

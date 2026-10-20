# Bibliothèque et images privées — MEDIA-001

Dans le dashboard authentifié, **Ma bibliothèque de médias** ouvre la grille privée.
L'éditeur Creative Editorial propose la même bibliothèque dans Portrait, Logo et
Couverture de projet. Aucun UUID n'est demandé à l'utilisateur.

1. Ouvrir **Choisir dans ma bibliothèque**, sélectionner jusqu'à4 JPEG/PNG/WebP,
   confirmer les droits puis **Importer une image**.
2. Choisir une miniature ; le renderer affiche l'image réelle après résolution
   serveur. Décrire l'image dans Texte alternatif, puis régler les deux curseurs
   de cadrage au clavier ou à la souris.
3. Enregistrer le portfolio. Les textes, références, alt et cadrages sont conservés
   avec les contrôles de version et révisions existants. On peut quitter, se
   déconnecter, se reconnecter et reprendre le brouillon.
4. **Remplacer** choisit une autre image ; l'alt et le cadrage précédents sont
   conservés et restent modifiables. **Retirer** enlève seulement la référence du
   slot, sans détruire l'asset ou modifier les autres contenus.

La bibliothèque est paginée (12 éléments). Les imports sont atomiques par lot : si
une image est invalide ou si le quota/disque refuse le lot, aucune image du lot
n'est enregistrée. Une rupture réseau peut rendre la confirmation d’import ambiguë : actualiser la bibliothèque avant de réessayer, les binaires potentiellement validés restent conservés. Un échec de sauvegarde du portfolio conserve la saisie et les
images déjà importées dans la bibliothèque ; aucun lien partiel n'est sauvegardé.
Un fichier indisponible affiche un état explicite, sans image de démonstration de
remplacement. Un échec de résolution peut être réessayé depuis l'aperçu.

Limites :8Mio par source,4 sources par import,20Mpx et8192px par côté, formats
statiques uniquement,200 images/200Mio de variantes stockées par compte. Les
originaux ne sont pas conservés : WebP normalisé max2560px et miniature max400px,
orientation corrigée et EXIF/ICC/XMP retirés. Le nom original nettoyé reste une
métadonnée privée ; une information sensible incluse dans le nom ne disparaît pas
par le retrait des EXIF.

**Supprimer** demande confirmation et la version de l'asset. Un média présent dans
un design ou une révision est protégé, même après retrait d'un slot ou suppression
logique du portfolio. Un média non référencé est retiré de la bibliothèque ; les
binaires restent privés pendant7jours, comptés dans le quota, puis une purge
administrative explicite est possible. Il n'existe pas de purge automatique ni de
suppression forcée de révisions. Une politique future de rétention des révisions
sera nécessaire si le quota est saturé par des images historiques protégées.

Les anciens brouillons E.07.04 avec UUID inconnus ne sont pas modifiés silencieusement.
Ils restent lisibles, avec placeholders. Avant une nouvelle sauvegarde, remplacer
ou retirer ces références ; toute association nouvelle doit être prête et appartenir
au compte autorisé. Les instances v1/v2 et les contrats immuables restent inchangés.

La réponse historique ready-instances.v1 conserve `media_status: unavailable` pour
sa projection **sans résolution inline** ; les clients MEDIA utilisent l'endpoint
privé `/api/v1/ready-portfolios/{id}/media` comme source de vérité. Le champ
historique ne doit pas servir à détecter la disponibilité de MEDIA-001. Une
suppression/renommage de ce champ nécessiterait une évolution d'API séparée.

Aucun lien public, stockage objet, upload SVG/vidéo, publication ou nouveau moteur
graphique. L'amélioration esthétique du template demeure hors périmètre.

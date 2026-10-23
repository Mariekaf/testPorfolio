# MEDIA-001 — Architecture et décisions MVP

Base bf605838b1d3fc3fa61533777bf95c8eccf08262, branche feature/media-001.
E.07.04 est accepté MVP selon décision utilisateur : Windows passé avec deux tests
ignorés ; lecteur d'écran toujours ouvert. Aucun résultat Windows inventé ici.

## Stockage et validation avant migrations

Asset UUID lié à Account, sans owner User concurrent. Métadonnées séparées des
binaires. Stockage local privé explicite SAAS_MEDIA_ROOT hors dépôt/public/.local,
répertoire dédié protégé avec marqueur .portfolio-media-v1, aucune valeur par défaut vers des fichiers personnels.
Interface stockage remplaçable par un adaptateur objet ; aucune URL interne rendue.
Sources JPEG/PNG/WebP seulement, statiques. Pillow13.0.0 justifié pour décodage réel,
EXIF transpose, réencodage et miniatures (dépendance verrouillée avec hashes).
8Mio/fichier,4 fichiers/requête,20Mpx,8192px par côté,200 assets et200Mio de variantes
stockées par compte ; suppression différée compte dans le quota jusqu'à purge.
Requêtes multipart bornées32Mio+64Kio, handlers mémoire bornés ; autres limites
API/AUTH inchangées. Aucun original conservé. WebP2560px maximum qualité85 et
thumbnail400px qualité75, sans EXIF/ICC/XMP/commentaire ; transparence conservée.
Orientation normalisée, animations et fichiers corrompus/refus MIME-extension refusés.

## Atomicité, concurrence et rétention

Décodage avant verrou, écritures sous verrou Account. Quotas sont recalculés dans
la transaction ; les nouveaux fichiers sont retirés si le rollback est confirmé. Si le COMMIT est ambigu et la base injoignable, conserver les binaires jusqu’à réconciliation pour ne pas casser une ligne potentiellement validée.
Une interruption brutale peut laisser un orphelin : réconciliation explicite en
mode dry-run par défaut, suppression seulement des clés orphelines de plus24h.
Un minimum de64Mio de disque libre est exigé. Pas de promesse de transaction SQL
atomique avec le système de fichiers ; un fichier perdu devient indisponible sans
fallback ni fuite, et les textes du portfolio restent consultables.

Association en PUT E.07.04 sous verrou Account : toutes les références non nulles
doivent exister, appartenir au compte et être ready avec binaires présents. Retirer
une référence ne détruit pas l'asset. Les anciens UUID non résolus restent visibles
en brouillon non modifié, mais doivent être retirés/remplacés pour une nouvelle
sauvegarde ; aucune conversion silencieuse. Les révisions existantes restent intouchées.

DELETE asset exige confirmation et If-Match. Refus409 s'il est référencé par un
design courant ou une révision, y compris portfolios archivés/supprimés. Un asset
non référencé est retiré de la bibliothèque, accès fichier fermé, fichiers retenus
7jours puis purge explicite hors requête HTTP. Le quota reste réservé jusque-là.
Aucune suppression silencieuse d'image référencée et aucune purge automatique.
Après purge : tombstone UUID/account/dates, nom/dimensions/hashes effacés. Les outils
maintenance revérifient les références sous le même verrou Account.

## Diffusion et Studio

Routes privées session+CSRF, même protections AUTH-001. GET fichier : owner contrôlé
sur chaque accès, chemins internes jamais renvoyés, Content-Type image/webp,
Content-Disposition inline générique, nosniff, CORP same-origin et private/no-store,
Vary Cookie. Aucun média sous public/ ou URL publique/objet signée en MVP.
La résolution serveur retourne uniquement les références autorisées du portfolio.
Le renderer E.07.03 partagé reçoit cette résolution distincte des fixtures
synthétiques ; aucune fixture ne prouve une propriété. Les slots E.07.02 restent
inchangés (asset_id,alt,decorative,focal_point).

Bibliothèque paginée privée et sélecteur réutilisable dans portrait/logo/couvertures,
import multiple, suppression contrôlée, alt et sliders de cadrage. Aucun UUID saisi.
Enregistrement ETag/révisions inchangé ; échec conserve saisie et binaires importés
non associés dans la bibliothèque, sans référence partiellement sauvegardée.

## Autorisation SQL et récupération

Migration additive app media uniquement, garde MEDIA001_ISOLATED_MIGRATIONS et
vérification cluster neuf par runner avant toute migration. Tests sur PostgreSQL17
neuf, stockage et mailbox temporaires ; aucun service/binaire/base personnel.
Les gardes E.04/E.07.04 et contrats historiques restent intacts. Une installation
réelle exigerait sauvegarde DB+stockage cohérente et autorisation distincte. Aucun
rollback destructif si assets existent : conserver les données et corriger en avant.
Pas de publication, PUB-001, PR, fusion, déploiement ou modification .local/CMS.

## Détails de transport et de charge

Next16 tronque à10Mo les corps clonés par son proxy de réécriture. Un Route Handler
Node limité à `/api/v1/media/assets` transporte GET/POST et lit au maximum32Mio+64Kio,
puis transmet Cookie/Origin/CSRF et Content-Type au backend local configuré.
Les autres routes restent sur leurs limites/proxy existants. Le backend reste
l'autorité de session et de validation ; ce transport ne crée aucune permission.
Le parcours teste réellement deux sources de6Mio dans une requête12Mio via Next.
Le handler est refus fermé sur origine backend non locale ou erreur réseau.

Deux décodeurs simultanés maximum par processus, réponse503 si saturés. Les quatre
images d'un lot sont traitées séquentiellement ; pas de file de travail distribuée.
La consommation mémoire reste bornée par les pixels et les buffers d'import, mais
n'est pas un test de charge de production. Chaque variante diffusée est comparée
à sa taille/hash avant ouverture en streaming ; les lectures restent privées.

Un verrou advisory transactionnel par clé binaire protège la fenêtre d'écriture
contre la réconciliation d'orphelins, même si un processus reste suspendu longtemps.
La réconciliation prend ce verrou sans attendre, revérifie les lignes en base et
ignore toute clé occupée ou non conforme ; aucune suppression récursive de fichiers
inconnus. L'adaptateur de stockage expose write/open/delete et une factory unique.
La réconciliation locale utilise l'inventaire de répertoires ; un futur adaptateur
objet devra fournir l'inventaire/entretien équivalent, sans URL publique automatique.


Un répertoire privé non marqué n'est jamais adopté. L'initialiseur crée seulement
un NOUVEAU chemin absolu hors dépôt/.local, protège ses permissions et écrit le
marqueur ; il refuse tout dossier déjà présent. Le stockage vérifie le marqueur
avant accès aux clés binaires. Cela évite qu'une configuration accidentelle vise
un dossier personnel. Les runners et tests initialisent uniquement leurs chemins
TEMP neufs ; aucun dossier utilisateur n'est reconfiguré.

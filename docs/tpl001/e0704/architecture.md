# E.07.04 — Parcours privé Creative Editorial

Base : 144043b67c96b7869c714e79a0b1b66c536ad5f5. Une livraison de revue.

## Décisions et récupération avant persistance

Deux tables additives : ReadyPortfolioDesign (OneToOne Portfolio, document JSONB
v3, empreinte de bundle immuable) et ReadyDesignRevision (snapshot après chaque
création/sauvegarde, version canonique Portfolio.version, auteur). Aucune colonne
ou contrainte v1/v2 modifiée, aucun backfill ni conversion. Ownership uniquement
via Portfolio.account et authorized_accounts AUTH/PORT. Révisions append-only,
clé unique design/version ; snapshot complet permet récupération ultérieure
contrôlée, sans endpoint de restauration destructive dans ce ticket.

La récupération opérationnelle commence par une sauvegarde de la base réelle
avant une éventuelle installation autorisée séparément. Le déploiement SQL réel
n'est pas autorisé ici. En cas de problème, désactiver l'accès Studio et conserver
les tables/révisions ; ne pas inverser la migration avec des données. Les écritures
sont atomiques : création compte/portfolio/design/révision/intention, ou sauvegarde
sous verrou portfolio avec If-Match, validation complète et nouvelle révision.
Un échec annule l'ensemble ; une réponse perdue après sauvegarde impose une lecture
explicite (pas de réessai aveugle). Création idempotente 24h via intention UUID.

## API privée nouvelle, contrats historiques inchangés

GET /api/v1/ready-templates : unique offre MVP, snapshot vide validé, style policy,
statut original draft, éligibilité privée explicite ; ce n'est pas le catalogue public.
POST /api/v1/ready-portfolios : {name}, Idempotency-Key UUID ; portfolio privé neuf.
GET/PUT /api/v1/ready-portfolios/{id} : lecture/reprise ; PUT {content,customization},
If-Match obligatoire ; réponse {portfolio, snapshot, version, etag, media_status}.
GET /api/v1/ready-portfolios/{id}/revisions : métadonnées de récupération privées.
POST /api/v1/ready-portfolios/{id}/validate : aperçu non persistant, même validation.
401 sans session ; 404 hors compte/supprimé ; 428 sans précondition, 412 conflit,
409 archivé/incohérent, 400 contrat invalide, 413 >256Kio. Sessions/CSRF inchangés.

Le middleware existant ne reçoit qu'une extension de chemins bornés ; aucune
augmentation globale de la limite AUTH. Les bundles et leurs hashes restent intacts.
La duplication historique d'une instance v3 est refusée explicitement plutôt que
créer une copie sans design (duplication v3 hors parcours demandé).

## Studio et renderer

Routes privées /portfolios/ready et /portfolios/{id}/ready sous le layout AUTH
existant. Sélection avec vraie miniature de composition, aperçu synthétique
explicitement étiqueté. Édition structurée des 14 slots : AST riche limité,
projets/liens/réseaux, références média et styles autorisés, sans grille éditable.
Le composant visuel E.07.03 est extrait sans modification de composition dans une
vue partagée ; wrapper historique validé côté serveur et client privé avec les mêmes
schémas/validateur E.07.02. Aucun moteur de rendu parallèle. Un aperçu invalide
reste signalé et n'est pas sauvegardé. Contenu conservé en mémoire sur erreur et
conflit, confirmation explicite avant recharge destructive/navigation. Aucun
brouillon personnel en localStorage. Avantunload + liens + événement logout.

MEDIA indisponible : UUID/cadrage/alt peuvent être saisis et conservés mais aucun
fait de propriété n'est inventé ; aucune source utilisateur chargée. Preview utilise
le renderer sans contexte média synthétique, placeholders explicites. Aucun upload,
stockage, publication, disponibilité publique, police distante ou SQL sur base réelle.

## Validation isolée

Migrations et tests seulement dans un cluster PostgreSQL17 fraîchement créé avec
identifiants aléatoires, configuration temporaire privée, aucun DSN existant.
Le runner doit vérifier le répertoire data_directory et serveur17 avant migrations,
provisionner rôles limités, exécuter suites Django et navigateur, arrêter et détruire
uniquement son cluster dans finally. Windows commandes fournies mais non exécutées
ici. E.07.03 Windows et lecteur d'écran restent ouverts.

# TPL-001.A — Contrats et architecture proposés

Version 0.1 — 19 octobre 2026. Branche `design/tpl-001-a`.

**TPL-001.A approuvé au commit `b151719`, avec ajustements documentaires intégrés avant B.**

Les choix structurants sont approuvés par décision utilisateur du 19 octobre 2026. TPL-001.B est autorisé ; C/D/E restent interdits avant revue de B. Les paragraphes de proposition ci-dessous conservent leur contexte historique de conception. Le périmètre global et les exigences précisés par l’utilisateur sont approuvés ; les décisions détaillées ci-dessous sont proposées. TPL-001.B/C/D/E ne commencent pas avant validation de A. Aucun modèle Django, renderer, composant React ou migration n’est implémenté ici.

## 1. Références et frontières

Socle fonctionnel accepté : PORT-001 `27a0b85`, clôture documentaire `4ce0f6b`. [ARCH-002](../architecture/ARCH-002.md), [API PORT](../api/portfolios-v1.md), contrat session AUTH-001 inchangés. Réserve [Windows PORT](../portfolios/windows-follow-up.md) toujours **NON EXÉCUTÉE**, non bloquante.

Acquis réellement présents : User/Account/AccountMembership, Portfolio.account, version et ETag, références de source versionnées optionnelles, thème strict `studio-neutral@1.0.0`, brouillon/privé imposés, migrations historiques conservées. Absents : catalogue actif, stockage de design, composition, rendu et personnalisation.

Tous les fichiers machine de ce dossier sont des **propositions isolées**. Ils ne sont pas référencés par l’OpenAPI actif, le registre du backend ou les migrations. Aucun contrat actif n’est modifié. Le [ticket](../tickets/TPL-001.md) reste le point d’entrée du périmètre.

## 2. Deux compositions réellement distinctes

| Élément | Minimal | Editorial |
|---|---|---|
| Structure | Flux vertical centré, largeur de lecture limitée | Grille éditoriale asymétrique, colonne de repères et colonne principale |
| Hero | Titre centré, sous-titre et action en pile | Titre aligné à gauche sur deux colonnes, repère de rubrique |
| Projets | Grille régulière de cartes, deux colonnes desktop | Premier projet pleine largeur puis liste de récits avec titres et résumés |
| Présentation | Bloc court après les projets | Colonne de texte avant les projets, titre marginal |
| Compétences | Liste compacte | Encadré latéral ; occupe la ligne principale sur mobile |
| Contact | Fin de page discrète | Panneau de conclusion typographique |
| Mobile | Une colonne, ordre du document | Grille rabattue à une colonne, repères conservés, même ordre accessible |

Les deux utilisent les mêmes tokens neutres mais des variantes, une hiérarchie, des espacements et un agencement différents. Pas de promesse de deux templates fonctionnels aujourd’hui : les exemples sont des données de conception. Les captures et la fidélité réelle seront vérifiées en B/D/E.

Le schéma permet un nombre et un ordre de sections différents : aucune obligation globale de posséder les cinq types. Chaque template fixe sa liste, ses variantes et ses permissions. Les deux premiers exemples couvrent hero, about, projects, skills et contact ; Editorial les ordonne différemment. Hero reste visible et ancré en tête, contact ancré en fin ; les autres sections peuvent être réordonnées et masquées selon leur politique.

Les cartes de case studies sont du contenu structuré simple (titre, résumé, lien externe HTTPS facultatif), **pas un modèle Projet ou un Case Study Builder inventé**. Les liens ne créent aucune page dédiée ni publication. Une future relation Project devra avoir son contrat et sa migration propres.

## 3. Documents versionnés et validation

Voir [schémas proposés](contracts/schemas/) et [exemples](examples/). JSON Schema draft 2020-12, objets fermés, limites de taille et versions explicites. Les valeurs par défaut sont matérialisées dans les exemples, jamais injectées implicitement par un validateur JSON Schema.

| Document | Rôle | Mutabilité de l’instance |
|---|---|---|
| composition v1 | Identité du template, layout, sections stables, ordre initial, variantes et politiques | Copie épinglée, non modifiable par les formulaires TPL |
| content v1 | Textes et données typés par section | Remplacement complet validé lors d’une sauvegarde |
| presentation v1 | Thème et réglages de base de chaque section | Copie de base non modifiable directement ; overrides autorisés |
| customization v1 | Ordre local, visibilité et réglages locaux | Remplacement complet, pas de fusion PATCH ambiguë |
| experience | Réservé, strictement null en v1 | Aucun moteur ni payload libre accepté |

Les identifiants de section sont des clés **locales au design**, non des UUID de ressource : ils restent stables lors d’une duplication afin de préserver les références internes. Les projets de démonstration ont des UUID de données locales régénérés lors de la duplication. Les futurs médias partagés auront une règle de copie distincte, pas un partage mutable implicite.

### Invariants sémantiques obligatoires côté serveur

JSON Schema seul ne suffit pas. À chaque chargement de catalogue et sauvegarde d’instance :

1. Refuser une version de schéma inconnue et les champs non déclarés ; contrôler les formats avec un FormatChecker explicite.
2. Vérifier l’unicité des section.id, leur type et la compatibilité type/variant. La table autorisée associe chaque type à ses variantes homonymes listées dans composition.v1 ; aucun variant de hero pour contact.
3. Content et presentation contiennent exactement une entrée par section de composition, sans référence étrangère ni doublon. Les valeurs initiales de présentation sont complètes ; chaque valeur doit appartenir à la politique de la section.
4. Un template a une identité/version cohérente avec son descripteur et le manifeste. La paire de thème existe et figure parmi les thèmes compatibles ; le premier lot n’admet que studio-neutral 1.0.0.
5. section_order, si fourni, est une permutation exacte de toutes les sections, visibles et masquées. Les sections non réordonnables gardent leur index initial. Les autres occupent les emplacements libres dans l’ordre fourni. Sinon utiliser l’ordre de composition.
6. Interdire visible=false pour une section obligatoire ou non désactivable. Un override ne peut mentionner qu’une section existante et une valeur de présentation autorisée par sa politique ; aucun changement de type, variante, layout ou permission.
7. Réglages effectifs = base de présentation puis clés d’override présentes. Clé absente = hériter ; false = valeur explicite ; null est invalide. Remettre à zéro = retirer la clé (ou l’entrée vide) du document complet. Aucun héritage du template source après instanciation.
8. Textes bruts échappés au rendu, aucun HTML/Markdown interprété. URL de projet : HTTPS uniquement, hôte non vide, sans identifiants ni javascript/data/file ; aucune récupération serveur. E-mail facultatif validé ; jamais exposé comme donnée privée de catalogue. Les coordonnées fictives des exemples restent null.
9. Limite JSON 256 Kio avant parsing, profondeur bornée par les schémas, tableaux bornés, chaînes bornées. Une section masquée conserve ses données. Une sauvegarde remplace atomiquement contenu et personnalisation ; elle ne supprime pas les ressources des sections masquées.

Les invariants transversaux seront implémentés et testés en C, pas dans cette phase documentaire. L’aperçu et le renderer d’instance devront appliquer le même calcul de document effectif.

### Évolution sans moteur fictif

Composition, contenu, présentation et expérience portent des versions de schéma indépendantes. Snapshot v1 est une enveloppe de transport, pas une autorisation à fusionner ces responsabilités. Aucun blob JSON libre d’animation. L’introduction ultérieure de timelines, scènes ou interactions requiert un schéma experience versionné, des cibles de sections stables et une migration explicite. Ni GSAP, ni Three.js, ni React Three Fiber ne sont ajoutés.

Creative et Experimental ne sont pas dans l’enum du descripteur actif ; ne pas les ajouter silencieusement. Recommandation : réserver leur évolution à un futur descripteur v2/additif et à des capacités renderer déclarées. Immersive existe comme catégorie de métadonnées mais n’est pas annoncé disponible. Aucun catalogue fictif ou carte « fonctionnelle » pour ces catégories.

## 4. Stockage proposé et migrations futures

### Tables proposées, non créées

**PortfolioDesign** : id UUID PK ; portfolio OneToOne PROTECT ; schema_version entier (=1) ; composition JSONB ; content JSONB ; presentation JSONB ; customization JSONB ; experience nullable JSONB imposé NULL pour v1 ; source_digest SHA-256 du bundle immuable ; created_at/updated_at. Pas de owner/account redondant : accès exclusivement par Portfolio.account et les contrôles PORT. Contrainte de présence du portfolio et unicité par portfolio. Les structures JSON sont validées côté service, sans prétendre que PostgreSQL applique JSON Schema.

Le compteur canonique reste **Portfolio.version**, aucun compteur design concurrent. Toute mutation de design verrouille Portfolio puis PortfolioDesign, vérifie If-Match sous verrou, écrit et incrémente version une fois. Les PATCH/archives/suppressions existants utilisent le même ordre de verrouillage. Sauvegarde identique acceptée = une version supplémentaire, règle explicite simple. Lecture retourne un snapshot cohérent et le même ETag que PORT ; pas deux lectures séparées pouvant associer données anciennes et version récente.

**TemplateCreationRequest** : UUID interne ; user FK PROTECT ; account FK PROTECT ; key UUID ; request_digest ; portfolio FK PROTECT nullable pendant la transaction ; response_body JSONB privé ; response_etag ; completed_at/expires_at. Unicité (user, account, key). Réservation et résultat dans la même transaction que Portfolio/Design. Nettoyage après 24 h, y compris réponse mémorisée ; aucun secret ou corps de requête dans les logs. La propriété de la cible est revérifiée avant tout replay. Pas de nouvelle session ni rôle collaboratif.

Catalogue : fichiers immuables dans Git ; un manifeste relie id/version aux fichiers descripteur, composition, contenu et présentation ainsi qu’aux empreintes. Le [manifeste de démonstration](examples/bundle-manifest.proposed.json) référence les fichiers descripteur et snapshot (ce dernier contient les quatre documents séparés). Empreintes SHA-256 sur les octets UTF-8 exacts, fins de ligne LF ; le source_digest stocké sera le SHA-256 du snapshot source. Les chemins sont locaux, résolus sous la racine du registre, sans URL ni traversée de répertoire. Les UUID document_id du descripteur actif ne sont pas inventés pour des fichiers : la référence est portée par le manifeste. Un catalogue disponible exige le bundle complet validé, pas seulement availability=available.

Proposition à valider pour la disponibilité : révisions de manifeste append-only, bundles et anciennes révisions conservés immuables. Le retrait d’une version se fait dans une nouvelle révision de catalogue ; il ne modifie pas son snapshot ni son empreinte. L’API projette availability depuis la révision courante sur les métadonnées retournées ; ce champ opérationnel n’est pas une personnalisation de contenu. Les exemples gardent unavailable. Aucun retrait automatique n’est exécuté ici.

### Plan additif à examiner avant C

1. Ajouter les deux tables uniquement ; conserver toutes les migrations existantes et contraintes PORT, thème inclus. Aucun backfill des portfolios vierges ni changement UUID/états/source.
2. Vérifier avant activation toute source_template déjà renseignée sans design : incohérence signalée, aucune composition inventée ou réparation silencieuse.
3. Les portfolios historiques restent vierges avec zéro PortfolioDesign. GET design pour une cible autorisée sans design renvoie 409 design_not_initialized, sans création implicite. Aucune conversion automatique d’un portfolio existant en template dans ce ticket.
4. Créer nouvelles instances et leur design atomiquement par le nouveau endpoint. Ne pas ouvrir les champs protégés du POST/PATCH PORT existant.
5. Étendre la duplication existante seulement après validation du contrat d’extension : design complet et nouveaux UUID de ressources locales, mêmes références source et empreinte, version du nouveau Portfolio=1 ; aucune mutation source. Les anciennes duplications vierges restent inchangées. L’appel existant conserve If-Match, sans nouvelle exigence d’Idempotency-Key.
6. Vérifier parcours 27a0b85 → schéma proposé avec données synthétiques PostgreSQL 17 et coexistence vierge/template. Réexécuter les scénarios historiques de migrations AUTH/provisoire. Aucun DDL ou test DB exécuté en A.
7. Retour arrière : avant les nouvelles écritures, réversible après vérification ; après création de designs, ne pas supprimer les tables/données pour revenir au code ancien. Préférer désactivation des écritures et correction en avant, ou restauration validée d’une sauvegarde séparée. Sauvegarde et autorisation explicites avant toute base réelle.

Suppression logique du portfolio conserve design et clés non expirées sans exposition API. Archive = lecture permise, écriture/duplication refusée comme PORT. Purge et conservation légale restent hors périmètre.

## 5. API proposée, erreurs et doubles soumissions

Référence machine autonome : [openapi.proposed.json](contracts/openapi.proposed.json). URL sans slash final. Aucun endpoint n’est enregistré dans l’application par cette proposition.

| Route | Comportement proposé |
|---|---|
| GET /api/v1/templates | Pagination 12, ordre stable id puis version semver décroissante ; filtres exacts category et availability ; défaut available uniquement. Pas de champs de comptes ou d’instances. |
| GET /api/v1/templates/{template_id}/versions/{template_version} | Descripteur exact authentifié ; unavailable/retired consultables avec état explicite. |
| GET .../preview | Snapshot synthétique complet validé d’une version disponible ; sinon 409 template_unavailable. Aucun portfolio créé. |
| POST /api/v1/portfolios/from-template | Version explicite, session+CSRF+Idempotency-Key UUID ; compte dérivé côté serveur, réponse Portfolio canonique 201 et ETag. |
| GET /api/v1/portfolios/{id}/design | Snapshot propriétaire et version cohérents ; 409 si portfolio vierge, 404 si inconnu/étranger/supprimé. |
| PUT .../design | Remplacement complet content+customization ; CSRF et If-Match ; composition/source/thème/expérience non assignables ; réponse Design 200 avec nouvel ETag. |

Toutes les réponses sont privées, Cache-Control: no-store. Même cookie et acquisition CSRF AUTH ; jamais de token localStorage. Validation de session avant de divulguer catalogue ou donnée privée. Body JSON strict. Les erreurs conservent {error:{code,message,fields?}}, sans trace, SQL ou corps privé.

Codes : 400 invalid_request/invalid_design/invalid_idempotency_key ; 401 authentication_required ; 403 csrf_failed ; 404 not_found ; 409 slug_conflict/account_inconsistent/portfolio_archived/design_not_initialized/template_unavailable/template_incompatible/idempotency_conflict ; 412 version_conflict ; 428 precondition_required ; 413 payload_too_large ; 415 unsupported_media_type ; 429 rate_limited ; 503 temporarily_unavailable. Vérifier autorisation avant If-Match pour ne pas distinguer une ressource étrangère. JSON Schema définit la forme, les codes exacts doivent être inscrits dans les tests d’intégration futurs. Une version de template inexistante donne 404 ; une version de document inconnue dans un PUT donne 400.

### Sémantique des doubles soumissions proposée

- Clé UUID créée par le client **une fois par intention de création**, conservée pour les retries réseau ; nouvelle intention = nouvelle clé. Aucun changement des endpoints PORT existants.
- Digest sur JSON canonique des champs acceptés après normalisation, incluant template_id/version et valeurs implicites matérialisées. Rejeter les champs inconnus avant calcul. Même clé et corps différent → 409, aucune création.
- Transaction : verrou/contrainte unique de clé, provisioning éventuel atomique, disponibilité du template, création Portfolio+Design+résultat. Échec = rollback intégral. Deux requêtes concurrentes ne créent qu’un portfolio ; attente bornée, 503 + Retry-After si verrou indisponible, retry avec la même clé.
- Même clé/corps dans 24 h : rejouer le 201, corps et ETag originaux, sans écriture ni incrément. Ce replay est une photographie de création, **pas une lecture actuelle** ; le client recharge le détail avant édition. Si la cible est ensuite supprimée/inaccessible, 404, jamais ressuscitée. Une indisponibilité ultérieure du template n’invalide pas un résultat déjà créé et encore accessible.
- Après expiration : la clé ne garantit plus la déduplication. Interface : recharger la liste et demander une nouvelle intention explicite avant nouvelle création ; ne pas relancer automatiquement une intention expirée.
- L’enregistrement privé de résultat n’est pas un journal de données à conserver sans limite. Nettoyage et tests d’expiration à prévoir en C/E.

## 6. Parcours et composants UI à construire ultérieurement

1. Dashboard → « Depuis un template » ; la création vierge reste disponible.
2. Bibliothèque : cartes Minimal/Editorial, filtre, pagination, états chargement/vide/erreur ; aucune catégorie future annoncée disponible.
3. Aperçu : sélection desktop/mobile par largeur de conteneur, thème neutre et contenu synthétique ; retour sans création. Bouton de sélection désactivé pour unavailable/retired.
4. Sélection : nom, slug optionnel, résumé du template/version ; validation, intention de création et état envoi. Erreur réseau conserve la clé et propose réessai sûr.
5. Création réussie : espace privé du nouveau portfolio, aucune URL publique ni publication ; données initiales éditables.
6. Personnalisation : formulaire de textes typés, liste de sections avec actions monter/descendre accessibles, bascule visible, sélecteurs bornés de présentation et aperçu du brouillon local.
7. Sauvegarder explicitement : PUT sous ETag, confirmation seulement après succès serveur ; avertissement de modifications non enregistrées à la navigation. Après reconnexion, rechargement depuis le serveur. Pas d’autosauvegarde ni de diffusion publique.
8. Conflit 412 : garder les modifications locales en mémoire, proposer rechargement avec confirmation de perte ; aucune réécriture forcée ni fusion silencieuse. Session expirée : reconnexion, rechargement et arbitrage explicite, aucun contenu privé persistant dans localStorage.

| Composant proposé | Responsabilité |
|---|---|
| TemplateLibrary / TemplateFilters / TemplateCard | Catalogue, filtres, états, disponibilité et version lisible |
| TemplatePreviewDialog / ViewportSwitch | Dialogue accessible, focus/Échap, aperçu desktop/mobile |
| PortfolioRenderer / SectionRenderer registry | Même rendu whitelist pour aperçu catalogue et aperçu d’instance ; variantes distinctes |
| TemplateCreateForm | Champs PORT, intention idempotente, erreurs et reprise réseau |
| PortfolioDesignForm / SectionContentFields | Édition typée des textes et listes, limites explicites |
| SectionOrderControls / VisibilityControl | Réorganisation clavier, permissions et conservation des sections masquées |
| PresentationControls | Choix issus des politiques, retour à l’héritage |
| DraftPreview / SaveBar / VersionConflictDialog | Aperçu local fidèle, sauvegarde explicite, statut et conflit |
| TemplateApiClient / DesignApiClient | Session, CSRF, erreurs, ETag ; pas de logique de propriété client |

Pas de nouveaux composants implémentés ici. Favoriser les composants de dialogue/formulaire déjà présents au moment de D ; lire les conventions Next du dépôt avant tout code React. Aucun besoin de dépendance DnD ou moteur de rendu externe pour ce périmètre.

## 7. Options et recommandations soumises à validation

| Sujet | Options, avantages et limites | Recommandation |
|---|---|---|
| Catalogue | Git : revue et versionnement, déploiement nécessaire ; DB : administration dynamique, rôles/édition à sécuriser | Git immuable avec manifeste et digest |
| Instance | Copie JSONB : indépendante et simple, validation applicative ; tables normalisées : requêtes fines mais migrations plus lourdes pour chaque type | PortfolioDesign en documents JSONB distincts et bornés |
| Overrides | Snapshot seul : simple mais perd la remise à zéro ; patch générique : flexible mais ambigu/risqué ; overrides typés : bornés et explicites | Base figée + overrides typés, contenu complet |
| Conflits | Version par document : écriture fine mais états composites ; version Portfolio : plus de conflits mais contrat cohérent | Version Portfolio commune, verrouillage uniforme |
| Aperçu | Capture statique : simple mais pas fidèle aux modifications ; même renderer : plus de travail mais cohérence | Renderer partagé sans code arbitraire |
| Doubles soumissions | Bouton désactivé seul : insuffisant réseau/concurrence ; clé serveur : table et expiration supplémentaires | Clé 24 h pour la nouvelle route uniquement |
| Catégories futures | Modifier enum v1 : casse l’immuabilité du contrat ; évolution versionnée : adaptation future explicite | V2 ultérieure, aucune carte Creative/Experimental disponible aujourd’hui |

À approuver explicitement : stockage et gestion du retour arrière ; politique d’overrides/ancrages et variantes ; premier lot et personnalisation bornée ; endpoints et extension de duplication ; durée/sémantique d’idempotence ; stratégie des catégories futures. L’approbation globale ne vaut pas validation anticipée de ces détails.

## 8. Validation future et découpage après A

[Plan de tests](test-plan.md). B : registre/descripteurs/compositions et rendu d’aperçu ; C : schéma additif, services transactionnels, API et duplication ; D : studio accessible et personnalisation persistante ; E : campagnes d’intégration/non-régression et rapport. Ordre recommandé : B fournit les bundles validés à C ; D consomme les contrats B/C ; E valide l’ensemble. Aucun de ces travaux n’est commencé.

Le présent dossier est livré pour revue de A, pas comme preuve d’une bibliothèque fonctionnelle.


## 9. Ajustements de revue A — intégrés avant TPL-001.B

### Extensibilité de la présentation et des expériences

Les futurs contrats pourront porter palettes, typographies, images, vidéos, animations et expériences immersives. Une évolution versionnée ajoutera des tokens autorisés, références de polices/médias et capacités de renderer ; elle définira des migrations explicites des documents, sans écraser les overrides existants. Les polices distantes, CSS libre, scripts, timelines et scènes 3D restent refusés en v1 ; experience reste null. Aucun moteur GSAP/Three.js ni éditeur visuel libre n’est développé dans B.

### Stratégie des médias futurs — contrat de frontière, aucune implémentation

Une future ressource MediaAsset aura son UUID, un compte propriétaire canonique, une clé de stockage opaque, type MIME détecté, taille, empreinte et état de traitement/quarantaine. Les documents référenceront des identifiants de médias, jamais des chemins disque ou URL de stockage fournis par le client. Une association PortfolioAsset autorisera leur utilisation dans un portfolio du même compte ; autorisation serveur à chaque lecture/écriture, accès privé à durée limitée pour les brouillons et publication explicite séparée pour d’éventuels dérivés publics.

Les originaux seront immuables, les transformations référencées et régénérables. Les images/vidéos auront dimensions/durée et variantes ; textes alternatifs, légendes et réglages de recadrage resteront dans les documents de présentation/contenu. Validation MIME réelle, quotas, analyse de sécurité, droits/licences et restrictions SVG/HTML seront spécifiés avant uploads. Aucune table, bucket, upload, téléchargement distant, miniature ou URL signée n’est créé dans B.

Duplication future dans le même compte : nouveaux UUID d’association et références locales indépendantes ; partage possible des seuls octets immuables après validation de la politique. Aucun partage inter-comptes implicite. Archivage/suppression logique ne suppriment pas un original encore référencé ; purge physique uniquement selon politique de rétention validée, références et sauvegardes vérifiées. Les fichiers historiques et .local ne deviennent jamais des ressources SaaS par découverte automatique.

### Rendu, démonstration et activation

Minimal et Editorial doivent produire deux compositions responsive professionnelles avec le même moteur que le futur rendu d’instance. Des JSON seuls ou captures statiques ne satisfont pas B. Les contenus sont entièrement fictifs, cohérents et représentatifs des projets UX/UI ; ils ne revendiquent aucun client ou résultat réel. Les visuels décoratifs de B sont dessinés en CSS, sans médias importés.

Les descripteurs source restent immuables et unavailable ; la révision du manifeste ne projette available qu’après validation des bundles, des capacités réelles du renderer, des références/thèmes et des tests de rendu. Une erreur de chargement échoue fermée : aucun template déclaré utilisable. Avant activation des routes en lecture B, vérifier la cohérence sémantique OpenAPI (formes de réponses, statuts/erreurs, filtres, versions et sécurité). Les routes de création et design proposées restent inactives jusqu’à C.

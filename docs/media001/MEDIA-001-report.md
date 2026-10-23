# MEDIA-001 — Rapport de livraison

**Livré pour revue, non déclaré validé.** 20 octobre2026.
Branche `feature/media-001`, issue exactement du commit E.07.04
`bf605838b1d3fc3fa61533777bf95c8eccf08262`. SHA de livraison communiqué à la remise.
Une seule livraison MEDIA-001 ; aucune PR, fusion ou mise en production.

## Résultat fonctionnel

L'utilisateur authentifié importe JPEG/PNG/WebP, parcourt sa bibliothèque privée
paginée, choisit une image pour portrait/logo/couverture, règle alt et cadrage,
prévisualise les véritables pixels, enregistre puis retrouve le résultat après
sortie, déconnexion et reconnexion. Aucun UUID n'est demandé. Remplacer/retirer une
référence préserve les autres contenus et le binaire historique. Le renderer
Creative Editorial reste partagé ; aucune composition ou direction artistique refaite.

La bibliothèque gère imports multiples, préparation, état vide, erreurs françaises,
miniatures, choix, pagination et suppression confirmée. Dialogue natif, focus rendu
au déclencheur, Escape et curseurs au clavier. Les images manquantes donnent un
état explicite sans image synthétique de remplacement. Les brouillons incomplets
restent possibles ; références non autorisées ou indisponibles refusées à la sauvegarde.

[Architecture et décisions](architecture.md) · [Guide utilisateur](usage.md) ·
[Commandes Windows isolées](windows.md) · [Inventaire](files.txt) ·
[Contrat API privé](../../contracts/api/media.v1.json).

Captures : [éditeur desktop](evidence/editor-desktop.png), [éditeur mobile](evidence/editor-mobile.png), [bibliothèque desktop](evidence/library-desktop.png), [bibliothèque mobile](evidence/library-mobile.png), [portfolio desktop](evidence/portfolio-desktop.png), [portfolio mobile](evidence/portfolio-mobile.png), [erreur](evidence/library-error.png).

## Architecture et protections

Asset UUID rattaché à Account via FK, version, nom nettoyé, dimensions/taille des deux
variantes, hashes et clé de stockage aléatoire interne. Aucune image en PostgreSQL,
aucun chemin interne dans les réponses. Tables additives app media uniquement,
aucun backfill, aucune modification des schémas/bundles immuables E.07.02 ni conversion v1/v2.

Stockage hors dépôt/public/.local, répertoire explicitement initialisé et marqué,
permissions700/600 ou DACL Windows restreinte vérifiée sans SACL. L'initialiseur
refuse un répertoire existant, même vide : aucun dossier personnel n'est adopté.
Adaptateur binaire abstrait et factory, sans fournisseur objet imposé. La maintenance
d'orphelins locale demandera son équivalent lors d'un futur adaptateur objet.

Pillow13.0.0 est ajouté pour **décoder réellement** les images, vérifier format,
orientation et dimensions, copier les seuls pixels et réencoder. JPEG/PNG/WebP
statiques seulement, extension/MIME cohérents avec le contenu, refus SVG/HTML,
corrompus, animations et bombes. Aucune source brute persistée. WebP normalisé
max2560px qualité85, miniature max400px qualité75, alpha conservé, EXIF/ICC/XMP retirés.
Le nom original reste une métadonnée privée, pas une promesse d'anonymisation.

| Limite MVP | Valeur |
|---|---|
| Source | 8Mio par fichier |
| Lot | 1 à4 fichiers |
| Corps multipart | 32Mio+64Kio maximum |
| Décodage | 20Mpx,8192px par côté, pas d'animation |
| Compte | 200 assets et200Mio de variantes retenues |
| Décodeurs | 2 simultanés par processus, sinon503 |
| Disque libre minimal | 64Mio en plus des nouvelles variantes |
| Suppression non utilisée | Logique, rétention7jours, purge explicite |
| Réconciliation | Clés orphelines >24h, dry-run par défaut |

Quotas recalculés sous verrou Account ; ce verrou protège aussi association et
suppression. Réencodage avant transaction ; nouveaux fichiers retirés si l'écriture
SQL échoue. Les erreurs disque ne laissent pas un lot partiellement visible. Si une réponse COMMIT est ambiguë, les binaires sont conservés tant que leur absence en base ne peut pas être prouvée ; la réconciliation les décide ultérieurement. Une
interruption brutale peut laisser un orphelin ; le nettoyage prend un verrou advisory
par clé, ne supprime que les clés sûres absentes de la base et ignore les clés actives.
Les fichiers inconnus ne sont jamais supprimés récursivement.

Suppression refusée409 si une référence du compte existe dans un design courant ou
une révision, y compris portfolio archivé/supprimé logiquement. Un fichier non utilisé
reste privé7jours après suppression et reste compté dans le quota jusqu'à purge.
La purge revérifie sous verrou, retire les binaires et efface nom/dimensions/hashes ;
il reste un tombstone UUID/account/dates. Les révisions ne sont ni modifiées ni purgées.

Les API utilisent session/CSRF AUTH-001 existants. Le serveur résout les références
pour le portfolio possédé ; hors compte retourne missing sans révéler l'existence.
Chaque accès au fichier refait le contrôle d'autorisation, intégrité taille/hash,
Content-Type image/webp, nom de téléchargement générique, nosniff, CORP same-origin,
CSP restrictive, private/no-store et Vary Cookie. Aucun accès par clé de stockage,
URL publique, CDN ou signature remplaçant une autorisation réelle.

Le transport Next par réécriture tronquait les corps >10Mo. Un Route Handler borné
**uniquement pour /api/v1/media/assets** transmet les corps jusqu'à la limite MEDIA,
Cookie/Origin/CSRF et la réponse Django ; il n'accorde aucune permission. Les limites
AUTH16Kio et autres API ne sont pas relevées. Le multipart12Mio est réellement
exécuté via ce transport dans la recette, et non envoyé directement à Django.

ETag/If-Match, Portfolio.version et révisions append-only sont conservés. La nouvelle
validation n'accepte que des assets prêts du même compte ; un échec laisse document,
version et révision inchangés. Les UUID inconnus pré-MEDIA ne sont pas réparés : les
anciens brouillons restent lisibles mais les références doivent être remplacées ou
retirées pour une nouvelle sauvegarde. Le champ historique media_status de l'API
ready v1 reste sans résolution inline ; la nouvelle route /media est la source de
vérité du client MEDIA. [Détails de compatibilité](usage.md).

## Tests Linux exécutés et preuves

Python backend3.13.5, Node24.19.0/npm11.9.0, TypeScript5.9.3, Next16.4.2,
React19.3.1, Pillow13.0.0 avec codec WebP exécuté. PostgreSQL17.11 dans un conteneur
neuf jetable épinglé par digest. Chromium154.0.8037.57 et Playwright1.62.0 dans
l'outillage Python3.12 existant. Aucune dépendance Node ajoutée ; versions Python
historiques conservées. Les deux locks universels incluent Pillow avec hashes,
dont le wheel CPython3.13 WindowsAMD64 vérifié dans les métadonnées PyPI ; ceci
**ne remplace pas une exécution Windows**.

| Vérification | Résultat | Preuve sous evidence/ |
|---|---|---|
| Suite Django complète AUTH/PORT/TPL/MEDIA | **389 réussis**, dont22 MEDIA | django-tests.log |
| Contrats/renderers/clients et transport Node | **220 réussis**, dont8 MEDIA | node-tests.log |
| Intégrité BASE + initialisation privée | **15 réussis**, dont3 nouveaux | integrity-tests.log |
| CMS historique sur données temporaires | **6 réussis** | legacy-tests.log |
| Référence historique | 11 fichiers identiques,4 checksums de fixture | historical-reference.log |
| TypeScript strict et génération Next | Réussi | typecheck.log |
| Build Next production | Réussi, aucune publication | build.log |
| Migrations et absence de dérive modèle | Réussi dans le cluster neuf uniquement | migrations.log,schema-check.log |
| Runtime PostgreSQL sans DDL/CREATEDB/superuser/BYPASSRLS | Vérifié | runtime-privileges.log |
| Dépendances installées et codecs | Compatibles, WebP utilisé | dependency-check.log,dependency-review.json |
| Parcours navigateur authentifié | **6 groupes réussis**, zéro erreur JS | browser-results.json,browser.log |
| Captures réelles1440/375px | **7 PNG examinés** | editor-*,library-*,portfolio-* |

Total : **630 tests automatiques réussis, zéro ignoré sous Linux**, plus les6 groupes
de recette navigateur. Les22 tests MEDIA sont déjà inclus dans les389, sans double
comptage. Les références HTML v1 Minimal/Editorial, les Hero E.05/E.06, la parité des
contrats et AUTH/session sont réexécutés dans les suites. Le test E.07.04 des14 slots
importe désormais une vraie image synthétique appartenant au compte avant de
remplacer les UUID de démonstration ; aucune fausse autorisation n'a été conservée
pour faire passer un test ancien. Les fixtures/bundles immuables restent identiques.

Les tests couvrent : trois décodeurs, EXIF/orientation, alpha/dimensions et miniature,
fichiers déguisés/corrompus/animés, bombes/pixels/corps/compte, CSRF/anonyme/tiers,
identifiants inconnus, chemins/symlinks/hashes altérés, métadonnées privées, pagination,
erreurs disque simulées et rollback, deux imports concurrents sous
quota et huit téléchargements parallèles identiques, conservation des binaires lors d’une panne de vérification du COMMIT, rétention des trois rôles de
slots et révisions, purge et orphelins dry-run/explicites, garde SQL, OpenAPI réel,
refus d'adopter un dossier existant et de créer .local.

La recette navigateur importe trois originaux **synthétiques générés**, les associe
aux trois rôles, vérifie naturalWidth et chargement effectif, alt et object-position,
enregistre, sort, se déconnecte puis se reconnecte et rouvre. Elle vérifie le refus
anonyme/inter-comptes, un fichier temporairement404 et sa récupération, SVG refusé,
retrait/remplacement sans perte des autres contenus, refus de suppression historique,
un import12Mio via Next et la suppression logique d'une image jamais référencée.
Les modales sont exercées via Escape/focus et les curseurs via clavier. Aucun compte,
photo, fichier d'authentification ou cookie personnel utilisé.

Les captures montrent le vrai Studio et le même renderer, aucune maquette substituée.
Les sept captures sont : bibliothèque desktop/mobile, éditeur desktop/mobile,
portfolio desktop/mobile, erreur bibliothèque. Trois PNG sources synthétiques
supplémentaires sont conservés comme fixtures de recette, pas comptés comme captures.
Le petit indicateur de développement Next peut apparaître ; il n'appartient pas au template.

## Périmètre et réserves

La dernière recette utilise un cluster17 neuf et un stockage TEMP marqué neuf. Le
runner vérifie version/data_directory et identité du conteneur, génère des rôles
et secrets temporaires, fixe ses seules variables enfants, démarre ses propres
Django/Next sur ports loopback libres puis les arrête. Le cluster et le stockage
sont retirés dans finally ; seules les preuves explicitement choisies sont copiées.
Aucune configuration privée ni secret n'est livré.

| Critère | Statut |
|---|---|
| Backend, Asset, migration additive, stockage privé abstrait | Réalisé, testé sur données synthétiques |
| Import et réencodage sécurisé, miniature, quotas | Réalisé, testé |
| Bibliothèque privée, trois sélecteurs sans UUID | Réalisé, testé desktop/mobile |
| Diffusion privée et résolution autorisée | Réalisé, testé avec vraies images |
| Sauvegarde/reconnexion/reprise, ETag et révisions | Réalisé, non-régressions réussies |
| Rétention/suppression, erreurs disque et concurrence | Réalisé, testé |
| Contrats E.07.02, CMS, AUTH et .local | Intacts ; suite et références vérifiées |
| Windows natif MEDIA-001 | **Non exécuté**, runner natif sans Docker fourni |
| Lecteur d'écran | **Non exécuté**, réserve toujours ouverte |
| Base/stockage existants, publication, PR/fusion/déploiement | Non utilisés/non effectués |
| Validation MEDIA-001 | **En attente de votre revue** |

Les deux skips Windows rapportés pour E.07.04 sont une preuve historique utilisateur,
pas des résultats MEDIA-001. Chaque nouveau skip (notamment symlink non autorisé)
doit être consigné, jamais compté réussi. DACL Windows et démarrage natif17 doivent
être confirmés sur le PC. Safari/Firefox, appareil mobile physique, lecteur d'écran,
charge/mémoire de production et audit exhaustif de codecs ne sont pas certifiés ici.

WebP est avec perte et les profils ICC sont retirés : les photos réelles pourront
nécessiter une recette colorimétrique ultérieure ; aucun original brut n'est conservé.
Deux décodeurs par processus ne constituent pas une file distribuée ni une politique
anti-abus complète de production. Les quotas incluent les médias historiques protégés :
une future politique de rétention des révisions sera nécessaire pour les libérer.
Le fournisseur objet, sauvegarde DB+binaires persistante, restauration de sauvegarde
réelle et déploiement restent à autoriser séparément. Aucun passage sur la base
habituelle ne doit être déduit de cette livraison.

**Arrêt après MEDIA-001. PUB-001 n'est pas commencé. Attente de la revue utilisateur.**

## Suivi — correctif Windows DACL

Recette Windows rapportée : 389 tests, 10 échecs, 6 erreurs, 3 ignorés.
Correctif ciblé OWNER RIGHTS proposé pour revue : [diagnostic, preuves et commandes](windows-acl-fix.md).
La validation Windows du correctif et l’analyse individuelle des traces complètes
restent ouvertes. Aucun push, PR, merge, déploiement ou PUB-001.

## Suivi — WinError 32 après confirmation ACL Windows

L’utilisateur confirme 25/25 tests ACL natifs réussis sur `4ad0e268`, puis une
seule erreur de nettoyage dans la suite Django (391 exécutés, trois ignorés).
Le correctif complémentaire ferme la réponse de streaming abandonnée par le test,
sans modification du code applicatif : [rapport WinError 32](windows-winerror32-fix.md).
Preuves finales Linux : 393 Django réussis, 22 contrôles hors base réussis et
3 contrôles DACL Windows ignorés, 6 CMS réussis. Les clusters/stockages sont neufs
et jetables. Validation Windows complémentaire encore ouverte ; commit local
pour revue, sans push, PR, merge, déploiement ni PUB-001.

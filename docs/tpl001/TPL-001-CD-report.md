# TPL-001.C+D — Livraison fonctionnelle pour revue

Date : 19 octobre 2026 (Africa/Douala). Branche : **`feature/tpl-001-cd`**.

**Implémenté et vérifié sous Linux ; revue utilisateur attendue. TPL-001.E non commencé.** Les vérifications obligatoires ci-dessous font partie de la livraison C+D autorisée, sans clôture anticipée de TPL-001 ni déploiement.

## Références et périmètre

Branche créée depuis le correctif Windows **`99b2269`**, descendant de la livraison B **`730384b`**. La recherche des branches distantes n’a révélé aucun commit de clôture B supplémentaire à intégrer. Les clôtures documentaires PORT antérieures sont conservées dans l’ascendance. Aucun merge ni réécriture d’historique.

Implémentation : `0d7a202`. Référence source avec le script final de preuves : **`e14139c57ea7f4f6dc16cd40f11ae4965078c305`**. Un commit documentaire ultérieur ajoute ce rapport, l’inventaire et les preuves ; il ne remplace pas la référence de code.

Contrats : [architecture A](design.md), [contrat API C+D actif](../../contracts/api/template-instances.v1.json), [schémas versionnés](../../contracts/schemas/templates/documents/). Le contrat AUTH et les schémas des documents de B ne sont pas modifiés. Les bundles B et leurs empreintes restent intacts.

## Backend livré

- **PortfolioDesign** : UUID indépendant, OneToOne Portfolio, documents JSONB distincts (composition/contenu/présentation/personnalisation/expérience), version de schéma et empreinte SHA-256 du snapshot source. Aucune propriété de compte dupliquée ; autorisation par Portfolio.account et ses invariants existants.
- **TemplateCreationRequest** : clé UUID liée à l’utilisateur et son compte, digest canonique de la requête normalisée, réponse de création et ETag originaux, expiration à 24 h. Contrainte unique et verrouillage du provisioning empêchent deux créations concurrentes pour la même clé. Une requête modifiée sous la même clé renvoie 409. Une clé rejouée ne remet pas en circulation un portfolio supprimé ou inaccessible.
- **Création transactionnelle** depuis une paire exacte id/version disponible, sans latest implicite. Échec de copie du design → rollback de Portfolio, Design et clé. Délais de verrou bornés ; attente excessive → 503 réessayable avec la même clé. Aucun champ account/owner/source n’est assignable par le client.
- Les documents de l’instance sont copiés ; lecture/édition/duplication ne rechargent pas le catalogue. Le retrait ou l’indisponibilité future d’un template ne réécrit pas l’instance. La version de document reste validée contre son schéma immuable, indépendamment de la disponibilité du catalogue.
- **GET/PUT design**, état privé, no-store. Lecture cohérente sous verrou Portfolio. Sauvegarde complète de content/customization uniquement ; composition, thème, provenance et expérience restent protégés. JSON Schema et invariants transversaux appliqués côté serveur.
- **Portfolio.version canonique**, partagé par les métadonnées, le design et les actions PORT. If-Match obligatoire, 428 absent / 412 périmé. Ordre de verrouillage Portfolio puis Design ; sauvegarde acceptée incrémente une seule fois le compteur. Aucune écriture forcée lors d’un conflit.
- **Duplication complète** via la route PORT existante : nouveau Portfolio et Design, nouveaux UUID des projets locaux, mêmes valeurs éditées et provenance source, aucune ressource JSON mutable partagée. La source reste intacte. Les portfolios vierges se dupliquent comme auparavant, sans design inventé.
- Nettoyage d’idempotence par `prune_template_requests` (comptage seul) ou `--execute` (suppression des réponses expirées, jamais des portfolios). La déduplication logique expire exactement après 24 h ; le nettoyage physique dépend de l’exécution de cette commande. Sa planification d’exploitation reste à configurer ultérieurement, sans déploiement ici.

### Migrations additives et données

Une seule **nouvelle migration** `templates/0001_initial.py` ajoute les tables/contraintes. Aucune migration historique modifiée, aucun backfill. Le précontrôle bloque une provenance de template préexistante sans design, au lieu d’inventer ou réparer des données. UUID, versions, dates, états et données des portfolios vierges préservés.

Exécution réelle uniquement sur une **nouvelle base PostgreSQL synthétique isolée C+D**, avec nouveaux rôles et secret, plus les bases de tests temporaires. Aucune migration de la base PORT de validation existante, d’une base réelle ou de `.local/`. Les helpers de préparation Windows ne font que générer une configuration privée séparée ; les commandes de création et migration restent explicites.

Retour arrière : avant toute écriture, migration réversible après vérification ; après création d’instances, ne pas supprimer les tables pour revenir à B. Désactiver les nouvelles écritures et corriger en avant, ou restaurer une sauvegarde vérifiée avec autorisation. Les FK PROTECT et la suppression logique conservent les ressources liées ; aucune purge de portfolios dans cette livraison.

### Sécurité et cohérence des contrats

La limite globale AUTH de **16 Kio reste inchangée**. Un middleware borné aux deux nouvelles routes POST from-template / PUT design autorise **256 Kio maximum**, avant parsing ; il ne change aucun réglage global par requête et ne désactive pas session/CSRF. Le parser strict refuse les clés JSON dupliquées. Tests explicites : design valide supérieur à 16 Kio accepté, requête supérieure à 256 Kio rejetée, requête AUTH supérieure à 16 Kio toujours refusée.

Textes bruts échappés par React, liens HTTPS sans identifiants, thèmes/réglages fermés, variantes et ancrages respectés, expérience strictement null. Aucun upload, CSS/HTML libre, palette libre, moteur 3D, paiement, publication ou accès public.

Le contrat actif ajoute uniquement les routes autorisées de création et design. Les réponses réelles 201/200 sont validées avec formats contre OpenAPI ; les tests couvrent erreurs 400/401/403/404/409/412/428 et protections de taille. Les erreurs restent génériques, sans SQL, chemin privé ou contenu sensible. Les routes B et les contrats PORT existants sont conservés.

## Studio livré

1. **Bibliothèque** : deux cartes de composition distincte, miniatures issues du même renderer responsive, filtres Minimal/Editorial, aperçu desktop/mobile et action « Utiliser ce template ».
2. **Création** : nom/slug, validation et états d’erreur/chargement, verrou de soumission immédiat et clé d’idempotence conservée pour un retry de la même intention. Une création réussie redirige vers l’éditeur privé.
3. **Éditeur** : navigation par sections, formulaires typés, aperçu en direct et enregistrement explicite. Hero, à propos, projets (ajout/retrait/titre/résumé/lien), compétences (ajout/retrait), contact, ordre/visibilité autorisés, espacement/alignement/emphase et remise à la présentation de base.
4. **Restrictions réelles** : Hero reste obligatoire ; les sections ancrées ne se déplacent pas ; seules les autres occupent les emplacements libres. Les données des sections masquées sont conservées. Aucun changement de variante, composition ou thème arbitraire.
5. **Sauvegarde** : état modifié détecté, avertissement sur les liens, Retour et déchargement de page ; confirmation avant déconnexion demandée. Conflit 412 : brouillon local conservé en mémoire, sauvegarde bloquée, rechargement serveur uniquement après confirmation de remplacement. Aucune fusion automatique ni conservation du contenu privé dans localStorage.
6. **Persistance** : rechargement et nouvelle connexion relisent les documents enregistrés. Une session expirée demande une reconnexion ; un brouillon non enregistré n’est pas une sauvegarde. Les données ne sont jamais publiées automatiquement.
7. **Dashboard** : badge du template, action « Modifier le portfolio », fonctionnalités PORT conservées, gestion des portfolios vierges, duplication, archivage et restauration. Les archives restent privées et leur éditeur est en lecture seule.

Les exemples de démonstration restent dans les aperçus du catalogue. Une nouvelle instance commence avec des contenus neutres : titre issu du nom du portfolio, listes vides et textes éditables. Aucun nom, projet ou commentaire fictif n’est imposé. Les compteurs et libellés des projets suivent les données ; les visuels décoratifs utilisent le titre local et ne portent les noms fictifs que dans la démonstration.

Panneaux/cartes/champs suivent le mode sombre du Studio et les boutons restent légèrement arrondis. Le portfolio rendu conserve le thème neutre clair de ce lot, indépendant du thème de l’interface ; aucune palette ou sélection de thème supplémentaire n’est introduite.

## Vérifications et preuves

Environnement : Linux, Python 3.13.5, PostgreSQL 17.11 réel, Node 24.19/npm 11.9, Next/React/TypeScript verrouillés inchangés, Chromium 154. Aucune nouvelle dépendance ni modification de lockfile.

| Contrôle | Résultat |
|---|---|
| Suite Django complète | **86/86 réussis** : 74 historiques + 12 nouveaux tests C+D |
| C+D ciblé après assertions de contrat et contrôles complémentaires | **12/12**, déjà compris dans 86, pas de double comptage |
| BASE / CMS historique | **12/12 + 6/6** |
| Clients health / AUTH / PORT / renderer B | **3/3 + 4/4 + 6/6 + 6/6** |
| Nouveau client des instances | **4/4** |
| Total distinct automatique | **127 réussis**, aucun échec ni skip sous Linux |
| Typecheck / build production | Réussis |
| Django / vérification migrations | Aucun problème, aucun changement de modèle sans migration |
| PostgreSQL runtime/test | UTF8, moindre privilège et accès de maintenance des tests vérifiés |
| Contrôles sources / bundles / preuves B | Inchangés, hors fichiers SaaS autorisés et nouvelle migration |

Les tests de migrations utilisent uniquement les bases temporaires de tests : parcours historiques AUTH/PORT conservés, nouvelle migration préservant un portfolio vierge et blocage d’une provenance incohérente sans réparation. Les tests de concurrence ouvrent deux connexions PostgreSQL : même clé → une seule instance ; sauvegarde design contre PATCH Portfolio avec même ETag → une réussite et un 412.

Chromium, **pour Minimal et Editorial** : bibliothèque → création (double clic : un seul POST) → personnalisation des cinq types → erreur HTTPS 400 → correction → ordre/visibilité/présentation → enregistrement → rechargement → conflit 412 avec brouillon conservé → duplication indépendante → archive/restauration → déconnexion/reconnexion et restitution du design. Vérifiés aussi : annulation de navigation avec données non enregistrées, absence de débordement à 1440/900/390 px, modes clair/sombre et zéro erreur de page. L’isolement inter-comptes est testé par l’API ; aucun audit d’accessibilité assistive complet n’est revendiqué.

Preuves : [résumé](cd-evidence/validation-summary.json), [Django](cd-evidence/django.txt), [C+D ciblé](cd-evidence/instances.txt), [build](cd-evidence/build.txt), [types](cd-evidence/types.txt), [client](cd-evidence/client.txt), [résultats navigateur](cd-evidence/browser-results.json). Captures : [création](cd-evidence/create-minimal.png), [conflit](cd-evidence/conflict-editorial.png), [bibliothèque sombre](cd-evidence/library-dark.png), [bibliothèque mobile](cd-evidence/library-mobile.png), [bibliothèque](cd-evidence/library-desktop.png), [Minimal desktop](cd-evidence/editor-minimal-desktop.png), [Editorial desktop](cd-evidence/editor-editorial-desktop.png), [Minimal mobile](cd-evidence/editor-minimal-mobile.png), [Editorial mobile](cd-evidence/editor-editorial-mobile.png), [tablette](cd-evidence/editor-minimal-tablet.png), [sombre](cd-evidence/editor-minimal-dark.png), [dashboard](cd-evidence/dashboard-templates.png). Les captures sont synthétiques et inspectées visuellement, jamais des maquettes remplaçant le rendu réel.

## Limites et réserves explicites

- **Windows natif C+D NON EXÉCUTÉ**. [Guide complet et commandes](TPL-001-CD-windows.md). Le correctif UTF-8 est inclus ; le skip symlink rapporté sur Windows B reste une limitation distincte, sans être déclaré réussi.
- E, publication publique, médias, moteur immersif et éditeur visuel libre non commencés. Les projets sont des éléments de contenu de cette version, pas un nouveau modèle métier de Case Study Builder.
- Le brouillon non enregistré vit en mémoire. Un rechargement confirmé, une fermeture confirmée ou une perte du processus le perd ; aucune sauvegarde privée dans localStorage. Le conflit n’applique pas automatiquement les changements locaux à une version distante : l’utilisateur garde son brouillon tant qu’il ne confirme pas le remplacement.
- Une intention de création est conservée dans le formulaire ouvert. Après rechargement ou expiration de 24 h, vérifier le dashboard avant de relancer une nouvelle intention. Le nettoyage physique des anciennes réponses nécessite la commande documentée et une planification ultérieure.
- Les essais navigateur créent des utilisateurs et portfolios synthétiques dans la base C+D jetable uniquement ; aucun fichier d’authentification ou mot de passe ne figure dans les preuves. Aucune validation CI GitHub distante n’est déduite de l’ajout des commandes CI.

## Livraison et critères

[Inventaire exhaustif relatif à `99b2269`](TPL-001-CD-files.txt). Nouvelle migration uniquement, contrats et helpers explicites, aucune dépendance nouvelle. Les fichiers fonctionnels historiques et `.local/` sont intacts ; les données réelles n’ont pas été migrées ou copiées.

| Critère utilisateur | Statut |
|---|---|
| Créer depuis les deux templates | Vérifié API et navigateur |
| Personnaliser et enregistrer les champs autorisés | Vérifié, validation serveur conservée |
| Retrouver après rechargement et reconnexion | Vérifié pour les deux templates |
| Idempotence et double clic | Vérifiés par API, deux connexions et navigateur |
| ETag/conflits et conservation du brouillon | Vérifiés |
| Isolation, CSRF, UUID, états privés, duplication | Vérifiés ; aucune publication |
| Portfolios vierges et migrations historiques | Préservés et tests réussis |
| Responsive, mode sombre, captures | Vérifiés Linux Chromium |
| Windows | À exécuter, aucun succès revendiqué |
| Revue et acceptation C+D | **En attente** |

Aucun merge, déploiement, migration de base réelle ou phase E. Attendre la revue de cette livraison.

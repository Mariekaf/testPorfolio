# E.07.02 — Contrats hors ligne des templates complets

Version livrée pour revue, 20 octobre 2026, Africa/Douala. Parent documentaire :
`329101d17a6566e6fa512094d782cd723707f6ae`.

## Ajustements conditionnels appliqués

La décision utilisateur approuve E.07.01 sur le principe et autorise **uniquement
les contrats, politiques, registre hors ligne et fixtures E.07.02**. Elle ne vaut
pas approbation du présent code. Ses sept conditions priment sur les propositions
historiques R01–R10, conservées telles quelles au commit de revue :

1. Familles v1/v2/v3 séparées, contrats et instances historiques inchangés.
2. Composition et bindings verrouillés ; seules valeurs de slots et overrides
   autorisés peuvent varier dans une instance v3.
3. Brouillons incomplets permis. Creative Editorial exige pour l'évaluation de
   préparation identité, titre, **au moins un projet réel**, un contact valide et
   des médias prêts/autorisés quand référencés. Le choix E.07.01 de permettre
   zéro projet à la publication est remplacé.
4. Références de polices autorisées par ID/version, sans téléchargement ou chargement.
5. UUID médias et faits de validation indépendants du stockage. Aucun fournisseur,
   quota de stockage ou durée de rétention décidé. Les chiffres suggérés E.07.01
   restent des propositions non adoptées.
6. Publication publique dans un **ticket PUB dédié**, non dans E.07.02 ni implicitement
   dans E.07.04. Tout DDL exige un plan et une autorisation SQL spécifiques.
7. Aucune conversion automatique v1/v2 ; les chemins E.04/E.05/E.06 restent inchangés.

## Fichiers et versions

Nouveau namespace `contracts/schemas/ready/`, sans élargissement d'un ancien schéma :

| Fichier | Rôle |
|---|---|
| snapshot.v3.json | Enveloppe Design3/composition3/content2/presentation3/customization3/experience null |
| content.v2.json | Sept types de slots, objets fermés, limites et UUID canoniques minuscules |
| descriptor.v2.json | Creative Editorial1.0.0, 14 slots et limites locales exactes, politique de publication |
| style-policy.v1.json | Deux palettes, références autorisées de polices |
| fonts.v1.json | Références système versionnées autorisées, sans URL et load_required false |
| responsive.v1.json | Mobile≤639, tablette640–1023, desktop≥1024 ; pas d'héritage tablette→desktop |
| manifest.v2.json | Statuts, six payloads, tailles, hashes et digest composé |
| assessment-facts.v1.json | Faits d'évaluation de confiance, hors document utilisateur |

Le bundle `contracts/ready-templates/creative-editorial/1.0.0/` contient exactement
six JSON : descriptor, snapshot neutre, style-policy, fonts, responsive et
**demo-content séparé**. Aucun média réel et aucun renderer complet n'est livré.
Le snapshot de création est vide et structurellement valide ; les textes fictifs
ne sont jamais copiés implicitement depuis la démonstration.

Le seul template et la seule version reconnus sont Creative Editorial1.0.0.
Étendre le registre à une nouvelle famille/version demande un nouveau contrat et
une revue ; pas de plugin ou code tiers téléchargé depuis un descriptor.

## Registre et empreintes

Python : `modules.templates.ready_registry.ReadyRegistry`.
Node : `packages/content-contracts/src/ready-registry.ts`, `loadReadyRegistry`.
Ce sont des bibliothèques **hors ligne**, sans import dans views, settings, routes,
éditeur ou registre v1. Elles lisent exclusivement les nouveaux contrats Git.

Le manifeste a schema_version2 et digest_algorithm `sha256-list-v1`. Pour chaque
entrée, vérifier rôle unique, chemin exact `id/version/role.json`, taille réelle,
SHA-256 des octets, puis digest global : trier les fichiers par chemin ASCII,
projeter chaque fichier sur les clés **path, bytes, sha256 dans cet ordre**, sérialiser
la liste en JSON UTF-8 compact (sans espaces), SHA-256. Le manifeste est exclu,
donc aucune empreinte circulaire ; les zéros de l'exemple E.07.01 ont été remplacés
par un vrai digest. Les JSON installés sont en UTF-8/LF ; une réécriture CRLF des
payloads immuables modifie leurs hashes et doit être refusée. Le checkout Git de
ces nouveaux JSON est fixé en LF par `contracts/ready-templates/.gitattributes`,
sans changer les règles des bundles historiques ; **aucun bypass de hash n'est permis**.

Paths absolus, traversée, antislash Windows, rôles/path en double, collision de
casse, symlink de payload, UTF-8 invalide, BOM, clés JSON dupliquées, NaN/Infinity
et profondeur excessive sont refusés. Les exemples d'erreurs n'exposent pas les
fichiers ou valeurs reçus. L'arbre des bundles doit rester un artefact Git de
confiance en lecture seule à une future intégration, pas un dossier d'uploads.
Ces gardes ne prétendent pas remplacer les ACL système ou rendre sûr un arbre
modifié concurremment par un processus local privilégié.

Le manifeste contient une entrée **draft**. `available` et `preview` sont refusés
par cette livraison car renderer complet/médias/publication ne sont pas implémentés.
`deprecated`, `retired`, `quarantined` sont des états de conservation lisibles hors
ligne ; ils n'activent aucune création. Le descriptor reste le contrat draft de
cette version ; l'état de découverte du manifeste peut empêcher son usage, sans
modifier ses payloads. Les capacités déclarées sont typed-slots-v2 (validation
implémentée), ready-renderer-v1, safe-media-v1, manual-publication-v1 (non implémentées).
Aucune méthode de catalogue utilisateur ni état selectable disponible.

## Validation de documents et politiques

`ReadyValidator.validate(document)` / `createReadyValidator(...).validate(document)`
valident le document entier puis retournent palette effective, référence de police
et IDs de sections visibles. Ce résultat n'est ni du HTML ni une sauvegarde.
Les entrées et le bundle sont copiés ; leurs mutations ne sont pas des permissions.

Le contrat impose les six sections et leurs bindings exacts : navigation, Hero,
about, projets, contact, footer. Les limites locales des 14 slots sont figées par
la version du descriptor, pas définies par le client. Les IDs projets sont uniques.
Un même type de slot ne peut pas être glissé dans un binding différent.

Textes : points de code Unicode, UTF-8 strict, aucun surrogate isolé. Les emoji
comptent un point de code, pas deux unités UTF-16. Espace blanc : ensemble explicite
partagé Python/JS (incluant FEFF et NEL), sans trim à la sauvegarde. Rich text :
paragraphes et marques strong/emphasis uniquement, plafond global/local cumulatif,
aucun HTML/Markdown libre. Un texte littéral contenant `<script>` reste du texte ;
aucun renderer n'est activé dans ce ticket.

Les JSON sur disque sont limités à 256 Kio et les valeurs en mémoire à une
**comptabilité conservative partagée** de 256 Kio, profondeur32 : nombres coût24,
booléens5, structures/clés/chaînes comptées de façon déterministe, échappements
potentiels inclus. Cela évite les écarts de sérialisation de floats Python/JS.
Le budget mémoire peut donc refuser un document un peu avant sa taille JSON exacte.
Ces bornes de contrat ne sont pas des quotas de médias ou des décisions de rétention.

Liens : union section/external/email fermée. HTTPS ASCII sans identifiants,
contrôle, antislash ou port invalide ; DNS syntaxique borné, pas d'IPv6 ni hôte
Unicode brut dans cette première version (forme ASCII IDNA préalablement fournie
possible). Aucune résolution DNS ni fetch externe. Email simple ASCII validé,
pas de paramètres mailto utilisateur. Projet : cible externe ou null, aucune
page case study inventée. Social : réseau autorisé, domaine attendu ou HTTPS
`other`, doublons de réseau refusés. Liens internes seulement vers sections présentes.

Les brouillons acceptent textes/titres de carte/libellés/alt vides, zéro projet,
absence d'image et de contact. Les données bien typées mais incomplètes restent
privées. About/projets/contact sans contenu utilisable sont omis du résultat de
visibilité ; navigation future devra suivre ce résultat. Un lien défini vers
une section absente est invalide, non remplacé par `#`.

Images/logos/covers : UUID, alt, decorative et focal_point normalisé uniquement,
aucun objet storage_key, chemin ou URL. Pour ce template ces emplacements sont
informatifs : decorative=true est refusé. Alt vide possible en brouillon mais
bloque la préparation. Les fichiers/références UUID ne sont pas résolus par le
validateur structurel : la vérification de médias relève du contexte ci-dessous.
Aucun import réel, traitement d'image, stockage ou pipeline de droits ici.

## Couleurs et polices

Deux palettes concrètes ink-lime/paper-cobalt ; seules quatre couleurs hex6 peuvent
être overridées. Priorité defaults → palette sélectionnée → overrides par couleur.
Les defaults copiés et leur policy_ref ne peuvent être réécrits par le client.
Toutes les palettes du bundle et les valeurs effectives doivent respecter 4,5:1
texte/background, texte/surface et accent/surface, sans arrondi. Les propriétés
inconnues, CSS arbitraire, null et hex avec caractère final caché sont refusés.

Reset : suppression de la clé d'override ; absence = héritage. Une palette
nouvelle ne supprime pas les couleurs explicites. Le futur formulaire doit le
montrer ; ce ticket ne construit pas de fonction d'éditeur.

`font_ref` est un couple exact id/version autorisé par la politique et le registre
fonts. `system-sans@1.0.0` et `system-serif@1.0.0` représentent deux familles
**génériques système**, sans ressource redistribuée ni chargement obligatoire.
Ce ne sont pas des polices propriétaires fictivement licenciées. Aucune URL,
police uploadée ou version inconnue. Une paire tierce ultérieure nécessitera
licence, contrat versionné et renderer validés. Ces références restent dans la
famille v3 ; elles ne sont pas injectées dans HeroConfig1 qui ne connaît que
system-sans. L'adaptateur de rendu futur devra traiter ce point explicitement.

## Évaluation de contenu, aucune publication

`readiness(document, facts)` renvoie **content_ready**, une liste de codes stables,
et **publication_enabled:false toujours**. Ce n'est jamais une décision Publish.
Les faits sont validés par assessment-facts.v1, pas stockés dans content/customization.

Le futur service authentifié devra construire les faits depuis le compte propriétaire :
account_id canonique, **verified_user_project_ids limités aux projets de ce même
compte et dont la provenance utilisateur a été vérifiée**, assets UUID et leurs
account_id/state/rights_confirmed. Ni ces IDs ni l'attestation de « réel » ne
peuvent venir de la requête client ou d'un marqueur de démo. Le contrat hors ligne
ne peut vérifier l'existence ou la réalité d'un travail ; ses fixtures simulent
explicitement ces faits, sans créer de projet, compte ou média.

Conditions Creative Editorial : identité et titre non blancs, au moins un ID
projet connu des faits fiables avec titre non blanc, contact externe/email ou
social valide **avec libellé non blanc**, et pour chaque média : alt présent,
asset ready, même compte, droits confirmés. UUID absent, compte étranger, média
processing ou droits absents ont la même erreur `media_unresolved:UUID`.
L'évaluation sans compte ne peut pas attester un projet réel. Les inconnus dans
les faits sont refusés ; impossible d'envoyer publication_enabled=true.

Même avec content_ready=true, l'absence de renderer, stockage, publication et
contrôles SQL réels maintient publication_enabled=false. Aucun endpoint ne reçoit
ces faits dans ce ticket.

## Compatibilité et tickets suivants

Aucun fichier historique de contrats, renderer, AUTH, CMS, instance ou transition
n'est modifié. V1/v2 gardent leurs façades et comportements ; le nouveau validateur
refuse un ancien document plutôt que de le convertir. Les snapshots v3 ne sont
pas acceptés par le SQL ou les APIs actuels, qui gardent leurs contraintes. Ne pas
importer les fixtures dans une base. Aucun tableau de contraintes n'est élargi.

E.07.03 reste non autorisée : renderer complet, médias privés et vraie preview
nécessiteront une revue distincte et une autorisation pour tout DDL. E.07.04 ne
porte plus implicitement la publication : instances/formulaire sont séparés de
**PUB — Publication publique**, ticket dédié avec revue de release/pointeur/états
et autorisation SQL explicite. Aucune conversion automatique v1/v2 n'est prévue.

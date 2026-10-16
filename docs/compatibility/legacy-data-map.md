# BASE-001 — Carte des données et invariants de migration

Document descriptif, sans importeur ni modification du CMS.

## Périmètre réel

Le dépôt ne contient pas toutes les données utilisateur. Le dossier choisi par `PORTFOLIO_DATA_DIR` (résolu depuis le dossier de travail pour un chemin relatif) ou `.local/` à côté de `server.py` contient l'état effectif. Chaque installation locale doit être inventoriée séparément. Ne pas supposer que le dossier de l'environnement cloud représente le PC Windows.

| Source | Contenu | Destination/consigne future |
|---|---|---|
| content.json | revision, site, projects | Portfolio de travail, accueil, projets/pages/blocs ; source archivée immuable |
| content.backup.json | Document précédemment enregistré | Historique importé séparément si présent et valide |
| uploads/ | Fichiers, y compris orphelins | Originaux conservés avec SHA-256 et correspondance de chemins |
| auth.json | Paramètres/empreinte scrypt | Sauvegarde privée uniquement ; jamais fixture, Git ou export partagé |
| initial-password.txt | Secret initial si présent | Même confidentialité ; ne pas recopier dans les livrables |
| exports hors de ce dossier | JSON/ZIP manuels | Inventaire distinct, pas de recherche automatique de fichiers privés |

## Contrat JSON historique

Pas de schema_version aujourd'hui. revision est le compteur global d'écritures, pas une version de format. Le document généré a revision=0 ; chaque sauvegarde augmente le compteur de 1 après comparaison de la révision cliente. Une ancienne révision entraîne 409.

### site

- Chaînes jusqu'à 5 000 caractères : name, job, location, availability, heroTitle, heroDescription, projectsTitle, projectsIntro, aboutTitle, aboutIntro, aboutText, skills, contactTitle, contactText, email, footer, photoAlt.
- name obligatoire ; email vide ou de forme e-mail. skills reste une chaîne séparée par virgules : ne pas réinterpréter ou perdre l'original pendant l'import.
- photo : chemin local autorisé ou URL HTTP(S). socials : liste ordonnée de `{label, url}`.
- theme : background, text, accent, surface en hex #RRGGBB ; font sans/serif ; radius square/soft/round ; density compact/airy ; columns one/two.

### projects

- Tableau ordonné, IDs texte 1–80 caractères `[A-Za-z0-9_-]`, pas nécessairement UUID. Conserver legacy_id et établir un mapping.
- slug en minuscules/chiffres/tirets, maximum 100 caractères, unique dans le document.
- Chaînes jusqu'à 20 000 caractères : id, slug, title, category, summary, role, duration, year, tools, coverAlt (avec restrictions supplémentaires ID/slug). title obligatoire. year et duration ne sont pas des nombres à normaliser sans validation.
- published est vrai uniquement si le JSON contient le booléen true. Ne pas assimiler une chaîne « true » à true.
- cover, coverAlt, color, links ordonnés et sections ordonnées.
- Chaque section : title (200), body (20 000), image (URL/chemin), alt (500), caption (1 000). Pas d'ID de section aujourd'hui : attribution future stable lors de l'import, sans modifier l'ordre.
- Une section devient d'abord un bloc `legacy.case-section@1` pour préserver exactement le groupement titre/récit/image/légende.

### URL, médias et options

URLs HTTP/HTTPS avec hôte et sans identifiant/mot de passe dans l'URL. Chemins locaux uniquement `/uploads/<32 caractères hex minuscules>.<png|jpg|webp|gif>`. Limite URL : 2 000 caractères. Les médias externes ne sont pas inclus dans un export ZIP : conserver leur URL et les marquer externes, sans téléchargement automatique.

L'alt et la légende sont des propriétés d'usage : deux sections peuvent utiliser le même original avec des descriptions différentes. Les variantes optimisées futures ne remplacent pas l'original.

## Invariants à vérifier avant une bascule

1. Compter tous les projets, sections et liens avant/après ; conserver leurs ordres.
2. Conserver les chaînes, accents, caractères non latins, paragraphes et champs vides. Aucun HTML historique ne devient exécutable.
3. Conserver IDs historiques, slugs et routes ; signaler les collisions au lieu de renommer sans accord.
4. Comparer empreinte et taille de chaque média, y compris orphelins et références cassées ; ne pas purger un orphelin.
5. Conserver les valeurs de thème ; utiliser un thème de compatibilité pour le rendu initial.
6. Distinguer le booléen published historique de la publication du nouveau SaaS. Construire une publication initiale seulement après validation du propriétaire ; les sauvegardes suivantes restent des brouillons.
7. Conserver source brute et sauvegarde précédente. Refuser la perte silencieuse des champs inconnus ou des listes trop longues.
8. Ne pas utiliser `validate()` comme importeur : il ignore des clés inconnues et tronque des listes. BASE-001 s'en sert seulement pour vérifier une fixture volontairement dans ses limites.
9. Ne pas déduire le compte SaaS de l'e-mail public. Prouver l'accès à la source dans le futur processus d'import.

## Cas de vérification à préparer pour IMPORT-001 (non implémentés)

Document vide/partiel ; plus de 100 projets/60 sections/10 liens ; clé inconnue ; slug dupliqué ; ID non UUID ; média absent ; orphelin ; URL externe indisponible ; deux installations avec mêmes IDs ; interruption/reprise ; sauvegarde précédente invalide ; très gros média ; archive avec chemins relatifs dangereux ; schéma futur inconnu.

Les cas hors limites ne sont pas injectés dans les vraies données ni corrigés dans BASE-001. Les écarts font l'objet d'un rapport avant migration.

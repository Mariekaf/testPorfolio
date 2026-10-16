# BASE-001 — Matrice de compatibilité

Référence historique : `bf8952534bf8a17e7eb4521fee91d62409edc62a`.

Légende des preuves : **H1/H2/H3** = tests historiques auth, médias et persistance (chacun aussi exécuté avec cp1252 simulé). **F** = vérificateur stdlib des sources/fixtures. **B01–B12** = scénarios navigateur supplémentaires isolés. **S** = lecture des sources, pas un test comportemental exécuté. Résultats exacts dans [le rapport](BASE-001-report.md) et `evidence/` ; S ne doit pas être lu comme « test réussi ».

| ID | Fonction à préserver | Données/source | Scénario de référence | Preuve prévue | Destination SaaS |
|---|---|---|---|---|---|
| C01 | Connexion/déconnexion et erreurs | session, admin.js | Refuser mauvais mot de passe, ouvrir puis révoquer session | H1, B03 | identity |
| C02 | Auth privée, CSRF, fichiers privés | Handler | Accès sans session 401, mutation sans CSRF 403, fichier privé 404 | H1 | identity/security |
| C03 | Limitation des connexions, expiration | ATTEMPTS, SESSIONS | 10 échecs/5 min ; expiration après huit heures | S | security, stockage partagé |
| C04 | Origine et en-têtes | same_origin/respond | Refuser origine différente, conserver CSP et no-store privé | S | middleware/proxy |
| C05 | Page d'accueil et portrait | site | Vérifier titre multiligne, portrait et présentation synthétiques | B01 | renderer home |
| C06 | Navigation et à propos | site, HTML | Ancres, contenu, compétences et pied de page | B01, S | pages/navigation |
| C07 | Grille publiée et ordre | projects[] | Seuls alpha/gamma visibles et dans cet ordre | F, B01 | projets/publication |
| C08 | Page dédiée et rechargement | slug, sections | Ouvrir puis recharger /projet/alpha | B02 | pages/routes |
| C09 | Métadonnées et liens projet | rôle, durée, outils, liens | Vérifier informations et lien prototype sans contacter l'URL | B02 | projet/renderer |
| C10 | Récit et médias de section | title/body/image/alt/caption | Paragraphes/Unicode conservés, texte HTML affiché littéralement | F, B02 | bloc legacy.case-section |
| C11 | Navigation projet suivant | ordre public | Passer d'alpha à gamma | B02 | renderer |
| C12 | Projet introuvable et erreur de chargement | casePage/start | Message introuvable ; chargement/erreur/réessayer spécifiés | B02 pour introuvable, S pour erreur réseau | vrais statuts HTTP/états UI |
| C13 | Contact et réseaux | email/socials | mailto correct, liens externes protégés | B01, B08 | contenu portfolio |
| C14 | Contact masqué sans e-mail | email vide | Retirer e-mail et vérifier absence de bouton | B08 | contenu portfolio |
| C15 | Création et métadonnées projet | projects[] | Nouveau brouillon, slug et résumé sauvegardés | B04 | content |
| C16 | Duplication | projet/sections | Nouvel ID/slug et published=false | B06 | content command |
| C17 | Suppression | projects[] | Confirmation puis sauvegarde, disparition du projet dupliqué | B06 | content command |
| C18 | Ordre des projets | projects[] | Déplacer et vérifier l'ordre après sauvegarde | B06 | content order |
| C19 | Ajouter/supprimer/réordonner sections | sections[] | Ajouter une section, déplacer puis retirer une section de test | B05 | case builder |
| C20 | Liens ajoutables/supprimables | links[] | Modifier la liste et sauvegarder | B05 | contenu structuré |
| C21 | Upload, aperçu et alt | cover/sections | Importer PNG synthétique et afficher sa couverture | H2, B04 | media privé |
| C22 | URL/retrait de référence image | imageField | Modifier référence sans effacer l'original | S, B05 pour retrait | media usage |
| C23 | Formats, limite et rejet SVG | upload/read_body | PNG accepté, SVG refusé ; limites 12 Mio spécifiées | H2 pour formats ; S pour limite | media validation |
| C24 | Paramètres identité/accueil/à propos | site | Formulaires de chaque champ inventoriés ; modifier présentation | B08, S pour tous les champs | portfolios/pages |
| C25 | Palette et options du thème | site.theme | Sauver couleurs et options, vérifier attributs et variables publics | B09 | thème compatible |
| C26 | Aperçu de palette | themeView | Échantillon suit l'accent choisi | B09 | studio appearance |
| C27 | Responsive et réduction mouvements | CSS | Absence de débordement mobile ; règles reduced-motion inventoriées | B12 pour viewport, S pour accessibilité complète | renderer/design system |
| C28 | Aperçu privé de tous projets | ?preview=1 | Invité refusé ; administrateur voit beta et page propre | B07 | preview révision privée |
| C29 | Sauvegarde et visibilité actuelle | revision/published | Sauver un publié modifie immédiatement son rendu actuel | H3, B04 | **évolution approuvée : publication manuelle séparée** |
| C30 | État dirty et avertissement | mark/beforeunload | Modifier, vérifier message puis garde avant fermeture | B11 | commandes d'éditeur |
| C31 | Conflit sans écrasement | revision | Ancienne révision refusée 409 | H3 | If-Match/412 cible |
| C32 | Persistance et sessions au redémarrage | disque/session mémoire | Données conservées, ancienne session invalidée | H3 | PostgreSQL/sessions partagées |
| C33 | Export JSON | mémoire admin | Télécharger document avec modification non sauvegardée | B10 | portability |
| C34 | Export ZIP et médias orphelins | disque/uploads | Archive : contenu enregistré, médias référencés et orphelin ; sans auth | H2, B10 | portability/revision |
| C35 | Import JSON avec confirmation | import-picker | Annuler puis confirmer, contenu en attente jusqu'à sauvegarde | B10 | import contrôlé |
| C36 | Sauvegarde précédente | content.backup.json | Fichier créé avant remplacement | S | révisions |
| C37 | Validation liens/slugs | validate | javascript refusé, slugs dupliqués refusés | H2 | schémas/contraintes |
| C38 | UTF-8 et paragraphes | lecture/écriture | Suite cp1252 simulée, fixture non latine sans altération | H1–H3 simulés, F, B02 | contrats/migration |
| C39 | Initialisation et CLI | initialize/argparse | Champs host/port/password ; pas de données initiales écrasées | S, serveurs éphémères démarrés par H/B | runbooks/identity |
| C40 | Cohérence fichiers historiques | 11 fichiers suivis | SHA-256 identiques au commit de référence | F | exigence de transition |
| C41 | Portabilité données locales | dossier hors Git possible | Copie privée à froid, empreintes, restauration isolée | protocole documenté, non exécuté sur PC utilisateur | futur import |

## Limites à corriger ultérieurement, pas à reproduire

- **L01** : médias publics par URL même en brouillon ; aucune isolation multi-utilisateur.
- **L02** : sauvegarde = publication immédiate pour un projet publié. Dans la cible, la publication est manuelle et les snapshots immuables.
- **L03** : troncature silencieuse à 10 réseaux/liens et 60 sections ; 100 projets maximum. Le futur import doit signaler/conserver les dépassements.
- **L04** : sessions, limitation et verrou en mémoire, non partagés entre processus ; sauvegarde du document entier.
- **L05** : signature d'image seulement, sans décodage complet ni contrôle des dimensions.
- **L06** : shell HTTP 200 pour un projet absent, métadonnées principalement JavaScript ; la cible doit produire de vrais statuts et HTML SEO.
- **L07** : aperçu non propagé par tous les retours accueil ; couverture URL modifiée sans aperçu immédiat avant re-render.
- **L08** : export ZIP sans sauvegarde précédente ni auth ; export JSON sans binaires ; restauration ZIP manuelle seulement.
- **L09** : contenu/identité et labels partiellement codés en dur ; pas de modèle projet, timeline, undo/redo ou collaboration.
- **L10** : exemples historiques suivis contenant l'identité initiale ; ils restent inchangés et ne sont pas recopiés dans les fixtures BASE-001.

Le SaaS doit conserver les capacités utiles et les données ; ces limites ne deviennent pas des exigences de fidélité.

# TPL-001 — Plan de validation proposé

Ce plan décrit des tests **à implémenter/exécuter en B/C/D/E après validation de A**. Il ne constitue pas un résultat applicatif ou Windows. En A, seules les propositions de contrats et données synthétiques sont vérifiées statiquement.

## Contrats et catalogue (B)

- Valider JSON Schema et formats, types/variantes, unicité/références croisées, limites, thèmes compatibles et digests de bundles. Refuser schéma/version inconnus, données supplémentaires, mauvais formats et références absentes.
- Contrôler deux compositions réellement différentes, aucun template disponible sans renderer/bundle validé ; catégories futures non proposées comme disponibles. Catalogue paginé stable et filtres exacts.
- Vérifier renderer partagé, textes échappés, aucune interprétation HTML/JS/CSS libre, aucun chargement distant à partir des exemples. Mode mobile : même contenu et même ordre de lecture accessible.

## PostgreSQL 17 synthétique (C)

- Migration depuis `27a0b85` avec portfolios vierges actifs/archivés/supprimés, slugs identiques sur comptes distincts, UUID et sessions AUTH existantes. Aucun backfill de design implicite ; source renseignée incohérente détectée sans réparation.
- Rejouer les chemins de migration AUTH-001 et PORT provisoire déjà validés, puis nouvelles migrations. Conserver UUID, états, textes et slugs réservés. Aucune base réelle.
- Créer instance atomique : injecter une panne après Portfolio, après Design et après réservation de clé ; tout doit être annulé. Thème incompatible, version inexistante, indisponible ou digest invalide : aucun résidu.
- Deux connexions PostgreSQL : même clé/même corps donne une seule instance, même clé/corps différent donne 409 ; conflits de slug et requête interrompue. Vérifier replay exact, cible supprimée et expiration 24 h avec horloge contrôlée. Jamais SQLite comme preuve de concurrence.
- Sauvegarde avec ETag manquant 428, périmé 412, faux compte 404 ; concurrence de PUT/PATCH/archivage/suppression/duplication sur le même verrou Portfolio. Deux écritures avec même version : une seule réussit. ETag de lecture cohérent avec tous les documents.
- Duplication complète : mêmes valeurs et provenance, nouveaux UUID de design/ressources locales, références de sections conservées, aucun document mutable partagé. Modifier l’original, la copie et un second compte indépendamment. Refuser une source archivée/supprimée/étrangère. Vérifier la duplication vierge historique.
- Expiration et suppression des réponses d’idempotence, contraintes FK/unicité, traitement sans logs de corps privés. Test explicite du retour arrière documenté, sans suppression de données après écritures.

## Sécurité (C/E)

Session AUTH, CSRF et absence de jetons navigateur persistants inchangés. Aucune route design publique ; tentative d’assignation account/owner/source/experience rejetée. Tests horizontaux entre utilisateurs, membership forgée/incohérente, comptes inactifs, UUID deviné et suppression logique : mêmes 404 externes, aucun détail privé.

Texte contenant HTML rendu comme texte ; liens javascript/data/file/http et identifiants d’URL refusés ; pas de SSRF via aperçu. FormatChecker activé. Objets profonds, gros payloads, tableaux hors limites, ordre partiel/dupliqué, section étrangère, visibilité interdite et valeur hors politique rejetés. Vérifier no-store, erreurs sans secrets et limites de fréquence sans modifier le contrat AUTH.

## Studio et parcours navigateur (D/E)

Pour chaque template et viewport desktop/mobile : bibliothèque → filtre → aperçu → sélection → création → personnalisation → sauvegarde → fermeture/reconnexion → restitution identique. Vérifier vrai changement de composition, ordre et visibilité, héritage/remise à zéro, textes conservés lors du masquage. Test d’aperçu contre le document effectif sauvegardé, sans prétendre à un site public livré.

Tester clavier/focus, annonces d’état et erreurs, actions monter/descendre sans glisser-déposer obligatoire, contraste, réduction des mouvements (aucune animation complexe requise). Réseau interrompu/retry même clé, double clic, session expirée, conflit 412 avec modifications locales conservées ; aucune publication automatique.

## Non-régression et preuves (E)

Réexécuter les suites de référence PORT-001 (88 tests historiques rapportés), les nouveaux tests TPL, builds/typecheck et parcours AUTH/PORT. Le nombre pourra évoluer : reporter les comptes réels, suites, versions, commits, réussites/échecs/omissions. Vérifier empreintes historiques et `.local/` intact sans lire ses données.

Windows natif reste à exécuter séparément (Python 3.13, Node 24/npm 11, PostgreSQL 17, PowerShell 5.1) sur base synthétique dédiée. Ne pas transformer la réserve PORT-001 en réussite Linux. Aucun nouveau test fonctionnel ni migration exécuté dans la phase A. Pas de dépendance ajoutée uniquement pour ces propositions.

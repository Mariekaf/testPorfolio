# Exemples de conception uniquement

Ces fichiers ne sont ni des bundles installables ni des données à importer.
Ils ne sont référencés par aucun registre ou endpoint de l'application.

- `creative-editorial.descriptor.proposed.json` : futur descriptor, état draft.
  Le bundle_digest composé de zéros est un **placeholder documentaire** ; aucun
  bundle disponible ne doit être construit en le considérant comme une empreinte vérifiée.
- `creative-editorial.content.proposed.json` : contenu fictif sans média et sans
  contact, utile pour les états vides. Ne satisfait pas les préconditions de publication.
- `creative-editorial.media-reference.proposed.json` : variantes des slots portrait
  et projets, avec UUID synthétiques sans fichier, droits ni asset ready associé.
  Les références https://example.invalid sont volontairement non opérationnelles.
- `creative-editorial.snapshot.proposed.json` : matrice v3 et six sections ;
  composition et bindings appartiennent au template, pas aux mutations utilisateur.

Les trois schémas `../schemas/*.proposed.schema.json` vérifient des **structures
proposées**. Le contenu est volontairement générique ; la validation métier devra
comparer les slots exacts et les limites de chaque template, les types de bindings,
ordre/variantes, contrastes, médias/ACL et préconditions de publication. Un succès
JSON Schema ne suffit pas pour accepter une sauvegarde ou une publication.

Aucune de ces extensions n'est approuvée ou activée par sa présence sous docs/.
Le document principal propose R01–R10 à la revue.

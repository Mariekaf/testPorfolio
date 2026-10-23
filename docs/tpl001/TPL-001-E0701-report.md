# Rapport de conception — TPL-001.E.07.01

**Statut : soumis pour revue, aucune implémentation autorisée par ce rapport.**

19 octobre 2026, Africa/Douala. Branche `design/tpl-001-e0701-ready-templates`.
Parent accepté : E.06 `f579f0dd3af147316115ae366dc2bcc798721db8`.
Le SHA du commit documentaire est fourni à la remise. E.05/E.06 sont considérées
validées selon l'instruction utilisateur, y compris Windows rapporté par celui-ci.

## Livrables

- [Architecture détaillée](TPL-001-E0701-architecture.md) : séparation layout /
  template complet / slots / personnalisation / instance ; audit des sources ;
  registre et capacités ; médias ; responsive ; preview, persistance, publication
  manuelle ; compatibilité et récupération ; trois lots recommandés et décisions R01–R10.
- [Trois schémas proposés](e0701/schemas/) : descriptor v2, contenu slots v2,
  snapshot v3 ; documentation exclusivement, sans modification des contrats actifs.
- [Quatre exemples JSON et leurs limites](e0701/examples/) : descriptor,
  contenus fictifs, références médias synthétiques et snapshot complet.
- [Preuves de vérification documentaire](e0701/design-validation.json).
- [Liste exhaustive des fichiers créés](e0701/files.txt).

L'inventaire Creative Editorial comporte **14 slots** et **6 sections**.
La mise en page et la direction artistique restent verrouillées ; les états
vides et les ajustements autorisés sont définis. Une maquette originale doit
encore être approuvée : l'image « Form & Play » n'est pas accessible dans le
contexte, seules ses caractéristiques décrites ont été prises en compte.

## Conclusions structurantes soumises à validation

1. Nouvelle famille documentaire v3 pour les portfolios complets, sans élargir
   les contrats v1/v2 ni simuler un snapshot Minimal pour le résolveur Hero.
2. Slots typés fermés ; données utilisateur et composition de confiance séparées.
   Le premier template n'est pas un éditeur libre ni sept portfolios dérivés des Hero.
3. Module médias sûr et publication immuable sont des capacités **manquantes**,
   avec validations d'isolation et contraintes SQL à traiter explicitement.
4. Publication manuelle par release et pointeur indépendant par portfolio ; aucun
   brouillon ne doit être lu publiquement. Les CHECK draft/private actuels sont
   un vrai blocage à lever par décision coordonnée, pas un détail déjà implémenté.
5. Minimal/Editorial v1 et Hero v2 restent épinglés. Aucune conversion ou mise à
   niveau automatique. Première extension recommandée : nouvelles instances v3 seulement.

## Vérifications réellement exécutées

**9 contrôles documentaires réussis**, sur Python 3.13 et jsonschema présent dans
l'environnement de développement existant :

- Trois schémas JSON Schema draft 2020-12 structurellement valides.
- Quatre exemples conformes à leur schéma proposé, avec format UUID/email vérifié.
- Correspondance des 14 slots, types, bindings, ordre des six sections et provenance.
- Parent E.06 exact, arbre initial propre et périmètre exclusivement documentaire.

Les SHA-256 des JSON proposés sont conservés dans design-validation.json.
Les liens documentaires locaux ont été vérifiés avant publication. Les fichiers
approuvés existants et l'application n'ont pas été modifiés ; ni tests applicatifs
ni navigateur relancés pour cette conception. Les succès historiques E.06 restent
leurs preuves d'origine, pas de nouveaux résultats E.07.01.

Ces vérifications ne prétendent pas valider un import, une ACL médias, un nouveau
renderer, un vrai bundle/digest ou une publication. Les UUID médias et digest nul
sont des placeholders explicitement documentés. **Aucune base utilisée, aucune
migration exécutée, aucune validation Windows E.07.01 réalisée.**

## Périmètre Git et limites

Tous les fichiers sont nouveaux sous `docs/tpl001/` ; aucun fichier existant,
code, contrat actif, bundle immuable, AUTH, CMS historique ou `.local/` modifié.
Aucune dépendance installée ou ajoutée. Aucune route activée. Publication de la
branche documentaire uniquement, sans PR, fusion ni déploiement.

E.07.02–04 constituent un **découpage recommandé non autorisé**. Les validations
requises sont les décisions R01–R10, les seuils médias/quotas/rétention, les
préconditions de publication et le traitement de la dépendance Publication.
Tout futur DDL exige un plan et une autorisation spécifique avant exécution.

**Arrêt après E.07.01 : attendre la revue avant toute implémentation.**

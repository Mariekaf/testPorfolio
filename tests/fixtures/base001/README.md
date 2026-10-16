# Fixtures BASE-001

`legacy-content.json` a été créé de zéro, sans lecture de `.local/`, d'un export utilisateur ou d'un fichier d'authentification. Les noms sont fictifs et les domaines/adresses utilisent `example.test`. Ne pas contacter ces URLs pendant les vérifications.

- Révision 7, trois projets ordonnés alpha/beta/gamma ; beta est en brouillon.
- Deux sections par projet, paragraphes, accents, ponctuation, caractères non latins et texte littéral ressemblant à du HTML.
- Portrait et image de section verts ; couverture violette.
- Trois PNG RGB 16 × 16 générés avec la bibliothèque standard, sans photo ni métadonnée personnelle.
- Le PNG beige `33333333333333333333333333333333.png` n'est pas référencé : il représente un média orphelin à conserver.
- `manifest.json` contient les empreintes du JSON et des trois PNG ; il ne s'inclut pas lui-même et n'inclut pas cette documentation.

Ne jamais copier ces fichiers dans les données réelles. Pour une vérification HTTP, les copier dans un répertoire temporaire isolé et définir `PORTFOLIO_DATA_DIR` uniquement pour le processus de test. Le serveur peut alors générer ses identifiants éphémères dans ce répertoire ; ils ne sont ni des fixtures ni des livrables. Supprimer uniquement le répertoire temporaire créé par le test.

Les tests historiques restent inchangés et utilisent leur fichier d'exemple historique : leur comportement n'a pas été réécrit pour utiliser ces nouvelles fixtures. Aucun contenu personnel historique n'est recopié dans les nouvelles fixtures ni dans les preuves.

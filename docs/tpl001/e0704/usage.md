# Creative Editorial — parcours privé E.07.04

Sur un environnement **isolé installé avec autorisation**, se connecter au Studio,
ouvrir le dashboard puis **Choisir Creative Editorial**. Le bouton de création
ouvre un portfolio neuf, privé et vide. Aucun utilisateur fictif n'est enregistré
par défaut et aucun portfolio Minimal/Editorial existant n'est converti.

L'éditeur conserve la composition : ouvrir Identité, Hero, Présentation, Projets,
Contact, Pied de page et Apparence. Les 14 slots sont disponibles : identity_name,
brand_logo, hero_title, hero_subtitle, hero_portrait, hero_cta, about_heading,
about_body, projects_heading, selected_projects, contact_heading, contact_link,
socials, footer_note. Les intitulés français décrivent leur rôle.

Les paragraphes riches contiennent des fragments avec gras/emphase. On peut ajouter,
retirer et modifier les paragraphes/fragments sans HTML. Les projets comportent un
UUID local stable, titre, résumé, lien HTTPS facultatif et référence de couverture.
Ils sont du contenu privé du portfolio ; ils ne constituent pas une attestation
« projet réel vérifié » pour une publication future. Les réseaux sont uniques par
identifiant ; utiliser un domaine conforme pour LinkedIn/Behance/Dribbble/GitHub.

Les liens internes ne sont valides que si la section visée est visible. Une section
Projets vide ne peut donc pas être la cible du bouton Hero. Choisir « aucun » ou
remplir un projet. Les brouillons vides sont autorisés, les documents invalides
(non-conformes aux contrats fermés) ne sont pas enregistrables.

Le logo, le portrait et les couvertures acceptent uniquement une référence UUID,
un texte alternatif et un cadrage0..1. **MEDIA-001 n'existe pas dans cette livraison** :
aucune vérification de propriété ou de disponibilité n'est simulée et aucune image
utilisateur n'est chargée. Le placeholder le signale. Ne pas considérer un UUID
conservé comme un média autorisé. Aucun upload, URL d'image ou fichier local saisi.

L'apparence expose deux palettes et deux références de police autorisées. Les
couleurs personnalisées restent indépendantes de la composition. La validation
refuse un contraste inférieur à4,5:1 ; Réinitialiser l'apparence retire les overrides.
Les polices sont système : pas de chargement distant ni de nouveau fournisseur.

L'aperçu desktop/mobile utilise le même composant visuel que E.07.03 et valide le
même document. Une configuration temporairement invalide affiche une erreur plutôt
qu'une approximation ; les champs restent modifiables. **Enregistrer** crée une
révision atomique et met à jour l'ETag. Quitter puis revenir via le dashboard et
« Modifier le portfolio » reprend le contenu enregistré.

En cas d'erreur réseau, la saisie reste en mémoire et la sauvegarde est réessayable.
En cas de conflit, la saisie est conservée, la nouvelle sauvegarde est bloquée,
et la recharge destructive demande confirmation. Aucun écrasement ni retry aveugle.
Les liens sortants, retour navigateur et fermeture d'onglet reçoivent une protection
de sortie. La connexion, déconnexion et expiration restent celles d'AUTH-001 :
aucun cache personnel persistant n'est ajouté et la récupération après fermeture
forcée/expiration exige un enregistrement préalable.

Aucune publication ni éditeur libre. La duplication v3 est explicitement indisponible
au lieu de produire une copie sans design ; duplication v1/v2 inchangée. Les états
archivé/supprimé et les changements de membership sont respectés sur chaque API.

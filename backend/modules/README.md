# Modules backend

CORE-001 installe seulement `identity.User`, modèle utilisateur UUID déclaré avant les premières migrations. Aucun endpoint d'inscription, de connexion, de compte ou de portfolio n'existe.

Les frontières accounts, portfolios, content, media, themes, experience, revisions, publishing, portability et audit sont définies dans ARCH-002 ; leurs modèles et services restent à implémenter dans leurs tickets respectifs. Aucune isolation multi-tenant n'est revendiquée avant SEC-001. Les API futures auront des permissions fermées par défaut.

# Modules SaaS

- `identity` : User UUID, authentification par e-mail, sessions et reset AUTH-001. Le contrat session.v1 reste inchangé.
- `accounts` : Account propriétaire canonique, Membership et provisioning personnel atomique/idempotent. Les rôles collaboratifs sont réservés ; aucune API de collaboration n’est activée.
- `portfolios` : ressources privées d’un Account, gestion active/archives/suppression logique, préconditions de version et descripteurs de thème/template versionnés. Publication et visibilité publique restent interdites.

ARCH-002 P01–P10 est approuvé sous les conditions consignées dans `docs/architecture/ARCH-002.md`. Le code et les migrations PORT-001 attendent une revue technique distincte. Les migrations identity historiques et portfolios.0001 sont conservées ; l’évolution Account est additive puis contracte explicitement l’ancienne FK owner après rattachement et contrôles.

Le filtrage serveur du compte personnel s’applique aux listes, détails et mutations. Il ne constitue pas une implémentation de collaboration, un audit de déploiement ou une politique de publication. Content, media, expérience, versions publiées, domaines et facturation restent hors de cette livraison. Aucun import du CMS ou accès à `.local/`.

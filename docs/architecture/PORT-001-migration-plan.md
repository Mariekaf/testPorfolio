# PORT-001 — Plan de migration contrôlée

18 octobre 2026. P01–P10 approuvées ; aucune base réelle autorisée dans cette exécution.

## Ordre et dépendances

1. `accounts.0001_initial` dépend explicitement de `identity.0002`. Créer Account et Membership avec contraintes uniques et FK protégées.
2. `accounts.0002_provision_personal_accounts` provisionne les identités existantes par UUID, sans copier e-mail/nom/hachage. Un compte préexistant incohérent bloque atomiquement ; aucune réparation automatique.
3. `portfolios.0002_expand_account_ownership` conserve `owner`, ajoute `account` nullable, états/versions/références avec valeurs initiales compatibles. Dépend de la migration historique portfolios.0001 et de accounts.0002.
4. `portfolios.0003_backfill_and_constrain` vérifie et rattache tous les portfolios (supprimés inclus) au compte personnel de leur propriétaire, sans save() modifiant les dates. Précontrôler syntaxe des slugs, thème par défaut et cohérence des memberships. Bloquer les anomalies. Remplacer l’unicité globale par l’unicité Account/Lower(slug), rendre account obligatoire et poser les contraintes d’état/références.
5. `portfolios.0004_contract_legacy_owner` retire uniquement l’ancienne FK User après validation du rattachement. `portfolio_type`, UUID, description, status/visibility, dates et deleted_at sont conservés. Les services ne lisent plus owner.

Aucune modification des fichiers historiques de migration. Aucune réécriture de identity.User ou des sessions. Le champ SQL `status` est conservé et exposé via `publication_state`.

## Arrêt des écritures et restauration

Arrêter Django et Next avant migration d’une base à conserver. Sauvegarde PostgreSQL et vérification du contenu de l’archive requises avant autorisation explicite de migrer des données réelles. Ne pas utiliser ce plan pour lire `.local/`, importer le CMS ou créer des fixtures personnelles. La contraction ne promet pas de retour automatique : une fois les slugs partagés entre comptes, l’ancienne unicité globale n’est plus rétablissable sans analyse. Préférer la restauration de la sauvegarde cohérente ; aucune commande destructive n’est automatisée.

## Preuves obligatoires sur base isolée

- Depuis identity.0002 sans tables comptes/portfolios : utilisateur synthétique préexistant, puis toutes les migrations ; UUID/hachage/session existante conservés.
- Depuis portfolios.0001 : plusieurs propriétaires synthétiques, portfolio actif et supprimé, dates imposées ; toutes les données et rattachements conservés.
- Incohérences membership, slug et propriétaire : blocage sans réparation ni modification des données sources.
- Rejouer migrate : aucun doublon ; vérifier contraintes SQL et absence de migrations manquantes.
- Ne pas confondre tests Linux et exécution Windows native ; fournir un guide Windows sans Docker et documenter les contrôles non exécutés.

# Scripts Windows

PowerShell 5.1 ou supérieur, depuis le dépôt. Aucune activation du venv ni modification globale de l'ExecutionPolicy nécessaire. Si une politique locale interdit les scripts, examiner les fichiers puis appliquer les règles de votre organisation ; les commandes Python équivalentes sont documentées dans le runbook.

- Initialize-Development.ps1 : choix obligatoire native/docker, génère uniquement les fichiers privés manquants et une exclusion Git locale de node_modules. Ne lance pas Docker en mode natif.
- Initialize-Database.ps1 : démarre le service Compose seulement en mode docker ; en natif vérifie le port, demande le mot de passe administrateur sans le sauver, puis provisionne les rôles et applique les migrations avec le rôle DDL.
- Start-Backend.ps1 : serveur local 127.0.0.1:8001 sous rôle runtime.
- Test-Foundations.ps1 : référence historique, tests historiques, PostgreSQL réel, tests Django sur base dédiée, TypeScript et build. Échoue si PostgreSQL n'est pas vérifié. Aucun drop de la base de développement ; Django peut créer/supprimer sa base de test dédiée préfixée test_.

Scripts livrés pour Windows ; exécution native Windows à confirmer sur le poste utilisateur. Les programmes Python appelés ont été testés sous Linux avec PostgreSQL réel.

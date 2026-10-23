# PORT-001-WIN — Suivi de la réserve Windows native

Statut au 19 octobre 2026 : **OUVERT — NON EXÉCUTÉ**, réserve non bloquante de PORT-001 clôturé. Aucun résultat Windows PORT-001 n’est revendiqué.

Référence fonctionnelle à vérifier : `27a0b85`, branche `feature/port-001`. Les changements documentaires ultérieurs ne changent pas cette référence. Exécution à organiser sur le PC Windows, sans Docker, selon le [guide existant](../runbooks/port001-windows-development.md).

## Vérifications attendues

1. Consigner commit exact, Windows/PowerShell, Python 3.13, Node 24/npm 11 et PostgreSQL 17 natif.
2. Préparer la configuration privée de validation, des rôles et une base synthétique séparés ; ne pas réutiliser une base réelle. Vérifier les ACL et les exclusions Git sans afficher de secrets.
3. Exécuter les commandes du guide, dont les tests de migrations depuis AUTH-001 et l’état provisoire PORT-001, puis Test-Foundations.ps1. Conserver les sorties et codes de retour expurgés. Distinguer réussites, échecs, omissions et tests non exécutés.
4. Démarrer Django et Next.js ; vérifier santé/connexion PostgreSQL, session AUTH, isolation entre deux utilisateurs et parcours portfolios : création, modification, duplication, archivage/restauration, suppression logique, conflits de version et absence de publication automatique.
5. Vérifier les sources historiques et `.local/` intacts. Toute correction de code doit être isolée sur une branche dédiée et revue ; aucune fusion automatique.

## Critère de levée

Preuves Windows natives réelles, versions/commit et résultats détaillés consignés, anomalies résolues ou explicitement arbitrées, puis confirmation utilisateur. Ne pas déduire la levée de cette réserve des preuves Linux. Ne publier ni configuration privée, ni identifiants, ni e-mails de réinitialisation.

Aucune migration de base réelle sans sauvegarde, restauration vérifiée et autorisation explicite. La préparation documentaire de TPL-001 reste autorisée pendant ce suivi.

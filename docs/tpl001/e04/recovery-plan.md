# E.04 — Plan de schéma, conversion et récupération avant exécution

Base approuvée : `ef4139109032f6974bd4b88dd3995879319ada78`.
Branche dédiée : `feature/tpl-001-e04`.

**Autorisation spécifique reçue dans la conversation** : « Autoriser uniquement le
cluster synthétique E.04 ». Exécution limitée aux nouveaux clusters jetables E04
créés pour ces tests. Les bases existantes et les anciennes validations restent
exclues. Cette autorisation ne vaut ni validation du code ni autorisation de
migration d'un environnement réel.

## Constat et autorisation à obtenir

`PortfolioDesign` impose actuellement `schema_version=1` par la contrainte SQL
`tpl_design_schema_v1`. Il est donc impossible d'enregistrer un design v2 sans
migration de structure. Aucune table ne conserve les anciennes révisions.
Les migrations historiques, les données et les bundles ne doivent pas changer.

Migration additive proposée, **non exécutée sans autorisation spécifique** :

1. Remplacer le CHECK v1 par un CHECK autorisant exactement 1 ou 2 ; garder
   experience SQL NULL et les autres contraintes.
2. Créer une table append-only de transitions/récupération, liée au design et à
   l'utilisateur initiateur. Chaque ligne conserve avant/après complets,
   empreintes canoniques, digest source, action, convertisseur, versions Portfolio,
   clé UUID d'idempotence et empreinte de requête. Unicité design/user/key.
3. Interdire UPDATE/DELETE des transitions par un trigger PostgreSQL ; aucune
   purge automatique. La propriété se déduit toujours du portfolio/account.
4. Aucun backfill, aucune conversion automatique et aucune requête vers une
   ancienne base. La migration pourra être testée seulement dans un cluster
   PostgreSQL 17 neuf et jetable, données exclusivement synthétiques.

Les fichiers de migration et le code peuvent être préparés pour revue ; leur
exécution, y compris pendant les tests PostgreSQL, exige l'autorisation demandée.
Cette condition a été satisfaite avant la première exécution du schéma E04.

## Contrats d'opération proposés

- GET/PUT design restent v1 par défaut. Un client doit déclarer explicitement
  Accept-Design-Schema: 2 ou 1,2 pour lire/écrire un design v2 ; sinon 406, aucune
  conversion implicite. Le Studio et le renderer ne sont pas modifiés.
- POST design/upgrade : target_schema_version=2 et converter_version=1.0.0.
- POST design/restore : recovery_revision_id désigne une transition d'upgrade
  appartenant au même design ; restauration exacte de son document before v1.
- AUTH/session/CSRF inchangés ; If-Match et Idempotency-Key UUID obligatoires.
- Les nouveaux endpoints de transition seront désactivés par défaut par une
  configuration explicite. Leur activation dans les tests ne concerne que le
  nouvel environnement synthétique.

## Atomicité, concurrence et idempotence

Autorisation du compte et suppression logique vérifiées avant toute divulgation.
Ordre des verrous : Portfolio puis PortfolioDesign. Le replay est recherché sous
ces verrous, avant de comparer le compteur actuel : même clé + même action/corps
+ même If-Match original renvoie le résultat historique sans nouvelle écriture.
Réutiliser la clé avec une autre intention donne 409. Une nouvelle clé avec un
ETag ancien donne 412 ; un If-Match absent donne 428. Un design archivé est en
lecture seule. Déjà v2 avec une nouvelle intention : 409, pas de seconde conversion.

Chaque transition conserve d'abord en mémoire le snapshot exact actuel, valide
source et cible, puis insère sa ligne de récupération avant de remplacer le design
et d'incrémenter Portfolio.version une fois, dans la même transaction. Une erreur
ou interruption annule la ligne, le design et le compteur. Un lock timeout échoue
sans fallback et permet un retry avec la même clé.

## Conversion et conservation

La conversion copie tous les contenus/UUID locaux, ordre, visibilité, réglages,
thème, provenance et source_digest. Elle ajoute les defaults Hero locaux nécessaires
et les politiques v2, sans relire le catalogue. Les réglages effectifs v1 sont
calculés explicitement pour éviter de perdre un override sous la priorité v2.
Les dimensions d'apparence restent fondées sur le thème neutre connu ; aucune
capacité nouvelle ne devient sélectionnable. Le document v2 complet doit passer
le validateur et le résolveur E.03 avant toute sauvegarde.

La révision contient le snapshot v1 original exact ; celui-ci n'est jamais
réécrit pour représenter la conversion. Les références de template et leur digest
ne sont pas remplacés par une nouvelle version fictive.

## Restauration sans perte

La restauration explicite vérifie le même propriétaire, le design de la révision,
son action, ses empreintes et son document before v1. Elle sauvegarde aussi le
snapshot courant (notamment les modifications v2 ultérieures) dans une **nouvelle**
transition avant d'appliquer l'ancien v1. Aucun mélange silencieux de contenus.
Les modifications remplacées restent récupérables dans cette révision immuable.
Le compteur Portfolio continue à croître, il n'est jamais remis à l'ancienne valeur.

Pour une reprise après incident : relire le design et ses ETags, réutiliser la même
clé si la réponse de commit a été perdue. Ne pas rejouer une nouvelle intention
sur un ETag obsolète. Une restauration est une mutation applicative, jamais un
rollback destructif de migration ni une suppression des documents v2.

## Sauvegardes et limites d'exécution

Une révision transactionnelle ne remplace pas une sauvegarde externe. Toute
application future sur données réelles exige une sauvegarde vérifiée et une
autorisation explicite distincte. Aucun dump, média local ou fichier privé n'est
lu dans E.04. Le cluster de test doit avoir un répertoire et un port nouveaux,
un nom E04 unique et ne réutiliser aucune configuration d'une validation précédente.

Les preuves devront distinguer tests purs, PostgreSQL synthétique autorisé et
Windows natif non exécuté. Sans autorisation de migration, les tests de persistance,
concurrence et interruption resteront explicitement non exécutés ; le ticket ne
sera pas annoncé complet ou validé sur la seule base de tests sans base.

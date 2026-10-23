# TPL-001.F — Livraison pour revue

## Périmètre et référence

Branche `design/tpl-001-f-navigation`, issue de
`41aaffd73d166ab0cbf6525a8df6d27465d8f7fa`. Implémentation de F.04,
puis F.01, F.02, F.03 et recette transversale, conformément à
[l’audit approuvé](../TPL-001-F-navigation-audit.md).
Livraison locale : aucun push, PR, merge, déploiement ou PUB-001.
Cette livraison n’est pas une validation utilisateur.

## Fonctionnalités accessibles

| Contexte | Projets | Sections | Apparence |
| --- | --- | --- | --- |
| Minimal / Editorial v1 | Champs et ajout/retrait existants, maximum 24 | Contenu, ordre et visibilité selon les contraintes du snapshot ; Hero obligatoire | Espacement, alignement, emphase et reset existants par section ; aucune nouvelle palette |
| Creative Editorial v3 | Liste existante, maximum 6, médias privés associés | Groupes de slots de la composition verrouillée ; pas de section libre | Palettes, couleurs, polices autorisées et reset existants ; raccourci vers les options Hero |
| Vierge | Explication et création d’un autre portfolio avec template | Aucun éditeur fictif | Aucun réglage fictif |
| Archivé | Lecture seule | Lecture seule | Lecture seule |
| Version inconnue / v2 non éditable | Refus explicite | Refus explicite | Refus explicite |

Sidebar commune avec portfolio actif, template, état, vue d’ensemble et réglages.
« Pages » devient « Sections ». La publication reste indisponible. Aucun nouveau
layout, champ métier, upload ou contrôle de présentation n’a été inventé.

Les trois panneaux sont des vues du même éditeur monté. Le changement local de
`?panel=` ne déclenche ni PUT ni relecture du snapshot. Le brouillon, la version et
la sauvegarde restent communs. Les 412 conservent la saisie et bloquent un nouvel
écrasement. Un POST de résolution privée des médias peut survenir dans l’aperçu :
ce n’est ni une sauvegarde ni une relecture du design.

## Historique et protections de sortie

Le hook commun préserve les gardes de liens, déconnexion, beforeunload et Navigation
API lorsqu’elle est annulable. Une entrée frontière, à URL identique à l’éditeur,
permet de confirmer un Précédent qui le quitterait avant son démontage par Next.
Elle est installée avant les changements de panneaux, même lorsque le brouillon
est propre. Un retour Suivant après sortie réinstalle cette protection.

L’état de navigation conserve les données internes de Next sans les interpréter et
ajoute seulement UUID du portfolio, identifiant aléatoire local de montage et type
d’entrée. Aucun contenu, ETag, mot de passe ou jeton de session n’y est stocké.
Cette entrée technique peut être visible dans l’historique du navigateur. Le parcours
Précédent/Suivant pas à pas est testé ; les sauts de plusieurs entrées via le menu
d’historique ne sont pas garantis sur les moteurs sans Navigation API annulable.

## Tests Linux exécutés

Environnement : Python 3.13, Node 24.19, Next 16.4.2, Chromium Linux et PostgreSQL
**17.11 natif**, sans Docker. Tous les clusters, rôles et stockages ont été créés
pour ces vérifications puis détruits par le runner ; aucune base existante ou
configuration habituelle n’a été utilisée.

| Vérification | Résultat exact | Preuve |
| --- | --- | --- |
| Suite Django complète | 393 exécutés, 393 réussis, 119,988 s | [journal](evidence/django-393.log) |
| Node / contrats / Studio | 226 réussis, aucun échec ni skip | [journal](evidence/node.log) |
| TypeScript strict | Réussi | [journal](evidence/typecheck.log) |
| Build Next production | Réussi ; build local uniquement | [journal](evidence/build.log) |
| Vérifications intégrité / ACL | 25 exécutés : 22 réussis, 3 ignorés Windows | [journal](evidence/integrity.log) |
| Référence historique | 11 fichiers + 4 empreintes de fixture préservés | [journal](evidence/historical.log) |
| CMS historique | 6 réussis, 1,196 s | [journal](evidence/cms.log) |
| Régression MEDIA ciblée Django | 24 réussis, 20,026 s ; sous-ensemble des 393 | [journal](evidence/media-24.log) |
| Parcours MEDIA navigateur original | 6 groupes réussis, aucune erreur de page | [résultat](evidence/media-results.json) |
| Recette F navigateur finale | 3 templates, tous les indicateurs vrais, aucune erreur de page | [résultat](evidence/navigation-results.json) |

La recette navigateur F finale utilise un autre cluster neuf, migré et provisionné,
et un précontrôle Django de 2 tests ACL. Elle ne réexécute pas les 393 tests ; leur
preuve est celle du run complet distinct ci-dessus. Les validations de privilèges
et d’isolation sont conservées dans [l’environnement](evidence/isolated-environment.json)
et [le contrôle des rôles](evidence/runtime-privileges.log).

Parcours F : projets ajoutés/modifiés/retirés, restrictions de sections, contraste
invalide puis correction, conservation des saisies via panneaux et historique,
sorties annulées/acceptées sans autosave, Suivant après sortie puis nouvelle sortie
annulée, sauvegarde/réouverture, 412 réel, archive, suppression réelle, compte étranger,
session révoquée et média privé réel avec alt/cadrage préservés.
Les réponses version inconnue, 406 v2 et 503 temporaire sont injectées côté navigateur
pour tester les états d’erreur, sans corrompre des données ou activer v2.

Les captures [Minimal desktop](evidence/minimal-desktop.png),
[Editorial desktop](evidence/editorial-desktop.png),
[Creative Editorial desktop](evidence/creative-editorial-desktop.png) et leurs
variantes mobiles documentent le rendu. Le runner produit aussi tablette, 320 px,
forced-colors et zoom équivalent.

## Limites et réserves

- Windows natif / Edge : **non exécutés**. Les trois skips ACL Windows ne sont pas
  des réussites. Les commandes sont dans [windows.md](windows.md).
- Le fallback sans Navigation API est simulé sous Chromium, pas validé dans Firefox
  ou Safari natifs. Les sauts multi-entrées restent une limite de protection de sortie.
- Zoom testé par viewport 720 CSS px et DPR 2 : ce n’est pas un zoom navigateur
  Ctrl+plus réel. Ce dernier et le lecteur d’écran restent à vérifier manuellement.
- Clavier, focus, tailles 1440/768/390/320, couleurs forcées et mouvement réduit ont
  été parcourus ; cela ne constitue pas une certification exhaustive WCAG.
- La révocation de session est réelle ; l’attente de toute sa durée d’expiration
  n’a pas été reproduite dans le navigateur.
- Aucun changement SQL, contrat API, AUTH, bundle immuable, renderer v1 ou CMS.
  Aucun accès à `.local/`, aux anciennes bases ou à la démonstration persistante.

## Fichiers et adaptations de recette

L’inventaire complet figure dans [files.txt](files.txt). Les modifications applicatives
se limitent au Studio (navigation, panneaux, états de compatibilité et type de la
réponse existante). Aucune dépendance applicative ajoutée.

Le runner existant accepte un scénario navigateur F explicitement autorisé et un
sous-ensemble ACL de précontrôle ; son défaut MEDIA est conservé. Le cluster natif
désactive seulement le socket Unix dans sa configuration temporaire pour éviter
une dépendance à `/var/run/postgresql` ; TCP loopback et SCRAM restent imposés.
La recette complète est reproductible sous Windows sans Docker et sans base
existante. Attendre la revue avant toute publication du commit ou suite du projet.

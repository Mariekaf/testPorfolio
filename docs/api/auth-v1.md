# AUTH-001 — API v1

Sessions Django, JSON, même origine via le proxy Next. Les URL canoniques sont **sans slash final**, conformément à CORE-001. Les autres routes métier restent absentes.

| Méthode | `/api/v1/auth/…` | Corps JSON | Réponse |
|---|---|---|---|
| GET | `csrf` | — | 200 `{csrf_token}` + cookie CSRF HttpOnly |
| POST | `register` | `first_name,last_name,email,password,password_confirmation` | 201 `{message}` ; aucune connexion automatique |
| POST | `login` | `email,password` | 200 session décrite ci-dessous + cookie |
| POST | `logout` | `{}` | 200 `{message}` ; session supprimée |
| GET | `me` | — | 200 session ; 401 anonyme/expirée |
| POST | `password-reset` | `email` | 200 `{message}` identique, compte connu ou inconnu |
| POST | `password-reset/confirm` | `uid,token,password,password_confirmation` | 200 `{message}` ; toutes les sessions suivies du compte révoquées |

Session : `{user:{id,email,first_name,last_name},expires_at}`. `id` conserve l’UUID du modèle CORE-001. `me` utilise exclusivement l’identité de la session ; aucun identifiant utilisateur fourni par le client ne sélectionne un autre profil. Aucun mot de passe, hachage ou privilège n’est renvoyé.

Toutes les mutations exigent le cookie CSRF **et** `X-CSRFToken`, y compris inscription/connexion/récupération anonymes. Initialiser un jeton masqué via GET `csrf` avant chaque POST, car la connexion le renouvelle. Cookies : `portfolio_saas_session`, `portfolio_saas_csrf`, HttpOnly, SameSite Strict ; Secure avec `SAAS_HTTPS=1`. Ne pas mélanger `localhost` et `127.0.0.1`.

Erreurs : `{error:{code,message,fields?}}`, `fields` associe chaque champ à une liste de messages. 400 validation/lien invalide, 401 identifiants invalides/session absente, 403 CSRF, 429 limitation avec `Retry-After`. Les erreurs de connexion ne distinguent pas compte absent, inactif et mot de passe erroné. Les réponses privées et d’authentification ne sont pas mises en cache.

Nom/prénom : après suppression des espaces périphériques, 1–100 caractères. E-mail valide, 254 caractères maximum, normalisé avec `strip().lower()`. Unicité simple et contrainte PostgreSQL `Lower(email)` pour les écritures contournant le manager. Mot de passe : 12–128 caractères, confirmation identique, validateurs Django de similarité, mots courants et mot de passe entièrement numérique.

## Sessions et réinitialisation

Durée absolue par connexion : `SAAS_SESSION_SECONDS` (28 800 par défaut). Délai reset : `SAAS_RESET_SECONDS` (1 800 par défaut). Valeurs acceptées : 60–86 400 secondes. Les jetons Django deviennent invalides après changement de mot de passe et peuvent également être invalidés par une connexion ultérieure. L’identité est verrouillée lors de la connexion et de la confirmation pour sérialiser ces opérations.

Les liens reset transportent `uid`/`token` dans le **fragment URL**, jamais la query string. Le navigateur les garde en mémoire puis efface le fragment de l’adresse. Ne jamais partager un lien, un fichier mail ou une capture contenant ce fragment. Les corps JSON ne doivent pas être journalisés par un futur proxy ou outil d’observabilité.

## Limites partagées et entretien

Compteurs PostgreSQL transactionnels partagés entre processus. Clés HMAC, aucun e-mail/IP en clair dans les compteurs. Fenêtres fixes, tentatives réussies incluses : inscription 10/IP/5 min ; connexion 20/IP/5 min et 8/e-mail/5 min ; reset 10/IP/5 min et 3/e-mail/15 min ; confirmation 20/IP/5 min. Ne pas réinitialiser ces compteurs pour contourner une limite.

`python backend/manage.py cleanup_auth_limits` supprime les compteurs expirés depuis au moins 24 h (ou la plus grande fenêtre configurée). `python backend/manage.py clearsessions` purge les sessions expirées et leurs associations. Prévoir une tâche quotidienne avant une exploitation prolongée.

`REMOTE_ADDR` est utilisé ; les en-têtes `X-Forwarded-For` client ne sont pas fiables. Le proxy local Next regroupe les visiteurs dans un même compteur IP ; la limitation e-mail reste indépendante. Une politique de proxy de confiance, des limites réseau et une revue de déploiement seront nécessaires avant ouverture publique. Le profil production demeure volontairement fermé dans CORE-001.

## E-mail

Défaut : backend de fichiers privés `infra/mailbox/` (ignoré Git), Linux dossier 0700/fichiers 0600 ; ACL Windows via `Initialize-Mailbox.ps1`, appelé avant le serveur par `Start-Backend.ps1`. La boîte contient des secrets temporaires : jamais de commit, pièce jointe, copie dans les journaux ou export public. Supprimer les messages de test devenus inutiles.

SMTP optionnel par variables du processus backend : `SAAS_EMAIL_HOST`, `SAAS_EMAIL_PORT` (587), `SAAS_EMAIL_USER`, `SAAS_EMAIL_PASSWORD`, `SAAS_EMAIL_FROM`. STARTTLS obligatoire dans ce mode, timeout 10 s. Aucun secret SMTP requis pour les tests locaux. `SAAS_MAILBOX_PATH` peut désigner une boîte privée temporaire ; `SAAS_STUDIO_ORIGIN` définit l’origine de retour (HTTP uniquement en loopback, HTTPS autrement). Les échecs de livraison ne révèlent ni destinataire, ni lien, ni détail SMTP dans le journal.

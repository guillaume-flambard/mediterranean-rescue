# ADR 0015 : inviter un ou une bénévole par lien à usage unique

Date : 25 octobre 2026. Statut : accepté pour le travail local, à revoir avant toute mise en ligne.

## Contexte

Guillaume demande qu'une personne qui coordonne puisse inviter un ou une bénévole par « magic link », sans lui créer un mot de passe. Les bénévoles ne sont pas techniques (ADR 0013), et l'application n'a encore ni serveur d'envoi d'e-mails ni hébergement décidé.

## Décision

- **Lien à usage unique, envoyé par la personne qui coordonne.** L'application n'envoie aucun e-mail. Elle crée le lien, l'affiche une seule fois avec « Copier le lien » et « Écrire l'e-mail » (un `mailto:` prérempli), et la personne qui coordonne l'envoie elle-même.
- **Jeton.** `secrets.token_urlsafe(32)` (256 bits, module `secrets` de Python). Seul son SHA-256 est stocké (`Invitation.token_hash`), donc la base ne contient jamais de lien utilisable. Le lien a la forme `/invite#<jeton>` : ce qui suit `#` n'est jamais envoyé au serveur et n'apparaît donc dans aucun journal d'accès.
- **Lire n'est pas utiliser.** La page d'invitation lit l'offre (`POST invitations/check/`, sans effet). On ne rejoint l'équipe qu'en cliquant sur le bouton (`POST invitations/accept/`), ce qui empêche un antivirus de messagerie qui suit les liens de les consommer. Les deux appels transportent le jeton dans le corps de la requête, sont ouverts aux visiteurs, vérifient le CSRF et ont leur propre limite de débit (`invitations`, 20 par minute).
- **Une fois, 72 heures, révocable.** Un lien expiré, déjà utilisé, retiré ou inventé reçoit la même réponse (`invitation_unusable`).
- **Lien lié à un compte précis.** Si un compte avait déjà cette adresse à la création, le lien ouvre ce compte et aucun autre. Le compte doit encore porter cette adresse au moment de l'utilisation. Un lien créé pour une adresse nouvelle n'ouvre jamais un compte qui aurait pris cette adresse après coup. Sinon, le compte est créé sans mot de passe utilisable, avec les rôles de l'invitation.
- **Jamais un compte sensible par la main d'une personne qui coordonne** (revue de sécurité du 25 octobre 2026). Un lien n'ouvre jamais un compte staff, superutilisateur ou inactif. Un compte qui peut publier ou coordonner, par rôle ou par permission individuelle, n'est ouvert que par le lien d'un superutilisateur. Une personne qui coordonne ne peut pas non plus donner ces rôles. C'est la même règle que dans l'administration, où seul un superutilisateur change le mot de passe d'une personne qui publie.
- **Le lien meurt avec le droit de la personne qui l'a créé.** Si la personne qui coordonne est désactivée ou perd le droit d'inviter, ses liens en attente ne servent plus.
- **Pas d'oracle.** La création répond pareil quel que soit le compte qui porte l'adresse. Le refus n'intervient qu'à l'utilisation.
- **Qui invite.** Le rôle « Coordinator » reçoit `add_invitation`, `view_invitation` et `delete_invitation` (migration 0011), ainsi que les superutilisateurs. L'écran est la section « Équipe » de l'espace équipe. Le modèle n'est volontairement pas enregistré dans l'administration Django : un formulaire générique y permettrait de choisir n'importe quel rôle.

## Conséquences

- Une personne qui coordonne et a accès à l'administration (staff) peut entrer dans le compte d'un bénévole ordinaire en s'invitant à sa place. C'est le même pouvoir que changer son mot de passe dans l'administration, qui existe déjà. Une personne qui coordonne sans accès à l'administration ne crée que de nouveaux comptes. L'invitation en garde la trace (créée par, utilisée par, quand).
- Pour se reconnecter, un ou une bénévole demande un nouveau lien. Une connexion par e-mail en libre-service demandera un serveur d'envoi, à décider avec l'hébergement.
- Avant une mise en ligne : HTTPS obligatoire (le lien vaut une session), un journal d'audit des invitations, et une purge des invitations anciennes.

## Sources

- Python, module `secrets` (génération de jetons) : https://docs.python.org/3/library/secrets.html
- Django 5.2, `login()` et rotation de session : https://docs.djangoproject.com/en/5.2/topics/auth/default/#how-to-log-a-user-in
- Django REST framework, CSRF et `SessionAuthentication` : https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication

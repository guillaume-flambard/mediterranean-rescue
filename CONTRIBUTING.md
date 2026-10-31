# Contribuer

Merci de donner de votre temps à la carte de SOS MEDITERRANEE. Première fois ? Lisez d'abord le
[guide des bénévoles](docs/guides/README.md).

## D'abord, les gens

Tout passe par le canal du projet sur le Mattermost de Data for Good : questions, entraide et
rendez-vous y sont annoncés. Présentez-vous en arrivant.

## En cinq étapes

1. **Choisir une issue** `good first issue` ou `prête`, et commenter « Je prends ». Une à la
   fois ; si vous arrêtez, dites-le, quelqu'un la reprendra.
2. **Créer sa branche** depuis `main` :

   ```sh
   git switch main && git pull
   git switch -c feature/12-fiche-operation   # type/numéro-de-l-issue-mots-cles
   ```

3. **Coder**, avec un test pour chaque critère de l'issue.
4. **Ouvrir la pull request** vers `main`, et cocher la liste du modèle.
5. **Répondre à la relecture.** Un tech lead relit, puis merge.

Les vérifications tournent toutes seules : à chaque commit sur votre machine, et à chaque pull
request sur GitHub. Pour les lancer vous-même : la tâche VS Code « Tout vérifier », ou les
commandes de [TECHNICAL.md](TECHNICAL.md#vérifier-avant-de-pousser).

Bloqué ? Écrivez-le dans l'issue ou sur le canal : c'est normal, et c'est plus rapide que de
chercher seul.

## Quatre règles

> [!IMPORTANT]
> 1. **Aucune donnée réelle, aucun secret** : ni dans Git, ni dans une issue, ni dans une pull
>    request, ni dans un outil d'IA. Les exemples sont fictifs et marqués `FICTIF`.
> 2. **Inconnu reste vide, jamais zéro.**
> 3. **Aucun code copié de la carte actuelle** (CartONG, sans licence) : elle sert de modèle,
>    pas de source.
> 4. **L'IA est permise, jamais obligatoire.** Même chemin pour tous ; si un outil d'IA a servi,
>    cochez-le dans la pull request, et sachez expliquer chaque ligne
>    ([conseils](docs/guides/assistant-ia.md)).

## Les étiquettes à connaître

`good first issue` pour commencer, `niveau-2` puis `niveau-3` ensuite, `prête` quand on peut la
prendre. Les autres sont décrites au survol sur GitHub.

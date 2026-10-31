# Contribuer

Merci de donner de ton temps à la carte de SOS MEDITERRANEE. Première fois ? Lis d'abord le
[guide des bénévoles](docs/guides/README.md).

## D'abord, les gens

Tout passe par le canal du projet sur le Mattermost de Data for Good : questions, entraide et
rendez-vous y sont annoncés. Présente-toi en arrivant, et demande l'accès en écriture au dépôt :
c'est lui qui te permet de pousser tes branches.

## Le modèle : une branche par issue

On travaille en **feature branching** : chaque issue a sa branche, créée depuis `main`, et revient
dans `main` par une pull request. Pas de fork : tu pousses ta branche directement sur ce dépôt.

`main` est protégée. Personne n'y pousse directement ; une pull request n'y entre que si :

- la CI est verte ;
- un tech lead l'a approuvée (une approbation suffit) ;
- elle est mergée en **squash** : tous les commits de la branche deviennent un seul commit sur
  `main`, qui porte le titre de la pull request.

## En cinq étapes

1. **Choisir une issue** `good first issue` ou `prête`, et commenter « Je prends ». Un tech lead
   te l'assigne. Une à la fois ; si tu arrêtes, dis-le, quelqu'un la reprendra. Une issue
   assignée sans nouvelles reçoit un rappel au bout de 5 jours, et elle est rendue au bout de
   7 jours : elle redevient libre pour quelqu'un d'autre.
2. **Créer sa branche** depuis `main` :

   ```sh
   git switch main && git pull
   git switch -c feat/12-fiche-operation   # type/numéro-de-l-issue-mots-cles
   ```

3. **Coder**, avec un test pour chaque critère de l'issue, et pousser la branche :
   `git push -u origin feat/12-fiche-operation`.
4. **Ouvrir la pull request** vers `main`, et cocher la liste du modèle. Tu peux l'ouvrir tôt, en
   brouillon (« draft »), même avec des tests encore rouges : c'est la bonne façon de travailler
   en écrivant les tests d'abord. Seul le merge demande une CI verte.
5. **Répondre à la relecture.** Un tech lead relit, approuve, puis merge.

Les vérifications tournent toutes seules : à chaque commit sur ta machine, et à chaque pull
request sur GitHub. Pour les lancer toi-même : la tâche VS Code « Tout vérifier », ou les
commandes de [TECHNICAL.md](TECHNICAL.md#vérifier-avant-de-pousser).

Bloqué ? Écris-le dans l'issue ou sur le canal : c'est normal, et c'est plus rapide que de
chercher seul.

## Les messages de commit

On suit les [commits conventionnels](https://www.conventionalcommits.org/fr/v1.0.0/) : un type, deux
points, puis ce que fait le commit, en français ou en anglais. Le titre de la pull request suit le
même format, puisqu'il devient le message du commit sur `main`.

| Type | Quand | Exemple |
|---|---|---|
| `feat` | une fonctionnalité nouvelle | `feat: ajoute le modèle Operation` |
| `fix` | une correction de bug | `fix: garde vide un nombre de personnes inconnu` |
| `docs` | la documentation seule | `docs: corrige la définition du MRCC` |
| `test` | des tests, sans changer le code | `test: vérifie qu'une opération non publiée reste cachée` |
| `refactor` | le code change de forme, pas de comportement | `refactor: sépare le bandeau de la page de la carte` |
| `chore` | l'entretien : dépendances, réglages | `chore: met à jour Django en 6.1.3` |
| `ci` | la CI et l'outillage de vérification | `ci: lance les tests dans le navigateur sur Firefox` |

On peut préciser la zone entre parenthèses : `feat(frontend): affiche le bandeau`.

## Quatre règles

> [!IMPORTANT]
> 1. **Aucune donnée réelle, aucun secret** : ni dans Git, ni dans une issue, ni dans une pull
>    request, ni dans un outil en ligne. Les exemples sont fictifs et marqués `FICTIF`.
> 2. **Inconnu reste vide, jamais zéro.**
> 3. **Aucun code copié de la carte actuelle** (CartONG, sans licence) : elle sert de modèle,
>    pas de source.
> 4. **Un assistant IA ? Demande d'abord.** Les règles d'usage sont en cours d'écriture par les
>    tech leads, avec Data for Good. En attendant, parles-en à ton tech lead avant de t'en servir.

## Les étiquettes à connaître

`good first issue` pour commencer, `niveau-2` puis `niveau-3` ensuite, `prête` quand on peut la
prendre. Les autres sont décrites au survol sur GitHub.

Les outils et les robots en plus de la CI et de pre-commit arrivent petit à petit, chacun par une
issue `ci` que tu peux prendre. Améliorer la CI elle-même, c'est aussi du travail ouvert aux
bénévoles.

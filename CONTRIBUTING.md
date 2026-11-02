# Contribuer

Merci de donner de ton temps à la carte de SOS MEDITERRANEE.

Tout passe par le canal du projet sur le Mattermost de Data for Good : questions, entraide et
rendez-vous. Présente-toi en arrivant et demande l'accès en écriture au dépôt, pour pousser tes
branches.

## Le chemin d'une issue

On travaille en **feature branching** : une branche par issue, créée depuis `main`, qui revient
dans `main` par une pull request. Pas de fork.

1. **Prends une issue** et commente « Je prends ». Un tech lead te l'assigne. Une issue à la fois.
2. **Crée ta branche** depuis `main`, nommée `type/numéro-mots-cles` :

   ```sh
   git switch main && git pull
   git switch -c feat/12-modele-operation
   ```

3. **Code et teste.** Chaque critère de l'issue a au moins un test.
4. **Ouvre la pull request** vers `main`. Tu peux l'ouvrir tôt en brouillon, même avec des tests
   rouges : seul le merge demande une CI verte.
5. **Réponds à la relecture.** Un tech lead approuve (une approbation suffit) et merge en squash.

Sans nouvelles sur une issue assignée, un tech lead te relance au 5e jour. Au 7e jour, l'issue
redevient libre. Bloqué ? Écris-le dans l'issue ou sur le canal, c'est normal.

## Les messages de commit

On suit les [commits conventionnels](https://www.conventionalcommits.org/fr/v1.0.0/). Le titre de
la pull request aussi, puisqu'il devient le commit sur `main`.

| Type | Quand | Exemple |
|---|---|---|
| `feat` | une fonctionnalité | `feat: ajoute le modèle Operation` |
| `fix` | une correction | `fix: garde vide un nombre inconnu` |
| `docs` | la documentation | `docs: corrige la définition du MRCC` |
| `test` | des tests seuls | `test: vérifie qu'une opération non publiée reste cachée` |
| `refactor` | la forme change, pas le comportement | `refactor: sépare le bandeau de la carte` |
| `chore` | l'entretien, les dépendances | `chore: met à jour Django en 6.1.3` |
| `ci` | la CI et l'outillage | `ci: lance les tests sur Firefox` |

## Les règles

- **Aucune donnée réelle, aucun secret** dans Git, une issue ou une pull request. Les exemples
  sont fictifs et marqués `FICTIF`.
- **Inconnu reste vide, jamais zéro.**

## Les étiquettes

`good first issue` pour commencer, puis `niveau-2` et `niveau-3`. `front`, `back`, `data`, `docs`
et `ci` disent la zone touchée, `bloquée` qu'une issue attend une réponse. L'avancement se suit
dans les colonnes du projet GitHub.

Les outils en plus de la CI et de pre-commit arrivent petit à petit, chacun par une issue `ci`.
Améliorer la CI, c'est aussi du travail ouvert aux bénévoles.

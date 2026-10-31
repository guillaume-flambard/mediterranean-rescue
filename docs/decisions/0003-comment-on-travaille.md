# 0003. Comment on travaille : un dépôt, des specs courtes, un test par critère

Date : 30 octobre 2026. Statut : en vigueur, mise à jour le 31 octobre 2026 (branches, commits,
assistants IA).

## Contexte

Le nombre de bénévoles peut aller de quelques-uns à plusieurs dizaines, de tous niveaux. Chacun
doit trouver du travail clair à sa mesure, et un dépôt où tout le monde pousse sans cadre devient
vite impossible à relire. Les tech leads relisent et mergent
toutes les pull requests : le cadre doit leur faciliter la relecture, pas l'alourdir.

Trois méthodes ont été envisagées :

- **DDD complet** (agrégats, couches, architecture hexagonale) : trop lourd pour des bénévoles
  qui découvrent Django.
- **Spec-driven outillé** (Spec Kit, OpenSpec) : une seconde source de vérité à côté des issues,
  et un outil de plus à apprendre.
- **Aucun cadre** : ça casse dès le cinquième bénévole.

## Décision

**Un seul dépôt, deux dossiers.** `backend/` (Django) et `frontend/` (Vue) vivent dans le même
dépôt, sans outil de monorepo (ni workspace, ni Nx, ni Turborepo). Un bénévole clone une fois,
une issue et une pull request peuvent toucher l'API et la carte ensemble.

**Une spec courte par issue.** L'issue est la spec, il n'y a pas d'autre document. Elle dit :

1. le besoin, en une phrase d'utilisateur (« En tant que journaliste, je veux… pour… ») ;
2. les critères d'acceptation, vérifiables (« Étant donné…, quand…, alors… ») ;
3. ce qui est hors du périmètre ;
4. la zone de fichiers touchée et le niveau (1, 2 ou 3).

Une issue sans critères n'est pas « prête » ([quand une issue est prête](../equipe.md#quand-une-issue-est-prête)).
Les PM/PO écrivent le besoin, les tech leads ajoutent les critères, la zone et le niveau.

**Du DDD, on ne garde que le vocabulaire et le découpage.** Les mots du métier sont dans le
[glossaire](../glossaire.md) et le code les reprend. Une application Django par domaine
(`operations` aujourd'hui, puis par exemple `vessels`, `sources`), comme le tutoriel Django.

**Un test par critère, pas de TDD imposé.** Chaque critère d'acceptation a au moins un test dans
la pull request. Pour un bug, le test qui reproduit le bug s'écrit en premier : c'est le seul
endroit où l'ordre est imposé. Écrire les tests avant le code reste conseillé, jamais exigé : une
pull request peut s'ouvrir en brouillon avec des tests rouges, seul le merge demande une CI verte.

**Feature branching, sans fork.** Chaque issue a sa branche, créée depuis `main` et nommée
`type/numéro-mots-cles`, qui revient dans `main` par une pull request. Les bénévoles reçoivent
l'accès en écriture et poussent leurs branches sur le dépôt : pas de fork, un seul endroit où
chercher le travail en cours.

**Des commits conventionnels.** Les messages de commit et les titres de pull request suivent les
[commits conventionnels](https://www.conventionalcommits.org/fr/v1.0.0/) (`feat`, `fix`, `docs`,
`test`, `refactor`, `chore`, `ci`), en français ou en anglais. Les exemples sont dans
[CONTRIBUTING.md](../../CONTRIBUTING.md#les-messages-de-commit).

**La CI garde la porte.** Les mêmes contrôles tournent en local (pre-commit) et sur GitHub (CI) :
style, tests du backend et du front, migration oubliée, types, construction, parcours dans un
navigateur. `main` est protégée : pull request obligatoire, CI verte, une approbation d'un tech
lead, merge en squash. Une approbation suffit, pour que les relectures ne s'accumulent pas.

**Les outils arrivent un par un.** En dehors de la CI et de pre-commit, aucun robot n'est
installé d'office. Chaque outil en plus est une issue, que des bénévoles peuvent prendre ; le
polissage de la CI aussi.

**Ce qui empêche le chaos quand il y a du monde :**

- une issue à la fois par bénévole, assignée avant de commencer ; sans activité, un rappel au
  bout de 5 jours, et l'issue est rendue au bout de 7 jours ;
- des petites pull requests (une issue, une PR, environ 300 lignes au plus hors tests) ;
- la zone de fichiers dans l'issue : deux issues prêtes en même temps ne touchent pas les mêmes
  fichiers ;
- chaque zone (backend et données, carte, CI) a un tech lead relecteur, déclaré dans
  `CODEOWNERS`.

**Les assistants IA, étape par étape.** Les règles d'usage des assistants de code sont en cours
d'écriture par les tech leads, avec Data for Good. Jusque-là :

- la documentation pour les personnes (README, CONTRIBUTING, guides) ne parle pas d'IA et ne la
  suppose jamais ;
- qui veut se servir d'un assistant en parle d'abord à son tech lead, puis le coche dans la pull
  request, avec le nom de l'outil ;
- les règles restent les mêmes pour tous : issue, tests par critère, CI, relecture, et la
  personne qui ouvre la PR sait expliquer chaque ligne ;
- l'usage s'ouvrira étape par étape, chaque étape par une nouvelle décision dans ce dossier.

Les consignes destinées aux outils eux-mêmes vivent dans `AGENTS.md`, à la racine. Ce fichier ne
s'adresse pas aux personnes.

## Conséquences

- Un bénévole a un seul chemin à apprendre : issue, branche, pull request. Il est écrit dans
  [CONTRIBUTING.md](../../CONTRIBUTING.md).
- Les tech leads relisent des PR courtes dont les critères sont connus d'avance.
- Si les relectures s'accumulent, des bénévoles confirmés (niveau 3) rejoignent les relecteurs.

# 0003. Comment on travaille : un dépôt, des specs courtes, un test par critère

Date : 30 octobre 2026. Statut : en vigueur.

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
endroit où l'ordre est imposé. Écrire les tests avant le code reste conseillé, jamais exigé.

**La CI garde la porte.** Les mêmes contrôles tournent en local (pre-commit) et sur GitHub (CI) :
style, tests du backend et du front, migration oubliée, types, construction, parcours dans un
navigateur. Personne ne pousse directement sur `main` : tout passe par une pull request.

**Ce qui empêche le chaos quand il y a du monde :**

- une issue à la fois par bénévole, assignée avant de commencer, rendue après 7 jours sans
  nouvelles ;
- des petites pull requests (une issue, une PR, environ 300 lignes au plus hors tests) ;
- la zone de fichiers dans l'issue : deux issues prêtes en même temps ne touchent pas les mêmes
  fichiers ;
- chaque zone (backend et données, carte, CI) a un tech lead relecteur, déclaré dans
  `CODEOWNERS` ;

**Avec ou sans IA, le même chemin.** Une partie des bénévoles se servira d'assistants de code,
une autre n'en veut pas. Le dépôt sert les deux sans trancher pour eux :

- la documentation pour les personnes (README, CONTRIBUTING, guides) ne suppose jamais l'IA ;
- les assistants ont leur fichier, `AGENTS.md`, et les personnes qui s'en servent un guide
  facultatif ([assistant-ia.md](../guides/assistant-ia.md)) ;
- les règles sont les mêmes pour tous : issue, tests par critère, CI, relecture ;
- l'IA est permise, jamais obligatoire, toujours déclarée dans la pull request (outil, modèle,
  ce qu'il a produit), comme le demande la charte de Data for Good. La personne qui ouvre la PR
  sait expliquer chaque ligne ;
- le code reste lisible par quelqu'un qui n'utilise pas d'IA : c'est une consigne d'`AGENTS.md`.

## Conséquences

- Un bénévole a un seul chemin à apprendre : issue, branche, PR. Il est écrit dans
  [CONTRIBUTING.md](../../CONTRIBUTING.md).
- Les tech leads relisent des PR courtes dont les critères sont connus d'avance.
- Si les relectures s'accumulent, des bénévoles confirmés (niveau 3) rejoignent les relecteurs.

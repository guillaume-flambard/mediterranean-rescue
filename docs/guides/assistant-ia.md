# Contribuer avec un assistant IA

Ce guide est facultatif. Vous ne vous servez pas d'IA ? Il ne vous concerne pas : le reste de
la documentation ne suppose jamais qu'on en utilise une, et la relecture est la même pour tout
le monde.

Vous vous en servez ? L'IA est permise par la charte de Data for Good, à trois conditions : vous
comprenez ce que vous proposez, vous le déclarez dans la pull request, et aucune donnée sensible
ne passe par l'outil.

## Le bon usage, en six points

1. **Donnez-lui l'issue, pas une idée.** Collez le besoin et les critères d'acceptation, et
   demandez-lui de lire [AGENTS.md](../../AGENTS.md) : c'est le fichier de consignes écrit pour
   les assistants. La plupart des outils le lisent seuls ; sinon, indiquez-le.
2. **Faites-lui écrire les tests d'abord.** Un test par critère, que vous lisez avant le code :
   s'ils ne disent pas ce que demande l'issue, le code ne le fera pas non plus.
3. **Gardez des petits pas.** Une issue, une branche, un diff que vous pouvez relire en entier.
   Un assistant qui « en profite » pour réorganiser d'autres fichiers sort de l'issue : refusez.
4. **Relisez chaque ligne.** Si vous ne savez pas expliquer une ligne, demandez-lui de
   l'expliquer, ou retirez-la. À la relecture, c'est à vous qu'on posera la question.
5. **Lancez vous-même les vérifications** ([TECHNICAL.md](../../TECHNICAL.md#vérifier-avant-de-pousser)).
   Un assistant peut affirmer qu'un test passe sans l'avoir lancé.
6. **Déclarez-le** dans la pull request : l'outil, le modèle, ce qu'il a produit. C'est une
   information pour la relecture, pas un reproche.

## Ce qui ne passe jamais par un assistant

- Une donnée réelle de SOS MEDITERRANEE, même un extrait, même « pour tester » : personnes
  secourues, positions non publiques, fichiers internes.
- Un secret : clé d'API, mot de passe, contenu d'un fichier `.env`.
- Une traduction publiée sans relecture par une personne qui parle la langue.
- Un message, un compte rendu ou une réponse à un humain du projet copié tel quel depuis l'IA
  (charte de Data for Good).

## Pour les tech leads

`AGENTS.md` et les règles des assistants sont maintenus par les tech leads, qui les relisent
comme du code. Une proposition d'amélioration se fait par une pull request, relue avec soin.

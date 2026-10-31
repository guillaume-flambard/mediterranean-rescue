<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/assets/banniere-sombre.svg">
  <img alt="SOSmed Carto, la carte des opérations de sauvetage en Méditerranée centrale" src=".github/assets/banniere-claire.svg">
</picture>

<p align="center">
  <a href="https://github.com/dataforgoodfr/mediterranean-rescue/actions/workflows/ci.yml"><img alt="Vérifications" src="https://github.com/dataforgoodfr/mediterranean-rescue/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/dataforgoodfr/mediterranean-rescue/issues?q=is%3Aopen+label%3A%22good+first+issue%22"><img alt="Premières issues" src="https://img.shields.io/github/issues/dataforgoodfr/mediterranean-rescue/good%20first%20issue?label=premi%C3%A8res%20issues&color=E83E1B"></a>
  <a href="CONTRIBUTING.md"><img alt="Bénévoles bienvenus" src="https://img.shields.io/badge/b%C3%A9n%C3%A9voles-bienvenus-1B2747"></a>
  <a href="LICENSE"><img alt="Licence MIT" src="https://img.shields.io/badge/licence-MIT-1B2747"></a>
</p>

<p align="center">
  <a href="https://map.sosmediterranee.org/">La carte actuelle</a> ·
  <a href="docs/guides/README.md">Le guide des bénévoles</a> ·
  <a href="https://dataforgood.fr/">Data for Good</a>
</p>

SOS MEDITERRANEE recherche et secourt les personnes en détresse en Méditerranée centrale. Avec
les bénévoles de [Data for Good](https://dataforgood.fr/), on refait la carte publique de ses
opérations, pour trois usages : **la transparence**, **le plaidoyer** (journalistes, chercheurs,
étudiants) et **la collecte de fonds**.

Chaque opération affichée a été vérifiée par une personne avant d'être publiée. Ce qui n'est pas
connu reste vide : la carte n'invente jamais un chiffre.

> [!NOTE]
> Socle en construction. La carte actuelle n'est plus mise à jour depuis février 2024.

## Contribuer

> [!TIP]
> Première fois ? Commencez par le [guide des bénévoles](docs/guides/README.md) : cinq minutes
> pour savoir comment l'équipe marche et par où entrer.

| Je veux… | Par où commencer |
|---|---|
| **Coder** (Django, Vue, données) | Une issue [`good first issue`](https://github.com/dataforgoodfr/mediterranean-rescue/issues?q=is%3Aopen+label%3A%22good+first+issue%22), puis [CONTRIBUTING.md](CONTRIBUTING.md) |
| **Aider sans connaître Git** | Corriger un texte directement dans GitHub : ouvrir le fichier, puis le crayon « Modifier » |
| **Aider sans coder** | Tester la carte, relire un texte, proposer une idée : sur le canal du projet du Mattermost de Data for Good |

```mermaid
flowchart LR
  A[Je choisis une issue] --> B[Je dis « Je prends »]
  B --> C[Je crée ma branche]
  C --> D[Je code et je teste]
  D --> E[J'ouvre une pull request]
  E --> F[Un tech lead relit]
  F --> G[C'est en ligne]
```

Installer le projet et le lancer en local : [TECHNICAL.md](TECHNICAL.md).

## Licence

[MIT](LICENSE). Sans lien avec CartONG ; ce n'est pas le site officiel de SOS MEDITERRANEE.

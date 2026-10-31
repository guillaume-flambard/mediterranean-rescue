# Le guide des bénévoles

Bienvenue ! Cinq minutes pour savoir comment l'équipe marche et par où entrer.

## Le projet en deux phrases

SOS MEDITERRANEE secourt des personnes en détresse en Méditerranée centrale. Avec Data for Good,
on refait la carte publique de ses opérations, pour la transparence, le plaidoyer et la collecte
de fonds.

Le code part des gabarits officiels de Django et de Vue : la carte se construit pièce par pièce,
une issue à la fois. Les premières issues sont là pour toi.

## Qui fait quoi

| Qui | Ce qu'il fait |
|---|---|
| SOS MEDITERRANEE | dit ce dont elle a besoin, valide ce qui est publié |
| Les PM/PO | recueillent les besoins, les transforment en issues |
| Les tech leads | préparent les issues, relisent et mergent, aident quand on bloque |
| Toi | tu prends une issue, tu la mènes jusqu'au merge, tu demandes de l'aide tôt |

On se retrouve sur le canal du projet du Mattermost de Data for Good : les rendez-vous y sont
annoncés.

## Le chemin d'une contribution

```mermaid
flowchart LR
  A[Je choisis une issue] --> B[Je dis « Je prends »]
  B --> C[Je crée ma branche]
  C --> D[Je code et je teste]
  D --> E[J'ouvre une pull request]
  E --> F[Un tech lead relit]
  F --> G[C'est en ligne]
```

Le détail tient en cinq étapes : [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Trois quêtes

On commence au niveau 1 quelle que soit son expérience : c'est le plus court chemin pour
connaître le projet. On passe au suivant quand la quête est faite.

**1. Premiers pas** ([guide](01-premiers-pas.md))
- [ ] Lancer le backend et le frontend sur sa machine.
- [ ] Se connecter à l'admin de Django.
- [ ] Faire merger une première pull request sur une `good first issue`.
- [ ] Noter dans une issue `docs` ce qui t'a surpris ou bloqué en arrivant.

**2. De bout en bout**
- [ ] Faire merger deux pull requests `niveau-2`, chacune avec ses tests.
- [ ] Suivre une donnée du modèle Django jusqu'à l'écran, dans une de ces deux pull requests.
- [ ] Relire la pull request d'un autre bénévole et y laisser un commentaire utile.

**3. Confirmé** ([architecture visée](03-architecture.md))
- [ ] Faire merger une pull request `niveau-3`.
- [ ] Aider un tech lead à découper une issue, ou proposer une [décision](../decisions/).

Quête 3 faite : tu peux relire des pull requests avec les tech leads.

## Sous la main

- Les mots du métier (SAR, MRCC, AIS…) : le [glossaire](../glossaire.md).

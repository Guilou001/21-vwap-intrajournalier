# De très petits frais peuvent-ils effacer les gains d'une stratégie ?

Une stratégie peut paraître très rentable si chaque achat et chaque vente se font au prix affiché. En pratique, le prix obtenu peut être légèrement moins bon. Cet écart se répète à chaque opération.

Ce projet reprend une règle publiée par Zarattini et Aziz. Elle achète quand le prix dépasse la moyenne payée depuis l'ouverture et vend à découvert dans le cas inverse.

**La règle change de position environ seize fois par jour. Après la période de l'article, moins d'un demi-cent de coût supplémentaire par action suffit à effacer son gain.**

## Le coût qui fait basculer le résultat

![Rendement annuel de la stratégie selon le coût ajouté à chaque exécution](results/figures/seuil.png)

L'axe horizontal ajoute un glissement de prix à chaque action échangée. L'axe vertical montre le rendement annuel. Quand une courbe passe sous zéro, la stratégie perd de l'argent.

| Période sur QQQ | Coût supplémentaire annulant le rendement |
|---|---:|
| Du 2 janvier 2018 au 28 septembre 2023 | 1,02 cent US par action échangée |
| Du 29 septembre 2023 au 28 août 2026 | 0,41 cent US par action échangée |

Ces seuils sont calculés séparément par recherche numérique. Les traits de la figure relient une grille de coûts et ne donnent qu'une approximation visuelle des passages à zéro. [Seuils et dates](results/tables/seuils.csv).

Une commission de 0,0005 dollar US par action est déjà facturée dans tous les cas. « Sans glissement » ne signifie donc pas « sans aucun frais ».

## Vérifier la reproduction avant de parler de rentabilité

Le placement passif de l'article est retrouvé à 0,03 point de pourcentage près. La stratégie active donne toutefois 587 % de rendement total contre 671 % publiés. Les conventions de prix et de clôture changent les résultats, et l'écart exact à l'article reste inexpliqué.

Le dépôt publie ces variantes, les résultats annuels et un contrôle utilisant la moyenne d'un autre jour.

## Les limites du test

Le coût est imposé, pas mesuré sur un carnet d'ordres. Il ne tient pas compte de l'effet croissant des gros ordres sur les prix.

La seconde période commence après l'échantillon de l'article, mais 31 de ses séances précèdent sa publication. Elle ne mesure donc pas un effet causé par la publication.

## Refaire les calculs

```bash
uv sync --locked --all-extras
uv run pytest
uv run vwp fetch
uv run vwp tout
```

Le téléchargement nécessite des identifiants Alpaca conservés hors du dépôt. Les tests utilisent des séances fabriquées et ne demandent aucune donnée de marché.

## Pour aller plus loin

[Méthodes, résultats complets et références](docs/ETUDE_DETAILLEE.md) · [Présentation en PDF](rapport/rapport.pdf) · [Citer le projet](CITATION.cff) · [Licence](LICENSE).

## English summary

A published VWAP trading rule is replayed with commissions and a range of execution costs. Its break-even slippage falls from 1.02 US cents per traded share in the paper's sample to 0.41 cents afterward. The active strategy is not replicated exactly.

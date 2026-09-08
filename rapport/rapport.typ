#set document(title: "De très petits frais peuvent-ils effacer les gains d'une stratégie ?", author: "Guillaume Vaudescal")
#set page(
  paper: "a4",
  margin: (x: 2.2cm, y: 2.4cm),
  numbering: "1 / 1",
  footer: context [
    #set text(size: 8pt, fill: luma(90))
    #grid(columns: (1fr, auto), align: (left, right),
      [vwap-intrajournalier], [#counter(page).display("1 / 1", both: true)])
  ],
)
#set text(font: ("Helvetica", "Arial", "DejaVu Sans"), size: 10pt, lang: "fr")
#set par(justify: true, leading: 0.68em, spacing: 1.1em)
#set heading(numbering: none)
#show heading.where(level: 2): it => block(above: 1.6em, below: 0.8em, text(size: 13pt, it))
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.6em, text(size: 11pt, it))
#show raw.where(block: true): it => block(
  fill: luma(246), inset: 8pt, radius: 3pt, width: 100%, text(size: 8.5pt, it))
#show raw.where(block: false): it => text(size: 9pt, fill: rgb("#1a3f66"), it)
#show quote.where(block: true): it => block(
  inset: (left: 10pt), stroke: (left: 1.5pt + luma(180)),
  text(style: "italic", fill: luma(45), it.body))
// la table NE DOIT PAS être enfermée dans un par() : Typst 0.15 la supprime alors
// entièrement, sans erreur. Le réglage se pose donc dans la portée du bloc.
#show table: it => block(above: 1.1em, below: 1.1em,
  [#set par(justify: false); #text(size: 8.8pt, it)])
#show figure: it => block(above: 1.4em, below: 1.4em, it)
#show figure.caption: it => text(size: 8.5pt, fill: luma(70), it)
#show link: it => text(fill: rgb("#0072B2"), it)

#align(center)[
  #block(width: 100%)[
    #text(size: 18pt, weight: "bold")[De très petits frais peuvent-ils effacer les gains d'une stratégie ?]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-09-08 · #link("https://github.com/Guilou001/21-vwap-intrajournalier")[Guilou001/21-vwap-intrajournalier]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Une stratégie peut paraître très rentable si chaque achat et chaque vente se font au prix affiché. En pratique, le prix obtenu peut être légèrement moins bon. Cet écart se répète à chaque opération.

Ce projet reprend une règle publiée par Zarattini et Aziz. Elle achète quand le prix dépasse la moyenne payée depuis l'ouverture et vend à découvert dans le cas inverse.

*La règle change de position environ seize fois par jour. Après la période de l'article, moins d'un demi-cent de coût supplémentaire par action suffit à effacer son gain.*

== Le coût qui fait basculer le résultat

#figure(image("../results/figures/seuil.png", width: 100%), caption: [Rendement annuel de la stratégie selon le coût ajouté à chaque exécution])

L'axe horizontal ajoute un glissement de prix à chaque action échangée. L'axe vertical montre le rendement annuel. Quand une courbe passe sous zéro, la stratégie perd de l'argent.

#table(
  columns: 2,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Période sur QQQ*],
    [*Coût supplémentaire annulant le rendement*],
    [Du 2 janvier 2018 au 28 septembre 2023],
    [1,02 cent US par action échangée],
    [Du 29 septembre 2023 au 28 août 2026],
    [0,41 cent US par action échangée],
)

Ces seuils sont calculés séparément par recherche numérique. Les traits de la figure relient une grille de coûts et ne donnent qu'une approximation visuelle des passages à zéro. #link("results/tables/seuils.csv")[Seuils et dates].

Une commission de 0,0005 dollar US par action est déjà facturée dans tous les cas. « Sans glissement » ne signifie donc pas « sans aucun frais ».

== Vérifier la reproduction avant de parler de rentabilité

Le placement passif de l'article est retrouvé à 0,03 point de pourcentage près. La stratégie active donne toutefois 587 % de rendement total contre 671 % publiés. Les conventions de prix et de clôture changent les résultats, et l'écart exact à l'article reste inexpliqué.

Le dépôt publie ces variantes, les résultats annuels et un contrôle utilisant la moyenne d'un autre jour.

== Les limites du test

Le coût est imposé, pas mesuré sur un carnet d'ordres. Il ne tient pas compte de l'effet croissant des gros ordres sur les prix.

La seconde période commence après l'échantillon de l'article, mais 31 de ses séances précèdent sa publication. Elle ne mesure donc pas un effet causé par la publication.

== Refaire les calculs

#raw("uv sync --locked --all-extras\nuv run pytest\nuv run vwp fetch\nuv run vwp tout", block: true, lang: "bash")

Le téléchargement nécessite des identifiants Alpaca conservés hors du dépôt. Les tests utilisent des séances fabriquées et ne demandent aucune donnée de marché.

== Pour aller plus loin

#link("docs/ETUDE_DETAILLEE.md")[Méthodes, résultats complets et références] · #link("rapport/rapport.pdf")[Présentation en PDF] · #link("CITATION.cff")[Citer le projet] · #link("LICENSE")[Licence].

== English summary

A published VWAP trading rule is replayed with commissions and a range of execution costs. Its break-even slippage falls from 1.02 US cents per traded share in the paper's sample to 0.41 cents afterward. The active strategy is not replicated exactly.

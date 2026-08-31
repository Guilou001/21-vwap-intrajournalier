#set document(title: "La stratégie qui transforme 25 000 dollars en 2 millions en perd si l'on paie un demi-cent", author: "Guillaume Vaudescal")
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
    #text(size: 18pt, weight: "bold")[La stratégie qui transforme 25 000 dollars en 2 millions en perd si l'on paie un demi-cent]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-08-31 · #link("https://github.com/Guilou001")[Guilou001]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Un article très lu annonce qu'un signal fondé sur le prix moyen pondéré par les volumes aurait transformé 25 000 dollars en 192 656 sur six ans, et en 2 millions avec un fonds à levier. Il suppose un glissement nul. La stratégie change de position *seize fois par jour* : ce dépôt mesure ce que cette hypothèse vaut.

*Résultat en une phrase.* Le repère passif de l'article se reproduit *à trois dixièmes de point près*, ce qui atteste les données ; sa stratégie active se reproduit à 587 % contre 671 % publiés, avec un ratio de Sharpe de 2,01 contre 2,10 ; mais elle s'annule à *1,05 cent* de glissement par passage, et à *0,42 cent* sur la fenêtre postérieure à sa publication, où son rendement annuel tombe de 40,5 % à *7,0 %* avant même le moindre frais.

_Summary in English. Zarattini and Aziz (SSRN 4631351) report that a VWAP trend-following day trading system would have turned \$25,000 into \$192,656 on QQQ between January 2018 and September 2023, a 671 % return with a 2.1 Sharpe ratio and a 9.4 % maximum drawdown, and into \$2,085,417 using the 3x leveraged TQQQ. Their backtest assumes zero slippage. Replaying the published rules on consolidated one-minute bars: the passive benchmark reproduces to within 0.03 percentage points, confirming the data and window; the active strategy reaches 587 % with a 2.01 Sharpe and a 9.3 % drawdown. It flips position 15.9 times per session. Charging 1.05 cents of slippage per fill wipes the entire in-sample return; on the post-publication window the break-even is 0.42 cents and the zero-slippage annual return falls from 40.5 % to 7.0 %. On TQQQ, half a cent turns the reported \$2 million into a 13 % loss. Finally, the two years immediately preceding the paper's sample, 2016 and 2017, are both negative._

== 1. La question posée

*Le signal, en mots simples.* À chaque minute, on divise tout l'argent échangé depuis l'ouverture par toutes les actions échangées. Le résultat est le prix moyen payé depuis le matin. Si le prix du moment est au-dessus, les acheteurs paient plus cher que la moyenne du jour, ce que l'article lit comme un déséquilibre en faveur de la hausse.

*La règle.* On est acheteur quand le prix est au-dessus de cette moyenne, vendeur à découvert sinon, tout le capital à chaque fois, et l'on solde à la clôture. Rien de plus.

*Ce que l'article annonce*, dans son tableau 1 :

#table(
  columns: 6,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [**],
    [*Rendement total*],
    [*Par an*],
    [*Volatilité*],
    [*Sharpe*],
    [*Pire creux*],
    [Le signal sur QQQ],
    [671 %],
    [43 %],
    [18 %],
    [2,1],
    [9,4 %],
    [Acheter et conserver QQQ],
    [126 %],
    [15 %],
    [25 %],
    [0,7],
    [35,6 %],
)

*L'hypothèse qui porte tout.* L'article l'écrit lui-même : « Since we initiated our system with a small account of only \$25,000, we assumed *no slippage* in our order fills. » Une stratégie qui change de position seize fois par jour paie seize écarts entre les meilleurs prix acheteur et vendeur. La question du dépôt est de savoir combien.

== 2. D'où vient le projet, et ce qu'il apporte

Trois apports.

- *Le repère passif d'abord*, qui n'a aucun paramètre : s'il tombe juste, un écart sur la stratégie

active vient de ses règles et non des prix.

- *La facture*, en cents par passage, dans l'échantillon de l'article puis après sa publication.
- *Trois contrôles* que l'article ne fait pas : le prix retenu pour la moyenne, un placebo qui

emploie la moyenne d'un autre jour, et le rendement année par année de part et d'autre de la fenêtre choisie.

Une correction au passage : le registre du portefeuille tenait le PDF pour inaccessible aux scripts, 403 sur SSRN. Il est en libre accès sur le site du premier auteur, #raw("concretumgroup.com"), mesuré le 30 août 2026 à 1 012 421 octets et 26 pages. La règle générale se confirme : chercher le PDF chez l'auteur avant de conclure qu'il est fermé.

== 3. Les données

Barres d'une minute du *flux consolidé*, prix bruts, de janvier 2016 au 28 août 2026, sur QQQ et sur TQQQ. Séances régulières de 9 h 30 à 16 h, séances écourtées de veille de congé retirées.

Le flux consolidé et non celui d'IEX : ce dernier ne capte que 1,81 % du volume et n'a vu aucune transaction sur 57 % des minutes, si bien qu'un prix moyen pondéré par les volumes calculé dessus porterait sur un cinquantième du marché.

== 4. La méthode, pas à pas

+ *Reproduire le repère passif* sur la fenêtre exacte de l'article, sans aucun paramètre.
+ *Écrire la règle* telle que la section 3 de l'article l'énonce, la position d'une minute venant du signal de la minute précédente.
+ *Composer le capital*, tout engagé à chaque instant, donc un nombre d'actions qui grandit avec lui, et facturer chaque changement de position pour *deux fois* la position détenue.
+ *Balayer le glissement* de zéro à deux cents et chercher le seuil qui annule le rendement.
+ *Rejouer après la publication*, puis avec la moyenne pondérée d'un autre jour, puis année par année.

== 5. Les résultats

=== 5.1 Le repère passif se reproduit, donc les données sont les bonnes

#table(
  columns: 4,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Grandeur*],
    [*Publiée*],
    [*Recalculée*],
    [*Écart*],
    [Rendement total],
    [126 %],
    [*125,97 %*],
    [−0,03 point],
    [Rendement annuel],
    [15 %],
    [15,5 %],
    [+0,5 point],
    [Volatilité],
    [25 %],
    [23,5 %],
    [−1,5 point],
    [Ratio de Sharpe],
    [0,7],
    [0,73],
    [+0,03],
    [Pire creux],
    [35,6 %],
    [*35,64 %*],
    [+0,04 point],
)

Comment lire ce tableau, en trois constats. Le premier est que le rendement total et le pire creux tombent au centième de point, ce qu'aucune coïncidence ne produit : la source de prix et les dates sont bien celles de l'article. Le deuxième est que ce contrôle n'a *aucun paramètre*, donc il ne peut pas être ajusté pour tomber juste. Le troisième est qu'il rend interprétable tout écart sur la stratégie active : il viendra de ses règles, pas des prix.

=== 5.2 La stratégie se reproduit à 84 points près, et le prix retenu en explique 74

#table(
  columns: 5,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Prix entrant dans la moyenne pondérée*],
    [*Capital final*],
    [*Rendement total*],
    [*Sharpe*],
    [*Pire creux*],
    [la clôture de chaque minute],
    [171 831 \$],
    [*587 %*],
    [2,01],
    [9,3 %],
    [la moyenne pondérée de la barre],
    [169 666 \$],
    [579 %],
    [2,00],
    [8,4 %],
    [la moyenne des extrêmes et de la clôture],
    [153 309 \$],
    [*513 %*],
    [1,88],
    [10,4 %],
    [*publié*],
    [*192 656 \$*],
    [*671 %*],
    [*2,10*],
    [*9,4 %*],
)

Comment lire ce tableau, en trois constats. Le premier est que la mécanique est reproduite : la volatilité tombe à 17,6 % contre 18 % publiés et le pire creux à 9,3 % contre 9,4 %, ce qui veut dire que les positions prises sont bien les mêmes. Le deuxième est que *l'article ne dit pas sur quel prix il calcule sa moyenne*, et que ce seul choix déplace le rendement total de 74 points, soit davantage que ce que le fonds lui-même a rapporté sur la période. Le troisième est qu'il reste 84 points d'écart avec le chiffre publié, que ce dépôt n'explique pas et déclare ainsi.

Une subtilité que l'article ne relève pas explique une part de la divergence entre conventions : à la première barre, la moyenne pondérée n'a qu'une observation, donc elle *est* le prix de cette barre. Avec la convention de la clôture, la comparaison annoncée pour 9 h 31 donne exactement zéro et la position ne se prend qu'à 9 h 32.

#figure(image("../results/figures/courbes.png", width: 100%), caption: [La courbe de capital selon le glissement facturé])

Comment lire cette figure : l'échelle est logarithmique, donc une même pente est un même taux de croissance. La ligne pointillée marque le capital final publié.

=== 5.3 Un cent de glissement efface tout

La stratégie change de position *15,9 fois par jour*. Chaque changement échange deux fois la position détenue.

#table(
  columns: 5,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Glissement par passage*],
    [*Rendement total*],
    [*Par an*],
    [*Sharpe*],
    [*Pire creux*],
    [aucun],
    [587 %],
    [40,5 %],
    [2,01],
    [9,3 %],
    [0,10 cent],
    [469 %],
    [35,9 %],
    [1,81],
    [10,5 %],
    [0,25 cent],
    [330 %],
    [29,3 %],
    [1,52],
    [13,2 %],
    [0,50 cent],
    [168 %],
    [19,0 %],
    [1,04],
    [19,4 %],
    [*1 cent*],
    [*4,8 %*],
    [*0,8 %*],
    [*0,13*],
    [*46,5 %*],
    [2 cents],
    [−84 %],
    [−27,7 %],
    [−1,57],
    [84,4 %],
)

Comment lire ce tableau, en trois constats. Le premier est que le seuil qui annule le rendement vaut *1,05 cent par passage*, c'est-à-dire l'écart usuel entre les meilleurs prix acheteur et vendeur sur ce fonds : le résultat de l'article tient tout entier dans l'hypothèse de le franchir seize fois par jour sans rien payer. Le deuxième est que le pire creux passe de 9,3 % à 46,5 % au même seuil, donc que la stratégie ne perd pas seulement son rendement mais aussi la propriété qui la rendait attirante. Le troisième est qu'un demi-cent, moitié moins que l'écart usuel, laisse encore 19 % par an : le verdict n'est pas que la stratégie ne vaut rien, c'est que tout dépend d'une grandeur que l'article a posée à zéro sans la discuter.

#figure(image("../results/figures/seuil.png", width: 100%), caption: [Le rendement annualisé contre le glissement])

Comment lire cette figure : deux courbes, l'échantillon de l'article et la période qui suit sa publication. Le trait vertical marque un cent.

=== 5.4 Après publication, le rendement tombe des deux tiers avant même les frais

#table(
  columns: 6,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Fenêtre*],
    [*Séances*],
    [*Sans glissement*],
    [*À 0,25 cent*],
    [*À 0,50 cent*],
    [*Seuil*],
    [échantillon de l'article],
    [1 428],
    [*40,5 %* par an],
    [29,3 %],
    [19,0 %],
    [1,05 cent],
    [après publication],
    [724],
    [*7,0 %* par an],
    [2,7 %],
    [−1,4 %],
    [*0,42 cent*],
)

Comment lire ce tableau, en trois constats. Le premier est que le rendement sans frais tombe de 40,5 % à 7,0 % par an, soit une perte de plus de quatre cinquièmes, sur près de trois ans de données que l'article ne pouvait pas voir. Le deuxième est que le seuil de glissement tombe à 0,42 cent, donc *sous* l'écart usuel entre les meilleurs prix : sur cette fenêtre, la stratégie perd de l'argent à un coût réaliste. Le troisième est que le nombre de changements de position n'a pas baissé, il a légèrement monté, à 16,5 par jour : ce n'est donc pas l'activité qui s'est réduite, c'est ce qu'elle rapporte.

=== 5.5 Sur le fonds à levier, un demi-cent transforme deux millions en perte

#table(
  columns: 3,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Glissement*],
    [*Capital final sur QQQ*],
    [*Capital final sur TQQQ*],
    [aucun],
    [171 831 \$],
    [*1 643 784 \$*],
    [0,50 cent],
    [67 102 \$],
    [*21 721 \$*],
    [1 cent],
    [26 203 \$],
    [*287 \$*],
)

Comment lire ce tableau, en trois constats. Le premier est que le chiffre le plus spectaculaire de l'article, 2 085 417 dollars, se reproduit à 1,64 million sans frais, soit dans le bon ordre de grandeur. Le deuxième est qu'à un demi-cent de glissement il devient *21 721 dollars*, donc une perte sur les 25 000 de départ. Le troisième est qu'à un cent il reste 287 dollars, une ruine à 98,9 %, parce que le levier de trois multiplie le coût de chaque passage autant que le gain de chaque mouvement.

=== 5.6 Les deux années qui précèdent l'échantillon sont négatives

#table(
  columns: 3,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Année*],
    [*La stratégie*],
    [*Le fonds*],
    [*2016*],
    [*−3,0 %*],
    [+8,0 %],
    [*2017*],
    [*−5,9 %*],
    [+30,3 %],
    [2018],
    [+46,3 %],
    [−2,7 %],
    [2020],
    [+61,2 %],
    [+45,4 %],
    [2022],
    [+73,3 %],
    [−33,7 %],
    [2024],
    [+18,3 %],
    [+27,0 %],
    [2025],
    [+3,6 %],
    [+20,4 %],
)

Comment lire ce tableau, en trois constats. Le premier est que la fenêtre de l'article commence au 1er janvier 2018, c'est-à-dire à la première année profitable, les deux qui la précèdent étant toutes deux négatives. Ce dépôt le mesure et ne l'interprète pas : le choix peut tenir à la disponibilité des données, à l'historique du fonds à levier ou à toute autre raison que l'article ne donne pas. Le deuxième est que la stratégie gagne dans les années de tension, 2018, 2020 et 2022, ce qui confirme l'explication que les auteurs eux-mêmes avancent. Le troisième est qu'elle a perdu son avance sur le fonds dès 2023, et qu'elle en reste loin depuis.

#figure(image("../results/figures/annees.png", width: 100%), caption: [Le rendement de la stratégie et celui du fonds, année par année])

Comment lire cette figure : deux barres par année. Les trois années où la stratégie l'emporte largement sont celles où le fonds baisse ou hésite.

=== 5.7 Le signal doit son avantage au jour même, mais pas en entier

Remplacer la moyenne pondérée du jour par celle d'une séance antérieure :

#table(
  columns: 5,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Moyenne pondérée employée*],
    [*Rendement total*],
    [*Par an*],
    [*Sharpe*],
    [*Changements par jour*],
    [celle du jour],
    [587 %],
    [40,5 %],
    [2,01],
    [15,9],
    [celle de la veille],
    [*106 %*],
    [13,7 %],
    [*0,83*],
    [4,9],
    [celle d'il y a deux séances],
    [95 %],
    [12,5 %],
    [0,75],
    [3,6],
    [celle d'il y a cinq séances],
    [33 %],
    [5,2 %],
    [0,36],
    [2,7],
)

Comment lire ce tableau, en trois constats. Le premier est que le placebo fonctionne : décaler la moyenne d'une seule séance divise le Sharpe par deux et le rendement par cinq, donc le signal tient bien à l'information du jour. Le deuxième est qu'il en reste beaucoup, un Sharpe de 0,83 et 13,7 % par an, ce qui veut dire qu'une partie de l'avantage n'a rien à voir avec la moyenne pondérée : c'est du suivi de tendance ordinaire. Le troisième est que le nombre de changements de position s'effondre de 15,9 à 4,9, donc que le placebo est aussi une stratégie bien moins chère, et qu'à un cent de glissement il survivrait là où l'original ne survit pas.

#figure(image("../results/figures/placebo.png", width: 100%), caption: [Ce que le décalage laisse au signal])

Comment lire cette figure : à gauche le ratio de Sharpe, à droite le nombre de changements de position par jour, selon le décalage donné à la moyenne pondérée.

== 6. Reproduire

#raw("uv sync --locked --all-extras\nuv run pytest                 # 20 tests fermés, sans réseau ni données de marché\nuv run vwp fetch              # QQQ et TQQQ, barres d'une minute, environ 4 millions\nuv run vwp tout               # les cinq études et les cinq figures", block: true, lang: "bash")

Le téléchargement demande une clé Alpaca, à poser dans l'environnement ou dans un fichier local que le client partagé lit. Les tests tournent sur des séances fabriquées dont chaque réponse se calcule de tête. Tous les chiffres de ce README viennent des fichiers de #raw("results/").

== 7. Limites, avec leur statut

#table(
  columns: 2,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Limite*],
    [*Statut*],
    [Il reste 84 points d'écart avec le rendement publié],
    [mesuré ; le repère passif tombe juste au centième, donc l'écart vient des règles et non des prix, mais sa cause exacte n'est pas identifiée],
    [Le prix entrant dans la moyenne pondérée n'est pas déclaré par l'article],
    [mesuré ; les trois conventions usuelles sont publiées côte à côte, et elles s'écartent de 74 points],
    [Le glissement est modélisé comme un coût fixe en cents par passage],
    [déclaré ; l'impact réel dépend de la taille et du moment, et croît avec le capital, ce que ce modèle ignore, donc les seuils publiés sont optimistes],
    [Le choix de la fenêtre par l'article n'est pas interprété],
    [déclaré ; les deux années qui la précèdent sont mesurées et négatives, et ce dépôt s'arrête là],
    [La stratégie est prise telle qu'écrite, sans filtre ni gestion du risque],
    [déclaré ; les auteurs disent eux-mêmes ne pas la tenir pour un système achevé],
    [Les rendements sont calculés de clôture de minute à clôture de minute],
    [déclaré ; une exécution réelle passerait par le carnet d'ordres, ce que le glissement facturé approche sans le modéliser],
    [Le fonds à levier porte un coût de financement non modélisé],
    [reconnu ; il est dans le prix du fonds, donc dans les rendements employés, mais il n'est pas isolé],
    [La fenêtre postérieure ne compte que 724 séances],
    [déclaré ; c'est peu pour trancher, et le verdict porte sur l'ordre de grandeur, non sur la décimale],
)

== 8. Crédits, licence, citation

Carlo Zarattini et Andrew Aziz, « Volume Weighted Average Price (VWAP): The Holy Grail for Day Trading Systems », 13 novembre 2023, #link("https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4631351")[SSRN 4631351], PDF en libre accès sur #link("https://concretumgroup.com/wp-content/uploads/2026/02/Volume-Weighted-Average-Price.pdf")[le site du premier auteur].

Données de marché : flux consolidé d'Alpaca, compte gratuit, usage personnel. Aucune barre n'est redistribuée. Code sous licence MIT, rapport sous licence CC BY 4.0. Figures et client de données produits par #link("https://github.com/Guilou001/gv-fintools")[gv-fintools].

Voisinage dans le portefeuille : #link("https://github.com/Guilou001/23-fnb-levier-quotidien")[23-fnb-levier-quotidien] mesure l'érosion du fonds à levier que ce dépôt emploie sans la décomposer. #link("https://github.com/Guilou001/22-derniere-demi-heure")[22-derniere-demi-heure] pose la même question à une autre anomalie intrajournalière publiée, et trouve un renversement de signe. Le rapport #raw("rapport/rapport.pdf") est engendré depuis ce README.

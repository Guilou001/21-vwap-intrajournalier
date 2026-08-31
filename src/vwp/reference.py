"""Ce que l'article publie, recopié tel qu'imprimé.

**L'article.** Carlo Zarattini et Andrew Aziz, « Volume Weighted Average Price (VWAP): The Holy
Grail for Day Trading Systems », 13 novembre 2023, SSRN 4631351. Le PDF est en libre accès sur le
site du premier auteur, `concretumgroup.com`, ce qui contredit la note du registre du portefeuille
qui le croyait inaccessible aux scripts : mesuré le 30 août 2026, 1 012 421 octets, 26 pages.

**Les règles, telles que la section 3 les énonce.**

> The system waits for the first 1-minute candle to close after the U.S. market opens at 9:30am ET.
> At exactly 9:31:00am ET if the price of the asset is above the VWAP (not including pre- or
> post-market trading hours) a long (buy) position is initiated. The strategy includes setting a stop
> loss at the price level where a 1-minute candle closes below VWAP.

Et, pour le reste de la séance :

> Apart from the first minute of the trading session and outside regular trading hours, the strategy
> always implied an open position, either long or short.

Autrement dit : à chaque minute, on est long si la dernière clôture est au-dessus de la moyenne
pondérée par les volumes du jour, court sinon, et l'on solde à la clôture. Le dimensionnement est
« 100 % of available funds », sans levier, et la commission « $0.0005 per share ».

**Ce que l'article suppose et qui n'est pas neutre.**

> Since we initiated our system with a small account of only $25,000, we assumed **no slippage** in
> our order fills.

C'est le point que ce dépôt éprouve.

**Ce que l'article ne dit pas.** Sur quel prix la moyenne pondérée se calcule. Trois conventions
existent, la clôture, la moyenne des extrêmes et de la clôture, et la moyenne pondérée propre à
chaque barre. Le choix n'est pas anodin : ce dépôt le mesure.
"""

from __future__ import annotations

import datetime as dt

# Le tableau 1 de l'article, page 13, recopié tel qu'imprimé.
TABLE_UN = {
    "VWAP TT (QQQ)": {"total": 6.71, "annuel": 0.43, "volatilite": 0.18, "sharpe": 2.1,
                      "creux": 0.094},
    "Achat et conservation (QQQ)": {"total": 1.26, "annuel": 0.15, "volatilite": 0.25,
                                    "sharpe": 0.7, "creux": 0.356},
}

CAPITAL_INITIAL = 25_000.0
CAPITAL_FINAL_PUBLIE = 192_656.0
CAPITAL_FINAL_PUBLIE_TQQQ = 2_085_417.0
RENDEMENT_TQQQ_PUBLIE = 82.42
COMMISSION_PAR_ACTION = 0.0005

DEBUT_ECHANTILLON = dt.date(2018, 1, 2)
FIN_ECHANTILLON = dt.date(2023, 9, 28)
PUBLICATION = dt.date(2023, 11, 13)

# L'alpha annualisé et sa significativité, également publiés en section 3.6.
ALPHA_PUBLIE = 0.38
STUDENT_ALPHA_PUBLIE = 5.0

SOURCE = ("Carlo Zarattini et Andrew Aziz, « Volume Weighted Average Price (VWAP): The Holy Grail "
          "for Day Trading Systems », 13 novembre 2023, SSRN 4631351")

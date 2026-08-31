"""Les barres d'une minute des deux fonds de l'article.

QQQ suit le Nasdaq 100, TQQQ promet trois fois sa variation quotidienne. L'article emploie les deux,
et le second porte son chiffre le plus spectaculaire.

Le flux consolidé, en prix bruts, pour les raisons dites dans le client partagé : le flux IEX ne
capte que 1,81 % du volume et manque 57 % des minutes, et l'ajustement des dividendes diffère d'un
fournisseur à l'autre.
"""

from __future__ import annotations

from pathlib import Path

from gvf.marches import Requete, barres_alpaca

CACHE = Path("data/marches")
SYMBOLES = ("QQQ", "TQQQ")
PREMIER_EXERCICE = 2016
DERNIER_JOUR = "2026-08-29"
FUSEAU = "America/New_York"


def telecharger(symbole: str, cache: Path = CACHE, premier: int = PREMIER_EXERCICE,
                dernier_jour: str = DERNIER_JOUR):
    import pandas as pd

    dernier = int(dernier_jour[:4])
    morceaux = []
    for an in range(premier, dernier + 1):
        fin = f"{an}-12-31" if an < dernier else dernier_jour
        morceaux.append(barres_alpaca(Requete(symbole, f"{an}-01-01", fin, flux="sip"),
                                      cache=cache))
    table = pd.concat(morceaux, ignore_index=True)
    return table.drop_duplicates("horodatage").sort_values("horodatage").reset_index(drop=True)


def tout_telecharger(cache: Path = CACHE) -> dict:
    return {s: telecharger(s, cache) for s in SYMBOLES}

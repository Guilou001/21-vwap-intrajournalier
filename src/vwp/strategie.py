"""La stratégie de l'article, écrite telle qu'il l'énonce, et facturée telle qu'il ne la facture pas.

**La moyenne pondérée par les volumes, en mots simples.** À chaque minute de la séance, on divise
tout l'argent échangé depuis l'ouverture par tout le nombre d'actions échangées. Le résultat est le
prix moyen payé depuis le matin. Un prix au-dessus dit que les acheteurs du moment paient plus cher
que la moyenne de la journée ; un prix en dessous, l'inverse.

**La règle.** On est long quand la dernière clôture d'une minute est au-dessus de cette moyenne,
court sinon, et l'on solde à la clôture. Toute la position à chaque fois, sans levier.

**Le prix qui entre dans la moyenne n'est pas dit.** Trois conventions existent, et l'article ne
choisit pas. La clôture de chaque minute, la moyenne des deux extrêmes et de la clôture, ou la
moyenne pondérée que le fournisseur calcule dans la barre elle-même. Ce module les offre toutes les
trois, et `etudes.py` mesure ce que le choix coûte : soixante-quatorze points de rendement total,
plus que ne rapporte le fonds sur toute la période.

**Une subtilité que l'article ne relève pas.** À la première barre, la moyenne pondérée n'a qu'une
observation : elle **est** le prix de cette barre. Avec la convention de la clôture, la comparaison
annoncée pour 9 h 31 donne donc exactement zéro, et la position ne peut se prendre qu'à 9 h 32. Avec
la convention des extrêmes, l'égalité se brise selon la place de la clôture dans la barre, et la
position se prend bien à l'heure dite. C'est une des raisons pour lesquelles les trois conventions
ne donnent pas le même résultat.

**Le glissement, que l'article met à zéro.** Passer d'une position à l'autre demande de vendre le
double de ce qu'on détient. La stratégie le fait seize fois par jour en moyenne. Facturer chaque
passage d'un demi-cent, moins que l'écart usuel entre les meilleurs prix acheteur et vendeur sur ce
fonds, suffit à ramener le rendement de l'article au tiers.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

OUVERTURE = pd.Timestamp("09:30").time()
FERMETURE = pd.Timestamp("16:00").time()
BARRES_ATTENDUES = 390
SEANCES_PAR_AN = 252
PRIX_DE_LA_MOYENNE = {"cloture": "cloture", "typique": None, "barre": "prix_moyen"}


def seances(barres: pd.DataFrame, fuseau: str = "America/New_York") -> pd.DataFrame:
    """Les barres de la séance régulière, séances écourtées retirées.

    Les séances de veille de congé ferment à 13 h. Les garder mélangerait une journée de six heures
    et demie avec une de trois heures et demie, alors que la stratégie tient sa position jusqu'à la
    clôture, quelle qu'elle soit.
    """
    table = barres.copy()
    table["local"] = table["horodatage"].dt.tz_convert(fuseau)
    heure = table["local"].dt.time
    table = table[(heure >= OUVERTURE) & (heure <= FERMETURE)].copy()
    table["seance"] = table["local"].dt.date
    complet = table.groupby("seance")["cloture"].transform("size") >= BARRES_ATTENDUES
    return table[complet].copy()


def prix_de_reference(table: pd.DataFrame, convention: str) -> pd.Series:
    """Le prix qui entre dans la moyenne pondérée, selon la convention choisie."""
    if convention == "typique":
        return (table["haut"] + table["bas"] + table["cloture"]) / 3.0
    if convention == "cloture":
        return table["cloture"]
    if convention == "barre":
        return table["prix_moyen"]
    raise ValueError("la convention est « cloture », « typique » ou « barre »")


def moyenne_ponderee(table: pd.DataFrame, convention: str = "cloture") -> pd.Series:
    """La moyenne pondérée par les volumes, cumulée depuis l'ouverture, séance par séance.

    Elle repart de zéro chaque matin : l'article précise « not including pre- or post-market trading
    hours », donc ni la veille ni l'avant-bourse n'y entrent.
    """
    prix = prix_de_reference(table, convention)
    valeur = (prix * table["volume"]).groupby(table["seance"]).cumsum()
    quantite = table["volume"].groupby(table["seance"]).cumsum()
    return valeur / quantite


def signaux(table: pd.DataFrame, convention: str = "cloture",
            decalage_de_placebo: int = 0) -> pd.DataFrame:
    """La position à tenir à chaque minute, et le rendement de la minute.

    `decalage_de_placebo` décale la moyenne pondérée d'un nombre de séances : c'est le test qui dit
    si le signal tient à la moyenne du jour ou à n'importe quelle moyenne. Un signal qui marcherait
    aussi bien avec celle de la veille ne mesurerait rien du jour.
    """
    sortie = table.copy()
    sortie["vwap"] = moyenne_ponderee(sortie, convention)
    if decalage_de_placebo:
        rang = sortie.groupby("seance").cumcount()
        journalier = sortie.assign(rang=rang).pivot_table(index="seance", columns="rang",
                                                          values="vwap")
        decale = journalier.shift(decalage_de_placebo).stack()
        sortie["vwap"] = decale.reindex(
            pd.MultiIndex.from_arrays([sortie["seance"], rang])).to_numpy()
    sortie["signal"] = np.sign(sortie["cloture"] - sortie["vwap"])
    groupes = sortie.groupby("seance")
    # la position tenue pendant une minute vient du signal de la minute précédente : agir sur le
    # signal de la minute en cours reviendrait à connaître sa clôture avant qu'elle n'existe
    sortie["position"] = groupes["signal"].shift(1).fillna(0.0)
    sortie["rendement"] = groupes["cloture"].pct_change().fillna(0.0)
    return sortie.dropna(subset=["position", "rendement"])


@dataclass(frozen=True)
class Resultat:
    """Ce que la stratégie a fait, et ce qu'elle a coûté pour le faire."""

    courbe: pd.Series
    changements_par_jour: float
    commission_payee: float
    glissement_paye: float

    @property
    def rendements(self) -> pd.Series:
        return self.courbe.pct_change().dropna()

    def mesures(self, capital_initial: float) -> dict:
        c, r = self.courbe, self.rendements
        annees = len(c) / SEANCES_PAR_AN
        final = float(c.iloc[-1])
        total = final / capital_initial - 1.0
        return {
            "seances": int(len(c)), "capital_final": final, "rendement_total": total,
            "annualise": (final / capital_initial) ** (1 / annees) - 1 if final > 0 else -1.0,
            "volatilite": float(r.std(ddof=1)) * np.sqrt(SEANCES_PAR_AN),
            "sharpe": float(r.mean() / r.std(ddof=1)) * np.sqrt(SEANCES_PAR_AN)
            if r.std(ddof=1) > 0 else float("nan"),
            "pire_creux": float((1 - c / c.cummax()).max()),
            "changements_par_jour": self.changements_par_jour,
            "commission_payee": self.commission_payee,
            "glissement_paye": self.glissement_paye,
        }


def rejouer(table: pd.DataFrame, capital_initial: float = 25_000.0,
            commission_par_action: float = 0.0005,
            glissement_cents: float = 0.0) -> Resultat:
    """La stratégie rejouée minute par minute, capital composé.

    Le capital entier est engagé à chaque instant, donc le nombre d'actions détenues change avec le
    capital : c'est ce que l'article appelle « 100 % of available funds ». Un changement de position
    fait passer de plus une à moins une unité de capital, donc échange **deux fois** le nombre
    d'actions détenues, et se facture en conséquence.
    """
    cout_par_action = commission_par_action + glissement_cents / 100.0
    capital = capital_initial
    courbe, changements = [], []
    commission_totale = glissement_total = 0.0
    for _, jour in table.groupby("seance", sort=True):
        position = jour["position"].to_numpy()
        rendement = jour["rendement"].to_numpy()
        prix = jour["cloture"].to_numpy()
        precedente = 0.0
        n = 0
        for i in range(len(jour)):
            capital *= 1.0 + position[i] * rendement[i]
            echange = abs(position[i] - precedente)
            if echange > 0:
                n += 1
                actions = echange * capital / prix[i]
                commission_totale += actions * commission_par_action
                glissement_total += actions * glissement_cents / 100.0
                capital -= actions * cout_par_action
            precedente = position[i]
        if precedente != 0.0:
            actions = abs(precedente) * capital / prix[-1]
            commission_totale += actions * commission_par_action
            glissement_total += actions * glissement_cents / 100.0
            capital -= actions * cout_par_action
        courbe.append(capital)
        changements.append(n)
    index = pd.Index(sorted(table["seance"].unique()), name="seance")
    return Resultat(courbe=pd.Series(courbe, index=index),
                    changements_par_jour=float(np.mean(changements)),
                    commission_payee=commission_totale, glissement_paye=glissement_total)


def achat_et_conservation(table: pd.DataFrame, capital_initial: float = 25_000.0) -> Resultat:
    """Le point de comparaison de l'article : acheter le fonds et ne rien faire."""
    clotures = table.groupby("seance")["cloture"].last()
    courbe = capital_initial * clotures / clotures.iloc[0]
    return Resultat(courbe=courbe, changements_par_jour=0.0, commission_payee=0.0,
                    glissement_paye=0.0)

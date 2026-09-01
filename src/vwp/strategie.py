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
soit près de trois cinquièmes des cent vingt-six points que le fonds rapporte sur la fenêtre de
l'article.

**Une subtilité que l'article ne relève pas.** À la première barre, la moyenne pondérée n'a qu'une
observation : elle **est** le prix de cette barre. Avec la convention de la clôture, la comparaison
annoncée pour 9 h 31 donne donc zéro sur 1 335 des 1 428 séances de la fenêtre de l'article, et la
position ne s'y prend qu'à 9 h 32. Sur les 93 autres, la division laisse un résidu d'au plus
5,7 × 10⁻¹⁴ dollar, le dernier bit d'un prix en virgule flottante, et non un signal. Avec
la convention des extrêmes, l'égalité se brise selon la place de la clôture dans la barre, et la
position se prend bien à l'heure dite. C'est une des raisons pour lesquelles les trois conventions
ne donnent pas le même résultat.

**Le glissement, que l'article met à zéro.** Le glissement, l'écart entre le prix visé et le prix
réellement obtenu, se paie à chaque passage. Passer d'une position à l'autre demande de vendre le
double de ce qu'on détient. La stratégie le fait seize fois par jour en moyenne. Facturer chaque
passage d'un demi-cent ramène le rendement total de 587 % à 168 %, et le rendement annuel de
40,5 % à 19,0 %.

**La commission, elle, est celle de l'article.** Il déclare 0,0005 $ par action, et tous les
résultats de ce dépôt la portent. Ce qui est mis à zéro puis facturé ici, c'est le glissement seul.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

OUVERTURE = pd.Timestamp("09:30").time()
FERMETURE = pd.Timestamp("16:00").time()
BARRES_MINIMALES = 390
SEANCES_PAR_AN = 252


def seances(barres: pd.DataFrame, fuseau: str = "America/New_York") -> pd.DataFrame:
    """Les barres de la séance régulière, séances incomplètes retirées.

    La grille d'une séance régulière tient 391 minutes, de celle de 9 h 30 à celle de 16 h 00, qui
    recueille l'impression de clôture. Le filtre en exige au moins 390, donc il tolère une minute
    manquante et une seule. Sur QQQ toutes les séances gardées portent les 391 ; sur TQQQ, moins
    échangé, 67 d'entre elles n'en portent que 390.

    Il retire donc deux choses que rien ne distingue ici. Les séances de veille de congé, qui
    ferment à 13 h : les garder mélangerait une journée de six heures et demie avec une de trois
    heures et demie. Et les séances pleines qu'une interruption a trouées, dont les quatre de
    mars 2020. `etudes.sensibilites` mesure ce que coûte ce second retrait, et le README le publie.
    """
    table = barres.copy()
    table["local"] = table["horodatage"].dt.tz_convert(fuseau)
    heure = table["local"].dt.time
    table = table[(heure >= OUVERTURE) & (heure <= FERMETURE)].copy()
    table["seance"] = table["local"].dt.date
    complet = table.groupby("seance")["cloture"].transform("size") >= BARRES_MINIMALES
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
        # les premières séances n'ont pas de moyenne à leur disposition : les mettre à plat les
        # ferait compter comme des séances sans position, elles sortent donc de l'échantillon
        sortie = sortie[sortie["vwap"].notna()].copy()
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
    capital : c'est ce que l'article appelle « 100 % of available funds ». Un renversement fait passer
    de plus une à moins une unité de capital, donc échange **deux fois** le nombre d'actions
    détenues, et se facture en conséquence.

    Deux passages n'échangent, eux, qu'une fois : la première prise du matin, qui part de zéro et
    compte dans `changements_par_jour`, et le solde du soir, facturé hors de la boucle et hors de ce
    compte. La facturation suit dans tous les cas l'écart de position, `|position moins précédente|`.
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
    """Le repère passif de l'article : acheter le fonds et ne rien faire."""
    clotures = table.groupby("seance")["cloture"].last()
    courbe = capital_initial * clotures / clotures.iloc[0]
    return Resultat(courbe=courbe, changements_par_jour=0.0, commission_payee=0.0,
                    glissement_paye=0.0)

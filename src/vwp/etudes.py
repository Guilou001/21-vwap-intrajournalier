"""Les cinq études du dépôt, chacune rendant le tableau qu'elle produit."""

from __future__ import annotations

import datetime as dt

import pandas as pd

from . import donnees, reference, strategie

CONVENTIONS = ("cloture", "typique", "barre")
GLISSEMENTS = (0.0, 0.1, 0.25, 0.5, 1.0, 2.0)


def preparer(symbole: str, convention: str = "cloture", cache=donnees.CACHE) -> pd.DataFrame:
    return strategie.signaux(strategie.seances(donnees.telecharger(symbole, cache)), convention)


def _fenetre(table: pd.DataFrame, debut: dt.date, fin: dt.date) -> pd.DataFrame:
    return table[(table["seance"] >= debut) & (table["seance"] <= fin)]


def repere_passif(symbole: str = "QQQ", cache=donnees.CACHE) -> pd.DataFrame:
    """Le point de comparaison de l'article, acheter et ne rien faire, sur sa propre fenêtre.

    C'est le contrôle qui décide si les données et la période sont les bonnes. Le repère passif n'a
    aucun paramètre : s'il tombe juste, un écart sur la stratégie active vient de ses règles et non
    des prix.
    """
    table = preparer(symbole, cache=cache)
    dedans = _fenetre(table, reference.DEBUT_ECHANTILLON, reference.FIN_ECHANTILLON)
    mesures = strategie.achat_et_conservation(dedans).mesures(reference.CAPITAL_INITIAL)
    publie = reference.TABLE_UN["Achat et conservation (QQQ)"]
    lignes = [
        ("rendement total", publie["total"], mesures["rendement_total"]),
        ("rendement annuel", publie["annuel"], mesures["annualise"]),
        ("volatilité", publie["volatilite"], mesures["volatilite"]),
        ("ratio de Sharpe", publie["sharpe"], mesures["sharpe"]),
        ("pire creux", publie["creux"], mesures["pire_creux"]),
    ]
    return pd.DataFrame([{"grandeur": nom, "publie": p, "recalcule": r, "ecart": r - p}
                         for nom, p, r in lignes])


def conventions(symbole: str = "QQQ", cache=donnees.CACHE) -> pd.DataFrame:
    """Ce que coûte le choix du prix qui entre dans la moyenne pondérée.

    L'article ne le dit pas. Les trois conventions usuelles donnent trois résultats, et l'écart
    entre la plus haute et la plus basse dépasse le rendement du fonds sur toute la période.
    """
    lignes = []
    for convention in CONVENTIONS:
        table = preparer(symbole, convention, cache)
        dedans = _fenetre(table, reference.DEBUT_ECHANTILLON, reference.FIN_ECHANTILLON)
        mesures = strategie.rejouer(dedans).mesures(reference.CAPITAL_INITIAL)
        lignes.append({"convention": convention, **mesures})
    return pd.DataFrame(lignes)


def glissement(symbole: str = "QQQ", convention: str = "cloture",
               glissements=GLISSEMENTS, cache=donnees.CACHE) -> pd.DataFrame:
    """Ce que devient la stratégie quand on la facture, dans et hors de l'échantillon de l'article.

    L'article suppose un glissement nul. Sur un fonds dont l'écart entre les meilleurs prix acheteur
    et vendeur vaut environ un cent, et pour une stratégie qui change de position seize fois par
    jour, c'est l'hypothèse qui porte tout le résultat.
    """
    table = preparer(symbole, convention, cache)
    fenetres = {
        "échantillon de l'article": (reference.DEBUT_ECHANTILLON, reference.FIN_ECHANTILLON),
        "après publication": (reference.FIN_ECHANTILLON + dt.timedelta(days=1),
                              max(table["seance"])),
    }
    lignes = []
    for nom, (debut, fin) in fenetres.items():
        sous = _fenetre(table, debut, fin)
        for cents in glissements:
            mesures = strategie.rejouer(sous, glissement_cents=cents).mesures(
                reference.CAPITAL_INITIAL)
            lignes.append({"symbole": symbole, "fenetre": nom, "glissement_cents": cents,
                           **mesures})
    return pd.DataFrame(lignes)


def seuil_de_glissement(table: pd.DataFrame) -> pd.DataFrame:
    """Le glissement qui annule le rendement, fenêtre par fenêtre, par interpolation.

    Le rendement décroît avec le coût sans être linéaire, le capital étant composé. L'interpolation
    entre les deux points qui encadrent le zéro suffit à situer le seuil au centième de cent.
    """
    lignes = []
    for fenetre, groupe in table.groupby("fenetre", sort=False):
        g = groupe.sort_values("glissement_cents")
        positifs = g[g["rendement_total"] > 0]
        negatifs = g[g["rendement_total"] <= 0]
        if positifs.empty:
            seuil = 0.0
        elif negatifs.empty:
            seuil = float("nan")
        else:
            haut, bas = positifs.iloc[-1], negatifs.iloc[0]
            poids = haut["rendement_total"] / (haut["rendement_total"] - bas["rendement_total"])
            seuil = float(haut["glissement_cents"]
                          + poids * (bas["glissement_cents"] - haut["glissement_cents"]))
        lignes.append({"fenetre": fenetre, "seuil_cents": seuil,
                       "changements_par_jour": float(g["changements_par_jour"].iloc[0])})
    return pd.DataFrame(lignes)


def placebo(symbole: str = "QQQ", convention: str = "cloture", cache=donnees.CACHE) -> pd.DataFrame:
    """La même stratégie avec la moyenne pondérée d'une autre séance.

    Si le signal tient au marché du jour, remplacer la moyenne du jour par celle de la veille doit
    le détruire. S'il survit, c'est qu'il ne mesurait pas ce qu'on croyait.
    """
    table = strategie.seances(donnees.telecharger(symbole, cache))
    lignes = []
    for decalage in (0, 1, 2, 5):
        signaux = strategie.signaux(table, convention, decalage_de_placebo=decalage)
        dedans = _fenetre(signaux, reference.DEBUT_ECHANTILLON, reference.FIN_ECHANTILLON)
        mesures = strategie.rejouer(dedans).mesures(reference.CAPITAL_INITIAL)
        lignes.append({"decalage_de_seances": decalage, **mesures})
    return pd.DataFrame(lignes)


def par_annee(symbole: str = "QQQ", convention: str = "cloture",
              glissement_cents: float = 0.0, cache=donnees.CACHE) -> pd.DataFrame:
    """Le rendement année par année, pour voir si tout vient d'une seule.

    Une stratégie dont un exercice porte la moitié du résultat n'a pas la régularité que sa courbe
    de capital suggère.
    """
    table = preparer(symbole, convention, cache)
    lignes = []
    for annee in sorted({d.year for d in table["seance"]}):
        sous = table[[d.year == annee for d in table["seance"]]]
        if len(sous) < 20 * strategie.BARRES_ATTENDUES:
            continue
        mesures = strategie.rejouer(sous, glissement_cents=glissement_cents).mesures(
            reference.CAPITAL_INITIAL)
        passif = strategie.achat_et_conservation(sous).mesures(reference.CAPITAL_INITIAL)
        lignes.append({"annee": annee, "strategie": mesures["rendement_total"],
                       "passif": passif["rendement_total"], "sharpe": mesures["sharpe"],
                       "pire_creux": mesures["pire_creux"],
                       "changements_par_jour": mesures["changements_par_jour"]})
    return pd.DataFrame(lignes)


def deux_fonds(cache=donnees.CACHE) -> pd.DataFrame:
    """La stratégie sur les deux fonds de l'article, avec et sans glissement."""
    lignes = []
    for symbole in donnees.SYMBOLES:
        table = preparer(symbole, cache=cache)
        dedans = _fenetre(table, reference.DEBUT_ECHANTILLON, reference.FIN_ECHANTILLON)
        for cents in (0.0, 0.5, 1.0):
            mesures = strategie.rejouer(dedans, glissement_cents=cents).mesures(
                reference.CAPITAL_INITIAL)
            lignes.append({"symbole": symbole, "glissement_cents": cents, **mesures})
    return pd.DataFrame(lignes)


def verdict(glissements: pd.DataFrame, seuils: pd.DataFrame) -> dict:
    """Les six nombres qui répondent à la question du dépôt."""
    dedans = glissements[(glissements["fenetre"] == "échantillon de l'article")]
    dehors = glissements[(glissements["fenetre"] == "après publication")]
    sans_frais = dedans[dedans["glissement_cents"] == 0.0].iloc[0]
    apres = dehors[dehors["glissement_cents"] == 0.0].iloc[0]
    return {
        "publie_total": reference.TABLE_UN["VWAP TT (QQQ)"]["total"],
        "recalcule_total": float(sans_frais["rendement_total"]),
        "recalcule_sharpe": float(sans_frais["sharpe"]),
        "changements_par_jour": float(sans_frais["changements_par_jour"]),
        "seuil_dans_l_echantillon_cents": float(
            seuils[seuils["fenetre"] == "échantillon de l'article"]["seuil_cents"].iloc[0]),
        "seuil_apres_publication_cents": float(
            seuils[seuils["fenetre"] == "après publication"]["seuil_cents"].iloc[0]),
        "annualise_dans_l_echantillon": float(sans_frais["annualise"]),
        "annualise_apres_publication": float(apres["annualise"]),
    }

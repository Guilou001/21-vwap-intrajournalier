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


DEDANS = "échantillon de l'article"
DEHORS = "après l'échantillon"


def fenetres(table: pd.DataFrame) -> dict:
    """Les deux fenêtres de lecture : celle de l'article, et tout ce qui la suit.

    La seconde s'appelle « après l'échantillon » et non « après publication ». L'article paraît le
    13 novembre 2023, sept semaines après la fermeture de son échantillon, si bien que ses trente et
    une premières séances précèdent sa parution.
    """
    return {
        DEDANS: _fenetre(table, reference.DEBUT_ECHANTILLON, reference.FIN_ECHANTILLON),
        DEHORS: _fenetre(table, reference.FIN_ECHANTILLON + dt.timedelta(days=1),
                         max(table["seance"])),
    }


def repere_passif(symbole: str = "QQQ", cache=donnees.CACHE) -> pd.DataFrame:
    """Le repère passif de l'article, acheter et ne rien faire, sur sa propre fenêtre.

    C'est lui qui décide si les données et la période sont les bonnes. Le repère passif n'a aucun
    paramètre : s'il tombe juste, un écart sur la stratégie active vient de ses règles et non des
    prix.
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

    L'article suppose un glissement nul. Pour une stratégie qui change de position seize fois par
    jour, c'est l'hypothèse qui porte tout le résultat. Le balayage va de zéro à deux cents par
    passage, et `seuil_de_glissement` cherche ensuite le coût qui annule le rendement.
    """
    table = preparer(symbole, convention, cache)
    lignes = []
    for nom, sous in fenetres(table).items():
        for cents in glissements:
            mesures = strategie.rejouer(sous, glissement_cents=cents).mesures(
                reference.CAPITAL_INITIAL)
            lignes.append({"symbole": symbole, "fenetre": nom, "glissement_cents": cents,
                           **mesures})
    return pd.DataFrame(lignes)


def seuil_exact(sous: pd.DataFrame, borne_haute: float = 4.0,
                tolerance: float = 1e-4) -> float:
    """Le glissement qui annule le rendement, cherché par bissection sur la stratégie elle-même.

    Interpoler entre deux points du balayage donnerait un chiffre faux. Le rendement total n'est pas
    linéaire en glissement, le capital étant composé sur des milliers de passages. Sur l'échantillon
    de l'article, les deux points qui encadrent le zéro sont écartés d'un cent entier, et
    l'interpolation y surestime le seuil de trois centièmes de cent, dans le sens qui flatte la
    stratégie. La bissection rejoue la stratégie à chaque essai : elle coûte une trentaine de
    rejeux et ne dépend d'aucune hypothèse de forme.
    """
    def rendement(cents: float) -> float:
        return strategie.rejouer(sous, glissement_cents=cents).mesures(
            reference.CAPITAL_INITIAL)["rendement_total"]

    if rendement(0.0) <= 0:
        return 0.0
    if rendement(borne_haute) > 0:
        return float("nan")
    bas, haut = 0.0, borne_haute
    while haut - bas > tolerance:
        milieu = (bas + haut) / 2.0
        if rendement(milieu) > 0:
            bas = milieu
        else:
            haut = milieu
    return float((bas + haut) / 2.0)


def seuil_de_glissement(table: pd.DataFrame, signaux: dict) -> pd.DataFrame:
    """Le seuil qui annule le rendement, fenêtre par fenêtre.

    `signaux` porte la table de signaux de chaque fenêtre, celle que `fenetres` a découpée. Le seuil
    est mesuré sur elle, pas déduit du balayage.
    """
    lignes = []
    for fenetre, groupe in table.groupby("fenetre", sort=False):
        jours = sorted(set(signaux[fenetre]["seance"]))
        lignes.append({"fenetre": fenetre, "seuil_cents": seuil_exact(signaux[fenetre]),
                       "changements_par_jour": float(groupe["changements_par_jour"].iloc[0]),
                       "premiere_seance": jours[0], "derniere_seance": jours[-1],
                       "seances_avant_la_publication":
                           int(sum(1 for j in jours if j < reference.PUBLICATION))})
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
        for cents in (0.0, 1.0):
            mesures = strategie.rejouer(dedans, glissement_cents=cents).mesures(
                reference.CAPITAL_INITIAL)
            lignes.append({"decalage_de_seances": decalage, "glissement_cents": cents, **mesures})
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
        if len(sous) < 20 * strategie.BARRES_MINIMALES:
            continue
        mesures = strategie.rejouer(sous, glissement_cents=glissement_cents).mesures(
            reference.CAPITAL_INITIAL)
        passif = strategie.achat_et_conservation(sous).mesures(reference.CAPITAL_INITIAL)
        lignes.append({"annee": annee, "strategie": mesures["rendement_total"],
                       "passif": passif["rendement_total"], "sharpe": mesures["sharpe"],
                       "pire_creux": mesures["pire_creux"],
                       "changements_par_jour": mesures["changements_par_jour"]})
    return pd.DataFrame(lignes)


BARRES_MINIMALES_POUR_UNE_INTERRUPTION = 370


def seances_retirees(symbole: str = "QQQ", cache=donnees.CACHE) -> pd.DataFrame:
    """Ce que le filtre de séances écarte, séance par séance, sans le classer.

    Quatre colonnes mesurées : le nombre de barres, la première, la dernière, et la plus longue
    interruption d'une minute à l'autre. Le lecteur classe lui-même. Une veille de congé se
    reconnaît à sa dernière barre dense en début d'après-midi ; une séance pleine trouée par un
    coupe-circuit garde sa barre de 16 h 00 et porte un seul trou de quinze minutes.
    """
    brut = donnees.telecharger(symbole, cache)
    table = brut.copy()
    table["local"] = table["horodatage"].dt.tz_convert(donnees.FUSEAU)
    heure = table["local"].dt.time
    table = table[(heure >= strategie.OUVERTURE) & (heure <= strategie.FERMETURE)].copy()
    table["seance"] = table["local"].dt.date
    compte = table.groupby("seance")["cloture"].size()
    lignes = []
    for jour in compte[compte < strategie.BARRES_MINIMALES].index:
        minutes = table[table["seance"] == jour]["local"].sort_values()
        ecarts = minutes.diff().dt.total_seconds().div(60.0)
        lignes.append({
            "seance": jour, "barres": int(compte[jour]),
            "premiere_barre": minutes.iloc[0].time().isoformat(timespec="minutes"),
            "derniere_barre": minutes.iloc[-1].time().isoformat(timespec="minutes"),
            "plus_longue_interruption_minutes": float(ecarts.max()),
        })
    return pd.DataFrame(lignes)


def _seances_interrompues(retirees: pd.DataFrame) -> list:
    """Les séances écartées qui ont pourtant tenu jusqu'à la cloche.

    Le critère est déclaré et se vérifie sur `seances_retirees` : une barre de clôture à 16 h 00 et
    au moins 370 des 391 minutes de la grille. Sur QQQ il retient les quatre coupe-circuits de mars 2020 à
    l'intérieur de la fenêtre de l'article.
    """
    garde = ((retirees["derniere_barre"] == "16:00")
             & (retirees["barres"] >= BARRES_MINIMALES_POUR_UNE_INTERRUPTION))
    return list(retirees[garde]["seance"])


def sensibilites(symbole: str = "QQQ", cache=donnees.CACHE) -> pd.DataFrame:
    """Ce que trois choix non dictés par l'article déplacent, mesuré sur sa propre fenêtre.

    Le premier est le retrait des séances trouées par une interruption. Le deuxième est la
    commission de 0,0005 $ par action. L'article la déclare et ce dépôt la facture partout, donc la
    mettre à zéro n'explique pas l'écart avec lui. Elle chiffre seulement ce que le courtage coûte.
    Le troisième est la minute où la position se solde, l'article ne disant pas laquelle.
    """
    brut = donnees.telecharger(symbole, cache)
    table = strategie.signaux(strategie.seances(brut), "cloture")
    dedans = _fenetre(table, reference.DEBUT_ECHANTILLON, reference.FIN_ECHANTILLON)
    lignes = [{"variante": "les règles publiées",
               **strategie.rejouer(dedans).mesures(reference.CAPITAL_INITIAL)}]
    lignes.append({"variante": "commission mise à zéro",
                   **strategie.rejouer(dedans, commission_par_action=0.0).mesures(
                       reference.CAPITAL_INITIAL)})

    interrompues = set(_seances_interrompues(seances_retirees(symbole, cache)))
    large = brut.copy()
    large["local"] = large["horodatage"].dt.tz_convert(donnees.FUSEAU)
    heure = large["local"].dt.time
    large = large[(heure >= strategie.OUVERTURE) & (heure <= strategie.FERMETURE)].copy()
    large["seance"] = large["local"].dt.date
    compte = large.groupby("seance")["cloture"].transform("size")
    large = large[(compte >= strategie.BARRES_MINIMALES) | large["seance"].isin(interrompues)]
    avec = _fenetre(strategie.signaux(large.copy(), "cloture"),
                    reference.DEBUT_ECHANTILLON, reference.FIN_ECHANTILLON)
    lignes.append({"variante": "séances interrompues réintégrées",
                   **strategie.rejouer(avec).mesures(reference.CAPITAL_INITIAL)})

    # la barre de 16 h 00 porte l'impression de clôture, donc la position s'y solde ; la retirer
    # fait solder à 15 h 59, et l'écart mesure ce que cette convention non déclarée vaut
    sans_cloche = brut[brut["horodatage"].dt.tz_convert(donnees.FUSEAU).dt.time
                       < strategie.FERMETURE]
    court = _fenetre(strategie.signaux(strategie.seances(sans_cloche), "cloture"),
                     reference.DEBUT_ECHANTILLON, reference.FIN_ECHANTILLON)
    lignes.append({"variante": "position soldée à 15 h 59",
                   **strategie.rejouer(court).mesures(reference.CAPITAL_INITIAL)})
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
    """Les huit nombres qui répondent à la question du dépôt."""
    dedans = glissements[(glissements["fenetre"] == DEDANS)]
    dehors = glissements[(glissements["fenetre"] == DEHORS)]
    sans_frais = dedans[dedans["glissement_cents"] == 0.0].iloc[0]
    apres = dehors[dehors["glissement_cents"] == 0.0].iloc[0]
    return {
        "publie_total": reference.TABLE_UN["VWAP TT (QQQ)"]["total"],
        "recalcule_total": float(sans_frais["rendement_total"]),
        "recalcule_sharpe": float(sans_frais["sharpe"]),
        "changements_par_jour": float(sans_frais["changements_par_jour"]),
        "seuil_dans_l_echantillon_cents": float(
            seuils[seuils["fenetre"] == DEDANS]["seuil_cents"].iloc[0]),
        "seuil_apres_l_echantillon_cents": float(
            seuils[seuils["fenetre"] == DEHORS]["seuil_cents"].iloc[0]),
        "annualise_dans_l_echantillon": float(sans_frais["annualise"]),
        "annualise_apres_l_echantillon": float(apres["annualise"]),
    }

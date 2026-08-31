"""Les études, éprouvées sur des tables fabriquées, sans réseau ni données de marché.

Trois branches produisent les chiffres de tête du README et ne passaient par aucun test : la
recherche du seuil de glissement, le décalage du placebo, et le découpage des deux fenêtres.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pytest
from test_strategie import seance, signaux_fabriques

from vwp import etudes, reference, strategie


def _table(prix: list[float], jour: str = "2026-06-15") -> pd.DataFrame:
    return strategie.signaux(strategie.seances(seance(jour, prix)), "cloture")


def test_le_seuil_annule_vraiment_le_rendement():
    """La bissection rejoue la stratégie à chaque essai. Au seuil qu'elle rend, le rendement total
    doit être nul au dix-millième près, et un centième de cent de moins doit le laisser positif. Sur
    cette séance, une interpolation linéaire entre deux points de balayage écartés d'un cent rendrait
    2,4584 au lieu de 2,4488, un point où la stratégie a déjà perdu sept centièmes de point."""
    prix = [100.0 if i % 2 == 0 else 100.05 for i in range(391)]
    rendement = [0.0] + [prix[i] / prix[i - 1] - 1.0 for i in range(1, 391)]
    position = [0.0] + [np.sign(r) for r in rendement[1:]]
    table = signaux_fabriques(prix, position, rendement)
    assert strategie.rejouer(table).mesures(25_000.0)["rendement_total"] > 0
    seuil = etudes.seuil_exact(table)
    assert 0.0 < seuil < 4.0
    au_seuil = strategie.rejouer(table, glissement_cents=seuil).mesures(25_000.0)
    juste_avant = strategie.rejouer(table, glissement_cents=seuil - 0.01).mesures(25_000.0)
    assert abs(au_seuil["rendement_total"]) < 1e-4
    assert juste_avant["rendement_total"] > 0


def test_une_strategie_deja_perdante_a_un_seuil_nul():
    prix = [100.0, 101.0, 99.0, 101.0, 99.0] * 79
    table = _table(prix[:391])
    perdante = strategie.rejouer(table).mesures(25_000.0)["rendement_total"]
    assert perdante <= 0
    assert etudes.seuil_exact(table) == 0.0


def test_le_placebo_emploie_la_moyenne_de_la_veille_minute_par_minute():
    """Le décalage doit prendre la moyenne pondérée du jour précédent, à la même minute. Un décalage
    de signe inverse prendrait celle du LENDEMAIN, donc une fuite d'information franche, et rien ne
    l'attraperait sans ce test."""
    deux = pd.concat([seance("2026-06-15", list(np.linspace(100.0, 110.0, 391))),
                      seance("2026-06-16", list(np.linspace(200.0, 190.0, 391)))],
                     ignore_index=True)
    barres = strategie.seances(deux)
    veille = strategie.moyenne_ponderee(barres, "cloture").to_numpy()[:391]
    decale = strategie.signaux(barres, "cloture", decalage_de_placebo=1)
    assert decale["seance"].nunique() == 1
    assert decale["seance"].iloc[0] == dt.date(2026, 6, 16)
    assert decale["vwap"].to_numpy() == pytest.approx(veille)


def test_la_premiere_seance_sort_de_l_echantillon_au_lieu_d_etre_mise_a_plat():
    """La remplir par zéro compterait une séance entière comme une séance sans position, et le
    résultat serait publié comme s'il portait sur toutes les séances."""
    trois = pd.concat([seance(j, list(np.linspace(100.0, 110.0, 391)))
                       for j in ("2026-06-15", "2026-06-16", "2026-06-17")], ignore_index=True)
    barres = strategie.seances(trois)
    assert strategie.signaux(barres, "cloture", decalage_de_placebo=2)["seance"].nunique() == 1
    assert not strategie.signaux(barres, "cloture", decalage_de_placebo=1)["vwap"].isna().any()


def test_les_deux_fenetres_se_partagent_les_seances_sans_recouvrement():
    """La seconde s'appelle « après l'échantillon » : elle commence au lendemain de la fermeture de
    l'échantillon, le 29 septembre 2023, sept semaines avant la parution du 13 novembre."""
    jours = pd.date_range("2023-09-01", "2023-12-01", freq="B").date
    table = pd.DataFrame({"seance": jours})
    coupees = etudes.fenetres(table)
    dedans = set(coupees[etudes.DEDANS]["seance"])
    dehors = set(coupees[etudes.DEHORS]["seance"])
    assert dedans & dehors == set()
    assert max(dedans) == reference.FIN_ECHANTILLON
    assert min(dehors) == dt.date(2023, 9, 29)
    assert min(dehors) < reference.PUBLICATION
    assert len([j for j in dehors if j < reference.PUBLICATION]) > 0

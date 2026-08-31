"""Ce que l'article publie, et ce que la reproduction doit en retrouver."""

from __future__ import annotations

import pytest

from vwp import reference


def test_le_tableau_publie_porte_les_deux_lignes_de_l_article():
    assert set(reference.TABLE_UN) == {"VWAP TT (QQQ)", "Achat et conservation (QQQ)"}
    for ligne in reference.TABLE_UN.values():
        assert set(ligne) == {"total", "annuel", "volatilite", "sharpe", "creux"}


def test_les_deux_chiffres_de_tete_se_recoupent():
    """L'article annonce 671 % de rendement à partir de 25 000 dollars et un capital final de
    192 656. Les deux doivent dire la même chose, et ils le disent au millier près."""
    implique = reference.CAPITAL_INITIAL * (1 + reference.TABLE_UN["VWAP TT (QQQ)"]["total"])
    assert implique == pytest.approx(reference.CAPITAL_FINAL_PUBLIE, rel=0.01)


def test_le_rendement_annuel_publie_est_coherent_avec_le_total():
    """Cinq ans et neuf mois à 43 % par an font bien 671 %, à l'arrondi de la publication près."""
    annees = (reference.FIN_ECHANTILLON - reference.DEBUT_ECHANTILLON).days / 365.25
    ligne = reference.TABLE_UN["VWAP TT (QQQ)"]
    compose = (1 + ligne["annuel"]) ** annees - 1
    assert compose == pytest.approx(ligne["total"], rel=0.05)


def test_le_sharpe_publie_est_coherent_avec_le_rendement_et_la_volatilite():
    """43 % divisé par 18 % fait 2,4, et l'article imprime 2,1. L'écart vient de ce que son ratio
    emploie le rendement MOYEN des rendements quotidiens et non le rendement composé, deux
    grandeurs qui divergent quand la volatilité monte."""
    ligne = reference.TABLE_UN["VWAP TT (QQQ)"]
    brut = ligne["annuel"] / ligne["volatilite"]
    assert brut > ligne["sharpe"]
    assert brut - ligne["sharpe"] < 0.5


def test_le_rendement_du_fonds_a_levier_est_coherent_avec_son_capital_final():
    implique = reference.CAPITAL_INITIAL * (1 + reference.RENDEMENT_TQQQ_PUBLIE)
    assert implique == pytest.approx(reference.CAPITAL_FINAL_PUBLIE_TQQQ, rel=0.01)


def test_l_echantillon_precede_la_publication():
    """La fenêtre de l'article se ferme sept semaines avant qu'il ne paraisse : tout ce qui suit
    est donc du hors échantillon au sens strict."""
    assert reference.FIN_ECHANTILLON < reference.PUBLICATION
    assert (reference.PUBLICATION - reference.FIN_ECHANTILLON).days < 60


def test_la_commission_est_celle_que_l_article_declare():
    """Un demi-millième de dollar par action, le tarif qu'il attribue à Interactive Brokers."""
    commission = reference.COMMISSION_PAR_ACTION
    assert commission == pytest.approx(0.0005)

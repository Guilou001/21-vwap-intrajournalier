"""La stratégie, éprouvée sur des séances fabriquées dont la réponse se calcule de tête."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from vwp import strategie


def seance(jour: str, prix: list[float], volume: float = 1000.0,
           debut: str = "09:30") -> pd.DataFrame:
    """Une séance d'une minute par barre, avec les clôtures qu'on lui donne."""
    n = len(prix)
    depart = pd.Timestamp(f"{jour} {debut}", tz="America/New_York")
    horodatage = pd.date_range(depart, periods=n, freq="1min").tz_convert("UTC")
    p = np.asarray(prix, dtype=float)
    return pd.DataFrame({"horodatage": horodatage, "ouverture": p, "haut": p, "bas": p,
                         "cloture": p, "volume": np.full(n, volume), "transactions": 1.0,
                         "prix_moyen": p})


def test_la_moyenne_ponderee_est_la_moyenne_courante_a_volume_constant():
    """À volume constant, la moyenne pondérée est la moyenne arithmétique courante. C'est le cas
    limite qui vérifie que le cumul repart bien de l'ouverture."""
    barres = strategie.seances(seance("2026-06-15", [10.0, 20.0, 30.0] + [30.0] * 388))
    v = strategie.moyenne_ponderee(barres, "cloture")
    assert float(v.iloc[0]) == pytest.approx(10.0)
    assert float(v.iloc[1]) == pytest.approx(15.0)
    assert float(v.iloc[2]) == pytest.approx(20.0)


def test_la_moyenne_ponderee_repart_a_chaque_seance():
    """L'article le précise : ni la veille ni l'avant-bourse n'y entrent. Un cumul qui traverserait
    la nuit donnerait un signal complètement différent le matin."""
    deux = pd.concat([seance("2026-06-15", [10.0] * 391),
                      seance("2026-06-16", [100.0] * 391)], ignore_index=True)
    v = strategie.moyenne_ponderee(strategie.seances(deux), "cloture")
    assert float(v.iloc[391]) == pytest.approx(100.0)


def test_les_trois_conventions_de_prix_different():
    barres = strategie.seances(seance("2026-06-15", [10.0] * 391))
    barres.loc[barres.index[0], "haut"] = 12.0
    barres.loc[barres.index[0], "bas"] = 8.0
    barres.loc[barres.index[0], "prix_moyen"] = 11.0
    assert float(strategie.prix_de_reference(barres, "cloture").iloc[0]) == 10.0
    assert float(strategie.prix_de_reference(barres, "typique").iloc[0]) == pytest.approx(10.0)
    assert float(strategie.prix_de_reference(barres, "barre").iloc[0]) == 11.0
    with pytest.raises(ValueError):
        strategie.prix_de_reference(barres, "mediane")


def test_la_position_vient_du_signal_de_la_minute_precedente():
    """Agir sur le signal de la minute en cours reviendrait à connaître sa clôture avant qu'elle
    n'existe. C'est le défaut qui fait briller un backtest et échouer un pupitre."""
    barres = strategie.seances(seance("2026-06-15", list(np.linspace(100.0, 110.0, 391))))
    s = strategie.signaux(barres, "cloture")
    assert float(s["position"].iloc[0]) == 0.0
    assert list(s["position"].iloc[1:5]) == list(s["signal"].iloc[0:4])


def test_la_premiere_barre_donne_un_signal_nul_avec_la_convention_de_cloture():
    """Une subtilité que l'article ne relève pas. À la première barre, la moyenne pondérée n'a
    qu'une observation : elle EST le prix de cette barre. Comparer l'un à l'autre donne donc zéro,
    et la stratégie ne peut pas prendre position à 9 h 31 comme l'article l'annonce ; elle doit
    attendre 9 h 32. Avec la convention des extrêmes, l'égalité se brise selon la place de la
    clôture dans la barre, et la position se prend bien à 9 h 31."""
    barres = strategie.seances(seance("2026-06-15", list(np.linspace(100.0, 110.0, 391))))
    s = strategie.signaux(barres, "cloture")
    assert float(s["signal"].iloc[0]) == 0.0
    assert float(s["position"].iloc[1]) == 0.0


def test_un_marche_qui_monte_sans_interruption_donne_une_position_longue():
    barres = strategie.seances(seance("2026-06-15", list(np.linspace(100.0, 110.0, 391))))
    s = strategie.signaux(barres, "cloture")
    assert (s["position"].iloc[2:] == 1.0).all()


def test_un_marche_qui_baisse_sans_interruption_donne_une_position_courte():
    barres = strategie.seances(seance("2026-06-15", list(np.linspace(110.0, 100.0, 391))))
    s = strategie.signaux(barres, "cloture")
    assert (s["position"].iloc[2:] == -1.0).all()


def test_une_seance_ecourtee_est_retiree():
    pleine = seance("2026-06-15", [100.0] * 391)
    courte = seance("2026-06-16", [100.0] * 211)
    gardees = strategie.seances(pd.concat([pleine, courte], ignore_index=True))
    assert gardees["seance"].nunique() == 1


def test_un_marche_plat_ne_gagne_rien_et_ne_coute_que_la_sortie():
    """Sans mouvement, la stratégie prend une position et la garde. Elle ne paie donc que deux
    passages, l'entrée et la sortie."""
    barres = strategie.seances(seance("2026-06-15", [100.0] * 391))
    s = strategie.signaux(barres, "cloture")
    r = strategie.rejouer(s, capital_initial=25_000.0, commission_par_action=0.0)
    assert float(r.courbe.iloc[-1]) == pytest.approx(25_000.0)
    assert r.changements_par_jour <= 1.0


def test_le_glissement_se_facture_a_chaque_passage():
    """Un changement de position vend le double de ce qu'on détient : passer de long à court, c'est
    solder puis vendre à découvert la même quantité. Le facturer une seule fois diviserait le coût
    par deux, ce qui change le verdict d'une stratégie dont le seuil vaut un cent."""
    prix = [100.0, 101.0, 99.0, 101.0, 99.0] * 79
    barres = strategie.seances(seance("2026-06-15", prix[:391]))
    s = strategie.signaux(barres, "cloture")
    sans = strategie.rejouer(s, commission_par_action=0.0, glissement_cents=0.0)
    avec = strategie.rejouer(s, commission_par_action=0.0, glissement_cents=1.0)
    assert float(avec.courbe.iloc[-1]) < float(sans.courbe.iloc[-1])
    assert avec.glissement_paye > 0
    assert sans.glissement_paye == 0.0


def test_le_capital_composé_fait_croitre_le_nombre_d_actions():
    """L'article engage « 100 % of available funds ». Le nombre d'actions suit donc le capital, et
    le coût en dollars aussi. Un backtest à taille fixe sous-estimerait les frais de fin de
    période."""
    montant = list(np.linspace(100.0, 130.0, 391))
    barres = strategie.seances(seance("2026-06-15", montant))
    s = strategie.signaux(barres, "cloture")
    r = strategie.rejouer(s, capital_initial=25_000.0, commission_par_action=0.0005)
    attendu = 25_000.0 * (130.0 / 100.0)
    assert float(r.courbe.iloc[-1]) < attendu
    assert float(r.courbe.iloc[-1]) > attendu * 0.99


def test_le_repere_passif_suit_le_prix():
    deux = pd.concat([seance("2026-06-15", [100.0] * 391),
                      seance("2026-06-16", [110.0] * 391)], ignore_index=True)
    r = strategie.achat_et_conservation(strategie.seances(deux), 25_000.0)
    assert float(r.courbe.iloc[-1]) == pytest.approx(27_500.0)
    assert r.changements_par_jour == 0.0


def test_les_mesures_se_calculent_a_la_main():
    courbe = pd.Series([100.0, 110.0, 121.0], index=pd.Index([1, 2, 3], name="seance"))
    r = strategie.Resultat(courbe=courbe, changements_par_jour=3.0, commission_payee=1.0,
                           glissement_paye=2.0)
    m = r.mesures(100.0)
    assert m["rendement_total"] == pytest.approx(0.21)
    assert m["pire_creux"] == pytest.approx(0.0)
    assert m["seances"] == 3

"""La stratégie, éprouvée sur des séances fabriquées dont la réponse se calcule de tête."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from vwp import strategie


def seance(jour: str, prix: list[float], volume=1000.0, debut: str = "09:30") -> pd.DataFrame:
    """Une séance d'une minute par barre, avec les clôtures qu'on lui donne.

    `volume` accepte un nombre, le même pour toutes les barres, ou une liste d'un volume par barre.
    """
    n = len(prix)
    depart = pd.Timestamp(f"{jour} {debut}", tz="America/New_York")
    horodatage = pd.date_range(depart, periods=n, freq="1min").tz_convert("UTC")
    p = np.asarray(prix, dtype=float)
    v = np.full(n, float(volume)) if np.isscalar(volume) else np.asarray(volume, dtype=float)
    return pd.DataFrame({"horodatage": horodatage, "ouverture": p, "haut": p, "bas": p,
                         "cloture": p, "volume": v, "transactions": 1.0, "prix_moyen": p})


def test_la_moyenne_ponderee_est_la_moyenne_courante_a_volume_constant():
    """À volume constant, la moyenne pondérée est la moyenne arithmétique courante. C'est le cas
    limite qui vérifie que le cumul repart bien de l'ouverture."""
    barres = strategie.seances(seance("2026-06-15", [10.0, 20.0, 30.0] + [30.0] * 388))
    v = strategie.moyenne_ponderee(barres, "cloture")
    assert float(v.iloc[0]) == pytest.approx(10.0)
    assert float(v.iloc[1]) == pytest.approx(15.0)
    assert float(v.iloc[2]) == pytest.approx(20.0)


def test_la_moyenne_ponderee_pese_bien_par_les_volumes():
    """Le test qui distingue la moyenne pondérée d'une moyenne arithmétique courante. Deux barres,
    10 $ pour 1 000 actions puis 20 $ pour 3 000 actions : l'argent échangé vaut 10 000 puis 70 000
    dollars pour 1 000 puis 4 000 actions, donc 17,50 $ pondéré contre 15,00 $ non pondéré."""
    prix = [10.0, 20.0] + [20.0] * 389
    volumes = [1000.0, 3000.0] + [0.001] * 389
    barres = strategie.seances(seance("2026-06-15", prix, volume=volumes))
    v = strategie.moyenne_ponderee(barres, "cloture")
    assert float(v.iloc[0]) == pytest.approx(10.0)
    assert float(v.iloc[1]) == pytest.approx(17.5)
    assert float(v.iloc[1]) != pytest.approx(15.0)


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


def signaux_fabriques(prix: list[float], position: list[float],
                      rendement: list[float]) -> pd.DataFrame:
    """Une table de signaux écrite à la main, pour éprouver la facturation seule.

    Passer par `signaux` mêlerait le calcul du signal à celui du coût. Ici la position et le
    rendement sont donnés, donc chaque dollar facturé se calcule de tête.
    """
    return pd.DataFrame({"seance": ["2026-06-15"] * len(prix), "cloture": prix,
                         "position": position, "rendement": rendement})


def test_un_marche_qui_ne_bouge_plus_ne_paie_que_l_entree_et_la_sortie():
    """Le prix monte d'un cent à la deuxième barre puis ne bouge plus. La stratégie entre à la
    troisième minute, tient jusqu'à la cloche, et ne paie donc que deux passages. Chacun échange
    tout le capital au prix de 101 $, ce qui donne un coût exact."""
    barres = strategie.seances(seance("2026-06-15", [100.0] + [101.0] * 390))
    s = strategie.signaux(barres, "cloture")
    assert float(s["position"].iloc[2]) == 1.0
    r = strategie.rejouer(s, capital_initial=25_000.0, commission_par_action=0.0005)
    facteur = 1.0 - 0.0005 / 101.0
    assert float(r.courbe.iloc[-1]) == pytest.approx(25_000.0 * facteur**2, rel=1e-12)
    assert r.changements_par_jour == 1.0


def test_un_changement_de_position_se_facture_le_double_d_une_entree():
    """Passer de long à court, c'est solder puis vendre à découvert la même quantité : deux fois la
    position détenue. Prix figé à 100 $, un cent de glissement, donc un passage d'une unité coûte
    un dix-millième du capital. L'entrée coûte 2,50 $ sur 25 000 $, le renversement 4,9995 $ sur les
    24 997,50 $ restants, soit exactement le double du passage simple qui vaudrait 2,499 75 $, et la
    sortie 2,499 25 $."""
    n = 391
    position = [0.0, 1.0, -1.0] + [-1.0] * (n - 3)
    r = strategie.rejouer(signaux_fabriques([100.0] * n, position, [0.0] * n),
                          capital_initial=25_000.0, commission_par_action=0.0,
                          glissement_cents=1.0)
    # le solde de fin de séance n'entre pas dans le décompte, qui ne compte que les changements
    assert r.changements_par_jour == 2.0
    entree = 25_000.0 * 0.0001
    renversement = 2.0 * (25_000.0 - entree) * 0.0001
    sortie = (25_000.0 - entree - renversement) * 0.0001
    assert entree == pytest.approx(2.5)
    assert renversement == pytest.approx(2.0 * (25_000.0 - entree) * 0.0001)
    assert r.glissement_paye == pytest.approx(entree + renversement + sortie, rel=1e-12)
    assert float(r.courbe.iloc[-1]) == pytest.approx(
        25_000.0 - entree - renversement - sortie, rel=1e-12)


def test_le_nombre_d_actions_suit_le_capital_composé_et_non_le_capital_de_départ():
    """L'article engage « 100 % of available funds ». Trois barres : on entre à 100 $, le prix
    double, on solde à 200 $. Le capital vaut 25 000 $ à l'entrée et près de 50 000 $ à la sortie,
    donc la sortie porte sur 249,998 actions et non sur les 125 qu'un capital figé donnerait. La
    commission totale vaut 0,25 $ et non 0,1875 $."""
    r = strategie.rejouer(signaux_fabriques([100.0, 100.0, 200.0], [0.0, 1.0, 1.0], [0.0, 0.0, 1.0]),
                          capital_initial=25_000.0, commission_par_action=0.0005)
    entree = 250.0 * 0.0005
    capital = (25_000.0 - entree) * 2.0
    sortie = (capital / 200.0) * 0.0005
    assert r.commission_payee == pytest.approx(entree + sortie, rel=1e-12)
    assert r.commission_payee == pytest.approx(0.249999375, rel=1e-9)
    assert r.commission_payee > 1.3 * (entree + 125.0 * 0.0005)


def test_la_commission_double_quand_le_capital_double():
    """Le nombre d'actions suit le capital, donc la facture aussi, exactement."""
    table = signaux_fabriques([100.0] * 391, [0.0, 1.0] + [1.0] * 389, [0.0] * 391)
    petit = strategie.rejouer(table, capital_initial=25_000.0, commission_par_action=0.0005)
    grand = strategie.rejouer(table, capital_initial=50_000.0, commission_par_action=0.0005)
    assert grand.commission_payee == pytest.approx(2.0 * petit.commission_payee, rel=1e-12)


def test_le_glissement_se_facture_a_chaque_passage():
    """Le facturer une seule fois par changement diviserait presque le coût par deux, ce qui
    déplacerait le seuil publié de 1,02 à 1,93 cent. Le test précédent en fixe le montant ;
    celui-ci vérifie le signe et l'ordre sur une séance qui change de position à chaque minute."""
    prix = [100.0, 101.0, 99.0, 101.0, 99.0] * 79
    barres = strategie.seances(seance("2026-06-15", prix[:391]))
    s = strategie.signaux(barres, "cloture")
    sans = strategie.rejouer(s, commission_par_action=0.0, glissement_cents=0.0)
    avec = strategie.rejouer(s, commission_par_action=0.0, glissement_cents=1.0)
    assert float(avec.courbe.iloc[-1]) < float(sans.courbe.iloc[-1])
    assert avec.glissement_paye > 0
    assert sans.glissement_paye == 0.0


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

"""Les cinq figures du dépôt. Chacune reçoit un tableau déjà calculé et n'invente aucun nombre."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from gvf.style import GRIS, OKABE_ITO, appliquer, enregistrer, formateur, fr

DOSSIER = Path("results/figures")


def _fin(fig, nom: str, dossier: Path = DOSSIER) -> list[Path]:
    # pas de `tight_layout` : la feuille de style partagée active la mise en page sous contrainte
    chemins = enregistrer(fig, dossier, nom)
    plt.close(fig)
    return chemins


def courbes(courbes_par_cout: dict, passif, publie: float, dossier: Path = DOSSIER) -> list[Path]:
    """La courbe de capital selon le glissement facturé, contre le fonds et contre l'article."""
    appliquer()
    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    for i, (cents, courbe) in enumerate(sorted(courbes_par_cout.items())):
        etiquette = "aucun glissement" if cents == 0 else f"{fr(cents, 2)} cent par passage"
        ax.plot(courbe.index, courbe.to_numpy(), lw=1.9,
                color=OKABE_ITO[i % len(OKABE_ITO)], label=etiquette)
    ax.plot(passif.index, passif.to_numpy(), lw=1.6, ls="--", color=GRIS,
            label="achat et conservation")
    ax.axhline(publie, color=OKABE_ITO[3], lw=1.1, ls=":")
    ax.annotate("le capital final publié", (courbe.index[len(courbe) // 6], publie),
                textcoords="offset points", xytext=(0, 8), fontsize=8, color=OKABE_ITO[3])
    ax.set_yscale("log")
    ax.set_ylabel("capital, échelle logarithmique")
    ax.set_xlabel("séance")
    ax.yaxis.set_major_formatter(formateur(decimales=0, suffixe=" $"))
    ax.legend(fontsize=8, ncols=3, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.01))
    return _fin(fig, "courbes", dossier)


def seuil(table, dossier: Path = DOSSIER) -> list[Path]:
    """Le rendement annualisé contre le glissement, dans et hors de l'échantillon."""
    appliquer()
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    for i, fenetre in enumerate(dict.fromkeys(table["fenetre"])):
        sous = table[table["fenetre"] == fenetre].sort_values("glissement_cents")
        ax.plot(sous["glissement_cents"], sous["annualise"], marker="o", lw=1.9,
                color=OKABE_ITO[i], label=fenetre)
    ax.axhline(0, color=GRIS, lw=1.1, ls="--")
    ax.axvline(1.0, color=GRIS, lw=0.9, ls=":")
    ax.annotate("un cent par passage,\nrepère de lecture", (1.0, 0.30),
                textcoords="offset points", xytext=(8, 0), fontsize=8, color=GRIS)
    ax.set_xlabel("glissement facturé par passage de marché, en cents")
    ax.set_ylabel("rendement annualisé")
    ax.xaxis.set_major_formatter(formateur(decimales=2))
    ax.yaxis.set_major_formatter(formateur(decimales=0, suffixe=" %", facteur=100))
    ax.legend(fontsize=8, ncols=2, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.01))
    return _fin(fig, "seuil", dossier)


def conventions(table, publie: float, dossier: Path = DOSSIER) -> list[Path]:
    """Ce que coûte le choix du prix qui entre dans la moyenne pondérée."""
    appliquer()
    noms = {"cloture": "la clôture", "typique": "la moyenne des\nextrêmes et de la clôture",
            "barre": "la moyenne pondérée\nde la barre"}
    t = table.sort_values("rendement_total")
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    y = np.arange(len(t))
    ax.barh(y, t["rendement_total"], color=OKABE_ITO[0], height=0.66)
    ax.axvline(publie, color=OKABE_ITO[3], lw=1.4, ls="--")
    # l'étiquette se pose sur la barre la plus haute : au-dessus, elle sortirait du cadre
    ax.annotate("publié", (publie, len(t) - 1), textcoords="offset points", xytext=(-40, 26),
                fontsize=8.5, color=OKABE_ITO[3])
    for k, v in enumerate(t["rendement_total"]):
        ax.text(v, k, "  " + fr(100 * v, 0) + " %", va="center", fontsize=8.5, color=GRIS)
    ax.set_yticks(y, [noms.get(c, c) for c in t["convention"]], fontsize=8.5)
    ax.set_xlabel("rendement total sur l'échantillon de l'article")
    ax.xaxis.set_major_formatter(formateur(decimales=0, suffixe=" %", facteur=100))
    return _fin(fig, "conventions", dossier)


def annees(table, dossier: Path = DOSSIER) -> list[Path]:
    """Le rendement de la stratégie et celui du fonds, année par année."""
    appliquer()
    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    x = np.arange(len(table))
    largeur = 0.38
    ax.bar(x - largeur / 2, table["strategie"], width=largeur, color=OKABE_ITO[0],
           label="la stratégie")
    ax.bar(x + largeur / 2, table["passif"], width=largeur, color=OKABE_ITO[1],
           label="achat et conservation")
    ax.axhline(0, color=GRIS, lw=1.1)
    ax.set_xticks(x, [str(int(a)) for a in table["annee"]])
    ax.set_ylabel("rendement de l'année")
    ax.yaxis.set_major_formatter(formateur(decimales=0, suffixe=" %", facteur=100))
    ax.legend(fontsize=8, ncols=2, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.01))
    return _fin(fig, "annees", dossier)


def placebo(table, dossier: Path = DOSSIER) -> list[Path]:
    """Ce que devient la stratégie quand on lui donne la moyenne pondérée d'un autre jour."""
    appliquer()
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.4))
    x = np.arange(len(table))
    etiquettes = ["le jour même"] + [f"{int(d)} séance" + ("s" if d > 1 else "")
                                     for d in table["decalage_de_seances"][1:]]
    axes[0].bar(x, table["sharpe"], color=[OKABE_ITO[0]] + [OKABE_ITO[4]] * (len(table) - 1))
    axes[0].set_ylabel("ratio de Sharpe")
    axes[0].yaxis.set_major_formatter(formateur(decimales=2))
    axes[0].set_title("Ce que le décalage laisse", fontsize=10)
    axes[1].bar(x, table["changements_par_jour"],
                color=[OKABE_ITO[0]] + [OKABE_ITO[4]] * (len(table) - 1))
    axes[1].set_ylabel("changements de position par jour")
    axes[1].yaxis.set_major_formatter(formateur(decimales=0))
    axes[1].set_title("Et ce qu'il fait à l'activité", fontsize=10)
    for ax in axes:
        ax.set_xticks(x, etiquettes, fontsize=8.5)
        ax.set_xlabel("moyenne pondérée décalée de")
    return _fin(fig, "placebo", dossier)

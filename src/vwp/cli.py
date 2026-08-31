"""La ligne de commande : vérifier le repère, refaire la stratégie, la facturer, la pousser dehors."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from . import donnees, etudes, figures, reference, strategie

app = typer.Typer(add_completion=False, help=__doc__)
TABLES = Path("results/tables")


def _ecrire(table, nom: str) -> Path:
    TABLES.mkdir(parents=True, exist_ok=True)
    chemin = TABLES / f"{nom}.csv"
    table.to_csv(chemin, index=False)
    typer.echo(f"  {chemin}  {len(table)} lignes")
    return chemin


@app.command()
def fetch() -> None:
    """Les barres d'une minute de QQQ et TQQQ, flux consolidé."""
    for symbole, table in donnees.tout_telecharger().items():
        typer.echo(f"  {symbole}: {len(table):>9,} barres")


@app.command()
def repere() -> None:
    """Le repère passif de l'article, qui décide si les données sont les bonnes."""
    table = etudes.repere_passif()
    typer.echo(table.to_string(index=False))
    _ecrire(table, "repere_passif")


@app.command()
def replication() -> None:
    """La stratégie refaite, et ce que coûte la convention que l'article ne déclare pas."""
    table = etudes.conventions()
    typer.echo(table[["convention", "capital_final", "rendement_total", "annualise",
                      "volatilite", "sharpe", "pire_creux", "changements_par_jour"]]
               .to_string(index=False))
    _ecrire(table, "conventions")
    figures.conventions(table, reference.TABLE_UN["VWAP TT (QQQ)"]["total"])


@app.command()
def cout() -> None:
    """Ce que devient la stratégie quand on la facture, dans et hors de l'échantillon."""
    table = etudes.glissement()
    signaux_par_fenetre = etudes.fenetres(etudes.preparer("QQQ"))
    seuils = etudes.seuil_de_glissement(table, signaux_par_fenetre)
    typer.echo(table[["fenetre", "glissement_cents", "rendement_total", "annualise", "sharpe",
                      "pire_creux"]].to_string(index=False))
    typer.echo("\n" + seuils.to_string(index=False))
    _ecrire(table, "glissement")
    _ecrire(seuils, "seuils")
    resume = etudes.verdict(table, seuils)
    Path("results").mkdir(exist_ok=True)
    Path("results/verdict.json").write_text(json.dumps(resume, indent=2), encoding="utf-8")
    for cle, valeur in resume.items():
        typer.echo(f"  {cle:34} {valeur}")
    figures.seuil(table)

    dedans = signaux_par_fenetre[etudes.DEDANS]
    par_cout = {cents: strategie.rejouer(dedans, glissement_cents=cents).courbe
                for cents in (0.0, 0.5, 1.0)}
    figures.courbes(par_cout, strategie.achat_et_conservation(dedans).courbe,
                    reference.CAPITAL_FINAL_PUBLIE)


@app.command()
def robustesse() -> None:
    """Le placebo, l'année par année, et les deux fonds de l'article."""
    p = etudes.placebo()
    typer.echo(p[["decalage_de_seances", "glissement_cents", "rendement_total", "annualise",
                  "sharpe", "changements_par_jour"]].to_string(index=False))
    _ecrire(p, "placebo")
    s = etudes.sensibilites()
    typer.echo("\n" + s[["variante", "seances", "capital_final", "rendement_total", "annualise",
                         "sharpe", "pire_creux"]].to_string(index=False))
    _ecrire(s, "sensibilites")
    _ecrire(etudes.seances_retirees(), "seances_retirees")
    a = etudes.par_annee()
    typer.echo("\n" + a.to_string(index=False))
    _ecrire(a, "par_annee")
    _ecrire(etudes.deux_fonds(), "deux_fonds")
    figures.placebo(p[p["glissement_cents"] == 0.0].reset_index(drop=True))
    figures.annees(a)


@app.command()
def tout() -> None:
    """Tout, dans l'ordre de la démonstration."""
    repere()
    replication()
    cout()
    robustesse()


if __name__ == "__main__":      # pragma: no cover
    app()

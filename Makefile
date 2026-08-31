# Prérequis : uv (https://docs.astral.sh/uv/)
UV ?= uv

setup:
	$(UV) sync --locked --all-extras

test:             ## 28 tests fermés, sans réseau ni données de marché
	$(UV) run pytest

lint:
	$(UV) run ruff check .

data:             ## QQQ et TQQQ, barres d'une minute de 2016 à aujourd'hui
	$(UV) run vwp fetch

all:              ## tout : le repère, la réplication, le coût, la robustesse
	$(UV) run vwp tout

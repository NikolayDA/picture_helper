.PHONY: all check pr-check install-test doctor lint lint-shell type test coverage ui screenshots bench bench-compare clean

VENV_BIN := $(CURDIR)/.venv/bin
PYTHON ?= $(shell if [ -x "$(VENV_BIN)/python" ]; then printf '%s' "$(VENV_BIN)/python"; elif command -v python >/dev/null 2>&1; then printf '%s' python; else printf '%s' python3; fi)
QT_QPA_PLATFORM ?= offscreen
PIP_CONSTRAINT ?= $(CURDIR)/requirements/constraints.txt
RUN_ENV := PATH="$(VENV_BIN):$(PATH)"
QT_ENV := QT_QPA_PLATFORM=$(QT_QPA_PLATFORM) PATH="$(VENV_BIN):$(PATH)"
PIP_INSTALL := $(RUN_ENV) "$(PYTHON)" -m pip install --constraint "$(PIP_CONSTRAINT)"

# Schnelle lokale PR-Pruefung; entspricht .github/workflows/pr-ci.yml.
# Installiert das Paket bewusst nicht-editable, damit die App-Smoke-Tests
# denselben Einstieg wie CI/Release/App-Bundle pruefen.
pr-check: install-test doctor check

install-test:
	$(PIP_INSTALL) ".[test]"

doctor:
	$(RUN_ENV) "$(PYTHON)" scripts/check_test_env.py

# Standardpruefung. Laeuft in der PR-CI und in der vollen Release-/Manual-
# Matrix. 'test' zieht ueber das addopts-Filter '-m not ui or ui_smoke' das
# kleine ui_smoke-Subset mit; die volle qtbot-Suite bleibt dem 'ui'-Target
# (nightly) vorbehalten.
check: lint type test

# '$(PYTHON) -m' statt der blanken Binaries: robust gegen PATH-/venv-
# Eigenheiten (z. B. isoliert installierte Tools), nutzt denselben
# Interpreter wie das Projekt. PYTHON kann bei Bedarf ueberschrieben werden:
# make PYTHON=/pfad/zur/python check
lint: lint-shell
	$(RUN_ENV) "$(PYTHON)" -m ruff check bgremover scripts tests

# shellcheck nur ausfuehren, wenn das Tool installiert ist – Entwickler
# ohne shellcheck sollen nicht hart scheitern (CI installiert es separat).
lint-shell:
	@if command -v shellcheck >/dev/null 2>&1; then \
		shellcheck -x BgRemover.command create_BgRemover_app.sh diagnose_mac.sh; \
	else \
		echo "shellcheck nicht installiert – ueberspringe Shell-Lint (CI installiert das Paket)."; \
	fi

type:
	$(RUN_ENV) "$(PYTHON)" -m mypy

test:
	$(QT_ENV) "$(PYTHON)" -m pytest

# 'coverage xml' erzeugt zusaetzlich coverage.xml fuer den Codecov-Upload in
# der Full CI; HTML bleibt fuer die lokale Durchsicht.
coverage:
	$(QT_ENV) "$(PYTHON)" -m coverage run -m pytest
	$(RUN_ENV) "$(PYTHON)" -m coverage report
	$(RUN_ENV) "$(PYTHON)" -m coverage html
	$(RUN_ENV) "$(PYTHON)" -m coverage xml

# Volle UI-Interaktionssuite (nightly). Explizites -m ui ueberschreibt das
# '-m not ui or ui_smoke' aus pyproject [tool.pytest.ini_options].addopts und
# laeuft damit alle ui-Tests (inkl. des ui_smoke-Subsets).
ui:
	$(QT_ENV) "$(PYTHON)" -m pytest -m ui

# Vollstaendiger, reproduzierbarer UI-Screenshot-Satz fuer die Doku/PR-Review.
# Der Generator nutzt Qt offscreen, In-Memory-QSettings und simuliert den KI-
# Ergebniszustand ohne rembg-Modell-Download.
screenshots:
	$(QT_ENV) "$(PYTHON)" scripts/generate_app_screenshots.py

# Performance-Benchmark der Bild-Pipeline pro Format (PNG/JPEG/WebP/TIFF).
# 'bench' misst, speichert nach benchmarks/results/ und vergleicht gegen den
# letzten Lauf; 'bench-compare' vergleicht die letzten zwei Laeufe ohne neue
# Messung. Details: benchmarks/README.md.
bench:
	$(QT_ENV) "$(PYTHON)" scripts/benchmark.py run

bench-compare:
	$(QT_ENV) "$(PYTHON)" scripts/benchmark.py compare

# Alles: check + lokale UI-Tests.
all: check ui

clean:
	rm -rf .pytest_cache build dist *.egg-info

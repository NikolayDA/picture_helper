.PHONY: all check pr-check install-test doctor lint lint-shell type test coverage ui clean

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

# Standardpruefung ohne ui-Tests. Laeuft in der PR-CI und in der vollen
# Release-/Manual-Matrix.
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

coverage:
	$(QT_ENV) "$(PYTHON)" -m coverage run -m pytest
	$(RUN_ENV) "$(PYTHON)" -m coverage report
	$(RUN_ENV) "$(PYTHON)" -m coverage html

# Lokale UI-Interaktionstests. Explizites -m ui ueberschreibt das
# '-m not ui' aus pyproject [tool.pytest.ini_options].addopts.
ui:
	$(QT_ENV) "$(PYTHON)" -m pytest -m ui

# Alles: check + lokale UI-Tests.
all: check ui

clean:
	rm -rf .pytest_cache build dist *.egg-info

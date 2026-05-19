.PHONY: all check lint type test ui clean

# Spiegelt .github/workflows/ci.yml exakt (ohne ui-Tests, wie die CI).
check: lint type test

# 'python -m' statt der blanken Binaries: robust gegen PATH-/venv-Eigenheiten
# (z. B. isoliert installierte Tools), nutzt denselben Interpreter wie das
# Projekt. Befehle/Reihenfolge entsprechen exakt .github/workflows/ci.yml.
lint:
	python -m ruff check bgremover tests

type:
	python -m mypy

test:
	QT_QPA_PLATFORM=offscreen python -m pytest

# Lokale UI-Interaktionstests. Explizites -m ui ueberschreibt das
# '-m not ui' aus pyproject [tool.pytest.ini_options].addopts.
ui:
	QT_QPA_PLATFORM=offscreen python -m pytest -m ui

# Alles: CI-Aequivalent + lokale UI-Tests.
all: check ui

clean:
	rm -rf .pytest_cache

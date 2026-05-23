.PHONY: all check pr-check lint type test ui clean

# Schnelle lokale PR-Pruefung; entspricht .github/workflows/pr-ci.yml.
pr-check: check

# Standardpruefung ohne ui-Tests. Laeuft in der PR-CI und in der vollen
# Release-/Manual-Matrix.
check: lint type test

# 'python -m' statt der blanken Binaries: robust gegen PATH-/venv-Eigenheiten
# (z. B. isoliert installierte Tools), nutzt denselben Interpreter wie das
# Projekt.
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

# Alles: check + lokale UI-Tests.
all: check ui

clean:
	rm -rf .pytest_cache

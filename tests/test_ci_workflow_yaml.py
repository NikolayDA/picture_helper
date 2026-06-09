"""Syntax-Schutz für die GitHub-Actions-Workflows.

Jede Datei unter ``.github/workflows/`` muss valides YAML sein und einen
``jobs``-Block besitzen. Hintergrund: ein unquotierter ``name:``-Wert mit
eingebettetem ``": "`` (z. B. ``name: ... (security: pip>=26.1.2)``) wird von
YAML als verschachteltes Mapping gelesen und lässt den Workflow als
``startup_failure`` mit null Jobs scheitern – ohne dass ein Test läuft. Die
text-basierten CI-Tests (`test_ci_pip_pin`/`test_ci_qt_packages`) fangen das
nicht; dieser Parse-Test schliesst die Lücke.

``yaml`` ist keine deklarierte Projekt-Abhängigkeit, aber im Test-Env
vorhanden – fehlt es, wird der Test übersprungen statt fälschlich rot.
"""
from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

_ROOT = Path(__file__).resolve().parent.parent
_WORKFLOW_DIR = _ROOT / ".github" / "workflows"

_WORKFLOWS = sorted(_WORKFLOW_DIR.glob("*.yml")) + sorted(_WORKFLOW_DIR.glob("*.yaml"))


def test_workflow_dir_is_non_empty() -> None:
    # Schutz gegen einen leeren Glob (verschobenes Verzeichnis o. Ä.), der die
    # Parametrisierung sonst lautlos auf null Fälle schrumpfen liesse.
    assert _WORKFLOWS, f"keine Workflow-Dateien unter {_WORKFLOW_DIR} gefunden"


@pytest.mark.parametrize("path", _WORKFLOWS, ids=lambda p: p.name)
def test_workflow_is_valid_yaml(path: Path) -> None:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # pragma: no cover - Fehlertext ist die Aussage
        pytest.fail(f"{path.name} ist kein valides YAML: {exc}")

    assert isinstance(doc, dict), f"{path.name}: Top-Level ist kein Mapping"
    # ``on`` wird von PyYAML (YAML 1.1) als Boolean-Key True gelesen – daher
    # nur den robusten ``jobs``-Block prüfen.
    assert "jobs" in doc, f"{path.name}: kein 'jobs'-Block"

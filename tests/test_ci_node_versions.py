"""Drift-Schutz gegen node20-basierte GitHub-Actions (Befund #312).

GitHub deprecatet die Node.js-20-Runtime für Actions: node20-basierte Actions
laufen derzeit nur noch mit einer Warnung zwangsweise unter Node 24 und brechen,
sobald GitHub den Fallback entfernt. Dieser Test hält ALLE Workflow-Dateien auf
node24-fähigen Action-Majors – analog zu ``tests/test_ci_qt_packages.py``: ein
versehentliches Zurückfallen auf eine node20-Version (oder eine neue node20-
Action) fällt sofort auf, statt erst spät in einer Deprecation-Warnung/-Brechung.

Die Mindest-Majors sind die ERSTE node24-Version der jeweiligen Action,
verifiziert am 2026-06-18 gegen die ``action.yml`` der Tags (``runs.using``):

* ``actions/upload-artifact``   – v5 = node20, **v6** = node24
* ``actions/download-artifact`` – v6 = node20, **v7** = node24
* ``actions/github-script``     – v7 = node20, **v8** = node24
* ``actions/checkout``          – v4 = node20, **v5** = node24
* ``actions/setup-python``      – v5 = node20, **v6** = node24
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_WORKFLOW_DIR = _ROOT / ".github" / "workflows"

# action → erste Major-Version, ab der ``runs.using == node24`` gilt.
_MIN_NODE24_MAJOR = {
    "actions/upload-artifact": 6,
    "actions/download-artifact": 7,
    "actions/github-script": 8,
    "actions/checkout": 5,
    "actions/setup-python": 6,
}

# ``uses: actions/foo@v4`` (Kommentar/Whitespace dahinter erlaubt).
_USES_RE = re.compile(r"uses:\s*(actions/[A-Za-z0-9_-]+)@v(\d+)")

_WORKFLOWS = sorted(_WORKFLOW_DIR.glob("*.yml"))


def test_workflow_dir_has_files() -> None:
    assert _WORKFLOWS, "keine Workflow-Dateien gefunden"


@pytest.mark.parametrize("workflow", _WORKFLOWS, ids=lambda p: p.name)
def test_no_node20_based_actions(workflow: Path) -> None:
    """Keine getrackte Action läuft unter ihrer node24-Mindest-Major."""
    text = workflow.read_text(encoding="utf-8")
    violations = [
        f"{action}@v{major} (node24 erst ab v{_MIN_NODE24_MAJOR[action]})"
        for action, major in _USES_RE.findall(text)
        if action in _MIN_NODE24_MAJOR and int(major) < _MIN_NODE24_MAJOR[action]
    ]
    assert not violations, (
        f"{workflow.name}: node20-basierte Action(s): {violations}. "
        "GitHub deprecatet die node20-Runtime – auf den node24-Major heben "
        "(Befund #312)."
    )


def test_tracked_node20_prone_actions_are_actually_present() -> None:
    """Sanity: die drei vom Befund betroffenen Actions kommen tatsächlich vor.

    Sonst prüfte ``test_no_node20_based_actions`` nichts und bliebe still grün,
    falls eine Action umbenannt/entfernt würde.
    """
    all_text = "\n".join(p.read_text(encoding="utf-8") for p in _WORKFLOWS)
    used = {action for action, _ in _USES_RE.findall(all_text)}
    for action in (
        "actions/upload-artifact",
        "actions/download-artifact",
        "actions/github-script",
    ):
        assert action in used, f"{action} nirgends referenziert – Guard wirkungslos?"

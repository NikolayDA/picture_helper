"""Drift-Schutz für den geteilten Diagnoseschritt der Claude-Workflows (#825).

``claude-code-review.yml`` und ``claude.yml`` führen denselben Schritt
„Abgelehnte Werkzeugaufrufe ausweisen": Er zieht aus dem Protokoll der Action
ausschließlich ``permission_denials`` ins Joblog. Der Schritt existiert, weil
ein Agent, der eine Quelle nicht abrufen darf, stillschweigend rät statt
nachzuschlagen – und weil abgelehnte Aufrufe Turns bis zum Budgetende
verbrauchen. Beides war ohne diese Ausgabe nicht erkennbar.

Der Block ist bewusst in beide Dateien kopiert (ein Workflow kann keinen
Schritt aus einem anderen einbinden). Dieser Test hält die Kopien wortgleich –
dasselbe Muster wie der Qt-Paketlisten-Schutz aus Befund N6.

Zusätzlich schützt die Datei den engen Lese-/Kommentierrahmen des automatischen
Reviews aus #841. Diese Invarianten sind textbasiert, damit sie auch ohne die
optionale PyYAML-Abhängigkeit im regulären ``[test]``-Umfang laufen.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_WORKFLOWS = (
    ".github/workflows/claude-code-review.yml",
    ".github/workflows/claude.yml",
)
_DIAGNOSTIC_NAME = "Abgelehnte Werkzeugaufrufe ausweisen"
_REVIEW_WORKFLOW = ".github/workflows/claude-code-review.yml"
_EXPECTED_REVIEW_GIT_TOOLS = {
    "Bash(git status --short)",
    "Bash(git show-ref --head)",
    "Bash(git log --oneline --decorate --max-count=30 HEAD)",
    "Bash(git diff --stat HEAD^ HEAD)",
    "Bash(git diff --name-only HEAD^ HEAD)",
    "Bash(git show --stat --oneline HEAD)",
    "Bash(git show --format=fuller --no-patch HEAD)",
}
_EXPECTED_REVIEW_BASH_TOOLS = {
    "Bash(gh pr diff:*)",
    "Bash(gh pr view:*)",
    "Bash(gh pr list:*)",
    "Bash(gh pr comment:*)",
    *_EXPECTED_REVIEW_GIT_TOOLS,
}


def _steps(relative: str) -> list[dict[str, Any]]:
    """Die Schritte des einzigen Jobs in *relative*."""
    yaml = pytest.importorskip("yaml")
    data = yaml.safe_load((_ROOT / relative).read_text(encoding="utf-8"))
    jobs = list(data["jobs"].values())
    assert len(jobs) == 1, f"{relative}: unerwartet mehrere Jobs"
    return list(jobs[0]["steps"])


def _step_by_name(relative: str, name: str) -> dict[str, Any]:
    for step in _steps(relative):
        if step.get("name") == name:
            return step
    raise AssertionError(f"{relative}: Schritt {name!r} fehlt")


def _review_allowed_tools() -> set[str]:
    """Kommagetrennte ``--allowedTools`` des automatischen Reviews."""
    text = (_ROOT / _REVIEW_WORKFLOW).read_text(encoding="utf-8")
    match = re.search(
        r'(?m)^ {12}--allowedTools "(?P<tools>[^"]+)"$',
        text,
    )
    assert match, "--allowedTools im Review-Workflow nicht gefunden"
    return set(match.group("tools").split(","))


def _review_workflow_text() -> str:
    return (_ROOT / _REVIEW_WORKFLOW).read_text(encoding="utf-8")


def _review_prompt() -> str:
    """Prompt-Block ohne optionale PyYAML-Abhängigkeit extrahieren."""
    lines = _review_workflow_text().splitlines()
    marker = "          prompt: |"
    try:
        start = lines.index(marker) + 1
    except ValueError as exc:
        raise AssertionError("Prompt im Review-Workflow nicht gefunden") from exc

    prompt: list[str] = []
    for line in lines[start:]:
        if line and not line.startswith("            "):
            break
        prompt.append(line[12:] if line else "")
    return "\n".join(prompt)


@pytest.mark.parametrize("relative", _WORKFLOWS)
def test_action_step_carries_the_referenced_id(relative: str) -> None:
    """Der Diagnoseschritt liest ``steps.claude.*`` – die ID muss vergeben sein.

    Ohne ``id: claude`` liefern sowohl ``outcome`` als auch ``execution_file``
    still einen leeren Wert; der Schritt liefe dann nie an, ohne dass es
    auffällt.
    """
    ids = {s.get("id") for s in _steps(relative) if "claude-code-action" in str(s.get("uses", ""))}
    assert ids == {"claude"}, f"{relative}: Action-Schritt ohne id 'claude' ({ids})"


@pytest.mark.parametrize("relative", _WORKFLOWS)
def test_diagnostic_step_never_fails_the_job(relative: str) -> None:
    """Die Diagnose darf einen sonst grünen Lauf nie rot färben.

    Zusätzlich hängt das Gating am Schritt-*Ergebnis*, nicht am Output-Pfad:
    Bricht die Action früh ab (Auth, Nutzungslimit, Modell nicht gedeckt), gibt
    es kein ``execution_file`` – und genau dann wird die Diagnose gebraucht.
    """
    step = _step_by_name(relative, _DIAGNOSTIC_NAME)
    assert step.get("continue-on-error") is True
    assert step.get("if") == "always() && steps.claude.outcome != 'skipped'"


def test_diagnostic_step_is_identical_in_both_workflows() -> None:
    """Beide Kopien müssen wortgleich bleiben (Drift-Schutz analog N6)."""
    first, second = (_step_by_name(w, _DIAGNOSTIC_NAME) for w in _WORKFLOWS)
    assert first == second, "Diagnoseschritt driftet zwischen den Claude-Workflows"


def test_diagnostic_reports_unreadable_log_instead_of_zero() -> None:
    """Ein jq-Fehler darf nicht als „0 Ablehnungen" durchgehen.

    Das wäre im Joblog nicht vom sauberen Lauf zu unterscheiden – dieselbe
    Falle, die CLAUDE.md für den ClamAV-Scan ausschließt („ein still
    übersprungener Scan gilt nie als bestanden").
    """
    script = _step_by_name(_WORKFLOWS[0], _DIAGNOSTIC_NAME)["run"]
    assert "if ! denials=$(jq" in script, "jq-Fehler wird nicht abgefangen"
    assert "::warning::Protokoll nicht auswertbar" in script


def test_review_bash_allowlist_matches_inspection_and_comment_boundary() -> None:
    """#841: nur belegte Lesewege und der PR-Kommentar dürfen Bash nutzen."""
    allowed = _review_allowed_tools()
    allowed_bash = {tool for tool in allowed if tool.startswith("Bash(")}
    assert allowed_bash == _EXPECTED_REVIEW_BASH_TOOLS, (
        "Review-Bash-Allowlist weicht vom engen Lese-/Kommentierrahmen ab: "
        f"fehlt={sorted(_EXPECTED_REVIEW_BASH_TOOLS - allowed_bash)}, "
        f"unerwartet={sorted(allowed_bash - _EXPECTED_REVIEW_BASH_TOOLS)}"
    )
    assert allowed >= {
        "mcp__github_inline_comment__create_inline_comment",
        "Read",
        "Grep",
        "Glob",
    }


def test_review_allowlist_keeps_checkout_and_remote_mutations_forbidden() -> None:
    """#841 erweitert Lesezugriffe, nicht die Schreib- oder Ausführungsrechte."""
    allowed = _review_allowed_tools()
    forbidden_prefixes = (
        "Edit",
        "Write",
        "Bash(cp",
        "Bash(mv",
        "Bash(git checkout",
        "Bash(git restore",
        "Bash(git commit",
        "Bash(git push",
        "Bash(git fetch",
        "Bash(gh api",
        "Bash(pytest",
        "Bash(python",
    )
    offenders = sorted(
        tool for tool in allowed if tool.startswith(forbidden_prefixes)
    )
    assert not offenders, f"Review-Allowlist erweitert Schreib-/Ausführungsscope: {offenders}"

    workflow = _review_workflow_text()
    review_prefix = re.search(
        r"(?ms)^  review:\n(?P<body>.*?)(?=^    steps:\n)",
        workflow,
    )
    assert review_prefix, "Review-Jobkopf nicht gefunden"
    assert re.search(r"(?m)^      contents: read\s*$", review_prefix.group("body"))


def test_review_git_allowlist_uses_only_exact_non_writing_forms() -> None:
    """Review-Befund: Git-Präfixe würden ``--output``-Schreibzugriffe erlauben."""
    git_tools = {
        tool for tool in _review_allowed_tools()
        if tool.startswith("Bash(git ")
    }
    assert git_tools == _EXPECTED_REVIEW_GIT_TOOLS
    assert all("*" not in tool for tool in git_tools), "Git-Regel mit Präfix-Wildcard"
    assert all("--output" not in tool for tool in git_tools), "Git-Regel schreibt Dateien"


def test_review_checkout_provides_history_before_git_inspection() -> None:
    """Review-Befund: Der Agent darf nicht auf einem Merge-Commit ohne Eltern lesen."""
    checkout = re.search(
        r"(?ms)^      - name: Checkout repository\n(?P<body>.*?)(?=^      - name:)",
        _review_workflow_text(),
    )
    assert checkout, "Checkout-Schritt im Review-Workflow nicht gefunden"
    assert re.search(r"(?m)^          fetch-depth: 0\s*$", checkout.group("body"))


def test_review_prompt_states_the_non_mutating_tool_boundary() -> None:
    """Prompt verhindert die in #841 belegten Ablehnungs- und Schreibversuche."""
    prompt = _review_prompt()
    required_phrases = (
        "Arbeite ausschließlich bewertend",
        "lasse den Checkout unverändert",
        "git fetch",
        "Tests oder PR-Code lokal auszuführen",
        "gh api",
        "git checkout`/`restore",
        "Read, Grep oder Glob",
        "verwende **nur** eine der folgenden exakten Formen",
        "git diff --stat HEAD^ HEAD",
        "ohne weitere Flags",
        "**unbelegt**",
    )
    missing = [phrase for phrase in required_phrases if phrase not in prompt]
    assert not missing, f"Prompt-Grenze unvollständig: {missing}"


def test_review_allowlist_rationale_stays_above_claude_args() -> None:
    """Hausstil aus #841: Risikoerklärung steht über, nie im Argumentblock."""
    text = _review_workflow_text()
    args_index = text.index("          claude_args: |")
    rationale = "          # Nur-Lese-Freigaben (#841):"
    rationale_index = text.index(rationale)
    assert rationale_index < args_index
    assert args_index - rationale_index < 1200, "Begründung steht nicht direkt am Block"

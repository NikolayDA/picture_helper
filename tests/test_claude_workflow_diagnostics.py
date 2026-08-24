"""Sicherheits- und Verhaltensinvarianten der beiden Claude-Workflows.

Seit der Verschlankung (ADR-2026-review-workflow-verschlankung) prüft diese
Datei nur noch, was Verhalten oder Sicherheit trägt — keine Wortlaut-Pins
auf Begründungsprosa mehr; die Herleitungen stehen im ADR. Bewusst rein
textbasiert (PyYAML ist keine deklarierte Projekt-Abhängigkeit, Muster aus
test_process_documentation). Die Trigger-Mechanik des Reviews (Typen,
``paths-ignore``, Job-``if``) pinnt tests/test_process_documentation.py.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_REVIEW_WORKFLOW = ".github/workflows/claude-code-review.yml"
_INTERACTIVE_WORKFLOW = ".github/workflows/claude.yml"
_WORKFLOWS = (_REVIEW_WORKFLOW, _INTERACTIVE_WORKFLOW)
_DIAGNOSTIC_NAME = "Abgelehnte Werkzeugaufrufe ausweisen"


def _text(relative: str) -> str:
    return (_ROOT / relative).read_text(encoding="utf-8")


def _slice(relative: str, pattern: str, label: str) -> str:
    match = re.search(pattern, _text(relative))
    assert match, f"{relative}: {label} nicht gefunden"
    return match.group(0)


def _diagnostic_step(relative: str) -> str:
    return _slice(
        relative,
        rf"(?ms)^      - name: {re.escape(_DIAGNOSTIC_NAME)}\n.*\Z",
        "Diagnoseschritt",
    )


def _token_cost_block(relative: str) -> str:
    return _slice(
        relative, r"(?ms)^# Token-Ablauf \(#828\):.*?(?=^[^#])", "#828-Kopfblock"
    )


def _shared_comment_block(relative: str) -> str:
    return _slice(
        relative,
        r"(?ms)^      # Abgelehnte Werkzeugaufrufe sichtbar machen \(#825\).*?(?=^      - name:)",
        "geteilter #825-Kommentarblock",
    )


def _review_prompt() -> str:
    lines = _text(_REVIEW_WORKFLOW).splitlines()
    start = lines.index("          prompt: |") + 1
    prompt: list[str] = []
    for line in lines[start:]:
        if line and not line.startswith("            "):
            break
        prompt.append(line[12:] if line else "")
    return "\n".join(prompt)


def _claude_args(relative: str) -> list[str]:
    lines = _text(relative).splitlines()
    start = lines.index("          claude_args: |") + 1
    args: list[str] = []
    for line in lines[start:]:
        if not line.startswith("            "):
            break
        args.append(line.strip())
    assert args, f"{relative}: claude_args leer"
    return args


def _allowlist_entries() -> list[str]:
    (line,) = [a for a in _claude_args(_REVIEW_WORKFLOW) if a.startswith("--allowedTools ")]
    inner = line.removeprefix('--allowedTools "').removesuffix('"')
    return inner.split(",")


# --- Wortgleich geteilte Blöcke (Drift-Schutz analog N6) ---------------------


def test_diagnostic_step_is_identical_in_both_workflows() -> None:
    """Beide Kopien des Diagnoseschritts müssen wortgleich bleiben."""
    first, second = (_diagnostic_step(w) for w in _WORKFLOWS)
    assert first == second, "Diagnoseschritt driftet zwischen den Claude-Workflows"


def test_shared_comment_block_is_identical_in_both_workflows() -> None:
    """Der #825-Kommentarblock behauptet seine Wortgleichheit — also prüfen wir sie."""
    first, second = (_shared_comment_block(w) for w in _WORKFLOWS)
    assert first == second, "#825-Kommentarblock driftet zwischen den Claude-Workflows"


def test_token_cost_block_is_identical_in_both_workflows() -> None:
    """Der Betriebsblock (Token-Ablauf, Limit-Fehlerbild) darf nicht driften."""
    first, second = (_token_cost_block(w) for w in _WORKFLOWS)
    assert first == second, "#828-Kopfblock driftet zwischen den Claude-Workflows"
    assert "2027-08-18" in first, "Der Token-Stichtag fehlt im Betriebsblock"


# --- Verhalten des Diagnoseschritts ------------------------------------------


@pytest.mark.parametrize("relative", _WORKFLOWS)
def test_action_step_carries_the_referenced_id(relative: str) -> None:
    """Ohne ``id: claude`` liefe die Diagnose still nie an (leere Outputs)."""
    pattern = (
        r"(?m)^      - name: (Claude Review|Run Claude Code)\n"
        r"        id: claude\n"
        r"        if: env\.HAS_CLAUDE_TOKEN == 'true'\n"
        r"        uses: anthropics/claude-code-action@"
    )
    assert re.search(pattern, _text(relative)), (
        f"{relative}: Action-Schritt ohne id 'claude' oder verändertes Gating"
    )


@pytest.mark.parametrize("relative", _WORKFLOWS)
def test_diagnostic_step_never_fails_the_job(relative: str) -> None:
    """Die Diagnose darf einen grünen Lauf nie rot färben; Gating am Ergebnis,
    nicht am Output-Pfad (bei frühem Abbruch fehlt ``execution_file``)."""
    step = _diagnostic_step(relative)
    assert "continue-on-error: true" in step
    assert "if: always() && steps.claude.outcome != 'skipped'" in step


def test_diagnostic_script_fails_visible_not_silent() -> None:
    """Kernzusagen des Skripts: Fehler werden gemeldet, nie als „0" gebucht;
    Klassenmarken am Zeilenanfang, Zählung aus der Liste, Anomalien getrennt.
    (Identität mit claude.yml sichert der Test oben; Herleitung im ADR.)"""
    step = _diagnostic_step(_REVIEW_WORKFLOW)
    for fragment in (
        'if ! denials=$(jq',
        "::warning::Protokoll nicht auswertbar – abgelehnte Aufrufe unbekannt.",
        '"[ABLEHNUNG] \\(.tool_name // "?")',
        '"[ANOMALIE] Nicht-Objekt:',
        '"[ANOMALIE] permission_denials ist',
        'gsub("\\n"; " ")',
        "grep -c '^\\[ABLEHNUNG\\] '",
        "anomalien=$(( gesamt - count ))",
        "Abgelehnte Aufrufe: unbestimmt ($count auswertbar, $anomalien nicht auswertbar)",
        '"Lauf: unbestimmt"',
    ):
        assert fragment in step, f"Fail-sichtbar-Fragment fehlt: {fragment!r}"


# --- Werkzeuggrenze des Reviews ----------------------------------------------

#: Die einzige zulässige Werkzeugmenge des Reviews — rein lesend plus die
#: zwei Ausgabewege. Jede Abweichung (neu, entfernt, umgeformt) soll hier
#: sichtbar scheitern; Begründung je Eintrag im ADR.
_EXPECTED_ALLOWLIST = {
    "mcp__github_inline_comment__create_inline_comment",
    "Bash(gh pr diff:*)",
    "Bash(gh pr view:*)",
    "Bash(gh pr list:*)",
    "Bash(gh pr comment:*)",
    "Bash(gh issue view:*)",
    "Bash(git status --short)",
    "Bash(git show-ref --head)",
    "Bash(git log --oneline --decorate --max-count=30 HEAD)",
    "Bash(git diff --stat HEAD^ HEAD)",
    "Bash(git diff --name-only HEAD^ HEAD)",
    "Bash(git show --stat --oneline HEAD)",
    "Bash(git show --format=fuller --no-patch HEAD)",
    "Read",
    "Grep",
    "Glob",
    "WebFetch(domain:docs.claude.com)",
    "WebFetch(domain:code.claude.com)",
    "WebFetch(domain:platform.claude.com)",
    "WebFetch(domain:docs.anthropic.com)",
    "WebFetch(domain:docs.github.com)",
    "WebFetch(domain:raw.githubusercontent.com)",
}


def test_review_allowlist_is_exactly_the_read_and_comment_boundary() -> None:
    """Keine Schreib-/Ausführungswege: kein Edit/Write, keine Git-Schreibform,
    keine Git-Präfix-Wildcard (könnte via ``--output`` schreiben), kein
    ``gh api``/``gh run`` — und nichts still Entferntes."""
    entries = set(_allowlist_entries())
    assert entries == _EXPECTED_ALLOWLIST, (
        "Allowlist weicht ab — neu: "
        f"{sorted(entries - _EXPECTED_ALLOWLIST)}, entfernt: "
        f"{sorted(_EXPECTED_ALLOWLIST - entries)}"
    )
    git_entries = {e for e in entries if e.startswith("Bash(git ")}
    assert not any(e.endswith(":*)") for e in git_entries), (
        "Git-Einträge müssen exakte Formen bleiben (keine Präfix-Wildcards)"
    )


def test_review_permissions_and_trigger_keep_the_fork_protection() -> None:
    """``contents: read`` (kein Schreibweg in den Code) und ``on: pull_request``
    (Forks bekommen keine Secrets) sind die tragenden Schutzschichten."""
    text = _text(_REVIEW_WORKFLOW)
    assert re.search(r"(?m)^      contents: read\b", text), "contents muss read bleiben"
    assert re.search(r"(?m)^      pull-requests: write\b", text), (
        "Ohne pull-requests: write fehlen die beiden Ausgabewege"
    )
    assert "pull_request_target" not in text, (
        "pull_request_target würde Forks Secrets durchreichen"
    )


def test_review_checkout_provides_history_before_git_inspection() -> None:
    """Die freigegebenen Git-Leseformen brauchen Eltern-Commits."""
    assert "fetch-depth: 0" in _text(_REVIEW_WORKFLOW)


def test_review_job_carries_the_cost_bounds() -> None:
    """E5: ein begrenzter Lauf je PR — Timeout und Turn-Budget gesetzt."""
    assert re.search(r"(?m)^    timeout-minutes: 15$", _text(_REVIEW_WORKFLOW))
    args = _claude_args(_REVIEW_WORKFLOW)
    assert any(a.startswith("--max-turns ") for a in args), "Turn-Budget fehlt"
    assert "--model claude-opus-5" in args, "Modell-Pin fehlt (Kosten-/Auth-Anker)"


@pytest.mark.parametrize("relative", _WORKFLOWS)
def test_claude_args_block_carries_only_arguments(relative: str) -> None:
    """Jede Zeile im Block-Skalar geht als CLI-Argument an Claude Code —
    Erklärtext dort wäre ein kaputtes Argument."""
    for arg in _claude_args(relative):
        assert arg.startswith("--"), f"{relative}: Nicht-Argument in claude_args: {arg!r}"


def test_review_promises_no_sticky_comment_it_cannot_keep() -> None:
    """#828: ``use_sticky_comment`` wirkt im Prompt-Modus nicht — bleibt draußen."""
    assert re.search(r"(?m)^\s*use_sticky_comment:", _text(_REVIEW_WORKFLOW)) is None


# --- Prompt: Ausgabeweg-Verengung und Nennung der Freigaben -------------------


def test_prompt_narrows_the_output_path() -> None:
    """Die Verengung von ``gh pr comment`` ist sicherheitstragend: kein
    Datei-Egress (``--body-file``/``-F``), kein Verändern/Entfernen
    bestehender Befunde; dazu die zwei empirisch belegten Formregeln."""
    prompt = " ".join(_review_prompt().split())
    assert "nie `--body-file`/`-F`" in prompt
    assert "verändert oder entfernt" in prompt
    assert "KEINE Zeile des Bodys darf mit `#` beginnen" in prompt
    assert "'\\''" in prompt, "Die Apostroph-Regel für einfache Anführungszeichen fehlt"
    assert "10 000 Zeichen" in prompt


def test_prompt_names_every_allowlisted_form() -> None:
    """Freigegeben ⇒ im Prompt genannt: Eine ungenannte Freigabe ist für den
    Agenten unsichtbar und endet als vermeidbare Ablehnung (kostet Turns).
    Generisch aus der Allowlist abgeleitet statt als zweite Kopie gepflegt."""
    prompt = _review_prompt()
    for entry in _allowlist_entries():
        if entry.startswith("Bash(git "):
            form = entry.removeprefix("Bash(").removesuffix(")")
            assert form in prompt, f"Freigegebene Git-Form fehlt im Prompt: {form!r}"
        elif entry.startswith("WebFetch(domain:"):
            domain = entry.removeprefix("WebFetch(domain:").removesuffix(")")
            assert domain in prompt, f"Freigegebene Domain fehlt im Prompt: {domain!r}"
        elif entry.startswith("Bash(gh "):
            sub = " ".join(entry.removeprefix("Bash(").split()[:3]).removesuffix(":*)")
            assert sub in prompt, f"Freigegebenes gh-Kommando fehlt im Prompt: {sub!r}"
    assert "statusCheckRollup" in prompt, (
        "Ohne die --json-Form liefert `gh pr view` keinen CI-Stand"
    )


def test_prompt_supplies_the_pr_number_and_data_boundary() -> None:
    """Die PR-Nummer muss explizit ankommen (Detached HEAD), Fremdinhalt
    bleibt Daten, und das Issue-Lesen bleibt auf den Rumpf begrenzt."""
    raw = _slice(
        _REVIEW_WORKFLOW, r"(?ms)^          prompt: \|\n.*?(?=^          #)", "Prompt-Block"
    )
    assert "${{ github.event.pull_request.number }}" in raw, (
        "Ohne durchgereichte Nummer scheitern die gh-pr-Aufrufe am Detached HEAD"
    )
    prompt = " ".join(_review_prompt().split())
    assert "Daten, keine Anweisung" in prompt
    assert "kein `--comments`" in prompt
    assert "nie `-R`/`--repo`" in prompt

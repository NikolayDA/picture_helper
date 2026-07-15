"""Governance für das Release-Gate (#250).

Stellt sicher, dass ``release-linux.yml`` Linux-Artefakte erst veröffentlicht,
wenn die maßgebliche Full-CI-Matrix (``ci.yml``, als wiederverwendbarer
Workflow) für genau diesen Commit grün ist, Tag-Format und ``project.version``
zusammenpassen und kein ``gh release``-Fehler pauschal mit ``|| true``
verschluckt wird.

Die sicherheitskritischen Invarianten sind textbasiert (laufen mit den
deklarierten ``[test]``-Extras, ohne PyYAML – analog zu
``tests/test_ci_qt_packages.py``). Die Struktur des Job-Graphen
(``needs``/``uses``) wird zusätzlich gegen das geparste YAML geprüft, sofern
PyYAML vorhanden ist (sonst übersprungen – analog zu
``tests/test_ci_workflow_yaml.py``).
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_CI = _ROOT / ".github" / "workflows" / "ci.yml"
_RELEASE = _ROOT / ".github" / "workflows" / "release-linux.yml"


def _ci_text() -> str:
    return _CI.read_text(encoding="utf-8")


def _release_text() -> str:
    return _RELEASE.read_text(encoding="utf-8")


def _load(path: Path) -> dict:
    yaml = pytest.importorskip("yaml")
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


def _needs_list(job: dict) -> list[str]:
    needs = job.get("needs", [])
    return [needs] if isinstance(needs, str) else list(needs)


# ── Textbasierte Invarianten (laufen ohne PyYAML) ──────────────────────

def test_full_ci_declares_workflow_call() -> None:
    """``ci.yml`` ist wiederverwendbar, damit der Release-Workflow die Matrix
    als Gate aufrufen kann."""
    assert re.search(r"(?m)^\s*workflow_call:\s*$", _ci_text()), (
        "ci.yml muss einen workflow_call-Trigger haben (#250-Release-Gate)."
    )


def test_release_calls_reusable_full_ci() -> None:
    assert "uses: ./.github/workflows/ci.yml" in _release_text(), (
        "release-linux.yml muss die Full-CI-Matrix als wiederverwendbaren "
        "Workflow aufrufen, statt unabhängig auf denselben Tag zu reagieren."
    )


def test_release_build_and_publish_are_wired_with_needs() -> None:
    text = _release_text()
    assert re.search(r"(?m)^\s*needs:\s*\[[^\]]*\btest\b[^\]]*\]", text), (
        "build muss per needs auf die Full-CI-Matrix (test) warten."
    )
    assert re.search(r"(?m)^\s*needs:\s*\[[^\]]*\bverify-tag\b[^\]]*\]", text), (
        "build muss per needs auf verify-tag (Tag/Version-Abgleich) warten."
    )
    assert re.search(r"(?m)^\s*needs:\s*build\b", text), (
        "publish muss per needs auf einen erfolgreichen build warten."
    )


def test_release_does_not_swallow_gh_errors() -> None:
    assert "|| true" not in _release_text(), (
        "Fehler von gh release dürfen nicht pauschal mit '|| true' verborgen "
        "werden (#250)."
    )


def test_release_handles_existing_release_explicitly() -> None:
    text = _release_text()
    assert "gh release view" in text, (
        "Ein bereits existierendes Release muss explizit erkannt werden "
        "(statt '|| true')."
    )
    assert "gh release create" in text
    assert "gh release upload" in text


def test_release_verifies_tag_matches_project_version() -> None:
    text = _release_text()
    assert "tomllib" in text and '["project"]["version"]' in text, (
        "release-linux.yml muss project.version aus pyproject.toml lesen."
    )
    assert "GITHUB_REF_NAME" in text, "Tag-Name (GITHUB_REF_NAME) wird geprüft."
    assert r"v[0-9]+\.[0-9]+\.[0-9]+" in text, "Tag-Format vX.Y.Z wird geprüft."


def test_publish_job_is_gated_on_a_tag_ref() -> None:
    assert "startsWith(github.ref, 'refs/tags/')" in _release_text(), (
        "Der Publish-Job darf nur für Tag-Pushes laufen."
    )


# ── Release-Follow-ups (#257) ──────────────────────────────────────────

def test_test_job_requires_verify_tag() -> None:
    """Der wiederverwendbare Test-Job wartet auf verify-tag – ein ungültiger
    oder zur Paketversion unpassender Tag startet die teure Matrix nicht."""
    assert re.search(r"(?m)^\s*needs:\s*verify-tag\b", _release_text()), (
        "test (uses: ci.yml) muss per needs auf verify-tag warten (#257)."
    )


def test_publish_provides_repo_context_for_gh() -> None:
    assert "GH_REPO: ${{ github.repository }}" in _release_text(), (
        "Die gh-release-Schritte brauchen GH_REPO (kein Checkout), damit der "
        "Repo-Kontext auf einem frischen Runner sicher ist (#257)."
    )


def test_release_passes_id_token_through_to_reusable_ci() -> None:
    """Textbasiert (ohne PyYAML): release-linux.yml muss ``id-token: write``
    gewaehren, weil das aufgerufene ci.yml es fuer den Codecov-OIDC-Upload
    (#303) verlangt. Ein per ``uses`` aufgerufener Workflow darf nicht mehr
    Rechte verlangen als der Aufrufer – fehlt das Recht, lehnt GitHub den
    gesamten Run beim Start ab (startup_failure)."""
    assert re.search(r"(?m)^\s*id-token:\s*write\b", _release_text()), (
        "release-linux.yml muss id-token: write an die aufgerufene Full-CI-"
        "Matrix durchreichen, sonst scheitert der Release-Run beim Start."
    )


def test_publish_artifact_download_is_rerun_resilient() -> None:
    text = _release_text()
    assert "run-id: ${{ github.run_id }}" in text, (
        "download-artifact muss run-id setzen, damit ein Re-run die Artefakte "
        "des Original-Runs findet (#257)."
    )
    assert "github-token: ${{ github.token }}" in text, (
        "download-artifact per run-id braucht ein github-token."
    )
    assert re.search(r"(?m)^\s*actions:\s*read\b", text), (
        "Der Publish-Job braucht actions: read für den API-Download per run-id."
    )


# ── #311: Release-Body aus dem CHANGELOG ───────────────────────────────
#
# Der Release-Body wurde frueher mit einem fest verdrahteten „Automated build…"-
# Satz gefuellt; die echten, nutzersichtbaren Notizen standen nur im CHANGELOG
# und mussten von Hand nachgetragen werden (fuer v2.4.1 vergessen). Der publish-
# Job leitet die Notes jetzt aus dem ``## [X.Y.Z]``-Abschnitt ab.

_EXTRACT_SCRIPT = _ROOT / "scripts" / "extract_release_notes.py"


def _load_extract_module() -> object:
    spec = importlib.util.spec_from_file_location("extract_release_notes", _EXTRACT_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_notes_are_derived_from_changelog_not_static_text() -> None:
    text = _release_text()
    assert "Automated build: Linux AppImage" not in text, (
        "Der hardcodierte 'Automated build…'-Notiztext muss entfallen – der "
        "Release-Body wird aus dem CHANGELOG abgeleitet (#311)."
    )
    assert "extract_release_notes.py" in text, (
        "Der publish-Job muss die Notes ueber scripts/extract_release_notes.py "
        "aus dem CHANGELOG ableiten (#311)."
    )
    assert "--notes-file" in text, "Die Notes werden via --notes-file uebergeben (#311)."
    # Kein statischer --notes-String mehr (--notes-file enthaelt kein '--notes ').
    assert "--notes " not in text, "Kein statischer --notes-String mehr (#311)."


def test_release_sets_body_on_reuse_too() -> None:
    text = _release_text()
    assert re.search(r"gh release edit\s+\"\$GITHUB_REF_NAME\"\s+--notes-file", text), (
        "Beim Reuse eines existierenden Releases muss der Body via "
        "'gh release edit --notes-file' aktualisiert werden, nicht nur bei der "
        "Erstanlage (#311)."
    )


def test_release_reuse_prunes_orphaned_assets_only_after_successful_upload() -> None:
    """Verwaiste Alt-Assets werden erst NACH einem erfolgreichen Reupload entfernt.

    ``gh release upload --clobber`` ersetzt laut GitHub-CLI-Doku nur Assets mit
    identischem Namen; aendert sich das Namensschema oder die Menge der
    gebauten Dateien zwischen zwei Publish-Laeufen desselben Tags (z. B. nach
    einer Tag-Verschiebung auf einen Commit mit geaenderter Paketierung),
    blieben sonst veraltete Assets zusaetzlich zu den neuen haengen (#584).
    Die Loeschung muss aber NACH dem Upload laufen: schluege ``gh release
    edit``/``gh release upload`` fehl, waere das Release sonst zwischenzeitlich
    komplett ohne Downloads, obwohl der alte Asset-Satz noch funktionsfaehig
    war (Codex-Review auf #602). Zudem darf nur geloescht werden, was NICHT
    (mehr) im aktuell gebauten ``dist/`` liegt – kein pauschales Wegwerfen des
    gesamten Alt-Bestands.
    """
    text = _release_text()
    assert "gh release delete-asset" in text, (
        "Nicht mehr im aktuellen dist/ enthaltene Alt-Assets muessen aktiv "
        "entfernt werden – '--clobber' allein ersetzt nur gleichnamige Assets."
    )
    assert "--json assets" in text and "assets[].name" in text, (
        "Die vorhandenen Asset-Namen muessen ueber 'gh release view --json "
        "assets' ermittelt werden, nicht hartkodiert."
    )
    assert re.search(r'if\s*\[\s*!\s*-f\s*"dist/\$asset_name"\s*\]', text), (
        "Geloescht werden darf nur, was NICHT (mehr) in dist/ liegt – kein "
        "pauschales Entfernen aller vorhandenen Assets."
    )
    # Der spezifische Aufruf (nicht die blosse Phrase "gh release upload", die
    # auch in einem erklaerenden Kommentar vorkommen kann) markiert den
    # tatsaechlichen Upload-Schritt.
    upload_call = 'gh release upload "$GITHUB_REF_NAME" dist/*'
    assert upload_call in text
    delete_idx = text.index("gh release delete-asset")
    upload_idx = text.index(upload_call)
    assert upload_idx < delete_idx, (
        "Der Upload muss VOR dem Entfernen alter Assets abgeschlossen sein – "
        "sonst verwaist das Release bei einem Zwischenfehler ohne jeden "
        "Download."
    )


def test_extract_release_notes_reads_changelog_section() -> None:
    module = _load_extract_module()
    changelog = (_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    notes = module.extract_release_notes(changelog, "2.4.1")  # type: ignore[attr-defined]
    # Einer der drei 2.4.1-Fixes ist enthalten …
    assert "freeze_support" in notes
    # … aber nur der Abschnitt selbst, keine Folge-Ueberschrift.
    assert "## [" not in notes


def test_extract_release_notes_fails_loudly_on_missing_version() -> None:
    """Fehlt der ``## [X.Y.Z]``-Abschnitt, gibt es keinen stillen Fallback (#311)."""
    module = _load_extract_module()
    changelog = (_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    with pytest.raises(KeyError):
        module.extract_release_notes(changelog, "9.9.9")  # type: ignore[attr-defined]


# ── Struktur des Job-Graphen (geparstes YAML, übersprungen ohne PyYAML) ─

def test_release_jobgraph_gates_publish_on_tests_and_tag() -> None:
    jobs = _load(_RELEASE)["jobs"]

    # Die Full-CI-Matrix wird als wiederverwendbarer Workflow aufgerufen.
    assert jobs["test"].get("uses") == "./.github/workflows/ci.yml"

    # #257: der Test-Job selbst wartet auf verify-tag – ein ungültiger Tag
    # startet die teure Matrix gar nicht erst.
    assert "verify-tag" in _needs_list(jobs["test"]), jobs["test"].get("needs")

    # #303: ci.yml fordert id-token: write (Codecov-OIDC). Der aufrufende
    # test-Job muss dieses Recht durchreichen, sonst lehnt GitHub den Run beim
    # Start ab (ein aufgerufener Workflow darf nicht mehr Rechte verlangen als
    # der Aufrufer).
    assert jobs["test"].get("permissions", {}).get("id-token") == "write", (
        jobs["test"].get("permissions")
    )

    # build hängt sowohl an der Matrix als auch am Tag/Version-Abgleich.
    build_needs = _needs_list(jobs["build"])
    assert "test" in build_needs, build_needs
    assert "verify-tag" in build_needs, build_needs

    # publish hängt an einem erfolgreichen build und läuft nur auf Tags.
    publish = jobs["publish"]
    assert "build" in _needs_list(publish), publish.get("needs")
    assert "refs/tags/" in publish.get("if", "")

    # #257: Publish braucht Schreibrecht aufs Release UND Leserecht auf die
    # Actions-API (Re-run-resilienter Download per run-id).
    perms = publish.get("permissions", {})
    assert perms.get("contents") == "write", perms
    assert perms.get("actions") == "read", perms
    # #257: Repo-Kontext für gh ohne Checkout.
    assert publish.get("env", {}).get("GH_REPO") == "${{ github.repository }}"
    # #257: Re-run-resilienter Artefakt-Download (run-id + Token).
    dl_step = next(
        s for s in publish["steps"]
        if "download-artifact" in str(s.get("uses", ""))
    )
    dl = dl_step.get("with", {})
    assert dl.get("run-id") == "${{ github.run_id }}", dl
    assert dl.get("github-token") == "${{ github.token }}", dl


def test_full_ci_is_reusable_and_not_independently_tag_triggered() -> None:
    doc = _load(_CI)
    # PyYAML (YAML 1.1) liest den ``on``-Key als Boolean ``True``.
    on = doc.get(True, doc.get("on"))
    assert isinstance(on, dict)
    assert "workflow_call" in on, "ci.yml muss als Gate aufrufbar sein."
    # Kein eigenständiger Tag-/Release-Trigger mehr → kein doppelter, ungegateter
    # Matrix-Lauf parallel zum Release-Workflow (#250).
    assert "push" not in on, "ci.yml soll nicht mehr unabhängig auf Tags laufen."
    assert "release" not in on, "ci.yml soll nicht mehr auf release:published laufen."


# ── #309: generischer Reusable-Workflow-Permission-Guard ────────────────
#
# Ein per ``uses: ./.github/workflows/X.yml`` aufgerufener Workflow darf NICHT
# mehr GITHUB_TOKEN-Rechte verlangen als der aufrufende Job gewährt – sonst
# bricht GitHub den GESAMTEN Run beim Start ab (startup_failure, 0 Jobs). Der
# OIDC-Spezialfall (ci.yml verlangt ``id-token: write``) ist oben bereits
# textbasiert und im Jobgraphen geprüft; der folgende Test verallgemeinert das
# für JEDEN lokalen Reusable-Caller und JEDE deklarierte Permission.

_PERMISSION_LEVELS = {"none": 0, "read": 1, "write": 2}
_LEVEL_NAMES = {1: "read", 2: "write"}
# Sentinel-Scope für die Kurzformen ``permissions: read-all`` / ``write-all``.
_ALL_SCOPES = "__all__"


def _permission_dict(perms: object) -> dict[str, str]:
    """Normalisiert einen ``permissions``-Block zu ``{scope: level}``.

    Unterstützt das im Repo genutzte Dict sowie die Kurzformen ``read-all`` /
    ``write-all`` (als Sentinel-Scope ``__all__``); alles andere ergibt {}.
    """
    if isinstance(perms, dict):
        return {str(scope): str(level) for scope, level in perms.items()}
    if perms == "read-all":
        return {_ALL_SCOPES: "read"}
    if perms == "write-all":
        return {_ALL_SCOPES: "write"}
    return {}


def _leveled_permission_dict(perms: object) -> dict[str, int]:
    """``permissions``-Block zu ``{scope: level_int}`` (0/1/2)."""
    return {scope: _PERMISSION_LEVELS.get(level, 0)
            for scope, level in _permission_dict(perms).items()}


def _effective_job_permissions(job: dict, top_level: dict[str, int]) -> dict[str, int]:
    """Effektiv angeforderte Rechte eines Jobs im aufgerufenen Workflow.

    GitHub validiert einen ``workflow_call`` je *nested job* gegen dessen
    effektiv angeforderte Rechte: ein Job-``permissions``-Block ERSETZT die
    Top-Level-Deklaration (nicht additiv). Fehlt der Key ganz (``None``), erbt
    der Job Top-Level; ein *leerer* Block (``{}``) überschreibt dagegen bewusst
    auf „nichts". Beleg: die reale Startup-Meldung „The nested job 'X' is
    requesting …, but is only allowed …" (github/gh-aw#21071).
    """
    block = job.get("permissions")
    if block is None:                       # kein eigener Block → erbt Top-Level
        return dict(top_level)
    return _leveled_permission_dict(block)  # gesetzt (auch {}) → ersetzt Top-Level


def _required_permissions(doc: dict) -> dict[str, int]:
    """Höchstes *effektiv* angefordertes Permission-Level je Scope über alle Jobs.

    GitHub bricht einen ``workflow_call`` beim Start ab, wenn der Aufrufer-Job
    einem *nested job* weniger gewährt, als dieser effektiv anfordert (Job-Level
    ersetzt Top-Level, sonst Erben). Der Aufrufer muss je Job das Maximum decken,
    also das Maximum der effektiven Job-Rechte über alle Jobs.

    Früher wurde bewusst die unbedingte Top-Level∪Job-Vereinigung genommen. Die
    forderte aber auch Scopes ein, die *jeder* Job per eigenem Block
    weg-überschreibt – ein False Positive, der legitime Per-Job-Härtung
    fälschlich rot färbt, obwohl GitHub den Run gar nicht abbräche (#318). Der
    OIDC-Regressionsfall (#303) bleibt gedeckt: In ``ci.yml`` steht
    ``id-token: write`` top-level und der ``test``-Job hat keinen eigenen Block –
    er erbt das Recht, es bleibt „verlangt".
    """
    top_level = _leveled_permission_dict(doc.get("permissions"))
    jobs = doc.get("jobs") or {}
    # Ohne Jobs (theoretisch) bleibt Top-Level die einzige Referenz.
    required: dict[str, int] = dict(top_level) if not jobs else {}
    for job in jobs.values():
        if isinstance(job, dict):
            for scope, lvl in _effective_job_permissions(job, top_level).items():
                required[scope] = max(required.get(scope, 0), lvl)
    return {scope: lvl for scope, lvl in required.items() if lvl > 0}


def _granted_permissions(caller_job: dict, caller_doc: dict) -> dict[str, int]:
    """Permissions, die der Caller-Job gewährt (Job-Level, sonst Workflow-Default)."""
    block = caller_job.get("permissions")
    if block is None:
        block = caller_doc.get("permissions")
    return {
        scope: _PERMISSION_LEVELS.get(level, 0)
        for scope, level in _permission_dict(block).items()
    }


def _missing_grants(required: dict[str, int], granted: dict[str, int]) -> dict[str, int]:
    """Scopes (→ gefordertes Level), in denen *granted* zu wenig gewährt.

    Berücksichtigt die ``__all__``-Kurzform: ein ``read-all``/``write-all``-Grant
    deckt jeden konkreten Scope bis zu seinem Level ab.
    """
    all_granted = granted.get(_ALL_SCOPES, 0)
    missing: dict[str, int] = {}
    for scope, needed in required.items():
        have = all_granted if scope == _ALL_SCOPES else max(
            granted.get(scope, 0), all_granted
        )
        if have < needed:
            missing[scope] = needed
    return missing


def _declares_workflow_call(doc: dict) -> bool:
    """Ob *doc* als wiederverwendbarer Workflow aufrufbar ist (``on.workflow_call``).

    PyYAML (YAML 1.1) liest den ``on``-Key als Boolean ``True`` – beide Lesarten
    werden abgedeckt, ebenso die String-/Listen-Kurzformen von ``on``.
    """
    on = doc.get(True, doc.get("on"))
    if isinstance(on, dict):
        return "workflow_call" in on
    if isinstance(on, list):
        return "workflow_call" in on
    return on == "workflow_call"


def _workflow_files() -> list[Path]:
    """Alle Workflow-Dateien – GitHub akzeptiert ``.yml`` UND ``.yaml``."""
    workflow_dir = _ROOT / ".github" / "workflows"
    return sorted([*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")])


def test_reusable_workflow_callers_grant_all_required_permissions() -> None:
    """Jeder lokale Reusable-Workflow-Caller gewährt JEDE vom aufgerufenen
    Workflow deklarierte Permission mindestens gleichwertig (#309).

    Deckt den OIDC-Fall ab (ci.yml ``id-token: write`` ⇒ Release-``test``-Job
    muss es gewähren) und ist selbst-validierend: entfernt man ``id-token`` aus
    dem Release-``test``-Job, wird dieser Test rot. Prüft zusätzlich, dass der
    aufgerufene Workflow überhaupt ``workflow_call`` deklariert – fehlt das,
    lehnt GitHub den Run ebenfalls beim Start ab.
    """
    yaml = pytest.importorskip("yaml")
    checked = 0
    for caller_path in _workflow_files():
        caller_doc = yaml.safe_load(caller_path.read_text(encoding="utf-8"))
        if not isinstance(caller_doc, dict):
            continue
        for job_name, job in (caller_doc.get("jobs") or {}).items():
            if not isinstance(job, dict):
                continue
            uses = job.get("uses")
            if not (isinstance(uses, str) and uses.startswith("./.github/workflows/")):
                continue
            called_path = _ROOT / uses.removeprefix("./")
            assert called_path.is_file(), (
                f"{caller_path.name}: Job '{job_name}' ruft fehlenden Workflow "
                f"{uses} auf."
            )
            called_doc = yaml.safe_load(called_path.read_text(encoding="utf-8"))
            assert _declares_workflow_call(called_doc), (
                f"{caller_path.name}: Job '{job_name}' ruft {called_path.name} auf, "
                f"das kein 'on: workflow_call' deklariert – GitHub bricht den Run "
                f"beim Start ab (startup_failure, #309)."
            )
            missing = _missing_grants(
                _required_permissions(called_doc),
                _granted_permissions(job, caller_doc),
            )
            pretty = {scope: _LEVEL_NAMES[lvl] for scope, lvl in missing.items()}
            assert not missing, (
                f"{caller_path.name}: Job '{job_name}' (uses: {called_path.name}) "
                f"gewährt nicht alle vom aufgerufenen Workflow verlangten "
                f"Permissions. Fehlend (scope→min): {pretty}. Ein aufgerufener "
                f"Workflow darf nicht mehr Rechte verlangen als der Aufrufer, sonst "
                f"startet der Run gar nicht (startup_failure, #309)."
            )
            checked += 1
    assert checked, (
        "kein lokaler Reusable-Workflow-Caller gefunden – Guard wirkungslos? "
        "(erwartet mind. release-linux.yml → ci.yml)"
    )


def test_permission_helpers_honor_all_shorthands_and_workflow_call() -> None:
    """Schützt die Sonderfälle des Guards: ``read-all``/``write-all`` und die
    ``workflow_call``-Erkennung in den üblichen ``on``-Schreibweisen."""
    # read-all deckt geforderte read-Scopes, aber kein write.
    read_all = _granted_permissions({"permissions": "read-all"}, {})
    assert _missing_grants({"contents": 1, "id-token": 2}, read_all) == {"id-token": 2}
    # write-all deckt alles.
    write_all = _granted_permissions({"permissions": "write-all"}, {})
    assert _missing_grants({"contents": 2}, write_all) == {}
    # workflow_call-Erkennung (PyYAML-True-Key, Listen-, String- und Dict-on).
    assert _declares_workflow_call({True: {"workflow_call": None}})
    assert _declares_workflow_call({"on": ["workflow_call"]})
    assert _declares_workflow_call({"on": "workflow_call"})
    assert not _declares_workflow_call({"on": {"push": None}})


# ── #318: effektiv-per-Job statt Top-Level∪Job-Vereinigung ──────────────
#
# GitHub validiert den startup einer workflow_call-Kette je *nested job* gegen
# dessen effektiv angeforderte Rechte (Job-Level ersetzt Top-Level, sonst
# Erben). Ein Top-Level-Recht, das JEDER Job weg-überschreibt, wird effektiv
# nicht angefordert – der Guard darf es dann nicht einfordern (kein False
# Positive gegen legitime Per-Job-Härtung). Beleg der Semantik: github/gh-aw
# #21071 (reale Meldung „The nested job 'X' is requesting …, but is only
# allowed …").


def test_required_permissions_covers_inherited_top_level_oidc_case() -> None:
    """OIDC-Fall (#303): Top-Level ``id-token: write`` + Job ohne eigenen Block
    ⇒ der Job erbt das Recht, es bleibt „verlangt". So bleibt der Guard rot,
    wenn ein Caller ``id-token`` nicht durchreicht."""
    ci_like = {
        "permissions": {"contents": "read", "id-token": "write"},
        "jobs": {"test": {"runs-on": "ubuntu-latest"}},  # kein eigener Block → erbt
    }
    assert _required_permissions(ci_like) == {"contents": 1, "id-token": 2}


def test_required_permissions_ignores_top_level_scope_every_job_overrides() -> None:
    """Kein False Positive (#318): Ein Top-Level-Recht, das JEDER Job per
    eigenem ``permissions``-Block weg-überschreibt, wird effektiv nicht
    angefordert – der Guard darf es nicht als „verlangt" werten."""
    doc = {
        "permissions": {"contents": "read", "id-token": "write"},
        "jobs": {
            "a": {"permissions": {"contents": "read"}},  # id-token weg-überschrieben
            "b": {"permissions": {"contents": "read"}},
        },
    }
    required = _required_permissions(doc)
    assert "id-token" not in required, required
    assert required == {"contents": 1}
    # Verglichen mit einem Caller, der nur contents:read gewährt: kein Fehlbetrag.
    assert _missing_grants(required, {"contents": 1}) == {}


def test_required_permissions_takes_max_effective_across_jobs() -> None:
    """Ein Job, der ein Recht behält/anfordert, genügt – maximiert über Jobs.
    Ein leerer Block (``{}``) überschreibt bewusst auf „nichts"."""
    doc = {
        "permissions": {"contents": "read"},
        "jobs": {
            "keeps": {"permissions": {"contents": "read", "id-token": "write"}},
            "drops": {"permissions": {}},  # leerer Block → nichts
        },
    }
    assert _required_permissions(doc) == {"contents": 1, "id-token": 2}

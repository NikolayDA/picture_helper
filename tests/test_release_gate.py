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
_PUBLISH = _ROOT / ".github" / "workflows" / "release-publish.yml"


def _ci_text() -> str:
    return _CI.read_text(encoding="utf-8")


def _release_text() -> str:
    return _RELEASE.read_text(encoding="utf-8")


def _publish_text() -> str:
    return _PUBLISH.read_text(encoding="utf-8")


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


def test_candidate_build_is_gated_and_publish_is_separate() -> None:
    text = _release_text()
    assert re.search(r"(?m)^\s*needs:\s*\[[^\]]*\btest\b[^\]]*\]", text), (
        "build muss per needs auf die Full-CI-Matrix (test) warten."
    )
    assert re.search(r"(?m)^\s*needs:\s*\[[^\]]*\bverify-candidate\b[^\]]*\]", text), (
        "build muss per needs auf verify-candidate warten."
    )
    assert "\n  publish:" not in text
    assert _PUBLISH.is_file()
    assert "packaging/linux/build_appimage.sh" not in _publish_text()
    assert "packaging/mac/build_macos.sh" not in _publish_text()


def test_release_does_not_swallow_gh_errors() -> None:
    assert "|| true" not in _publish_text(), (
        "Fehler von gh release dürfen nicht pauschal mit '|| true' verborgen "
        "werden (#250)."
    )


def test_clamav_scans_extracted_payload_and_rejects_zero_byte_evidence() -> None:
    """#731: ``clamscan dist`` allein übersieht große/komprimierte Nutzdaten.

    Der Release-Workflow muss deshalb den Artefaktscanner verwenden, der alle
    Pakettypen entpackt, ClamAV auf Rohdatei und Nutzdaten ansetzt und einen
    0-Byte-Lauf als Fehler behandelt.
    """
    text = _release_text()
    assert (
        "python3 scripts/scan_release_artifacts.py "
        "--clamav-database clamav-db-cache dist"
    ) in text
    assert "clamscan --database clamav-db-cache --recursive --infected --stdout dist" not in text


def test_clamav_cache_miss_keeps_secret_scan_and_visible_unavailable_state() -> None:
    """MALWARE-01 bleibt bei Cache-Miss optional, #584 bleibt verbindlich."""
    text = _release_text()
    step = text[text.index("Scan built artifacts and extracted payloads") :]
    cache_miss = step[:step.index('version_line="$(clamscan')]
    assert "python3 scripts/scan_release_artifacts.py dist" in cache_miss
    assert "ClamAV-Signaturdatenbank UNAVAILABLE" in cache_miss
    assert cache_miss.index("python3 scripts/scan_release_artifacts.py dist") < cache_miss.index(
        "exit 0"
    )


def test_release_handles_existing_release_explicitly() -> None:
    text = _publish_text()
    assert "gh release view" in text, (
        "Ein bereits existierendes Release muss explizit erkannt werden "
        "(statt '|| true')."
    )
    assert "gh release create" in text
    assert "gh release upload" in text
    assert "plan-publish" in text
    assert "--clobber" not in text


def test_release_verifies_tag_matches_project_version() -> None:
    text = _publish_text()
    assert "RELEASE_TAG" in text
    assert "verify-approval" in text
    assert "expected_tag" in (_ROOT / "scripts" / "release_contract.py").read_text(
        encoding="utf-8"
    )
    assert r"v[0-9]+\.[0-9]+\.[0-9]+" in text, "Tag-Format vX.Y.Z wird geprüft."


def test_release_freeze_gate_runs_for_manual_dispatch_too() -> None:
    """#742: Jeder manuelle Kandidatenbau nutzt den abgeleiteten Vertrag."""
    text = _release_text()
    step_start = text.index("Release-Freeze-Gate und Provenienz")
    next_step = text.index("\n  test:", step_start)
    step_text = text[step_start:next_step]
    assert "verify_release_freeze.py" in step_text
    assert "--output-provenance release-evidence/release-freeze-provenance.json" in step_text
    assert "release-freeze-provenance-${{ github.run_attempt }}" in step_text
    assert "--require-pin" not in step_text
    assert "startsWith(github.ref" not in step_text
    assert "\n  push:" not in text


def test_build_logs_product_provenance() -> None:
    """#685: Jedes Kandidatenartefakt muss im Build-Log Produktversion,
    Commit-SHA und Workflow-/Run-ID ausweisen, damit alle fuenf Artefakte
    nachweislich aus demselben Commit stammen."""
    text = _release_text()
    assert "GITHUB_SHA" in text
    assert "GITHUB_RUN_ID" in text
    assert "GITHUB_WORKFLOW" in text
    assert 'project_version="$(python -c \'import tomllib' in text


def test_freeze_gate_has_no_self_referential_pin_contract() -> None:
    """#742: Weder Pin noch manueller Ledger duerfen wiederkehren."""
    text = _release_text()
    assert "--require-pin" not in text
    assert "Protokollierter Kandidaten-SHA" not in text
    assert "release-freeze-provenance" in text


def test_build_logs_actual_bundler_versions_not_only_runner_pip() -> None:
    """#709-Review: build_appimage.sh/build_macos.sh installieren die
    tatsaechlich verwendeten, unversionierten Bundler (``build``/
    ``python-appimage`` bzw. ``pyinstaller``) in eine isolierte ``toolenv``-
    venv, nicht in die vom Runner bereitgestellte Umgebung. Ein reines
    ``pip --version`` auf Runner-Ebene weist also nicht die Toolchain nach,
    die die Artefakte tatsaechlich baut."""
    text = _release_text()
    assert 'toolenv="build/appimage/toolenv"' in text
    assert re.search(r"toolenv/bin/pip.*python-appimage", text) or (
        "build/appimage/toolenv/bin/pip" in text and "python-appimage" in text
    )
    assert 'toolenv="build/macos/toolenv"' in text
    assert "pyinstaller" in text.split('toolenv="build/macos/toolenv"')[1][:400]


def test_release_runs_real_deb_install_start_remove_cycle() -> None:
    """#584 (Codex-Review auf PR #608): ein reales ``.deb`` muss ueber den
    echten Paketmanager installiert, gestartet und wieder entfernt werden –
    reine ``dpkg-deb --info/--contents``-Introspektion (statisch) beweist
    keinen funktionierenden Install-/Remove-Zyklus (z. B. kaputte Depends-
    Aufloesung oder falsche Pfade waeren damit unsichtbar)."""
    text = _release_text()
    assert re.search(r"apt-get install -y \"\./\$deb\"", text), (
        "Das gebaute .deb muss ueber 'apt-get install ./*.deb' installiert "
        "werden (loest Depends: libfuse2|libfuse2t64 aus den Runner-Repos "
        "auf), nicht nur mit dpkg-deb inspiziert."
    )
    assert "dpkg -r bgremover" in text, (
        "Nach dem Install-Smoke muss das Paket auch real entfernt werden "
        "(dpkg -r), um einen echten Install/Remove-Zyklus zu belegen."
    )
    assert '/opt/BgRemover/BgRemover.AppImage' in text, (
        "Der Installationspfad des gewrappten AppImage muss nach Install "
        "und nach Remove ueberprueft werden."
    )


def test_publish_is_dispatch_only_and_verifies_existing_tag_head() -> None:
    text = _publish_text()
    assert "workflow_dispatch:" in text
    assert "\n  push:" not in text
    assert 'rev-parse --verify "refs/tags/${RELEASE_TAG}^{commit}"' in text
    assert "--tag-sha" in text



# ── Tag im Publish-Workflow (#919, Stufe 1) ────────────────────────────

def test_tag_creation_is_opt_in_and_off_by_default() -> None:
    """Der bestehende manuelle Tag-Weg bleibt gueltig (#919, Stufe 1)."""
    doc = _load(_PUBLISH)
    create_tag = doc[True]["workflow_dispatch"]["inputs"]["create_tag"]
    assert create_tag["type"] == "boolean"
    assert create_tag["default"] is False, "create_tag muss standardmaessig aus sein"


def test_tag_is_created_only_after_the_full_approval_check() -> None:
    """Reihenfolge ist die Zusicherung: erst Manifestpruefung, dann Tag.

    Entstuende der Tag vorher, zeigte er auf einen Commit, den noch nichts
    gegen das Freigabemanifest gebunden hat. Und er muss **vor** dem
    candidate-source-Checkout entstehen, weil dessen ``fetch-depth: 0`` ihn
    mitbringt und die bestehende Tag-Verifikation sonst ins Leere liefe.
    """
    steps = _load(_PUBLISH)["jobs"]["publish"]["steps"]
    names = [str(step.get("name") or step.get("uses") or "") for step in steps]
    approval = next(i for i, n in enumerate(names) if n.startswith("Manifest, Workflows"))
    creation = next(i for i, n in enumerate(names) if n.startswith("Release-Tag anlegen"))
    checkout = next(i for i, n in enumerate(names) if n.startswith("Kandidaten-Commit fuer"))
    verify = next(i for i, n in enumerate(names) if n.startswith("Tag muss auf exakt"))
    assert approval < creation < checkout < verify, names

    step = steps[creation]
    assert step["if"] == "inputs.create_tag"
    # Sollwert ausschliesslich aus der Manifestpruefung, nie aus einem Input.
    assert step["env"]["CANDIDATE_SHA"] == "${{ steps.approval.outputs.candidate_sha }}"
    assert "inputs.tag" not in str(step.get("env"))


def test_tag_creation_asks_the_contract_and_creates_an_annotated_tag() -> None:
    run = next(
        step["run"] for step in _load(_PUBLISH)["jobs"]["publish"]["steps"]
        if str(step.get("name") or "").startswith("Release-Tag anlegen")
    )
    # Die Entscheidung faellt netzfrei im Vertrag, nicht im Shell.
    assert "release_contract.py plan-tag" in run
    # matching-refs statt git/ref: immer HTTP 200, leere Liste = Tag fehlt.
    assert "git/matching-refs/tags/" in run
    assert "git/ref/tags/" not in run, "404-Sonderfall gehoert nicht in den Shell"
    # Annotiert wie in Runbook-Schritt 7: Tag-Objekt, dann Ref darauf.
    assert 'gh api "repos/${GITHUB_REPOSITORY}/git/tags"' in run
    assert "-f type=commit" in run
    # Kein Verschieben: weder force noch delete auf dem Tag-Ref.
    assert "--method PATCH" not in run and "--method DELETE" not in run
    assert "-X DELETE" not in run


def test_publish_keeps_verifying_the_tag_even_when_it_created_it() -> None:
    """Die Anlage ersetzt die Verifikation nicht - sie kommt zusaetzlich.

    Ohne diesen Waechter koennte ein spaeterer Umbau die Tag-Pruefung als
    "schon durch die Anlage erledigt" streichen; dann faenge nichts mehr einen
    Tag ab, der zwischen Anlage und Upload bewegt wurde.
    """
    verify = next(
        step for step in _load(_PUBLISH)["jobs"]["publish"]["steps"]
        if str(step.get("name") or "").startswith("Tag muss auf exakt")
    )
    assert "if" not in verify, "Die Tag-Verifikation darf nicht an create_tag haengen"
    assert 'rev-parse --verify "refs/tags/${RELEASE_TAG}^{commit}"' in verify["run"]


# ── Update-Dispatch und Release-Instanz (#919, Stufen 2 und 3) ─────────

_ABNAHME = _ROOT / ".github" / "workflows" / "release-abnahme.yml"


def test_instance_job_runs_before_the_dispatch_that_consumes_it() -> None:
    """Der Abnahme-Lauf laedt die Instanz aus dem Publish-Lauf.

    Liefe der Dispatch zuerst, koennte der Abnahme-Lauf das Artefakt suchen,
    bevor es existiert - ein Wettlauf, den keine Wiederholung heilt.
    """
    jobs = _load(_PUBLISH)["jobs"]
    assert "release-instance" in _needs_list(jobs["update-dispatch"])
    assert set(_needs_list(jobs["release-instance"])) == {"publish", "public-download"}


def test_only_the_dispatch_job_may_start_workflows() -> None:
    """`actions: write` ist das einzige neue Schreibrecht - und liegt genau
    dort, wo es gebraucht wird. Der publish-Job bleibt bei contents/actions."""
    jobs = _load(_PUBLISH)["jobs"]
    assert jobs["update-dispatch"]["permissions"]["actions"] == "write"
    for name in ("publish", "public-download", "release-instance"):
        assert jobs[name]["permissions"].get("actions") in (None, "read"), name
    # Der Job, der den Release mutiert, darf weiterhin nicht kommentieren.
    assert "issues" not in jobs["publish"]["permissions"]


def test_predecessor_is_an_explicit_input_and_never_guessed() -> None:
    doc = _load(_PUBLISH)
    predecessor = doc[True]["workflow_dispatch"]["inputs"]["predecessor_tag"]
    assert predecessor["default"] == ""
    text = _publish_text()
    # /releases/latest waere durch Backfills und Pre-Releases verfaelschbar.
    assert "releases/latest" not in text


def test_dispatch_uses_the_verified_tag_as_ref_and_the_contract_script() -> None:
    run = next(
        step["run"] for step in _load(_PUBLISH)["jobs"]["update-dispatch"]["steps"]
        if str(step.get("name") or "").startswith("Abnahme-Lauf idempotent")
    )
    assert "release_update_dispatch.py" in run
    assert '--ref "$RELEASE_TAG"' in run
    assert "--publish-run-id" in run and "--predecessor-tag" in run


def test_acceptance_run_name_carries_the_correlation_marker() -> None:
    """Ohne Marker im run-name bliebe der ausgeloeste Lauf unauffindbar:
    workflow_dispatch antwortet mit HTTP 204 ohne Run-ID."""
    doc = _load(_ABNAHME)
    assert "inputs.dispatch_marker" in doc["run-name"]
    inputs = doc[True]["workflow_dispatch"]["inputs"]
    assert inputs["dispatch_marker"]["default"] == ""
    assert inputs["publish_run_id"]["default"] == ""


def test_final_instance_steps_are_gated_on_the_publish_run_id() -> None:
    """Ein manueller Abnahme-Lauf ohne publish_run_id bleibt unveraendert."""
    steps = [
        step for step in _load(_ABNAHME)["jobs"]["aggregation"]["steps"]
        if "Release-Instanz" in str(step.get("name") or "")
        or "Post-Release-Kriterien" in str(step.get("name") or "")
    ]
    assert len(steps) == 5, [s.get("name") for s in steps]
    for step in steps:
        assert "inputs.publish_run_id != ''" in str(step["if"]), step.get("name")


def test_final_instance_survives_a_blocking_validation() -> None:
    """Ein FAIL ist genau der Fall, in dem die Instanz gebraucht wird.

    Die Validierung laeuft im Skript nach dem Schreiben; Sicherung, Rendering
    und Kommentar haengen an !cancelled(), nicht an success().
    """
    steps = {
        str(step.get("name") or ""): step
        for step in _load(_ABNAHME)["jobs"]["aggregation"]["steps"]
    }
    for name in (
        "Finale Release-Instanz sichern und rendern",
        "Finale Release-Instanz als Actions-Artefakt sichern",
        "Finale Release-Instanz als Issue-Kommentar posten",
    ):
        assert "!cancelled()" in str(steps[name]["if"]), name

    finalize = steps["Post-Release-Kriterien nachtragen und bis post-release validieren"]
    assert "finalize-instance" in finalize["run"]
    # Erst nach dem Nachtrag darf bis post-release validiert werden. Geprueft
    # werden Kommandozeilen, nicht Kommentare - die duerfen die Phase nennen.
    publish_commands = [
        line for step in _load(_PUBLISH)["jobs"].values()
        for entry in step["steps"] if "run" in entry
        for line in entry["run"].splitlines()
        if not line.lstrip().startswith("#")
    ]
    assert not [line for line in publish_commands if "--through-phase post-release" in line], (
        "Der Publish-Lauf kann post-release nicht validieren - die "
        "Update-Kriterien sind dort noch PENDING."
    )
    assert any("--through-phase publish" in line for line in publish_commands)


def test_publish_instance_job_pins_the_candidate_checklist() -> None:
    """set-criterion vergleicht den Checklisten-Dateihash gegen den Pin.

    Nimmt der Job die Checkliste des Workflow-Checkouts statt die des
    Kandidaten, bricht die Pflege, sobald die Checkliste auf main weiterzieht.
    """
    steps = _load(_PUBLISH)["jobs"]["release-instance"]["steps"]
    run = next(
        step["run"] for step in steps
        if str(step.get("name") or "").startswith("Publish-Pflichten mit den")
    )
    assert 'checklist="candidate-source/docs/RELEASE_ACCEPTANCE_CHECKLIST.md"' in run
    assert any(
        step.get("with", {}).get("path") == "candidate-source"
        and "candidate_sha" in str(step.get("with", {}).get("ref"))
        for step in steps
    ), "Der Kandidaten-Checkout fehlt"

# ── Release-Follow-ups (#257) ──────────────────────────────────────────

def test_test_job_requires_verify_candidate() -> None:
    """Der wiederverwendbare Test-Job wartet auf die Kandidatenprovenienz."""
    assert re.search(r"(?m)^\s*needs:\s*verify-candidate\b", _release_text()), (
        "test (uses: ci.yml) muss per needs auf verify-candidate warten."
    )


def test_publish_provides_repo_context_for_gh() -> None:
    assert "GH_REPO: ${{ github.repository }}" in _publish_text(), (
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
    text = _publish_text()
    assert "run-id: ${{ inputs.candidate_run_id }}" in text
    assert "run-id: ${{ inputs.acceptance_run_id }}" in text
    assert "github-token: ${{ github.token }}" in text, (
        "download-artifact per run-id braucht ein github-token."
    )
    assert re.search(r"(?m)^\s*actions:\s*read\b", text), (
        "Der Publish-Job braucht actions: read für den API-Download per run-id."
    )


# ── #916: anonymer Öffentlichkeitsnachweis PUBLIC-DOWNLOAD-01 ──────────


def test_public_download_proof_runs_after_the_release_is_public() -> None:
    """Ein Draft-Asset ist anonym nicht erreichbar – der Nachweis muss deshalb
    ein eigener, dem publish-Job nachgelagerter Job sein. Liefe er im
    publish-Job, könnte er nur den authentifizierten Draft-Pfad belegen (#916).
    """
    jobs = _load(_PUBLISH)["jobs"]
    assert "public-download" in jobs, jobs.keys()
    proof = jobs["public-download"]
    assert _needs_list(proof) == ["publish"], proof.get("needs")
    assert "public_download_check.py" in _publish_text()


def test_only_the_proof_job_may_comment_and_publish_keeps_least_privilege() -> None:
    jobs = _load(_PUBLISH)["jobs"]
    proof_perms = jobs["public-download"].get("permissions", {})
    publish_perms = jobs["publish"].get("permissions", {})
    assert proof_perms.get("issues") == "write", proof_perms
    assert proof_perms.get("contents") == "read", proof_perms
    assert "issues" not in publish_perms, publish_perms
    assert publish_perms.get("contents") == "write", publish_perms


def _proof_steps() -> list[dict]:
    return list(_load(_PUBLISH)["jobs"]["public-download"]["steps"])


def test_anonymous_download_step_carries_no_github_token() -> None:
    """Der Nachweis ist wertlos, wenn ein Token mitläuft: weder Job- noch
    Schritt-Environment dürfen eines tragen, und das Skript prüft es selbst."""
    job = _load(_PUBLISH)["jobs"]["public-download"]
    assert "GH_TOKEN" not in job.get("env", {})
    assert "GITHUB_TOKEN" not in job.get("env", {})
    download = [
        step for step in _proof_steps() if "public_download_check.py" in str(step.get("run", ""))
    ]
    assert len(download) == 1, download
    assert "GH_TOKEN" not in download[0].get("env", {})
    assert 'if [ -n "${GH_TOKEN:-}" ] || [ -n "${GITHUB_TOKEN:-}" ]; then' in download[0]["run"]


def test_proof_verdict_uses_the_same_contract_gate_as_the_upload() -> None:
    """Sollwertquelle bleibt das Freigabemanifest, nicht der GitHub-Digest."""
    runs = "\n".join(str(step.get("run", "")) for step in _proof_steps())
    assert "release_contract.py verify-artifacts" in runs
    assert "release_contract.py verify-approval" in runs
    assert "$DOWNLOAD_DIR" in runs


def test_proof_is_archived_ninety_days_and_rendered_as_summary() -> None:
    steps = _proof_steps()
    uploads = [step for step in steps if "upload-artifact" in str(step.get("uses", ""))]
    assert len(uploads) == 1, uploads
    with_ = uploads[0]["with"]
    assert with_["name"] == "public-download-report-${{ github.run_attempt }}"
    assert with_["retention-days"] == 90
    assert any("GITHUB_STEP_SUMMARY" in str(step.get("run", "")) for step in steps)


def test_proof_comment_is_opt_in_and_also_posted_on_failure() -> None:
    comment = [
        step for step in _proof_steps() if "gh issue comment" in str(step.get("run", ""))
    ]
    assert len(comment) == 1, comment
    condition = str(comment[0].get("if", ""))
    assert "inputs.target_issue != ''" in condition
    # Ein gescheiterter Nachweis gehoert sichtbar ins Release-Issue.
    assert "!cancelled()" in condition
    doc = _load(_PUBLISH)
    inputs = doc.get(True, doc.get("on"))["workflow_dispatch"]["inputs"]
    assert inputs["target_issue"].get("required") is not True
    assert inputs["target_issue"].get("default") == ""


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
    text = _publish_text()
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
    text = _publish_text()
    assert "gh release edit \"$RELEASE_TAG\"" in text
    assert '--notes-file "${RUNNER_TEMP}/release-notes.md"' in text


def test_release_reuse_blocks_partial_or_divergent_state() -> None:
    text = _publish_text()
    contract = (_ROOT / "scripts" / "release_contract.py").read_text(encoding="utf-8")
    assert "plan-publish" in text
    assert "--clobber" not in text
    assert "gh release delete-asset" not in text
    assert "keine automatische Aenderung" in contract
    assert "--draft" in text
    assert "published-verification" in text


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

def test_release_jobgraph_separates_build_from_publish() -> None:
    jobs = _load(_RELEASE)["jobs"]

    # Die Full-CI-Matrix wird als wiederverwendbarer Workflow aufgerufen.
    assert jobs["test"].get("uses") == "./.github/workflows/ci.yml"

    assert "verify-candidate" in _needs_list(jobs["test"]), jobs["test"].get("needs")

    # #303: ci.yml fordert id-token: write (Codecov-OIDC). Der aufrufende
    # test-Job muss dieses Recht durchreichen, sonst lehnt GitHub den Run beim
    # Start ab (ein aufgerufener Workflow darf nicht mehr Rechte verlangen als
    # der Aufrufer).
    assert jobs["test"].get("permissions", {}).get("id-token") == "write", (
        jobs["test"].get("permissions")
    )

    # build hängt sowohl an der Matrix als auch an der Kandidatenprovenienz.
    build_needs = _needs_list(jobs["build"])
    assert "test" in build_needs, build_needs
    assert "verify-candidate" in build_needs, build_needs
    assert "publish" not in jobs

    publish_doc = _load(_PUBLISH)
    publish = publish_doc["jobs"]["publish"]
    perms = publish.get("permissions", {})
    assert perms.get("contents") == "write", perms
    assert perms.get("actions") == "read", perms
    assert publish.get("env", {}).get("GH_REPO") == "${{ github.repository }}"
    downloads = [
        step.get("with", {}) for step in publish["steps"]
        if "download-artifact" in str(step.get("uses", ""))
    ]
    assert any(item.get("run-id") == "${{ inputs.acceptance_run_id }}" for item in downloads)
    assert any(item.get("run-id") == "${{ inputs.candidate_run_id }}" for item in downloads)
    assert all(item.get("github-token") == "${{ github.token }}" for item in downloads)


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

"""Regression contracts for the canonical release documentation (#737/#745/#746)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from scripts import release_contract as rc

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
RUNBOOK = (ROOT / "docs" / "RELEASE_PROCESS.md").read_text(encoding="utf-8")
CHECKLIST = (ROOT / "docs" / "RELEASE_ACCEPTANCE_CHECKLIST.md").read_text(encoding="utf-8")
#: CLAUDE.md fuehrt die UML-Zeichnung als Darstellung derselben vier Ablaeufe.
#: Sie ist damit eine handgepflegte Kopie des Runbooks und braucht denselben
#: Waechter - sonst wandert der Widerspruch in die Hand des Operators.
PROCESS_UML = (ROOT / "docs" / "PROZESSE_UML.md").read_text(encoding="utf-8")


def test_claude_has_sources_instead_of_manual_release_state() -> None:
    assert "Letzter **veröffentlichter** Release" not in CLAUDE
    assert not re.search(r"(?i)aktueller\s+versionsschnitt.{0,80}\d+\.\d+\.\d+", CLAUDE)
    assert not re.search(r"(?i)(?:letzter\s+release-stand|aktuell)\D{0,30}v?\d+\.\d+\.\d+", CLAUDE)
    assert "project.version" in CLAUDE
    assert "docs/RELEASE_PROCESS.md" in CLAUDE
    assert "docs/RELEASE_ACCEPTANCE_CHECKLIST.md" in CLAUDE
    assert "github.com/NikolayDA/picture_helper/releases" in CLAUDE


def test_runbook_has_nine_complete_steps_and_operational_paths() -> None:
    steps = re.split(r"(?m)^### [1-9]\. ", RUNBOOK)[1:]
    assert len(steps) == 9
    for step in steps:
        for field in (
            "**Trigger:**",
            "**Owner:**",
            "**Input:**",
            "**Output/Evidenz:**",
            "**Erwartetes Ergebnis:**",
            "**Fehler/Wiederanlauf:**",
        ):
            assert field in step
    for required in (
        "## Hotfix-Pfad",
        "## Rollback, Yank und Teilzustände",
        "## Wiederanlaufmatrix",
        "## Eskalation und Waiver",
        "RELEASE_ACCEPTANCE_CHECKLIST.md",
        "ADR-2026-release-manifest-publish.md",
        "PUBLIC-DOWNLOAD-01",
        # Seit #917 zwei getrennte Plattform-IDs statt des gemeinsamen
        # UPDATE-01 – die alte ID darf hier nicht als Treffer durchgehen
        # (der Aenderungsverlauf nennt sie weiterhin).
        "UPDATE-LINUX-ARM-01",
        "UPDATE-MACOS-ARM-01",
    ):
        assert required in RUNBOOK


def test_runbook_names_all_release_workflows_and_dispatch_inputs() -> None:
    for workflow in ("release-linux.yml", "release-abnahme.yml", "release-publish.yml"):
        assert workflow in RUNBOOK
    for input_name in (
        "with_ai",
        "run_id",
        "platforms",
        "dry_run",
        "target_issue",
        "tag",
        "candidate_run_id",
        "acceptance_run_id",
        "approval_artifact_name",
    ):
        assert re.search(rf"(?:-f |`){input_name}(?:=|`)", RUNBOOK), input_name


def test_public_download_requires_separate_anonymous_evidence() -> None:
    assert "ohne GitHub-Anmeldung" in RUNBOOK
    assert "URL_DES_ANONYMEN_DOWNLOAD_UND_HASH_PROTOKOLLS" in RUNBOOK
    assert "PUBLISH-03 PUBLIC-DOWNLOAD-01" not in RUNBOOK
    public_command = RUNBOOK.split("--criterion PUBLIC-DOWNLOAD-01", maxsplit=1)[1]
    public_command = public_command.split("python scripts/release_contract.py", maxsplit=1)[0]
    assert '--evidence "$PUBLIC_DOWNLOAD_EVIDENCE_URL"' in public_command


def test_public_download_evidence_is_automated_with_a_documented_fallback() -> None:
    """#916: Schritt 9 liest den Bericht; die Handprozedur bleibt Rueckfallweg."""
    step_nine = RUNBOOK.split("### 9. ", maxsplit=1)[1].split("## Hotfix-Pfad", maxsplit=1)[0]
    assert "public-download-report.json" in step_nine
    assert "Rückfallweg" in step_nine
    # Der authentifizierte Draft-Download bleibt ausdruecklich kein Nachweis.
    assert "authentifiziert aus dem Draft" in step_nine
    publish = (ROOT / ".github" / "workflows" / "release-publish.yml").read_text(encoding="utf-8")
    assert "public_download_check.py" in publish
    # Ein roter Nachweis ist ein Incident, keine stille Wiederholung.
    assert "Öffentlicher Download-Nachweis rot" in RUNBOOK
    assert "PUBLIC-DOWNLOAD-01" in CHECKLIST


#: Betriebsdokumente, aus denen jemand Kommandos abtippt. Ein Resttreffer der
#: zurueckgezogenen ID ist hier nicht Kosmetik: ``set-criterion --criterion
#: UPDATE-01`` scheitert dann mit "Kriterium fehlt", statt auf die Nachfolger
#: zu zeigen (Review-Befund PR #926).
_OPERATIONAL_DOCS = (
    "CLAUDE.md",
    "docs/RELEASE_PROCESS.md",
    "docs/RELEASE_AUTOMATION.md",
    "docs/RELEASE_ACCEPTANCE_CHECKLIST.md",
    "docs/PACKAGING_SMOKE.md",
    "docs/PROZESSE_UML.md",
)


def test_retired_update_criterion_survives_only_next_to_its_migration_note() -> None:
    """#917: Die stabile ID `UPDATE-01` entfaellt (deshalb der Major-Bump).

    Sie darf in den Betriebsdokumenten nur noch dort stehen, wo auch die
    Migration benannt ist – sonst fuehrt sie jemanden in ein Kommando, das
    fehlschlaegt. Historie unter ``docs/history/`` bleibt unangetastet.
    """
    retired = re.compile(r"(?<![A-Z0-9-])UPDATE-01\b")
    for name in _OPERATIONAL_DOCS:
        for number, line in enumerate((ROOT / name).read_text(encoding="utf-8").splitlines(), 1):
            if retired.search(line):
                assert "#917" in line, f"{name}:{number} nennt UPDATE-01 ohne Migrationshinweis"
    # Die Nachfolger muessen ueberall dort stehen, wo der Ablauf beschrieben ist.
    for name in ("docs/RELEASE_PROCESS.md", "docs/PROZESSE_UML.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "UPDATE-LINUX-ARM-01" in text, name
        assert "UPDATE-MACOS-ARM-01" in text, name


def test_release_runs_on_the_immutable_release_ref_not_on_main() -> None:
    """#918: Ein Release friert `main` nicht mehr ein.

    Alle vier Dispatches laufen auf `release/vX.Y.Z`; die alte
    `MAIN_SHA`-Gleichheitsprüfung (die die Konvention prüfte, nicht die
    Bindung) ist ersatzlos verschwunden.
    """
    # Nur der Prozedurteil zaehlt: Der Aenderungsverlauf darf und soll
    # benennen, was ersetzt wurde (dasselbe Muster wie beim zurueckgezogenen
    # UPDATE-01 in #917).
    procedure = RUNBOOK.split("## Änderungsverlauf", maxsplit=1)[0]
    assert "MAIN_SHA" not in procedure
    # Beide operativen Dokumente, nicht nur das Runbook: Die UML-Zeichnung
    # beschrieb den main-Freeze noch, waehrend das Runbook ihn schon aufgab.
    for name, text in (("RELEASE_PROCESS.md", procedure), ("PROZESSE_UML.md", PROCESS_UML)):
        assert "--ref main" not in text, name
        assert "--branch main" not in text, name
        assert "main zeigt noch auf den Kandidaten" not in text, name
    assert "RELEASE_REF" in PROCESS_UML
    assert "verify-release-ref" in PROCESS_UML
    assert 'RELEASE_REF="release/${RELEASE_TAG}"' in RUNBOOK
    assert (ROOT / "docs" / "history" / "ADR-2026-release-ref-entkopplung.md").is_file()
    assert "ADR-2026-release-ref-entkopplung.md" in RUNBOOK

    dispatches = re.findall(r"gh workflow run (\S+) --ref (\S+)", RUNBOOK)
    assert len(dispatches) == 4, dispatches
    assert {workflow for workflow, _ in dispatches} == {
        "release-linux.yml", "release-abnahme.yml", "release-publish.yml",
    }
    assert {ref for _, ref in dispatches} == {'"$RELEASE_REF"'}


def test_every_dispatch_is_conditional_on_the_ref_check() -> None:
    """Die Prüfung muss den Dispatch **bedingen**, nicht ihm nur vorangehen.

    Der ersetzte `MAIN_SHA`-Block umschloss den Dispatch mit `if/else`, damit
    ein Fehlschlag ihn verhindert, ohne eine interaktive Shell zu beenden.
    Stünde die Prüfung nur davor, liefe der Dispatch in einer Shell ohne
    `set -e` trotz Exit 2 weiter — und genau das war beim Umbau kurzzeitig der
    Fall (auch ein leerer `CANDIDATE_SHA` wäre so durchgerutscht).
    """
    dispatches = [m.start() for m in re.finditer(r"gh workflow run \S+ --ref", RUNBOOK)]
    assert len(dispatches) == 4
    assert RUNBOOK.count("&& gh workflow run") == 4, (
        "jeder Dispatch muss per && an die Ref-Prüfung gekoppelt sein"
    )
    for start in dispatches:
        # Unmittelbar davor die Pruefung, im selben Kommando.
        head = RUNBOOK[:start]
        assert head.rstrip().endswith("&&"), "Dispatch nicht an die Prüfung gekoppelt"
        block_start = head.rfind("```bash")
        assert "verify-release-ref" in head[block_start:], (
            "Ref-Prüfung steht nicht im selben Codeblock wie der Dispatch"
        )
    # Das harte Gate bleibt der SHA-Vergleich in candidate-source.
    assert "candidate-source" in RUNBOOK
    assert "verify-release-ref" in (
        ROOT / "scripts" / "release_contract.py"
    ).read_text(encoding="utf-8")


def test_release_ref_creation_is_guarded_as_strictly_as_the_dispatches() -> None:
    """Auch die **Anlage** des Refs braucht einen Wächter, nicht nur die Dispatches.

    Die Unveränderlichkeit des Refs ist die Grundannahme dieser Entscheidung —
    trägt die Anlage sie nicht, hängt alles Weitere in der Luft. Ein bloß
    vorangestellter Existenz-Guard bindet den `git push` in einer Shell ohne
    `set -e` nicht: gegen ein lokales Remote geprüft, meldete sich der Guard,
    gab `false` zurück, und der Push bewegte den vorhandenen Ref trotzdem per
    Fast-Forward. Dieselbe Falle wie bei den vier Dispatches.
    """
    blocks = re.findall(r"```bash\n(.*?)```", RUNBOOK, flags=re.DOTALL)
    writes = [b for b in blocks if re.search(r"git push[^\n]*(\n[^\n]*)?refs/heads/\$\{RELEASE_REF\}", b)]
    assert len(writes) == 1, f"genau ein schreibender Push auf den Release-Ref erwartet: {len(writes)}"
    creation = writes[0]

    # 1. Existenz wird ueberhaupt geprueft, und zwar mit auswertbarem Exit-Code.
    assert 'git ls-remote --exit-code origin "refs/heads/${RELEASE_REF}"' in creation
    assert "case $?" in creation, "Exit-Code der Existenzpruefung wird nicht ausgewertet"

    # 2. Fail-closed in alle drei Ausgaenge: nur „Ref fehlt" (2) legt an,
    #    „existiert" (0) und jeder andere Ausgang (Netz/Auth, 128) brechen ab.
    arms = dict(re.findall(r"(?ms)^\s*([0-9*]+)\)\s*(.*?);;", creation))
    assert set(arms) == {"2", "0", "*"}, f"unerwartete case-Zweige: {sorted(arms)}"
    assert "git push" in arms["2"]
    for code in ("0", "*"):
        assert "git push" not in arms[code], f"Zweig {code} legt den Ref an"
        assert arms[code].rstrip().endswith("false"), f"Zweig {code} bricht nicht ab"

    # 3. Der Push selbst ist anlege-only: leerer Erwartungswert hinter dem
    #    Doppelpunkt heisst „der Ref darf nicht existieren" — ein vorhandener
    #    Ref liesse sich damit auch bei Fast-Forward nicht still bewegen.
    assert '--force-with-lease="refs/heads/${RELEASE_REF}:"' in arms["2"]


def test_the_ruleset_check_aborts_instead_of_merely_reporting() -> None:
    """#918: Der Schutz des Refs wird **bewertet**, nicht nur ausgegeben.

    Die erste Fassung gab die aktiven Regeltypen per `--jq` aus und überließ
    die Bewertung dem Augenschein — eine leere Liste (gar kein Ruleset) sah
    damit genauso aus wie eine bestandene Prüfung. Der Ref trägt die
    Unveränderlichkeit dieser Entscheidung; ohne erzwungenen Schutz ist er nur
    eine Verabredung.
    """
    procedure = RUNBOOK.split("## Änderungsverlauf", maxsplit=1)[0]
    assert "verify-ref-protection" in procedure
    assert "[.[].type] | sort | unique" not in procedure, "berichtende Altfassung zurück"

    # Die Prüfung bedingt den ersten Dispatch, statt ihm nur voranzugehen —
    # dieselbe Kopplung, die `test_every_dispatch_is_conditional_on_the_ref_check`
    # für die SHA-Prüfung festhält.
    first = procedure.index("gh workflow run release-linux.yml")
    block = procedure[procedure.rfind("```bash", 0, first) : first]
    assert "verify-ref-protection" in block, "Schutzprüfung nicht im Dispatch-Block"
    # Nur Fortsetzungszeilen (Backslash am Zeilenende) bis zum `&&`. Ein
    # bloßes "irgendwo danach steht ein &&" trüge nicht: Der Block endet per
    # Konstruktion direkt vor dem Dispatch und enthält deshalb immer noch das
    # `&&` der *zweiten* Prüfung — die Entkopplung, die dieser Wächter
    # ausschließen soll, bliebe damit grün (#936-Review).
    tail = block[block.index("verify-ref-protection") :]
    assert re.match(r"[^\n]*(?:\\\n[^\n]*)*\s*&&", tail), (
        "Schutzprüfung nicht per && an den Dispatch gekoppelt"
    )


def test_the_documented_ruleset_creates_exactly_the_required_rules() -> None:
    """Handgepflegte Kopie gegen ihre Quelle: Anlage-Rezept vs. Vertrag.

    Ein Rezept, das eine der drei Operationen vergisst, erzeugte ein Ruleset,
    das die eigene Prüfung nie besteht — und zwar erst mitten im Release.
    """
    payload = re.search(r"--input - <<'JSON'\n(.*?)\nJSON", RUNBOOK, flags=re.DOTALL)
    assert payload is not None, "Anlage-Rezept für das Ruleset fehlt im Runbook"
    ruleset = json.loads(payload.group(1))
    assert ruleset["target"] == "branch", "nur Branches tragen diesen Schutz"
    # `evaluate`/`disabled` erscheinen nicht in rules/branches – ein solches
    # Ruleset bestünde die Prüfung nie und schützte auch nichts.
    assert ruleset["enforcement"] == "active"
    assert ruleset["conditions"]["ref_name"]["include"] == ["refs/heads/release/*"]
    assert tuple(sorted(rule["type"] for rule in ruleset["rules"])) == rc.REQUIRED_REF_RULES
    # Rulesets binden anders als Branch-Protection auch Admins. Ohne Bypass
    # scheiterten die beiden Löschwege, die dieses Runbook selbst als
    # Owner-Handgriff vorsieht — der eine davon im Rollback-Moment.
    assert ruleset["bypass_actors"], "ohne Bypass blockiert das Rezept die eigenen Löschwege"


def test_tag_and_release_ref_have_separate_documented_roles() -> None:
    """Beide zeigen auf denselben Commit — genau deshalb braucht es die Rollen.

    Der zurückgebaute Schritt-9-Dispatch lief auf dem Tag statt auf dem Ref und
    fiel niemandem auf: fail-closed blieb er, nur eben aus einer zweiten
    Prozessquelle.
    """
    procedure = RUNBOOK.split("## Änderungsverlauf", maxsplit=1)[0]
    assert "veroeffentlichte Version" in procedure or "veröffentlichte Version" in procedure
    assert "Dispatch- und Wiederanlaufquelle" in procedure
    automation = (ROOT / "docs" / "RELEASE_AUTOMATION.md").read_text(encoding="utf-8")
    assert "Dispatch-Ref ist der Release-**Tag**" not in automation, "Altzustand zurück"


def test_release_workflow_paths_stay_dispatchable_from_the_default_branch() -> None:
    """`workflow_dispatch` braucht die Datei auf dem Default-Branch — auch beim Ref.

    Belegt in der GitHub-Ereignisreferenz: „This event will only trigger a
    workflow run if the workflow file exists on the default branch." Ausgeführt
    wird danach die Definition aus dem gewählten Ref. `main` darf seit #918
    weiterlaufen, aber ein Merge, der eine der drei Release-Workflow-Dateien
    dort umbenennt oder entfernt, blockiert die restlichen Dispatches mitten im
    Release. Dieser Wächter zieht den Fehler in den PR vor, in dem er entsteht.
    """
    dispatched = set(re.findall(r"gh workflow run (\S+\.yml)", RUNBOOK))
    assert dispatched == {"release-linux.yml", "release-abnahme.yml", "release-publish.yml"}
    for name in sorted(dispatched):
        path = ROOT / ".github" / "workflows" / name
        assert path.is_file(), (
            f"{name} fehlt — ohne die Datei auf dem Default-Branch loest kein Dispatch aus"
        )
        assert "workflow_dispatch" in path.read_text(encoding="utf-8"), name

    # Die Voraussetzung ist dokumentiert und hat einen Wiederanlaufweg.
    assert "Default-Branch" in RUNBOOK
    matrix = RUNBOOK.split("## Wiederanlaufmatrix", maxsplit=1)[1].split("## Eskalation", 1)[0]
    assert "Release-Workflow-Dateien" in matrix


def test_recovery_matrix_records_that_main_no_longer_burns_the_candidate() -> None:
    matrix = RUNBOOK.split("## Wiederanlaufmatrix", maxsplit=1)[1].split("## Eskalation", 1)[0]
    assert "Merge nach `main` während eines laufenden Releases" in matrix
    # Die alte Aussage „Jeder Merge nach main verbrennt diesen Kandidaten"
    # darf nirgends mehr unnegiert stehen.
    for line in RUNBOOK.splitlines():
        if "verbrennt" in line:
            assert "nicht" in line, f"unnegierte Freeze-Aussage: {line}"
    # Nachschieben auf den Release-Ref bleibt ausdruecklich unzulaessig.
    assert "nachschieben" in matrix.lower()


def _same_sha_after_repo_fix(rows: list[str]) -> list[str]:
    """Liefert Matrixzeilen, deren zulaessiger Wiederanlauf Same-SHA und Repo-Fix koppelt."""
    offending = []
    for row in rows:
        cells = row.strip().strip("|").split("|")
        assert len(cells) == 3, f"keine dreispaltige Matrixzeile: {row}"
        allowed = cells[1]
        if "demselben SHA" in allowed and "per PR" in allowed:
            offending.append(row)
    return offending


def test_recovery_matrix_never_pairs_same_sha_restart_with_repo_fix() -> None:
    """Ein per PR gemergter Fix wirkt auf dem unveraenderten Kandidaten-SHA nicht:
    Jeder Dispatch fuehrt die Workflow-Definition des Release-Refs aus (#918).
    Eine Matrixzeile, die als zulaessigen Wiederanlauf „per PR beheben" und
    „auf demselben SHA" kombiniert, wiederholte also den urspruenglichen Fehler
    (Codex-Review zu #985, Zeile zu #944). Das Prinzip steht vor der Tabelle,
    und keine Zeile darf es unterlaufen.
    """
    matrix = RUNBOOK.split("## Wiederanlaufmatrix", maxsplit=1)[1].split("## Eskalation", 1)[0]
    assert "außerhalb des Repositorys" in matrix
    assert "$RELEASE_REF" in matrix
    rows = [line for line in matrix.splitlines() if line.startswith("| ") and "---" not in line]
    assert rows[0].startswith("| Störung |")
    assert len(rows) > 10
    assert not _same_sha_after_repo_fix(rows[1:])
    # Negativkontrolle ueber denselben Helfer: die fruehere Zeile zu #944 faellt durch.
    stale_row = (
        "| Artefakt lässt sich im Security-Scan nicht entpacken (#944) "
        "| Ursache in Werkzeug oder Runner-Umgebung per PR beheben, danach "
        "Kandidatenlauf ab Schritt 3 auf demselben SHA "
        "| den `--logs-only`-Ersatzbericht als Scan-Ergebnis werten |"
    )
    assert _same_sha_after_repo_fix([stale_row]) == [stale_row]


def test_secondary_docs_only_point_to_canonical_release_sources() -> None:
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    automation = (ROOT / "docs" / "RELEASE_AUTOMATION.md").read_text(encoding="utf-8")
    packaging = (ROOT / "docs" / "PACKAGING_SMOKE.md").read_text(encoding="utf-8")
    for text in (contributing, automation, packaging):
        assert "RELEASE_PROCESS.md" in text
        assert "RELEASE_ACCEPTANCE_CHECKLIST.md" in text
    assert "attaches it to the GitHub Release on every `v*` tag" not in (
        ROOT / "packaging" / "mac" / "README.md"
    ).read_text(encoding="utf-8")


def test_workflows_create_and_verify_pinned_release_instance() -> None:
    acceptance = (ROOT / ".github" / "workflows" / "release-abnahme.yml").read_text(
        encoding="utf-8"
    )
    publish = (ROOT / ".github" / "workflows" / "release-publish.yml").read_text(encoding="utf-8")
    assert '--checklist "docs/RELEASE_ACCEPTANCE_CHECKLIST.md"' in acceptance
    assert "extract-instance" in acceptance
    assert '--checklist "candidate-source/docs/RELEASE_ACCEPTANCE_CHECKLIST.md"' in publish
    assert "release-checklist-json:start" in CHECKLIST
    assert "release-checklist-json:end" in CHECKLIST


# ── #922: der monatliche Pipeline-Dry-Run in der Prozessdokumentation ───────

AUTOMATION = (ROOT / "docs" / "RELEASE_AUTOMATION.md").read_text(encoding="utf-8")
RELEASE_WORKFLOW = (
    ROOT / ".github" / "workflows" / "release-linux.yml"
).read_text(encoding="utf-8")


def _automation_section(number: str) -> str:
    """Text eines ``## <number>.``-Abschnitts bis zur naechsten gleichen Ebene."""
    head = re.search(rf"(?m)^## {re.escape(number)}\. ", AUTOMATION)
    assert head, f"Abschnitt {number} fehlt in RELEASE_AUTOMATION.md"
    rest = AUTOMATION[head.start() :]
    following = re.search(r"(?m)^## (?!" + re.escape(number) + r"\.)", rest[1:])
    return rest if following is None else rest[: following.start() + 1]


def test_automation_documents_purpose_cost_and_delimitation_of_the_dry_run() -> None:
    section = _automation_section("8")
    for required in (
        "#880",           # Anlass
        "base-tag-missing",
        "WITH_AI=1",      # produktiver Pfad
        "workflow_dispatch",  # bindende Schranke
        "3 Tagen",        # Aufbewahrung
        "Owner: Repository-Owner",
        "Kosten",
        # Die Grenze des Meldewegs steht ausdruecklich dabei: Die
        # Actions-Fehlermail traegt nur den gefallenen Ausgang, nicht "hat
        # nicht stattgefunden" (abgebrochen oder gar nicht gestartet).
        "gh run list --workflow\nrelease-linux.yml --event schedule",
    ):
        assert required in section, required
    # ... und die genannte Ersatzpruefung existiert im Runbook wirklich.
    assert "release-linux.yml --event schedule" in RUNBOOK


def test_documented_dry_run_schedule_matches_the_workflow() -> None:
    """Handgepflegte Kopie gegen ihre Quelle: der Takt steht in zwei Dateien.

    Ohne Waechter bliebe ``make check`` gruen und die Betriebsanleitung
    nennte einen Termin, an dem nichts laeuft - dasselbe Muster wie beim
    Datums-Ausdruck der Lizenzpruefung (#879).
    """
    crons = re.findall(r"(?m)^\s*- cron: '([^']+)'", RELEASE_WORKFLOW)
    assert len(crons) == 1, crons
    minute, hour, day_of_month, _month, _dow = crons[0].split()
    expected = f"am {int(day_of_month)}. um {int(hour):02d}:{int(minute):02d} UTC"
    assert expected in _automation_section("8"), expected


def test_runbook_separates_the_three_meanings_of_dry_run() -> None:
    """Drei Bedeutungen desselben Wortes in einer Prozessdokumentation.

    Der Release-Owner liest sie unter Zeitdruck; ohne ausdrueckliche
    Abgrenzung wird aus "Dry-Run war gruen" schnell die falsche Aussage.
    """
    section = RUNBOOK.split("## Dry-Run und Pflege", 1)[1].split("\n## ", 1)[0]
    for meaning in ("Runbook-Probe", "Pipeline-Dry-Run", "Abnahme ohne Auswertung"):
        assert meaning in section, meaning
    # Schritt 1 verweist auf den geplanten Lauf, damit er vor dem
    # Kandidatenbau ueberhaupt jemand ansieht.
    step_one = RUNBOOK.split("### 1. Release vorbereiten", 1)[1].split("### 2. ", 1)[0]
    assert "release-linux.yml --event schedule" in step_one
    assert "RELEASE_AUTOMATION.md) §8" in step_one

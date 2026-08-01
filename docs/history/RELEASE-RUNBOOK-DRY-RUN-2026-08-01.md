# Release-Runbook-Dry-Run 2026-08-01

**Typ:** lokale, nicht mutierende Prozessprobe
**Owner:** Repository-Owner/Codex
**Geprüfter Stand:** Branch `codex/release-runbook-checklist`
**Ergebnis:** `PASS` für Dokument-, Vertrags- und Wiederanlaufprobe; echte
Workflows, Hardware, Tag und Veröffentlichung bewusst nicht ausgeführt.

## Ziel und Grenzen

Der Dry-Run prüfte das neue `docs/RELEASE_PROCESS.md` erstmals Schritt für
Schritt gegen Workflow-Inputs, Vertragsskript, Tests und lokale Links. Er ist
kein Ersatz für die End-to-End-Abnahme eines Release-Kandidaten. Es wurden
keine GitHub-Workflows gestartet, keine Issues kommentiert, kein Tag erzeugt
und kein Release verändert.

## Durchlauf

| Runbook-Schritt | Probe | Ergebnis/Evidenz |
|---|---|---|
| 1 Vorbereitung | Paketversionsquelle, Checklistenparser und lokale Links geprüft | `project.version` ist kanonisch; Checkliste 1.0.0 gültig |
| 2 Freeze | Befehl und fail-closed Pfad gegen Workflow/Tests gelesen | Kandidat bleibt der vollständige Workflow-Head; kein manueller Pin |
| 3 Build | `release-linux.yml`-Trigger und Input `with_ai` gegen Runbook geprüft | dispatch-only, kein Tag-Trigger, kein Publish |
| 4 Vertrag | Kandidaten-, Artefakt- und Provenienzregeln gegen `release_contract.py` geprüft | exakt fünf Dateien; Manipulationstests blockieren |
| 5 Hardware | Inputs `run_id`, `platforms`, `dry_run`, `target_issue` und Fehlerpfade geprüft | aktive arm64-Plattformen Pflicht; x86_64 bleibt `PENDING` |
| 6 Freigabe | Checkliste geladen, Manifest-/Instanztests und CLI-Verträge ausgeführt | Version, Commit, Dateihash und alle stabilen IDs gebunden |
| 7 Tag | SHA-Gleichheitsprüfung und Tag-Wiederanlauf gelesen | kein Tag im Dry-Run erzeugt; veröffentlichte Tags dürfen nicht verschoben werden |
| 8 Publish | Inputs und Draft-/Teilzustände gegen Workflow und Tests geprüft | kein Neubau, kein Clobber; nur manifestgebundene Bytes |
| 9 Nachlauf | öffentliche Download- und `UPDATE-01`-Evidenzpfade geprüft | bleibt für den echten v2.7.2-Release auszuführen |

## Ausgeführte Prüfungen

```text
python scripts/release_contract.py validate-checklist \
  --checklist docs/RELEASE_ACCEPTANCE_CHECKLIST.md
Ergebnis: Checkliste 1.0.0 ist gültig.

python -m pytest \
  tests/test_release_contract.py \
  tests/test_release_governance.py \
  tests/test_release_gate.py \
  tests/test_release_abnahme_workflow.py \
  tests/test_markdown_links.py \
  tests/test_recommendations_docs.py -q
Ergebnis des ersten Laufs: ein Fehler wegen des noch fehlenden Links auf dieses Protokoll.

Ergebnis nach Korrektur: 74 bestanden, 3 plattformabhängig übersprungen, 0 fehlgeschlagen.
```

## Gefundene und behobene Unklarheiten

1. **Kriterienquelle:** `PACKAGING_SMOKE.md` war zuvor als Quelle der Kriterien
   bezeichnet. Behoben: Die versionierte Checkliste ist kanonisch; Packaging-Smokes
   enthalten nur ausführbare Hardware-Prozeduren.
2. **Prozessduplikat:** `RELEASE_AUTOMATION.md` beschrieb Build und Publish
   zusätzlich. Behoben: Das Dokument verweist für Ablauf und Wiederanlauf auf
   das Runbook und behält nur Runnerbetrieb sowie Jobverhalten.
3. **Release-Stand:** `CLAUDE.md` enthielt manuell gepflegte Versionsnummern.
   Behoben: Paketversion und veröffentlichter Stand werden ausschließlich aus
   `pyproject.toml`, GitHub Releases und Tags abgeleitet.
4. **Plattformpause:** Linux x86_64 konnte als erfüllt missverstanden werden.
   Behoben: getrennte stabile IDs bleiben `PENDING`; Windows ist nicht im Vertrag.
5. **Checklistenbindung:** Eine nur benannte Checkliste wäre nachträglich
   mehrdeutig. Behoben: Jede Release-Instanz pinnt Version, vollständigen
   Kandidaten-Commit und SHA-256 der Datei.
6. **Toter Link:** Der erste Linktest fand den noch fehlenden Link auf dieses
   Dry-Run-Protokoll. Behoben durch Aufnahme dieses versionierten Protokolls;
   die vollständige Prüfsuite wird danach erneut ausgeführt.

## Offene echte Release-Evidenz

- Kandidatenbau und Full CI auf dem späteren v2.7.2-Commit
- Hardware-Abnahme auf macOS arm64 und Linux arm64
- menschliche Screenshot- und Security-Entscheidung
- Tag-/Publish-Lauf, anonymer öffentlicher Download und Bytevergleich
- `UPDATE-01` aus #748 mit einem echten Vorgängerartefakt

Diese Punkte sind nicht `PASS`; sie entstehen erst in der konkreten
Release-Instanz. Der Dry-Run autorisiert keinen Tag und keine Veröffentlichung.

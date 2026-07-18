# ADR (2026-07-18): Hybrides Sicherheitsscan-Modell – CodeQL automatisch, Codex manuell

ADR zu #551 („ci(security): CodeQL automatisieren und Codex Security nur noch
manuell ausführen"). Status: **beschlossen und umgesetzt**.

## Kontext

Der bisherige Codex Security Scan (`.github/workflows/codex-security-scan.yml`)
lief alle 14 Tage automatisch über `schedule` und war damit die einzige
automatisierte SAST-Ebene des Repos. Er hängt an einem `OPENAI_API_KEY` und
dessen Quota (separater Betriebs-Tracker: #245); fällt die Quota aus, läuft
**keine** automatisierte Quellcode-Sicherheitsprüfung mehr – ein automatischer
Scanner schützt nur, wenn er zuverlässig läuft. Gleichzeitig bleibt Codex für
repo-spezifische, semantische Prüfungen wertvoll (Bild-/Projektdatei-Grenzen,
Pfad-/Temp-Verhalten, Worker-/Prozessgrenzen, Packaging-/Release-/
CI-Vertrauensgrenzen), die eine generische SAST-Regel nicht abdeckt.

## Entscheidung

1. **CodeQL übernimmt die automatisierte SAST-Grundabdeckung für Python**
   (`.github/workflows/codeql.yml`): Push/PR auf `main`, wöchentlich (Frische-
   Gate für neue/aktualisierte Queries ohne Code-Änderung) sowie
   `workflow_dispatch`. GitHub-nativ, keine externe API-Quota-Abhängigkeit.
2. **Codex Security Scan wird rein manuell** (`workflow_dispatch`, Parameter
   `min_severity` bleibt erhalten). `schedule` sowie der bisherige 14-Tage-
   Cadence-Pfad (`SCAN_ANCHOR_DATE`, `cadence`-Job) und die dafür nötigen
   Enable-/Disable-Schalter (`CODEX_SECURITY_SCAN_ENABLED`-Repo-Variable,
   `run_scan`-Dry-Skip-Input) entfallen ersatzlos – für einen rein manuellen
   Trigger sind sie redundant: Wer nicht scannen will, startet den
   `workflow_dispatch` schlicht nicht.
3. Struktur, Rechte-Trennung und Validierung des Codex-Pfads bleiben
   unverändert: `contents: read` für den Scan-Job, `issues: write`
   ausschließlich im nachgelagerten `create-issues`-Job, JSON-Schema-
   Validierung, Artefakt-Upload und deduplizierender Issue-Sync
   (`scripts/create_security_scan_issues.py`).
4. `pip-audit` (`dependency-audit.yml`), Lizenzprüfung (`license-check.yml`)
   und die reguläre CI-Matrix bleiben unverändert ergänzende, aber
   nicht-substituierende Kontrollen.
5. Bandit/Semgrep werden **nicht** zusätzlich eingeführt; ein weiterer
   Scanner ist erst nach einer belegten Abdeckungslücke zu bewerten.

## Advanced Setup statt Default Setup

CodeQL bietet zwei Aktivierungswege: ein UI-/API-getriebenes „Default Setup"
(Repository-Einstellung, nicht im Diff sichtbar) oder ein versioniertes
„Advanced Setup" (Workflow-Datei im Repo). Dieses Repo verlangt durchgängig
versionierte, im PR review- und diffbare Konfiguration (siehe „Drift-
Disziplin", Befund N6, für die Qt-Paketliste). Ein Repository-Setting lässt
sich weder aus einem Code-Review noch aus `git log` nachvollziehen und wird
von keinem Test erzwungen. Daher: **Advanced Setup** über
`.github/workflows/codeql.yml` mit `github/codeql-action/{init,autobuild,analyze}@v3`.

## Query-Suite

Startpunkt ist die **Standard-Suite** (kein `queries:`-Override in
`codeql.yml`) – geringere False-Positive-Rate, geeignet für einen ersten
stabilen Kontrolllauf. `security-extended` bzw. `security-and-quality` sind
erst nach einer bewussten Signal-/Noise-Bewertung eines stabilen
Default-Laufs zu erwägen, nicht als Startkonfiguration.

## Branch-Protection-Entscheidung

**Noch kein Required Check.** CodeQL wird der Branch Protection erst
hinzugefügt, nachdem ein PR-/Änderungslauf auf diesem Repo kontrolliert
verifiziert wurde (Tool-Status, analysierte Sprache, Abdeckung, ggf. Alerts
nachvollziehbar) – siehe Abschlusskommentar zu #551 für den verlinkten
initialen Lauf. Ein späterer Wechsel zu „Required Check" ist eine separate,
bewusste Folgeentscheidung und kein Bestandteil dieses ADRs. Bis dahin bleibt
CodeQL eine informative, nicht blockierende Ebene – konsistent mit #580, das
die manuelle Codex-Prüfung ausdrücklich außerhalb des v2.6.0-Release-Gates
hält.

## Konsequenzen

- Automatisierte Grundabdeckung besteht unabhängig von OpenAI-Quota (#245)
  weiter fort; #245 blockiert damit weder CodeQL noch den Abschluss dieses
  Issues.
- Codex bleibt für semantische, repo-spezifische Fragen verfügbar, aber ohne
  Kosten-/Quota-Risiko im Normalbetrieb, da kein automatischer Lauf mehr
  stattfindet.
- `tests/test_security_scan_automation.py` sichert beide Trigger-Verträge
  strukturell ab: CodeQL automatisch (Push/PR/Schedule, Standard-Suite, kein
  `queries:`-Override), Codex ausschließlich `workflow_dispatch` (kein
  `schedule`/`cadence`/Enable-Schalter mehr).
- `SECURITY.md` beschreibt die vollständige, aktuell aktive Prüf-Landschaft
  in einer Tabelle (Ebene, Trigger, Rolle), um Rollen-/Trigger-Drift wie im
  bisherigen Text zu vermeiden.

## Nicht-Ziele

- Keine Wiederherstellung oder Änderung von OpenAI-Kontodaten (bleibt Scope
  von #245).
- Kein automatischer Codex-Lauf als PR-, Push-, Zeitplan- oder Release-Gate.
- Keine Einführung von Bandit/Semgrep ohne separat belegte Abdeckungslücke.
- Keine automatische Behebung bestehender oder künftiger CodeQL-/Codex-
  Findings in diesem ADR/Issue.

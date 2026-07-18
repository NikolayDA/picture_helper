# Sicherheitsrichtlinie

## Unterstützte Versionen

Sicherheitsupdates werden ausschließlich für die jeweils aktuelle Release-Version bereitgestellt.

| Version | Unterstützt |
|---------|-------------|
| 2.4.x   | ✓           |
| < 2.4   | ✗           |

## Sicherheitslücken melden

**Bitte keine Sicherheitslücken als öffentliches GitHub-Issue melden.**

Schwachstellen werden vertraulich über **GitHub Private Vulnerability Reporting** gemeldet:

- Über die Schaltfläche **„Report a vulnerability"** im Tab *Security* dieses Repositories — die Meldung ist privat und nur für die Maintainer sichtbar. Voraussetzung: *Private vulnerability reporting* ist unter *Settings → Security → Reporting* aktiviert.

### Was in der Meldung angeben?

- Betroffene Version(en) und Betriebssystem
- Reproduzierbarer Ablauf (Schritte, Eingabedaten, Fehlerbild)
- Mögliche Auswirkung und Angriffsvektor
- Optional: vorgeschlagener Fix oder Patch

### Ablauf nach dem Eingang

1. Eingangsbestätigung innerhalb von **48 Stunden**.
2. Erstbewertung (Severity, Reproduzierbarkeit) innerhalb von **7 Tagen**.
3. Koordinierte Offenlegung nach Verfügbarkeit eines Fixes — üblicherweise innerhalb von **30 Tagen**, bei komplexen Fällen länger.
4. Der Meldende wird im CHANGELOG und ggf. in den Release Notes erwähnt (sofern gewünscht).

## Sicherheitsprofil der Anwendung

BgRemover ist ein lokales Desktop-Tool ohne Netzwerkdienst, Nutzerdatenbank oder Browser-Oberfläche. Relevante Angriffsflächen:

- **Bilddateien:** Verarbeitung durch Pillow/rembg — malformte oder bösartige Bilddateien könnten Schwachstellen in diesen Bibliotheken ausnutzen.
- **Dateipfade:** Laden, Speichern und CLI-Argumente — Path-Traversal-Szenarien.
- **Qt-Plugins:** Staging in ein temporäres Verzeichnis beim Start (`qt_plugins.py`).
- **rembg / ONNX-Laufzeit:** Das optionale KI-Extra lädt Modelle aus dem Netz und führt ONNX-Inferenz lokal aus.
- **CI/CD und Abhängigkeiten:** Supply-Chain-Risiken in Workflows und transitiven Paketen.

### Aktive Sicherheitsprüf-Ebenen (#551)

| Ebene | Trigger | Rolle |
|-------|---------|-------|
| **CodeQL** (`.github/workflows/codeql.yml`) | automatisch: Push/PR auf `main`, wöchentlich, `workflow_dispatch` | Deterministische SAST-Grundabdeckung für Python (Standard-Query-Suite), GitHub-nativ über den *Security*-Tab, unabhängig von externer API-Quota. |
| **Codex Security Scan** (`.github/codex/`, `.github/workflows/codex-security-scan.yml`) | **ausschließlich manuell** über `workflow_dispatch` | Repo-spezifische, semantische Prüfung (Bild-/Projektdatei-Grenzen, Pfad-/Temp-Verhalten, Worker-/Prozessgrenzen, Packaging-/Release-/CI-Vertrauensgrenzen). Kein Zeitplan, kein automatischer Lauf bei Push/PR – abhängig von einem gültigen `OPENAI_API_KEY` und dessen Quota (separater Betriebs-Tracker: #245). |
| **pip-audit** (`dependency-audit.yml`) | PR + wöchentlich | Bekannte CVEs im gepinnten Abhängigkeits-Snapshot (`requirements/constraints.txt`). |
| **Lizenzprüfung** (`license-check.yml`) | PR | Inventar-/Lizenz-Drift der Abhängigkeiten. |
| **CI-Matrix** (`ci.yml`/`pr-ci.yml`) | PR | Qualität/Funktion (Lint, Typecheck, Tests) – ersetzt keine Quellcode-Sicherheitsanalyse. |

Die Entscheidung für dieses hybride Modell (CodeQL automatisch, Codex manuell) inklusive Begründung
und Branch-Protection-Abwägung ist dokumentiert in
[`docs/history/ADR-2026-codeql-codex-sicherheitsmodell.md`](docs/history/ADR-2026-codeql-codex-sicherheitsmodell.md).

## Abhängigkeiten

Bekannte CVEs in Abhängigkeiten werden in `pyproject.toml` durch Mindestversions-Pins ausgeschlossen und im CHANGELOG dokumentiert. Bitte melde schwerwiegende, noch nicht gepinnte CVEs ebenfalls über den oben beschriebenen vertraulichen Weg.

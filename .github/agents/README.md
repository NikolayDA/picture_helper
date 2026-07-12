# GitHub Agents für BgRemover

Diese Konfigurationen aktivieren zwei Agents mit hoher Priorität:

## 1. Code Review Agent (`code-review.yml`)

**Wofür:** Automatische Reviews aller PRs gegen deine QA-Standards.

**Prüft:**
- ✅ `make lint` (Ruff Code-Style)
- ✅ `make type` (mypy Type-Checking)
- ✅ `make test` (pytest Unit-Tests)
- ✅ Coverage ≥ 86%

**Aktualisiert automatisch:**
- Kommentare bei Fehlern
- Verbesserungsvorschläge
- Blockt Merge bei Failures

**Labels:** `agent:code-review`, `needs-review`

---

## 2. Bug Fix Agent (`bug-fix.yml`)

**Wofür:** Automatisches Diagnostizieren und Fixen von Test-Failures und Bugs.

**Kann automatisch fixen:**
- Type-Annotation-Fehler
- Lint-Violations (Ruff-Regeln)
- Import-Fehler
- Simple Logic-Fehler

**Analysiert auch:**
- Race Conditions in `QThread`s
- Memory-Leaks in Image-Ops
- Height-Map-Konvertierungen
- Qt-UI Edge Cases

**Wird ausgelöst durch:**
- Issues mit Label `bug`
- Fehlgeschlagene PR-CI-Läufe

**Labels:** `agent:bug-fix`, `auto-fix`

---

## Status: deklarative Spezifikation, (noch) nicht automatisch aktiv

> **Wichtig:** Diese `*.yml`-Dateien sind eine **deklarative Beschreibung** der
> gewünschten Agent-Aufgaben, Trigger und Fokusbereiche – **kein** von GitHub
> automatisch ausgeführtes Format. GitHub lädt aus `.github/agents/` nur
> [Copilot-Agent-Profile](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents)
> (Markdown mit YAML-Frontmatter + Prompt); ereignisgesteuerte Automatik
> (bei PR, `workflow_run`, Zeitplan) läuft ausschließlich über echte
> **GitHub-Actions-Workflows** in `.github/workflows/` bzw.
> [GitHub Agentic Workflows](https://docs.github.com/en/copilot/how-tos/github-agentic-workflows/creating-github-agentic-workflows).
> Ein Merge dieser Dateien aktiviert die Agents daher **nicht** von selbst.

## Aktivierung (manuell / geplant)

Um die hier beschriebenen Agents tatsächlich laufen zu lassen, muss die
jeweilige Aufgabe in ein unterstütztes Format überführt werden, z. B.:

- als echter Workflow unter `.github/workflows/` (Trigger + Aufruf eines
  AI-Agent-Actions/Skripts), oder
- als GitHub Agentic Workflow (Markdown → `*.lock.yml`), oder
- als Copilot-Agent-Profil (`.github/agents/<name>.md`) für die manuelle
  Zuweisung.

Diese YAML-Dateien dienen bis dahin als Referenz/Spezifikation für die
Umsetzung.

## Konfiguration anpassen

Solange die Umsetzung als Workflow aussteht, ändere die YAML-Dateien nur als
Spezifikation – ein Push allein löst keine Automatik aus.

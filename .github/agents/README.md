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

## Diese `*.yml` sind Spezifikation – ausgeführt werden echte Workflows

> **Wichtig:** Diese `*.yml`-Dateien sind eine **deklarative Beschreibung** der
> gewünschten Agent-Aufgaben, Trigger und Fokusbereiche – **kein** von GitHub
> automatisch ausgeführtes Format. GitHub lädt aus `.github/agents/` nur
> [Copilot-Agent-Profile](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents)
> (Markdown mit YAML-Frontmatter + Prompt); ereignisgesteuerte Automatik
> (bei PR, Erwähnung, Zeitplan) läuft ausschließlich über echte
> **GitHub-Actions-Workflows** in `.github/workflows/`.

## Live-Umsetzung (echte Workflows)

Die tatsächlich laufende Automatik steckt in zwei Workflows auf Basis der
offiziellen [`anthropics/claude-code-action`](https://github.com/anthropics/claude-code-action):

| Workflow | Trigger | Rolle | Deckt Spec ab |
|----------|---------|-------|---------------|
| [`.github/workflows/claude-code-review.yml`](../workflows/claude-code-review.yml) | PR `opened`/`synchronize` | Automatisches Review (nur Kommentare) | `code-review.yml` |
| [`.github/workflows/claude.yml`](../workflows/claude.yml) | `@claude`-Erwähnung in Issue/PR/Review | On-Demand-Agent: fixt Bugs, schreibt Tests, aktualisiert Doku, analysiert Performance | `bug-fix.yml`, `test.yml`, `documentation.yml`, `performance.yml` |

Für die On-Demand-Aufgaben beschreibt man die Aufgabe direkt in der Erwähnung,
z. B. `@claude schreib Tests für height_ops.py` oder `@claude fixe den roten
PR-CI-Lauf`. Die `*.yml`-Dateien hier dienen als **Aufgaben-/Persona-Referenz**
für diese Aufrufe.

### Voraussetzung

Ein Repo-Secret **`ANTHROPIC_API_KEY`** (Settings → *Secrets and variables* →
*Actions*); alternativ `CLAUDE_CODE_OAUTH_TOKEN` (dann Input im Workflow
ersetzen). Fehlt das Secret, überspringen sich beide Workflows sauber – ohne
roten Lauf.

### Optional erweitern

Rein zeit-/label-gesteuerte Automatik (z. B. wöchentliche Doku-/Performance-
Läufe aus den Specs) lässt sich als weiterer Workflow mit `on: schedule` bzw.
`label_trigger` ergänzen – bewusst nicht per Default aktiviert, um Kosten/
Rauschen zu vermeiden.

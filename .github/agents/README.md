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

Nur **ein** Repo-Secret nötig: **`CLAUDE_CODE_OAUTH_TOKEN`** (Settings →
*Secrets and variables* → *Actions*). Das Token erzeugt man lokal mit
`claude setup-token`; die Läufe rechnen damit über das Claude-Abo
(Pro/Max/Team/Enterprise) statt über eine API-Abrechnung. Fehlt das Secret,
überspringen sich beide Workflows sauber – ohne roten Lauf.

Drei Eigenheiten dieses Wegs:

1. **Das Token hängt am Abo der Person**, die `claude setup-token` ausgeführt
   hat – für ein org-weit geteiltes Secret ist ein API-Key aus der
   [Claude Console](https://console.anthropic.com) der bessere Weg.
2. **Die Läufe zehren am Nutzungslimit dieses Kontos.** Das Review startet bei
   jedem `opened`/`synchronize`, der On-Demand-Agent bei jeder
   `@claude`-Erwähnung. Ist das Limit erschöpft, wird der Lauf **rot** – das
   saubere Überspringen oben gilt ausdrücklich nur für ein *fehlendes* Secret.
   Dasselbe gilt für ein Modell, das die Abo-Stufe nicht hergibt – beide
   Workflows pinnen `claude-opus-5`.
3. **Es gilt ein Jahr** ab Erzeugung. Läuft es ab, melden die Workflows einen
   Authentifizierungsfehler; dann ein neues Token erzeugen und das Secret
   überschreiben.

Wer stattdessen per API abrechnen will, hinterlegt `ANTHROPIC_API_KEY` und
zieht in **beiden** Workflows drei Stellen mit: das Input
(`claude_code_oauth_token:` → `anthropic_api_key:`), die `env:`-Zeile der
`HAS_CLAUDE_TOKEN`-Prüfung und den Meldungstext im Skip-Schritt. Bleibt eine
davon stehen, löst der Workflow still nie aus.

Für den GitHub-Zugriff reichen die Workflows bewusst das automatische
`GITHUB_TOKEN` durch (`github_token: ${{ secrets.GITHUB_TOKEN }}`), damit die
[Claude-GitHub-App](https://github.com/apps/claude) **nicht** installiert werden
muss (die `anthropics/claude-code-action` würde sonst standardmäßig deren
Token-Austausch erwarten und ohne App fehlschlagen).

> **Trade-off:** Commits, die der interaktive Agent mit dem `GITHUB_TOKEN`
> pusht, lösen **keine** nachgelagerten Workflows aus (bekannte GitHub-
> Einschränkung). Wer das braucht, installiert die Claude-GitHub-App (oder eine
> eigene App via `actions/create-github-app-token`) und entfernt die
> `github_token`-Zeile bzw. setzt den App-Token ein. Für das reine
> Review-Feedback (`claude-code-review.yml`) spielt das keine Rolle.

### Optional erweitern

Rein zeit-/label-gesteuerte Automatik (z. B. wöchentliche Doku-/Performance-
Läufe aus den Specs) lässt sich als weiterer Workflow mit `on: schedule` bzw.
`label_trigger` ergänzen – bewusst nicht per Default aktiviert, um Kosten/
Rauschen zu vermeiden.

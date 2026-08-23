# GitHub Agents für BgRemover

Diese Konfigurationen aktivieren zwei Agents mit hoher Priorität:

## 1. Code Review Agent (`code-review.yml`)

**Wofür:** Automatische Reviews aller PRs gegen deine QA-Standards.

**Prüft:**
- ✅ `make lint` (Ruff Code-Style)
- ✅ `make type` (mypy Type-Checking)
- ✅ `make test` (pytest Unit-Tests)
- ✅ Coverage ≥ 86%

**Die Spezifikation beschreibt:**
- Kommentare bei Fehlern
- Verbesserungsvorschläge
- Blocker bei Fehlern

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

Das automatische Review bleibt dagegen strikt bewertend. Seine Allowlist
erlaubt neben PR-Diff/-Metadaten nur die belegten Nur-Lese-Inspektionen
`gh pr list`, `gh issue view` sowie `git show`, `git diff`, `git log`,
`git status` und `git show-ref`. Die Git-Befehle sind als vollständig
ausgeschriebene, feste Argumentformen freigegeben – keine Präfix-Wildcards,
über die etwa `--output` Dateien schreiben könnte. `gh issue view` ist rein
lesend, aber nicht harmlos: Issue-Text kann jeder Account verfassen, und er
erreicht einen Agenten mit `pull-requests: write` – dieselbe Kante wie bei
WebFetch. Tragend ist dabei nicht „der Agent kann nichts schreiben" (die
beiden Ausgabewege sind offen), sondern die Prompt-Regel, dass Fremdinhalt
Daten und keine Anweisung ist; `contents: read` verhindert nur den
Code-Weg. Die benötigte Historie stellt der
kontrollierte Checkout vor dem Agentenlauf bereit. Eigenständiges Nachladen,
PR-Code lokal ausführen, generisches `gh api` und Änderungen am Checkout
bleiben ausgeschlossen (#841). Die zugehörigen Prompt- und Allowlist-Grenzen
sind in `tests/test_claude_workflow_diagnostics.py` als Drift-Schutz
verankert.

Der Review-Job ist selbst kein Required Check; ein Inline-Befund verhindert
wegen der Branch-Protection-Regel für offene Review-Konversationen trotzdem
den Merge, bis die Konversation aufgelöst ist.

Abgelehnte Aufrufe sind dabei nicht gleichwertig. Der Review-Workflow führt
die Einteilung im Kommentarblock über dem `claude_args`-Block: **L** (lesende
Inspektion in einer in `--allowedTools` freigegebenen Form – `gh`-/Git-
Formen, Read, Grep, Glob und WebFetch auf die freigegebenen Domains) darf nie
abgelehnt werden; eine Ablehnung dieser Klasse ist eine Lücke in der Allowlist
und gehört geschlossen. **A** (Ausführung), **N** (Netzzugriff auf eine
**nicht** freigegebene Domain), **S** (Schreibzugriff) und
**P** (lesende Absicht in nicht freigegebener Form, etwa mit abweichenden
Flags oder einer Pipe) dürfen dagegen abgelehnt werden; sie sind ein
Prompt-Befund und rechtfertigen keine Erweiterung der Freigaben. **P setzt
voraus, dass dieselbe Information über eine freigegebene Form erreichbar
gewesen wäre – sonst ist die Ablehnung L, es sei denn, die Enge betrifft die
**Parameter eines bereits freigegebenen Kommandos** (Tiefe, Commit-Bereich,
Ausgabeumfang); dann bleibt es P. Ein gänzlich fehlendes Kommando fällt nie
darunter.** Ohne den ersten Teil ließe sich jede unbequeme L-Ablehnung als P
verbuchen; ohne den zweiten wäre jede gewollte Verengung per Definition eine
Lücke. Prüfsteine: `--max-count=20` und `--max-count=200` sind beide P (die
freigegebenen 30 sind gewollt), `gh issue view` war nie P. Genau eine
Ausnahme von **S**: Die beiden Ausgabewege des Reviews – das
Inline-Kommentar-Werkzeug und `gh pr comment` – sind selbst
Remote-Schreibzugriffe; ihre Ablehnung zählt wie **L**, sonst stünde der
schlimmste Fall (Befund gefunden, Kommentar abgewiesen, PR ohne Review) als
Normalfall im Joblog. Ohne diese Trennung ist ein grüner Lauf keine Aussage
über die Werkzeuggrenze: Lauf 32600075322 meldete `Lauf: success` bei sechs
Ablehnungen.

Für den interaktiven Agenten in `claude.yml` gilt diese Einteilung **nicht**.
Er hat keine Allowlist, hält `contents: write` und soll Code schreiben,
testen und committen – eine abgelehnte Ausführung oder ein abgelehnter
Schreibzugriff ist dort kein Normalfall, sondern der Befund, der die Aufgabe
blockiert hat. Der geteilte Diagnoseschritt meldet deshalb nur die
Rohdaten; gedeutet wird je Workflow.

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
zieht in **beiden** Workflows vier Stellen mit. Sie wirken unterschiedlich –
bleibt eine stehen, sieht der Fehler jeweils anders aus:

| Stelle | Bleibt sie stehen |
|---|---|
| `env:`-Zeile der `HAS_CLAUDE_TOKEN`-Prüfung | Workflow löst **still nie aus** |
| Input `claude_code_oauth_token:` | Job läuft an und scheitert **rot** mit Auth-Fehler |
| Meldungstext im Skip-Schritt | folgenlos, aber irreführende Warnung |
| Kopfkommentar der Workflow-Datei | folgenlos, aber die Datei widerspricht sich |

Der stille Fall ist der teuerste: Bei einem roten Lauf sucht man wenigstens an
der richtigen Stelle.

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

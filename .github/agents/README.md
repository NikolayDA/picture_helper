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

## Aktivierung

1. **Merge** diesen Branch in `main`
2. **GitHub Actions** erkennt automatisch die `.github/agents/*.yml`-Dateien
3. **Agents starten** beim nächsten PR oder Issue

## Überwachung

- Logs unter **Actions → Agent Workflows**
- Agent-Kommentare direkt in PRs/Issues
- Labels zeigen Agent-Aktivität an

## Konfiguration anpassen

Wenn später Anpassungen nötig sind:
- Ändere die YAML-Dateien
- Pushe auf `main`
- Agents nutzen die neuen Settings ab dem nächsten Trigger

# GitHub Agents – Erweiterte Konfigurationen (Prio 3-5)

Diese Dateien konfigurieren drei weitere Agents mit mittlerer Priorität:

---

## 3. Documentation Agent (`documentation.yml`)

**Prio:** MITTEL | **Wofür:** Automatische Generierung und Wartung von Dokumentation

### Funktionen:
- 📚 API-Docs aus Code-Kommentaren generieren
- 📖 Module dokumentieren (`height_ops.py`, `relief_preview.py`, etc.)
- 🔗 Links in CLAUDE.md, ANLEITUNG.md, README.md aktuell halten
- 🎨 Architektur-Diagramme (Mermaid) erstellen
- 📝 CHANGELOG-Snippets bei neuen Features

### Triggert bei:
- PRs mit Label `feature`
- Wöchentlich (automatisch)
- Pull Requests mit Änderungen in `bgremover/**/*.py`

### Fokus-Module:
1. `image_ops.py` (ImageOps)
2. `height_ops.py` (HeightOps)
3. `canvas.py` (Canvas)
4. `ai_process.py` (AI-Prozesse)
5. `right_panel_tabs/` (UI-Komponenten)

**Labels:** `agent:documentation`, `documentation`, `auto-docs`

---

## 4. Test Agent (`test.yml`)

**Prio:** MITTEL | **Wofür:** Automatische Test-Generierung und Fehler-Debugging

### Funktionen:
- ✍️ Tests für neue Features schreiben
- 🎯 Coverage ausbauen (Target: ≥86%)
- 🔍 Edge Cases in komplexen Modulen testen
- 🐛 Test-Failures automatisch debuggen
- 🪟 UI-Smoke-Tests erweitern (headless Qt offscreen)

### Triggert bei:
- PRs mit Label `feature`
- Issues mit Label `test:coverage` oder `test:edge-case`
- Fehlgeschlagene PR-CI Läufe (Test-Fehler)

### Test-Fokus:
- Image Operations (16-Bit, Floating, MedianBlur, GaussianBlur)
- Height Map Conversions
- Crop Geometry & Rule of Thirds
- Qt UI Components (headless)
- Worker Threads & Race Conditions
- Memory Management (Undo/Redo)

### Module mit niedriger Coverage (Priorität):
- `height_ops.py`
- `relief_preview.py`
- `image_ops.py`
- `project_model.py`

**Labels:** `agent:test`, `testing`, `coverage`

---

## 5. Performance Agent (`performance.yml`)

**Prio:** NIEDRIG | **Wofür:** Monitoring und Optimierung der Performance

### Funktionen:
- 📊 Weekly Benchmarks der Bild-Pipeline
- 🚨 Performance-Regressionen erkennen (>10% Schwelle)
- 💾 Memory-Profiling für große Bilder (bis 40 Megapixel)
- 🔥 Bottlenecks in `image_ops.py`, `height_ops.py` identifizieren
- 💡 Optimierungsempfehlungen generieren

### Benchmarkierte Formate:
- PNG, JPEG, WebP, TIFF

### Metriken pro Format:
- `encode_ms` — Speichern (Encode + atomare Ablage)
- `decode_ms` — Laden/Dekodieren
- `process_ms` — End-to-End (Laden → Drehen → Ecken runden → Zuschneiden → Speichern)

### Triggert bei:
- **Wöchentlich** (automatisch)
- PRs mit Label `performance`
- Änderungen in `image_ops.py`, `height_ops.py`, `canvas.py`

### Memory-Tests:
- Large-Image-Tests bis 40 Megapixel
- Undo/Redo Memory-Limit (Geschichte)
- Peak-Memory bei komplexen Operationen

**Labels:** `agent:performance`, `performance`, `benchmarks`

---

## Gesamtstapel (alle 5 Agents)

| Agent | Prio | Trigger | Auto-Commit | Labels |
|-------|------|---------|-------------|--------|
| Code Review | 🔴 HOCH | PR geöffnet | — | `agent:code-review` |
| Bug Fix | 🔴 HOCH | PR fehlgeschlagen | ✅ | `agent:bug-fix` |
| Documentation | 🟡 MITTEL | Feature PR + Weekly | ✅ | `agent:documentation` |
| Test | 🟡 MITTEL | Feature PR + Issue | ❌ (PR) | `agent:test` |
| Performance | 🟢 NIEDRIG | Weekly + Performance PR | ✅ | `agent:performance` |

---

## Aktivierung

> **Hinweis:** Wie in [`README.md`](README.md) beschrieben, sind diese
> `*.yml`-Dateien eine **deklarative Spezifikation** und werden von GitHub
> **nicht** automatisch ausgeführt. Ein Merge aktiviert die 5 Agents daher
> **nicht** von selbst – dazu muss jede Aufgabe als echter GitHub-Actions-
> Workflow, GitHub Agentic Workflow oder Copilot-Agent-Profil umgesetzt werden.

---

## Geplante Bedienung (nach Umsetzung als Workflow)

- **Dokumentation:** perspektivisch über einen `agent:documentation`-Trigger in
  PR-Kommentaren, um Docs zu aktualisieren
- **Tests:** Issues mit `test:coverage` → generierte Tests
- **Performance:** wöchentliche Reports unter **Actions → Performance Benchmark**

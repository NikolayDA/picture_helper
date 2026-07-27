# Release 2.7.1 – GL-Ressourcen-/Langzeittest und Regressionsgate

Testbericht zu **#684** (Epic #680). Validiert den in **PR #676** gemergten Fix
gegen reale Nutzungsmuster und protokolliert das vollständige Regressionsgate
des Release-Kandidaten.

> **Kurzfassung:** Über 1000 Aktualisierungszyklen je Datensatzgröße bleibt die
> Zahl lebender GL-Objekte konstant bei 4 (drei Puffer + VAO); erzeugte und
> freigegebene Objekte sind exakt gleich (16 000/16 000), nach dem Schließen
> bleiben 0 übrig. Doppelfreigaben und Zugriffe nach der Freigabe treten nicht
> auf. Eine Negativkontrolle stellt den Zustand vor #676 nach und wird von
> derselben Messung erkannt (480 lebende Objekte nach 120 Zyklen) – die grüne
> Messung ist damit nachweislich aussagefähig und keine leere Zusicherung.

## 1. Geprüfter Stand und Umgebung

| Angabe | Wert |
|---|---|
| Commit (Messläufe) | `e48dd89ab09da60e1604ae1fab0c40d8ad4c0852` (Zweig `claude/github-issue-684-jume86`) |
| Anwendungsversion | 2.7.1 (`pyproject.toml`, Release-Kandidat aus #683/#699) |
| Betriebssystem | Linux 6.18.5, x86_64, glibc 2.39 (Container der Web-Session) |
| Python | 3.11.15 |
| Qt / PyQt | 6.7.1 / 6.7.1 (PyQt6-Wheel) |
| Qt-Plattform (QPA) | `offscreen` |
| GPU / Treiber | **keine** – die Session hat keinen renderbaren FBO; `probe_3d_capability` meldet „nicht verfügbar" |

**Einschränkung, bewusst benannt (Akzeptanzkriterium 11):** In dieser Umgebung
existiert kein echter GL-Kontext. Der Nachweis läuft deshalb über den
*instrumentierten* Pfad (Abschnitt 2) und über die identisch aufgebauten
`gl_smoke`-Tests, die sich hier automatisch überspringen. Der Nachweis auf echter
Hardware inklusive GPU/Treiberangaben ist als Prozedur in Abschnitt 6
festgeschrieben und gehört zur Hardware-Abnahme (#685) – er ist **nicht** durch
diesen Bericht ersetzt.

## 2. Festgelegter Messwert und Abgrenzung Aufwärmphase

Gemessen wird die **Zahl lebender GL-Objekte**: drei `QOpenGLBuffer`
(Position/Slope/Index) plus ein `QOpenGLVertexArrayObject` je Mesh-Upload. Zwei
unabhängige Quellen, beide in `bgremover/viewer_3d.py`:

| Quelle | Was sie sieht | Warum sie nötig ist |
|---|---|---|
| `GLReliefViewer.gl_object_count` | die aktuell vom Viewer **referenzierten** Objekte (0–4), direkt aus den Attributen abgeleitet | kann nicht abdriften; belegt die harte Obergrenze je Viewer |
| `gl_resource_stats()` (`created`/`destroyed`/`live`) | prozessweite Zähler über **alle** Viewer | sieht auch **verwaiste** Objekte, die kein Viewer mehr referenziert – genau das Fehlerbild vor #676. `gl_object_count` allein würde das Leck **übersehen** (der alte Code hielt ebenfalls nur 4 Referenzen, die alten Objekte lebten daneben weiter) |

Beide sind reine Diagnose: keine GL-Aufrufe, kein Einfluss auf Rendern, Export
oder Modell.

**Aufwärmphase vs. Wachstum (Akzeptanzkriterium 3):** Bewertet wird der Wert
*nach* dem zweiten Zyklus gegen den Wert nach dem letzten Zyklus
(`WARMUP_CYCLES = 2` in `scripts/gl_stress_probe.py`). Einmalige Initialisierung
(Shader-Programm, erster Upload, Qt-interne Caches) fällt damit vor die Messung;
jeder pro Zyklus wiederkehrende Zuwachs fällt hinein. Zusätzlich wird der
Maximalwert über alle Zyklen geprüft – ein Sägezahnmuster (wachsen, gelegentlich
aufräumen) fällt dadurch ebenfalls auf.

Ergänzend wird der Arbeitsspeicher (RSS) je Szenario protokolliert. Er ist
**kein** verbindliches Kriterium: Treiberspeicher für GL-Objekte liegt oft
außerhalb des RSS, und die Sonde hält die gebauten Meshes absichtlich am Leben.
Innerhalb eines Szenarios muss er trotzdem flach bleiben – das tut er (Tabelle
in Abschnitt 4).

## 3. Werkzeug und exakte Befehle

`scripts/gl_stress_probe.py` ist die geteilte Messsonde. Die automatisierten
Tests importieren **dieselbe** Datei, damit CI-Aussage und Release-Nachweis nicht
auseinanderdriften (Muster von `renderer_provenance.py`, ADR #639).

```bash
# Regressionstests (laufen in jedem normalen pytest-Lauf mit)
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_viewer_3d_gl_lifecycle.py -v

# Nachweislauf: Standardsatz klein/typisch/groß, 120 Zyklen je Szenario
make gl-stress
QT_QPA_PLATFORM=offscreen python scripts/gl_stress_probe.py --cycles 120 \
    --json-out gl-stress-120.json

# Langlauf mit 1000 Zyklen
QT_QPA_PLATFORM=offscreen python scripts/gl_stress_probe.py --cycles 1000 \
    --sizes klein:64:REDUCED,typisch:512:STANDARD --json-out gl-stress-1000.json

# Auf renderfähiger Plattform zusätzlich mit echtem Kontext und echten Puffern
QT_QPA_PLATFORM=xcb python scripts/gl_stress_probe.py --mode gl --cycles 200
QT_QPA_PLATFORM=xcb python -m pytest -m gl_smoke -v
```

Exit-Code der Sonde: `0` = kein Befund, `1` = Ressourcenbefund, `2` = Sonde in
dieser Umgebung nicht ausführbar. Sie taugt damit direkt als Gate in einem
Abnahmeskript.

Zwei Absicherungen gegen ein **falsches Grün** (beide aus der Codex-Review zu
PR #706):

- **Mindestzyklen.** Ein Lauf unter 100 Zyklen wird abgelehnt; er ersetzt zu
  wenig Puffer, um ein Leck zu zeigen (bei einem einzigen Zyklus gäbe es gar
  keinen Wieder-Upload, und selbst der Zustand vor #676 meldete sich sauber).
  `--allow-short-run` erlaubt einen Diagnoselauf ausdrücklich und markiert den
  Bericht mit `gating: false`.
- **Fehlgeschlagener GL-Viewer.** Scheitert unter `--mode gl` Kontext, Shader
  oder Upload, fängt `paintGL` den Fehler ab: es entstünden 0 GL-Objekte, die
  Messreihe wäre konstant und damit formal „ohne Wachstum". Die Sonde bricht
  diesen Fall stattdessen mit Exit 2 ab – ebenso, wenn eine sich renderfähig
  meldende Plattform über alle Zyklen keinen einzigen Upload erzeugt.

Im Modus `fake` ersetzt die Sonde ausschließlich die GL-Objekte selbst durch
instrumentierte Attrappen; Meshes, `_ensure_buffers`, `_release_gl_objects` und
`cleanup_gl` sind der echte Produktionscode. Die Attrappen sehen zusätzlich zwei
Dinge, die ein echter Treiber bestenfalls indirekt zeigt: **Doppelfreigabe**
(`destroy` auf einem bereits zerstörten Objekt) und **use-after-delete** (jede
Benutzung nach der Freigabe).

## 4. Messergebnisse

### 4.1 Standardlauf – 120 Zyklen je Szenario

Kommando: `python scripts/gl_stress_probe.py --cycles 120` (offscreen).

| Szenario | Quelle | Vertices/Dreiecke | live nach Aufwärmen → nach Zyklus 120 | max live | erzeugt/freigegeben | nach `cleanup_gl` | RSS Start → Ende |
|---|---|---|---|---|---|---|---|
| klein | 64×64 | 4 096 / 7 938 | 4 → 4 | 4 | 480 / 480 | 0 | 64 036 → 67 132 KiB |
| typisch | 512×512 | 262 144 / 522 242 | 4 → 4 | 4 | 480 / 480 | 0 | 93 284 → 99 892 KiB |
| groß (dezimiert) | 2048×2048 | 262 144 / 522 242 | 4 → 4 | 4 | 480 / 480 | 0 | 118 348 → 123 068 KiB |
| wechselnd | 64+512+2048 | gemischt | 4 → 4 | 4 | 480 / 480 | 0 | 123 068 → 123 072 KiB |
| leere Daten (0 Dreiecke) | 64×64, Deckung 0 | 4 096 / 0 | 4 → 4 | 4 | 480 / 480 | 0 | 123 072 → 123 072 KiB |

Prozessweit: `created 2400 / destroyed 2400 / live 0`. Keine Doppelfreigabe, kein
use-after-delete, Urteil `ok`.

### 4.2 Langlauf – 1000 Zyklen je Szenario

Kommando: `python scripts/gl_stress_probe.py --cycles 1000 --sizes
klein:64:REDUCED,typisch:512:STANDARD`.

| Szenario | live nach Aufwärmen → nach Zyklus 1000 | max live | erzeugt/freigegeben | nach `cleanup_gl` | RSS Start → Ende |
|---|---|---|---|---|---|
| klein (64×64) | 4 → 4 | 4 | 4 000 / 4 000 | 0 | 63 960 → 67 080 KiB |
| typisch (512×512) | 4 → 4 | 4 | 4 000 / 4 000 | 0 | 93 200 → 100 032 KiB |
| wechselnd | 4 → 4 | 4 | 4 000 / 4 000 | 0 | 100 032 → 100 032 KiB |
| leere Daten | 4 → 4 | 4 | 4 000 / 4 000 | 0 | 100 036 → 100 036 KiB |

Prozessweit: `created 16000 / destroyed 16000 / live 0`, Urteil `ok`. Der RSS
steigt nur dort, wo ein *neues, größeres* Mesh gebaut und von der Sonde gehalten
wird; innerhalb der Zyklen bleibt er flach (die letzten beiden Szenarien bauen
kein neues Mesh mehr: 100 032 → 100 032 KiB über 1000 Zyklen).

### 4.3 Negativkontrolle – die Messung erkennt das alte Fehlerbild

Derselbe Lauf mit wirkungsloser Freigabe im Upload-Pfad (Zustand **vor** PR #676):

```text
live 8 -> 480 | max 480 | erzeugt 480 freigegeben 4
BEFUND lebende GL-Objekte wachsen nach der Aufwärmphase (8 → 480 über 120 Zyklen)
BEFUND mehr als 4 lebende GL-Objekte (Maximum 480)
BEFUND nach cleanup_gl() bleiben 476 GL-Objekt(e) übrig
BEFUND 476 Attrappe(n) ohne Freigabe
```

Exakt vier Objekte je Zyklus – das erwartete Muster des behobenen Lecks. Der
Fall ist als Test festgeschrieben
(`test_probe_detects_a_missing_release_path`), damit eine später „blinde"
Messung nicht unbemerkt grün bleibt.

## 5. Szenarien aus #684 ↔ Nachweis

| Szenario | Nachweis |
|---|---|
| Wiederholtes Öffnen/Schließen des Relief-Viewers | `test_view_cleanup_and_reopen_cycles_stay_bounded` (110× anzeigen → `cleanup()` → erneut) |
| Wiederholte Wechsel 2D ↔ 3D | `test_2d_3d_toggle_cycles_do_not_accumulate_gl_objects` (110× `set_active(False/True)` über `Preview3DController`, Cache-Treffer ohne Rebuild) |
| Laden/Ersetzen unterschiedlich großer HEIGHT-Daten | `test_long_run_keeps_live_gl_objects_bounded[klein/typisch/gross]`, `test_long_run_with_changing_height_data_is_bounded`, Sonden-Szenario „wechselnd" |
| Zoom/Rotation ohne Neuberechnung | `tests/test_preview3d_controller.py::test_exaggeration_and_light_are_uniforms_no_rebuild`, `tests/test_viewer_3d.py` (Maus-/Tastatur-Interaktion); Kamera/Licht/Überhöhung sind reine Uniforms |
| Neuberechnung/Buffer-Reupload | `test_every_created_object_is_released_exactly_once`, `test_upload_without_pending_mesh_creates_nothing` (ein Frame ohne neues Mesh alloziert **nichts** neu) |
| Fenstergrößenänderung | `resizeGL` ist ein reiner No-op (Qt setzt den Viewport); kein Ressourcenpfad – manuell in Abschnitt 6 |
| Projekt öffnen, schließen, erneut öffnen | `test_view_cleanup_and_reopen_cycles_stay_bounded`, `tests/test_preview3d_acceptance.py::test_hundred_viewer_lifecycle_cycles_do_not_leak_or_crash` |
| Fehlerpfad: leere/ungültige Daten | `test_empty_height_data_uploads_and_releases_cleanly` (0 Dreiecke), `test_failed_buffer_creation_leaves_no_orphans` (VAO-Erzeugung scheitert) |
| Fehlerpfad: abgebrochener Ladevorgang | `test_cancelled_build_and_unavailable_capability_release_resources` (superseded Generationen, Abbruch, wegfallende Capability) |
| Fehlerpfad: Schließen während/kurz nach Aktualisierung | `test_close_while_update_is_pending_leaves_nothing` |
| Kontextverlust | `test_context_loss_releases_and_schedules_reupload` (30 Verluste in Folge, jeweils Freigabe + geplanter Reupload) |
| Noch nicht initialisierter Kontext | `test_paint_before_initialization_allocates_nothing` |
| Bereits zerstörtes Widget | `test_cleanup_on_destroyed_widget_does_not_raise` |
| Längerer Lauf mit vielen Wiederholungen | Abschnitt 4.2 (1000 Zyklen je Szenario) |
| Normaler interaktiver Smoke-Test | `pytest -m ui` (20 Tests grün, Abschnitt 7) plus manuelle Prozedur in Abschnitt 6 |

## 6. Manuelle Hardware-Prozedur (Release-Checkliste)

Diese Schritte kann die Offscreen-CI prinzipiell nicht liefern; sie gehören zur
Abnahme auf echter Hardware (#685, ergänzt
[`docs/PACKAGING_SMOKE.md`](../PACKAGING_SMOKE.md) §2.3). Ergebnis jeweils im
Abnahmeprotokoll festhalten.

1. **Umgebung erfassen:** OS/Version, GPU, Treiberversion,
   `glxinfo -B | grep -E "OpenGL (vendor|renderer|version)"`, Python-/Qt-Version,
   Commit-SHA des getesteten Artefakts.
2. **Automatisierter GL-Nachweis auf der Zielmaschine:**
   `QT_QPA_PLATFORM=xcb python -m pytest -m gl_smoke -v` – enthält
   `test_repeated_uploads_do_not_accumulate_gl_objects` (110 Uploads wechselnder
   Größe mit echten Puffern; verlangt konstante Zählerstände und 0 nach dem
   Aufräumen). Der Test darf hier **nicht** übersprungen werden; wird er
   übersprungen, ist die Plattform nicht renderfähig und der Nachweis fehlt.
3. **Sonde mit echtem Kontext:**
   `QT_QPA_PLATFORM=xcb python scripts/gl_stress_probe.py --mode gl --cycles 200
   --json-out abnahme-gl.json` – JSON dem Abnahmeprotokoll beilegen. Erwartet:
   `verdict: ok`, `live` konstant, `live_after_cleanup: 0`.
4. **Interaktiver Smoke (ca. 10 Minuten):** Projekt mit typischer HEIGHT-Ebene
   öffnen → 20× zwischen 2D und 3D umschalten → Orbit/Pan/Zoom → Fenster
   mehrfach vergrößern/verkleinern und maximieren → HEIGHT-Daten ersetzen →
   Projekt schließen und erneut öffnen. Erwartet: keine Fehlermeldung, Anzeige
   und Interaktion unverändert gegenüber 2.7.0.
5. **GPU-Speicher beobachten:** parallel zu Schritt 4
   `nvidia-smi -l 1` bzw. `radeontop`/`intel_gpu_top` bzw. das
   Aktivitätsmonitor-GPU-Panel (macOS) mitlaufen lassen. Erwartet: der Wert
   pendelt sich ein; kein monotoner Anstieg über die Wechsel hinweg. Anfangs-
   und Endwert protokollieren.
6. **Software-Renderer gegenprüfen:**
   `LIBGL_ALWAYS_SOFTWARE=1 QT_QPA_PLATFORM=xcb python -m bgremover` – Schritt 4
   verkürzt wiederholen; erwartet: langsamer, aber ohne Absturz und ohne
   Ressourcenanstieg.
7. **Abweichungen:** jede Abweichung entweder als Blocker beheben oder als
   eigenes Issue mit begründeter Release-Entscheidung erfassen (#684,
   vorletztes Akzeptanzkriterium).

## 7. Regressionsgate auf demselben Stand

Alle Läufe lokal unter Linux/Python 3.11.15, `QT_QPA_PLATFORM=offscreen`,
nicht-editable Installation mit `requirements/constraints.txt`
(`make install-test`).

| Prüfung | Ergebnis |
|---|---|
| `make check` (ruff + mypy + pytest-Standardsatz) | grün – ruff „All checks passed", mypy „no issues found in 70 source files", pytest **2069 passed, 6 skipped, 14 deselected** |
| `make ui` (volle qtbot-Suite) | grün – **20 passed** |
| `make coverage` (`fail_under = 86`) | grün – **93 %** gesamt |
| `make gl-stress` (Sonde, 120 Zyklen) | Exit 0, Urteil `ok` (Abschnitt 4.1) |
| Langlauf 1000 Zyklen | Exit 0, Urteil `ok` (Abschnitt 4.2) |
| `pytest -m gl_smoke` | **übersprungen** – die Session hat keine renderfähige Qt-Plattform (erwartet, siehe Abschnitt 1 und die Prozedur in Abschnitt 6) |
| `python scripts/verify_release_freeze.py` | siehe [Scope-Freeze](RELEASE-2.7.1-scope-freeze.md) – dieser Zweig verschiebt den Kandidaten (Abschnitt 8) |

Neue Warnungen, Flakes oder Plattformabweichungen: **keine**. Die
`gl_smoke`-Übersprünge sind das dokumentierte, seit ADR #591 erwartete Verhalten
der Offscreen-Umgebung, kein neuer Befund.

## 8. Auswirkung auf den Release-Freeze

Die Änderung berührt `bgremover/**`, `tests/**`, `scripts/**`, `pyproject.toml`
und das `Makefile` – nach den Pfadklassen des
[Scope-Freeze](RELEASE-2.7.1-scope-freeze.md) also **kandidatenrelevant**. Sie
erzeugt damit einen neuen Release-Kandidaten; die Klassifizierungstabelle,
Fensterzahl und der protokollierte Kandidaten-SHA dort sind entsprechend
nachgezogen. Der SHA kann erst **nach** dem Merge nachgetragen werden (ein
Dokument kann seinen eigenen Commit nicht enthalten) – bis dahin steht dort
`nachzutragen`, und `verify_release_freeze.py --require-pin` schlägt bewusst
fehl. Vor #685 (Artefakte) und #686 (Tag) ist also genau ein Protokoll-Commit
nachzuziehen; das Verfahren steht im Scope-Freeze unter „Freeze-Regel".

Inhaltlich bleibt der Patch-Scope gewahrt: an der Anwendungslogik ändert sich
nichts außer zwei Diagnosezählern ohne Renderpfadwirkung; es kommen keine
Benutzerfunktionen, keine Abhängigkeiten und keine Formatänderungen hinzu.

## 9. Offene Punkte

- Der Nachweis auf echter GPU/Hardware (Abschnitt 6) steht aus und ist Teil von
  #685. Ohne ihn bleibt Akzeptanzkriterium „Testumgebung … GPU, Treiber" nur für
  die Offscreen-Umgebung erfüllt.
- Der Protokoll-Commit mit dem neuen Kandidaten-SHA (Abschnitt 8) ist nach dem
  Merge dieses Zweigs fällig.

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
>
> **Nachtrag #711:** Ein *stiller* Fehlschlag von `QOpenGLBuffer.create()`/
> `bind()` konnte die Messung anfangs noch täuschen (Urteil `ok` ohne einen
> einzigen erzeugten Puffer). Beides ist jetzt ein harter Fehler mit sofortiger,
> einmaliger Freigabe der Teilressourcen; die Sonde verlangt zusätzlich einen
> vollständigen Puffersatz je Lauf. Details und Messwerte in Abschnitt 4.4.

## 1. Geprüfter Stand und Umgebung

| Angabe | Wert |
|---|---|
| Commit (Messläufe) | `e48dd89ab09da60e1604ae1fab0c40d8ad4c0852` (Zweig `claude/github-issue-684-jume86`) |
| Commit (Nachmessung #711, Abschnitt 4.4) | Zweig `claude/github-issue-711-p4ru14` auf Basis `0b021ccfa5f7` |
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

Drei Absicherungen gegen ein **falsches Grün** (die ersten beiden aus der
Codex-Review zu PR #706, die dritte aus #711):

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
- **Unvollständiger Puffer-Upload (#711).** Die beiden vorigen Absicherungen
  greifen nur bei einem *sichtbaren* Fehlschlag. `QOpenGLBuffer.create()` und
  `bind()` melden ihren Fehlschlag aber ausschließlich über den Rückgabewert;
  vor #711 wurde er ignoriert. Ein Wrapper **ohne** GL-Namen blieb dann in
  `_pos_vbo`/`_slope_vbo`/`_index_ibo` stehen, `has_failed` blieb `false` und
  `gl_object_count` meldete – weil es Referenzen zählt, nicht GL-Namen – bis zu
  4 Objekte. Die Messreihe war konstant, das Urteil `ok`, obwohl nie ein Puffer
  entstanden war. Seit #711 gilt beides als harter Fehler (`GLBufferError`):
  der Viewer gibt Teilressourcen genau einmal frei und schaltet über `_fail`
  in den Fehlerzustand, und die Sonde verlangt zusätzlich mindestens
  `MIN_LIVE_PER_VIEWER = 3` gehaltene Objekte je Lauf (drei Puffer; der VAO ist
  in GL 2.1 eine Erweiterung und darf fehlen). Unter `--mode gl` ist das
  Exit 2 (`ProbeNotExecutable`), im Modus `fake` ein harter Befund mit Exit 1.

Im Modus `fake` ersetzt die Sonde ausschließlich die GL-Objekte selbst durch
instrumentierte Attrappen; Meshes, `_ensure_buffers`, `_make_buffer`,
`_release_gl_objects` und `cleanup_gl` sind der echte Produktionscode. Der
Einhängepunkt ist seit #711 bewusst `viewer_3d._new_buffer` (der reine
Konstruktor) statt `_make_buffer`: so läuft die produktive
`create()`/`bind()`-Prüfung in jeder Messung mit, statt vom Fake überdeckt zu
werden. Die Attrappen sehen zusätzlich zwei Dinge, die ein echter Treiber
bestenfalls indirekt zeigt: **Doppelfreigabe** (`destroy` auf einem bereits
zerstörten Objekt) und **use-after-delete** (jede Benutzung nach der Freigabe);
sie buchen einen GL-Namen außerdem erst bei **erfolgreichem** `create()` und
können ihn über `fail_create`/`fail_bind` deterministisch verweigern.

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

### 4.4 Verschärfte False-Green-Abwehr – stille Pufferfehler (#711)

Nachtrag zu diesem Bericht. Die Aussage aus Abschnitt 3, ein fehlgeschlagener
Buffer-Upload könne nicht als bestandener Nachweis durchgehen, galt vor #711 nur
für *sichtbare* Fehlschläge. `QOpenGLBuffer.create()`/`bind()` melden ihren
Fehlschlag ausschließlich über den Rückgabewert – und der wurde ignoriert.

**Reproduktion des alten Zustands** (Attrappen mit `create() == false`, sonst
unveränderter Messaufbau, 120 Zyklen):

```text
Befunde: KEINE -> verdict ok (falsches Grün)
Viewer max: 3 | live nach cleanup: 0
```

Der Viewer hielt drei Wrapper **ohne** GL-Namen, `has_failed` blieb `false`, die
Messreihe war konstant – Urteil `ok`, Exit 0, obwohl nie ein Puffer entstand.
Unter `--mode gl` wäre das genau das falsche Grün, das der Hardware-Nachweis in
#685 nicht liefern darf.

**Nach dem Fix** melden dieselben Läufe einen harten Befund:

```text
--- create()==false ---
BEFUND  Upload fehlgeschlagen: QOpenGLBuffer.create() ist fehlgeschlagen
BEFUND  kein vollständiger Puffer-Upload nachgewiesen (Viewer hielt höchstens 0 statt 3 GL-Objekte)
  live nach cleanup 0, erzeugt 0/freigegeben 0, Viewer max 0, Doppelfreigaben 0, use-after 0

--- bind()==false ---
BEFUND  Upload fehlgeschlagen: QOpenGLBuffer.bind() ist fehlgeschlagen
BEFUND  kein vollständiger Puffer-Upload nachgewiesen (Viewer hielt höchstens 0 statt 3 GL-Objekte)
  live nach cleanup 0, erzeugt 2/freigegeben 2, Viewer max 0, Doppelfreigaben 0, use-after 0
```

Die Bilanz im `bind()`-Fall zeigt den Teilerfolg sauber: VAO und erster Puffer
entstanden (2), beide wurden genau einmal freigegeben (2); der Wrapper des
gescheiterten Puffers wird nie als GL-Objekt gebucht, `allocate()` läuft nicht
mehr.

**Zwei Ebenen, bewusst getrennt** – die Reproduktion oben zeigt, warum beide
nötig sind:

1. **Primär im Viewer.** Nur die Auswertung der Rückgabewerte macht den
   Fehlschlag überhaupt sichtbar. Ohne sie meldete der Viewer weiterhin drei
   gehaltene „Objekte", und *keine* Sondenschwelle könnte das von einem echten
   Upload unterscheiden – die Sonde zählt Referenzen, nicht GL-Namen.
2. **Sekundär in der Sonde.** Weil der Viewer nach dem Fix auf 0 gehaltene
   Objekte zurückfällt, wäre die Messreihe konstant 0 und formal „ohne
   Wachstum". `MIN_LIVE_PER_VIEWER = 3` wertet genau das als Nicht-Nachweis:
   `--mode gl` → Exit 2 (`ProbeNotExecutable`), `--mode fake` → Exit 1.

Beide Ebenen sind als deterministische Regressionstests festgeschrieben (Zeile
„Fehlerpfad: stiller Pufferfehler" in Abschnitt 5), inklusive der Abgrenzung
gegen den zulässigen Fall „kein VAO" (GL-2.1-Erweiterung, drei Puffer genügen)
und einem Lauf über 110 gescheiterte Anläufe in Folge ohne Restbestand,
Doppelfreigabe oder Zugriff nach der Freigabe.

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
| Fehlerpfad: leere/ungültige Daten | `test_empty_height_data_uploads_and_releases_cleanly` (0 Dreiecke), `test_failed_vao_creation_leaves_no_orphans` (VAO-Erzeugung scheitert – zulässig, GL-2.1-Erweiterung) |
| Fehlerpfad: stiller Pufferfehler (#711) | `test_failed_buffer_create_is_treated_as_an_upload_error`, `test_failed_buffer_bind_stops_before_allocate`, `test_partial_buffer_failure_releases_everything_exactly_once`, `test_repeated_partial_failures_do_not_accumulate` (110 gescheiterte Anläufe ohne Restbestand), `test_upload_without_vao_support_still_counts_as_complete` (Abgrenzung), `test_gl_scenario_rejects_an_incomplete_buffer_upload` (Exit 2), `test_probe_reports_a_finding_when_no_buffer_upload_succeeds` / `test_probe_cli_fails_when_buffer_creation_silently_fails` (Exit 1 statt „ok") |
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

### 7.1 Nachmessung nach #711

Gleiche Umgebung, Zweig `claude/github-issue-711-p4ru14`:

| Prüfung | Ergebnis |
|---|---|
| `make check` | grün – ruff „All checks passed", mypy „no issues found in 70 source files", pytest **2082 passed, 6 skipped, 14 deselected** |
| `make ui` (volle qtbot-Suite) | grün – **20 passed** |
| `make coverage` (`fail_under = 86`) | grün – **93 %** gesamt |
| `make gl-stress` (Sonde, 120 Zyklen, Standardsatz) | Exit 0, Urteil `ok`; alle fünf Szenarien `live 4→4`, `max 4`, `480/480`, nach `cleanup_gl` 0; prozessweit `created 2400 / destroyed 2400 / live 0` |
| Negativkontrolle `create() == false` | Exit 1, zwei Befunde (Abschnitt 4.4) |
| Negativkontrolle `bind() == false` | Exit 1, zwei Befunde, Bilanz 2 erzeugt / 2 freigegeben (Abschnitt 4.4) |
| Reproduktion des Zustands vor #711 | Urteil `ok` **ohne** einen einzigen erzeugten Puffer – das behobene falsche Grün (Abschnitt 4.4) |
| `pytest -m gl_smoke` | weiterhin **übersprungen** (keine renderfähige Plattform). `test_repeated_uploads_do_not_accumulate_gl_objects` prüft seit #711 zusätzlich die *Untergrenze* von drei GL-Objekten – auf der Zielhardware kann ein Lauf ohne echten Upload damit nicht mehr grün werden. |

Die neun neuen Regressionstests in `tests/test_viewer_3d_gl_lifecycle.py` laufen
im normalen `pytest`-Satz mit; sie brauchen keinen GL-Kontext, weil die
Fehlschläge über die Attrappen-Rückgabewerte injiziert werden.

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

### 8.1 Nachtrag #711 – erneuter Kandidatenwechsel

Der Fix aus #711 berührt `bgremover/viewer_3d.py`, `scripts/gl_stress_probe.py`,
`tests/**` und die CHANGELOG-Dateien und ist damit **erneut
kandidatenrelevant**. Er verschiebt den Kandidaten also ein weiteres Mal.

Der Freeze wird dafür **nicht** in diesem Zweig nachgezogen: seit PR #708/#709
(README-Korrektur und Freeze-Pin im Release-Workflow) ist das Dokument ohnehin
gegenüber `main` im Rückstand (`make release-freeze-check` meldet dort vier
Fehler und eine Warnung), und der vollständige Nachtrag – neues Commit-Inventar
mit vollen SHAs, #706 als normale SHA-Zeile, Platzhalterzeile auf den finalen
Fix, vereinheitlichter Build-/Tag-SHA-Vertrag – ist als eigenes Issue **#710**
erfasst und dort ausdrücklich *nach* #711 eingeplant. Zwei Teilnachträge würden
sich nur gegenseitig überschreiben; die Reihenfolge lautet
**#711 → #710 → #685 → #686**.

Für #710 relevant: der Fix aus #711 ist Nachweis-/Regressionsarbeit an einer
release-relevanten Prüfung (dieselbe Kategorie wie #684) plus eine eng
begrenzte Fehlerbehebung im Darstellungscode der optionalen 3D-Vorschau. Er
bringt keine Benutzerfunktion, keine Abhängigkeit und keine Formatänderung mit
und ist in `CHANGELOG.md` `[2.7.1]` unter „Behoben" in allen sechs Sprachen
dokumentiert.

## 9. Offene Punkte

- Der Nachweis auf echter GPU/Hardware (Abschnitt 6) steht aus und ist Teil von
  #685. Ohne ihn bleibt Akzeptanzkriterium „Testumgebung … GPU, Treiber" nur für
  die Offscreen-Umgebung erfüllt. Seit #711 gilt dort zusätzlich: ein
  `--mode gl`-Lauf, der keinen vollständigen Puffersatz sieht, endet mit Exit 2
  und **darf nicht** als bestandener Nachweis protokolliert werden.
- Der Protokoll-Commit mit dem neuen Kandidaten-SHA (Abschnitt 8) ist nach dem
  Merge dieses Zweigs fällig – gebündelt in #710 (Abschnitt 8.1).

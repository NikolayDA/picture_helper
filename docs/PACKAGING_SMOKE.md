# Packaging-, Plattform- und Performance-Smokes der 3D-Reliefvorschau

Reproduzierbare **manuelle** Prüfprozeduren für die Abnahmekriterien des Epics
#582 (Issue #595), die sich in der Offscreen-CI **nicht** ehrlich grün melden
lassen: echte GPU-/Renderer-Nachweise, Start der fünf Artefaktklassen und
Screenshots auf realer Grafikhardware. Automatisiert und headless abgedeckte
Kriterien (Geometrie, Gating, Cache/Generation, Nicht-Mutation, Fallback-Zustände,
Mesh-Build-Baseline) liegen in der Testsuite bzw. im Benchmark; siehe
[Abschluss-Matrix](history/EPIC-582-ABNAHME.md).

> Prinzip: Jeder Smoke nennt **Vorbedingung → Schritte → erwartetes Ergebnis**
> und ein Protokollfeld. Kein Kriterium gilt als erfüllt, ohne dass der Lauf mit
> Commit-SHA, Umgebung und Ergebnis im Abnahmeprotokoll (#582-Abschlusskommentar)
> festgehalten ist.

## 1. Referenzumgebung erfassen

Die 3D-Vorschau ist reine Anzeige; absolute Zeiten hängen an der Grafikhardware.
Jeder Performance-/Plattform-Smoke protokolliert zuerst die Umgebung:

```sh
python - <<'PY'
import platform, sys
print("python", sys.version.split()[0], platform.machine(), platform.system(), platform.release())
PY
# GL-Backend (Linux): Vendor/Renderer/Version
QT_QPA_PLATFORM=xcb python -c "from bgremover.preview3d_capability import probe_3d_capability as p; print(p(use_cache=False))"
```

Festzuhalten: OS/Release, Architektur, CPU-Anzahl, GPU/Treiber bzw. Software-
Renderer (llvmpipe), Qt-/PyQt6-Version, ob X11/Wayland/Cocoa.

## 2. Performance-/Ressourcen-Protokoll

### 2.1 Mesh-Build, Peak-Speicher, Budgets (automatisiert, reproduzierbar)

```sh
QT_QPA_PLATFORM=offscreen python scripts/benchmark.py run --height-bench --no-compare
```

Liefert je Szenario (`HEIGHT16-1MP`/`-16MP`/`-40MP`) die Metriken
`mesh_build_ms`, `mesh_peak_mb`, `mesh_vertices`, `mesh_triangles`,
`mesh_decimation` (siehe [`benchmarks/README.md`](../benchmarks/README.md)).
Nachweise:

- **Kein Vollmesh bei 40 MP:** `mesh_vertices ≤ 262 144`
  (`MeshQuality.STANDARD.max_vertices`) und `mesh_peak_mb` deutlich unter dem
  128-MB-Deckel bei allen drei Größen.
- **Vertex-/Triangle-/CPU-Limits:** die vier `mesh_*`-Zahlen im JSON.
- **Regressionsschwelle:** `--metric mesh_build_ms --fail-on-regression`
  (Bestätigungslauf + 10-%-Schwelle wie bei `process_ms`).

### 2.2 GPU-Upload, Framerate, Update-Latenz (manuell, hardwaregebunden)

Vorbedingung: gebautes Artefakt **oder** Quell-Lauf unter echtem Backend
(`QT_QPA_PLATFORM=xcb`/Wayland/Cocoa) mit 3D-Capability.

Schritte:

1. Projekt mit 1-MP-, 16-MP- und 40-MP-HEIGHT laden, 3D-Vorschau öffnen.
2. Zeit bis erste sichtbare Vorschau grob stoppen (Debounce 200 ms + Build +
   Upload); Mesh-Build-Anteil aus 2.1 abziehen ⇒ Upload-Anteil.
3. Orbit/Pan/Zoom über ~10 s mit maximal zulässigem Mesh (HIGH); subjektiv
   flüssig? Bei Bedarf FPS-Overlay des Treibers nutzen.
4. Zehn schnelle HEIGHT-Änderungen in Folge auslösen: Vorschau bleibt reaktiv,
   nur der letzte Zustand wird gebaut (Debounce/Stale, automatisiert in
   `tests/test_preview3d_acceptance.py::test_ten_rapid_changes_build_only_latest_and_discard_stale`);
   Speicher fällt danach zurück (Task-Manager/`/usr/bin/time -v`).

Erwartet: interaktiv flüssig auf der Referenz-GPU; llvmpipe langsamer, aber ohne
Absturz. Abweichungen mit Begründung protokollieren.

### 2.3 Lifecycle-/Leak-Beobachtung

- Automatisiert: `tests/test_preview3d_acceptance.py::test_hundred_viewer_lifecycle_cycles_do_not_leak_or_crash`
  (100× Build/Anzeige/GL-Cleanup: Cache hält genau ein Mesh, ≤ 1 GL-Viewer).
- Manuell: 100× Projekt-/Moduswechsel unter `valgrind --tool=massif` bzw.
  RSS-Beobachtung; RSS pendelt sich ein, kein stetiges Wachstum.

## 3. Robustheits-/Fallback-Smokes

Automatisiert (headless, laufen in CI):

| Fehlerbild | Nachweis |
|---|---|
| Fehlender GL-Kontext / nicht unterstützte API | `tests/test_preview3d_capability.py::test_offscreen_default_probe_reports_unavailable`, `tests/test_preview3d_controller.py::test_unavailable_capability_shows_unavailable` |
| Shader-/Init-Fehler ohne Prozessabsturz | `tests/test_viewer_3d.py::test_gl_viewer_reports_init_failure_without_propagating` |
| Buffer-/Build-Fehler → Fehlerzustand + Retry | `tests/test_preview3d_controller.py::test_mesh_build_error_shows_error_state`, `tests/test_viewer_3d.py::test_failed_viewer_is_recreated_on_retry` |
| Kontextverlust → Reupload der CPU-Kopie | `tests/test_viewer_3d.py::test_context_loss_requeues_cpu_mesh_for_upload` |
| Projekt/History unbeschädigt nach Viewerfehler | `tests/test_preview3d_acceptance.py::test_viewer_error_does_not_corrupt_project_or_history` |

Manuell (Renderer erzwingen):

```sh
# Software-Renderer (llvmpipe) statt GPU:
LIBGL_ALWAYS_SOFTWARE=1 QT_QPA_PLATFORM=xcb python -m bgremover
# 3D absichtlich „nicht verfügbar": headless-Backend
QT_QPA_PLATFORM=offscreen python -m bgremover   # zeigt „nicht verfügbar" + Erneut versuchen
```

Erwartet in allen Fällen: **kein** Prozessabsturz, kontrollierter
`unavailable`/`error`-Zustand mit „2D-Relief anzeigen"/„Erneut versuchen", und
Bearbeitung/Projekt-Save/Export bleiben voll funktionsfähig.

## 4. Packaging-/Start-Smokes (fünf Artefaktklassen)

Für jede Klasse: Artefakt aus dem Release-Build beziehen, dann **headless**
(Start-Crash-/Fork-Bomb-Wächter) **und** unter echtem Backend (3D sichtbar)
starten.

Headless-Start (funktioniert für AppImage/`.app`-Binary):

```sh
QT_QPA_PLATFORM=offscreen python scripts/smoke_launch.py \
    --match <artefakt-token> --timeout 120 -- <startkommando>
```

| # | Artefaktklasse | Headless-Start | 3D-Sicht-Smoke | sauber entfernbar |
|---|---|---|---|---|
| 1 | Linux x86_64 AppImage | `smoke_launch.py` Exit 0 | unter xcb/Wayland: 3D öffnet, Ramp sichtbar | — |
| 2 | Linux aarch64 AppImage | nativer/CI-Smoke Exit 0 | nativer Zielumgebungs-Smoke | — |
| 3 | Linux x86_64 `.deb` | Installation + `smoke_launch.py` | 3D **oder** dokumentierter 2D-Fallback | `apt remove` rückstandsfrei |
| 4 | Linux aarch64 `.deb` | Zielumgebungs-Smoke | 3D/Fallback | rückstandsfrei |
| 5 | macOS arm64 DMG | `.app`-Binary Exit 0 | Retina/High-DPI: 3D öffnet | — |

Zusätzlich je Artefakt prüfen:

- Shader/Assets werden **arbeitsverzeichnisunabhängig** gefunden (die GLSL-Quellen
  sind als String-Literale in `bgremover/viewer_3d.py` eingebettet – keine
  externen Shader-Dateien; automatisiert flankiert durch
  `tests/test_app_smoke.py`).
- Keine neue Laufzeit-Pflichtabhängigkeit: der GL-Pfad nutzt ausschließlich die
  vorhandenen PyQt6-`QtOpenGL*`-Module. Lizenz-/Notice-Dateien bleiben
  unverändert (`make license-check`).
- Paketgröße und Startzeit gegen die #591-Baseline messen; Überschreitung
  begründen.

## 5. Screenshots

Auf realer Grafikhardware (nicht offscreen) aufnehmen. Der Generator legt den
vollständigen Satz samt `manifest.md` unter
`app_screenshots/bgremover_complete_<Zeitstempel>/` ab; der abgenommene native
3D-Zustand wird in README und ihren Sprachspiegeln verlinkt:

```sh
make screenshots-live-3d
```

Der Hybrid-Lauf erzeugt zuerst den vollständigen Offscreen-Satz und ergänzt
danach in einem nativen Qt/OpenGL-Teilprozess die 3D-Zustände. Für die Abnahme
müssen insbesondere `75_function_preview3d_loading.png`,
`76_function_preview3d_ready.png`, `77_function_preview3d_adjusted.png`,
`77b_function_preview3d_controls.png`, `78_function_preview3d_error.png` und
`79_function_preview3d_fallback.png` im Manifest erscheinen. Das Manifest muss
außerdem Aufnahmezeit, Qt-Plattform, Betriebssystem/Architektur und OpenGL
Vendor/Renderer/Version nennen; bekannte Software-Renderer werden vom Generator
abgelehnt. `76_function_preview3d_ready.png` und
`77_function_preview3d_adjusted.png` müssen ein gerendertes Relief zeigen, nicht
nur den Loading- oder Fallback-Text.

1. **Normaler 3D-Zustand:** geladenes HEIGHT-Relief, sichtbares Hillshade.
2. **Controls:** Segment „Darstellung [2D|3D]", Überhöhungs-/Licht-Regler und
   Decimation-Badge in `77_function_preview3d_adjusted.png`; die nach unten
   gescrollte Aufnahme `77b_function_preview3d_controls.png` zeigt zusätzlich
   Licht-Höhe, Qualitätswahl sowie Einpassen/Zurücksetzen.
3. **Fallback/Empty:** „nicht verfügbar" **oder** „kein HEIGHT" mit den
   Aktions-Buttons.

Der Offscreen-Render-Smoke `tests/test_viewer_3d_gl.py` (Marker `gl_smoke`)
belegt unter echtem Backend zusätzlich, dass ein nicht-schwarzes Frame ohne
Viewer-Fehler entsteht.

## 6. Go-/No-Go

Erst wenn Abschnitte 2–5 mit Commit-SHA, Umgebung und Ergebnissen protokolliert
sind, ist die Release-Freigabe (eigener Scope, siehe #582/#595) begründbar. Die
automatisierten Teile (2.1, 2.3, 3) laufen in jeder CI mit; die manuellen Teile
gehören in den Abschlusskommentar von #582.

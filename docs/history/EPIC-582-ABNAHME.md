# Abnahme-Matrix: Epic #582 – Echte 3D-Reliefvorschau

Verknüpft jedes Akzeptanzkriterium des Epics #582 (Abnahme-Issue #595) mit seinem
Nachweis (PR, Test, Benchmark, Screenshot oder Plattform-Smoke). Entscheidung/
Verträge: ADR
[ADR-2026-3d-reliefvorschau-renderer.md](ADR-2026-3d-reliefvorschau-renderer.md)
(#591), UX-Vertrag [UX_3D_PREVIEW.md](../UX_3D_PREVIEW.md). Umsetzung: #592–#595
(PR #620) + Post-Merge-Audit (PR #621). Manuelle, hardwaregebundene Prozeduren:
[PACKAGING_SMOKE.md](../PACKAGING_SMOKE.md).

Der 3D-Viewer ist **reine Darstellung ohne Schreibpfad ins Modell**: „Bild
speichern", EufyMake- und Projekt-Export bleiben unverändert, die
2D-`PreviewMode`-Pipeline bleibt der garantierte Fallback.

## Performance und Ressourcen

| Kriterium | Nachweis |
|---|---|
| Mesh-Build, Peak-Speicher, Vertex-/Triangle-Budgets messbar/reproduzierbar | `scripts/benchmark.py` (`benchmark_mesh_build`, Metriken `mesh_build_ms`/`mesh_peak_mb`/`mesh_vertices`/`mesh_triangles`/`mesh_decimation` je `HEIGHT16-1MP/16MP/40MP`), `tests/test_benchmark.py::test_run_benchmark_includes_mesh_build_metrics`, `::test_benchmark_mesh_build_respects_quality_budget`, [`benchmarks/README.md`](../../benchmarks/README.md) |
| 40-MP-Eingabe erzeugt nie ein unbeschränktes Vollmesh | `tests/test_relief_mesh.py::test_budget_respected_for_large_input`, `::test_wide_aspect_is_memory_bounded` (Peak < 128 MB), `tests/test_benchmark.py::test_benchmark_mesh_build_respects_quality_budget` (`mesh_vertices ≤ 262 144`, `mesh_peak_mb < 128 MB`) |
| Zehn schnelle Änderungen entprellt; veraltete Jobs/Uploads verworfen; Speicher fällt zurück | `tests/test_preview3d_acceptance.py::test_ten_rapid_changes_build_only_latest_and_discard_stale`, `tests/test_preview3d_controller.py::test_stale_generation_is_discarded`, `::test_supersede_cancels_running_build` |
| Cache-Hits vermeiden Rebuild; Cache-Miss/Invalidierung korrekt | `tests/test_preview3d_acceptance.py::test_returning_to_cached_state_reuses_without_rebuild`, `tests/test_preview3d_controller.py::test_unchanged_state_reuses_cache_without_rebuild`, `::test_quality_change_triggers_rebuild`, `::test_content_change_triggers_rebuild`, `tests/test_relief_mesh.py::test_cache_key_ignores_camera_but_tracks_geometry` |
| Mindestens 100 Lifecycle-Zyklen ohne stetiges Speicherwachstum | `tests/test_preview3d_acceptance.py::test_hundred_viewer_lifecycle_cycles_do_not_leak_or_crash` (100× Build/Anzeige/GL-Cleanup: Cache hält genau ein Mesh, ≤ 1 GL-Viewer); manuelle RSS/Massif-Beobachtung in [PACKAGING_SMOKE.md](../PACKAGING_SMOKE.md) §2.3 |
| Performance-Regression mit automatisierter Schwelle | Benchmark-Vergleich `--metric mesh_build_ms --fail-on-regression` (Bestätigungslauf + 10-%-Schwelle, Schema 2) |
| GPU-/Renderer-Upload, interaktive Framerate, Update-Latenz auf Referenzhardware | **Manueller Plattform-Smoke** [PACKAGING_SMOKE.md](../PACKAGING_SMOKE.md) §2.2 (hardwaregebunden, offscreen nicht ehrlich messbar) |

## Robustheit und Fallback

| Kriterium | Nachweis |
|---|---|
| Fehlender Kontext / nicht unterstützte API → kontrollierter Zustand | `tests/test_preview3d_capability.py::test_offscreen_default_probe_reports_unavailable`, `tests/test_preview3d_controller.py::test_unavailable_capability_shows_unavailable` |
| Shader-/Init-Fehler ohne Prozessabsturz → 2D-/Fehlerdarstellung | `tests/test_viewer_3d.py::test_gl_viewer_reports_init_failure_without_propagating`, `::test_show_mesh_reaches_ready_or_error` |
| Buffer-/Build-Fehler sicher wiederholbar/abbrechbar | `tests/test_preview3d_controller.py::test_mesh_build_error_shows_error_state`, `tests/test_viewer_3d.py::test_failed_viewer_is_recreated_on_retry`, `tests/test_relief_mesh.py::test_cancel_raises_and_yields_no_mesh` |
| Kontextverlust → Reupload ohne Nutzung freigegebener Objekte | `tests/test_viewer_3d.py::test_context_loss_requeues_cpu_mesh_for_upload` |
| Bearbeitung/Projekt-Save/Export bleiben nach Rendererfehler funktionsfähig | `tests/test_preview3d_acceptance.py::test_viewer_error_does_not_corrupt_project_or_history` |
| Projektwechsel/Schluss während Build/Upload ohne Race | `tests/test_worker_controller.py` (Mesh-Thread-Draining/`shutdown_all`), `tests/test_preview3d_controller.py::test_deactivate_cancels_running_build` |
| Diagnose ohne Bildinhalte/private Pfade/Geheimnisse | `tests/test_preview3d_acceptance.py::test_capability_diagnostic_does_not_leak_paths_or_secrets`, `RendererCapability` trägt nur Vendor/Renderer/Version + i18n-Key |
| Systeme ohne 3D nutzen 2D-Vorschau vollständig weiter | garantierter Fallback: `Relief3DView` (Empty/Unavailable/Error) + 2D-`PreviewMode`-Pipeline unverändert |
| Recovery/Retry ohne Endlosschleife, respektiert Nutzerentscheidung | `tests/test_preview3d_controller.py::test_retry_reevaluates`, `tests/test_viewer_3d.py::test_show2d_and_retry_signals_fire` |

## Packaging und Plattformen

| Kriterium | Nachweis |
|---|---|
| Shader/Assets arbeitsverzeichnisunabhängig gefunden | GLSL als String-Literale in `bgremover/viewer_3d.py` (keine externen Shader-Dateien); `tests/test_app_smoke.py` |
| Offscreen-/Headless-Start bleibt funktionsfähig | `tests/test_app_smoke.py`, gesamte Offscreen-CI grün; `gl_smoke`-Tests self-skippen auf offscreen |
| Keine neue Laufzeit-Pflichtabhängigkeit | GL-Pfad nutzt nur vorhandene PyQt6-`QtOpenGL*`-Module; `make license-check` unverändert |
| Fünf Artefaktklassen bauen und bestehen den automatisierten Start-/Crash-Smoke | Release-Läufe [mit KI](https://github.com/NikolayDA/picture_helper/actions/runs/29745404251) und [ohne KI](https://github.com/NikolayDA/picture_helper/actions/runs/29737924197): macOS-arm64-DMG sowie Linux-x86_64-/aarch64-AppImage und `.deb` |
| Sichtbarer 3D-/Fallback-Start auf Zielhardware, saubere Installation/Entfernung, Größe/Startzeit gemessen | **Manuelle Packaging-Smokes** [PACKAGING_SMOKE.md](../PACKAGING_SMOKE.md) §4; der reale Raspberry-Pi-5-AppImage-Smoke ist in [#595](https://github.com/NikolayDA/picture_helper/issues/595) protokolliert, die übrigen Artefakt-/Hardwarekombinationen bleiben Release-Scope |

## End-to-End und Regression

| Kriterium | Nachweis |
|---|---|
| 16-Bit-Low-Bit-Muster aus dem kanonischen Zustand dargestellt, ohne Quantisierung/Mutation | `tests/test_relief_mesh.py::test_height_maps_to_z_independent_of_bit_depth`, `::test_source_field_not_mutated`, Canvas speist `layer.height_data` (16-Bit) direkt ein |
| Workflow öffnen → HEIGHT → 3D → Orbit/Pan/Zoom → ändern → Undo/Redo → Save/Open → 3D | `tests/test_preview3d_integration.py` (Gating/Moduswechsel/Nicht-Mutation/Persistenz), `tests/test_preview3d_acceptance.py::test_viewer_error_does_not_corrupt_project_or_history` (Undo nach 3D), Camera-Uniforms `tests/test_preview3d_camera.py`; End-to-End-Sichtprüfung [PACKAGING_SMOKE.md](../PACKAGING_SMOKE.md) §2.2 |
| Moduswechsel Rohbild ↔ 2D-Relief ↔ 3D wiederholbar | `tests/test_preview3d_acceptance.py::test_repeated_mode_switches_are_stable`, `tests/test_preview3d_integration.py::test_toggle_switches_canvas_stack_and_menu` |
| COLOR/HEIGHT/GLOSS-Mischprojekte verhalten sich korrekt | `tests/test_preview3d_acceptance.py::test_mixed_project_feeds_height_layer_to_3d` |
| Exportdateien byte-/semantisch identisch vor/nach 3D-Interaktion | `tests/test_preview3d_acceptance.py::test_export_bytes_identical_after_full_3d_interaction`, `tests/test_preview3d_integration.py::test_3d_mode_does_not_mutate_project` |
| Kamera-/Überhöhungs-/Qualitätseinstellungen folgen dem Sitzungs-/Projektvertrag | `tests/test_preview3d_integration.py::test_persisted_3d_state_is_reflected_and_reset_consistently` |
| Kernpfade headless/offscreen automatisiert; manuelle Smokes reproduzierbar | 3D-Testsuite (`test_relief_mesh`/`_camera`/`_capability`/`_controller`/`_viewer_3d`/`_integration`/`_acceptance`) + [PACKAGING_SMOKE.md](../PACKAGING_SMOKE.md) |
| Bestehende 2D-Preview-/Canvas-/Projekt-/Export-/i18n-Tests bleiben grün | volle Suite unter `make check` |
| `make pr-check` und relevante CI-Matrix grün | Gate-Läufe PR #620/#621; jede Folgeänderung durchläuft erneut den vollständigen PR-Gate |

## Dokumentation, UX und Abschluss

| Kriterium | Nachweis |
|---|---|
| Nutzerdoku: Zweck, 3D-vs-2D, Einstieg, Steuerung, Überhöhung, Decimation, Fallback | README.md und ANLEITUNG.md (jeweils + 5 Spiegel), [UX_3D_PREVIEW.md](../UX_3D_PREVIEW.md) |
| 3D ist Vorschau, verändert weder HEIGHT noch Export | README.md, ANLEITUNG.md, [UX_3D_PREVIEW.md](../UX_3D_PREVIEW.md), CLAUDE.md-Architektur |
| Troubleshooting (fehlende GPU/API, schwarzer Viewport, Treiberfehler, langsame Vorschau, Fallback) | ANLEITUNG.md, [PACKAGING_SMOKE.md](../PACKAGING_SMOKE.md) §3 |
| Sechs Sprachfassungen synchron | README-/ANLEITUNG-Spiegel de/en/es/fr/uk/zh; Struktur-, Link- und 3D-Inhaltsprüfung in `tests/test_i18n_docs.py`; Laufzeit-Keys de/en in `tests/test_i18n_*` |
| Tastatur-/Accessibility-Hinweise dokumentiert | `tests/test_viewer_3d.py::test_accessible_names_present`, UX-Vertrag |
| Entwicklerdoku: Grenzen, Datenfluss, Budgets, Cache, Tests, Erweiterungspunkte | ADR #591, CLAUDE.md-Architekturabschnitt |
| Changelog nennt Plattformanforderungen und 2D-Fallback | CHANGELOG.md (+ 5 Spiegel) |
| Abschlussmatrix verknüpft jedes Kriterium mit Nachweis | **dieses Dokument** |
| Screenshots (3D, Controls, Fallback/Empty) | `make screenshots-live-3d` + [Manifest des Abnahmelaufs](../../app_screenshots/bgremover_complete_20260719_162826/manifest.md): `76_function_preview3d_ready.png`, `77_function_preview3d_adjusted.png` und `79_function_preview3d_fallback.png`; die README-Spiegel zeigen den nativen OpenGL-3D-Zustand |

## Bewusste Grenzen / offener Release-Scope (keine MVP-Blocker)

Die automatisierten Start-Smokes der fünf Artefaktklassen sind in den oben
verlinkten Release-Läufen grün. Auch der vollständige Screenshot-Satz ist
erzeugt: Die Ready-/Controls-Aufnahmen stammen laut
[Manifest](../../app_screenshots/bgremover_complete_20260719_162826/manifest.md)
von nativer Qt-/OpenGL-Grafikhardware; Fallback und Fehlerzustand wurden
deterministisch ergänzt.

Die folgenden Kriterien sind **nicht** durch diese Headless-/CI-Nachweise
abgedeckt und bleiben – wie im Issue #595 vorgesehen – dem eigenen
Release-Scope vorbehalten. Sie sind als reproduzierbare manuelle Prozeduren in
[PACKAGING_SMOKE.md](../PACKAGING_SMOKE.md) hinterlegt:

- GPU-/Renderer-Upload, interaktive Framerate und Update-Latenz auf der
  #591-Referenzhardware (§2.2).
- Sicht-/Installations-/Entfernungs-Smokes der noch nicht real protokollierten
  Artefakt-/Hardwarekombinationen inklusive Paketgröße und Startzeit gegen die
  #591-Baseline (§4). Der Raspberry-Pi-5-/aarch64-AppImage-Nachweis ist bereits
  in [#595](https://github.com/NikolayDA/picture_helper/issues/595) festgehalten.

Erst nach protokollierten manuellen Smokes (Commit-SHA, Umgebung, Ergebnis im
#582-Abschlusskommentar) ist die Produktveröffentlichung begründbar; der Abschluss
dieses Epics erzwingt sie nicht automatisch.

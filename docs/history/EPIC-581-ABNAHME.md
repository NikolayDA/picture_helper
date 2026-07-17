# Abnahme-Matrix: Epic #581 – Durchgängige 16-Bit-Höhenpipeline

Verknüpft jedes Akzeptanzkriterium des Epics #581 mit seinem Nachweis
(PR, Test oder Dokument). Datenvertrag: ADR
[ADR-2026-height-16bit-datenvertrag.md](ADR-2026-height-16bit-datenvertrag.md)
(#586). Umsetzung: #587 + #588 (PR #610, inkl. Review-Nachtrag `a42fe77`,
und Future-Version-Härtung PR #614), #589 (PR #612), #590 (PR #613).

| Epic-Kriterium | Nachweis |
|---|---|
| Alle Sub-Issues geschlossen | #586, #587, #588, #589, #590 (jeweils mit PR-Verweis geschlossen) |
| ADR mit Repräsentation, Coverage, Anzeigeableitung, Migration, Budget, Alternativen | [ADR #586](ADR-2026-height-16bit-datenvertrag.md) |
| Synthetisches Höhenfeld mit Niederbits übersteht Import → ≥ 2 Operationen → Undo/Redo → Save/Load → 16-Bit-Export bitgenau | `tests/test_height16_e2e.py::test_gradient_e2e_import_edit_save_export_reimport`, `::test_undo_redo_before_and_after_project_roundtrip`, `::test_low_bit_pattern_stays_distinguishable_until_lossless_export` |
| Bestehende Projektformate laden weiter; 8-Bit-Höhen migrieren deterministisch dokumentiert | `tests/test_project_io.py::test_v1_fixture_loads_and_migrates_deterministically`, `tests/test_height16_e2e.py::test_legacy_v1_project_migrates_edits_and_saves_reproducibly`, [PROJECT_FORMAT.md](../PROJECT_FORMAT.md) |
| Kein versehentlicher 8-Bit-Rückfall durch Preview, Layerwechsel, Duplizieren, Resize, Snapshot oder Speichern | `tests/test_canvas_layers.py::test_height_preview_never_writes_back_into_payload`, `::test_relief_preview_renders_from_canonical_16bit_payload`, `tests/test_project_model.py` (Duplicate/Resize/Swap), `tests/test_project_history.py` (bitgenaue Snapshots), `tests/test_project_io.py` (v2-Roundtrips) |
| 8-Bit-Export kontrolliert quantisiert; 16-Bit-Export echte Quellpräzision | `tests/test_height16_e2e.py::test_8bit_export_matches_reference_quantization`, `::test_16bit_export_metadata_and_independent_reread`, `tests/test_eufymake_writer.py` (Niederbit-Re-Read) |
| COLOR-/GLOSS- und Exportverhalten regressionsfrei | `tests/test_project_history.py::test_color_and_gloss_snapshots_stay_rgba_accounted`, `tests/test_height16_e2e.py::test_mixed_project_roundtrip_and_export_without_regression`, bestehende eufymake-/Canvas-Suiten grün |
| 40-MP-Grenzen, History-Budget, Temp-Puffer bewertet/limitiert/getestet | `tests/test_project_history.py::test_40mp_height_scenario_stays_within_adr_budget`, `tests/test_project_io.py::test_40mp_height_project_saves_and_opens_within_budget`, `tests/test_height16_e2e.py::test_40mp_e2e_stays_within_budgets` (nightly, `ui`-Marker), `scripts/benchmark.py` (`HEIGHT16-1MP/16MP/40MP`-Baseline) |
| Projektdatei-Validierung defensiv, Schreiben atomar | `tests/test_project_io.py::test_future_version_manifest_is_rejected`, `::test_future_version_file_is_rejected_without_modification`, `tests/test_main_window.py::test_future_project_version_keeps_current_project`, weitere Integritäts-/Security-Negativtests und Schreibabbruch, [PROJECT_FORMAT.md](../PROJECT_FORMAT.md) |
| Laufzeit-i18n, Doku, CHANGELOG konsistent | i18n-Paritätstests (6 Sprachen), ANLEITUNG + 5 Spiegel, CHANGELOG + 5 Spiegel, CLAUDE.md |
| `make pr-check`, `make check`, `make ui` grün; neue Qt-freie Module strikt getypt | Gate-Läufe der PRs #610/#612/#613/#614; `height_map`/`height_ops`/`project_*`/`eufymake_*` in der strikten mypy-Liste |

## Bewusste Grenzen (dokumentiert, keine offenen Pflichtkriterien)

- Pillow-quantisierte 16-Bit-Quellen (Grau+Alpha, Farbe) werden abgewiesen
  statt verlustfrei gelesen – klare Meldung, dokumentiert in ANLEITUNG und
  `image_loading` (Codex-Review #612).
- Ältere BgRemover-Versionen (≤ 2.6.0) können v2-Projektdateien nicht
  öffnen (kontrollierter Abweisungsfehler, [PROJECT_FORMAT.md](../PROJECT_FORMAT.md)).
- Generische RGBA-Pixelwerkzeuge auf HEIGHT-Ebenen laufen über den geloggten
  Legacy-Adapter (bewusst quantisierende Klasse im Operations-Inventar,
  `height_map`-Docstring).
- Die echte 3D-Vorschau konsumiert denselben `HeightField`-Vertrag, ist aber
  Epic #582 (ADR [ADR-2026-3d-reliefvorschau-renderer.md](ADR-2026-3d-reliefvorschau-renderer.md)).

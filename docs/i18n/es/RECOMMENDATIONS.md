[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones valoradas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Debe corregirse: provoca errores, bloqueos o inconsistencias |
| 🟠 | Alta | Debe corregirse pronto: afecta de forma importante a la fiabilidad o mantenibilidad |
| 🟡 | Media | Recomendado: mejora calidad de código, legibilidad o testabilidad |
| 🟢 | Baja | Opcional: pulido y mejoras complementarias |

---

## Estado actual (2026-06-01, revisión «modest-shannon»)

Revisión profunda del código posterior a v2.2 (código, docs, tests). Base excelente: ruff/mypy limpios, suite verde, cobertura 88 %. Encontrados **5 hallazgos (A–E)**: todos implementados, con tests de regresión, y fusionados vía **PR #135** (A, B) y **PR #136** (C–E). La evidencia se da con referencia a archivo/función.

### Estado de finalización

| Estado | Puntos |
|--------|--------|
| ✅ Hecho | A, B, C, D, E |

### Hallazgos

- **A 🟠 — Capturar `DecompressionBombError`.** `image_loading.py` no capturaba el `DecompressionBombError` de Pillow (no es subclase de `OSError`) → las imágenes por encima de 2× `MAX_IMAGE_PIXELS` (80 MP) eludían el mensaje amistoso «demasiado grande» y se propagaban sin capturar en la ruta síncrona `load_image`. Ahora se captura en ambas fases de apertura y se asigna al mensaje estándar; el test de regresión dispara la protección real de Pillow (sin mock de `Image.open`).
- **B 🟡 — Ciclo de vida de la varita mágica al cambiar de imagen.** `_reset_transient_state` (`canvas.py`) no restablecía `_wand_busy`, y `_load_image_async` (`main_window.py`) no cancelaba el flood fill: asimétrico con `cancel_ai()`. Consecuencia: la varita quedaba bloqueada tras cambiar/restaurar la imagen, además de CPU desperdiciada. Reinicio central del flag + `cancel_flood_fill()` al cargar.
- **C 🟡 — Aislamiento del logging.** `_setup_logging` (`logging_config.py`) usaba `basicConfig(force=True)` en la raíz → logs de terceros (rembg/onnxruntime/Pillow) acababan en el archivo de log de soporte, y los handlers ajenos se arrancaban. Ahora el logger nombrado `BgRemover` con sus propios handlers (`propagate=False`).
- **D 🟢 — Lastre de tests.** `test_static_checks.py` buscaba el monolito `BgRemover.py` eliminado y llevaba marcas `#N` engañosas (rondas históricas ≠ numeración actual). Rama del monolito eliminada, origen aclarado en la docstring.
- **E 🟢 — Red de seguridad i18n.** La comprobación de deriva suave solo cubría 3 de 8 docs traducidos. `WATCHED_DOCS` ampliado a los 8 (todos actualmente sincronizados estructuralmente).

---

## Recomendaciones abiertas

Mejoras surgidas del segundo análisis aún no implementadas (producto/proceso):

- **O1 🟠 — Localización de la app.** La UI está codificada en alemán; no hay i18n en tiempo de ejecución (sin `QTranslator`/`tr()`), aunque la documentación existe en cinco idiomas. Los mensajes de estado ya están centralizados (`status_messages.py`). De forma incremental vía Qt Linguist (`.ts`) o una tabla de cadenas ligera por `QLocale`.
- **O2 🟡 — App de Linux / empaquetado.** No hay bundle para Linux; arranque solo vía `python -m bgremover` desde una venv. Un paquete instalable (AppImage/Flatpak/`.deb`) para **Raspberry Pi OS** y grandes distribuciones (Debian/Ubuntu/Fedora) reduce la barrera de entrada para quienes no programan, análogo al bundle `.app` de macOS.
- **O3 🟡 — Matriz completa de CI antes.** La matriz completa (Linux/macOS × 3.10–3.13) solo corre en tags/release; las regresiones en macOS o Python 3.10/3.13 aparecen tarde. Ejecutarla también en push a `main` o como cron semanal.
- **O4 🟢 — Atajos de teclado para herramientas.** Varita/pincel/borrador/lazo solo se alcanzan con el ratón; añadir cambio con una tecla (p. ej. `B`/`E`).


## Paquetes de implementación de la contrarrevisión de calidad

Los hallazgos confirmados de calidad y estabilidad se agrupan en cuatro paquetes separados:

- **P1 ✅ — Mejoras rápidas de varita / CI (N1, N6, N8).** Liberar silenciosamente el bloqueo de la varita al iniciar un cambio de imagen para que un fallo posterior de carga no bloquee la herramienta. La CI completa de Linux instala ahora también `libgl1`; un test estático de deriva protege las listas de paquetes de sistema Qt. Se corrigió la nota obsoleta sobre la ruta síncrona de arrastrar y soltar.
- **P2 🟡 — Reforzar el guardado (N4, N5).** Validar explícitamente las extensiones de exportación y sustituir archivos existentes mediante un archivo temporal y reemplazo atómico.
- **P3 🟠 — Presupuesto de memoria adaptativo (N2, N3).** Comprobar el tamaño esperado antes de rotaciones libres; presupuestar conjuntamente undo, redo, estado original y operaciones intensivas en memoria, especialmente para Raspberry Pi.
- **P4 🟡 — Desacoplar imports del paquete (N7).** Reducir cuidadosamente o cargar de forma diferida los reexports GUI eager para que los módulos de lógica pura puedan probarse y reutilizarse sin un runtime Qt completo. No es un bug de bootstrap; los imports públicos deben seguir siendo compatibles.


---

## Ronda anterior (v2.2, «admiring-mayer»)

Lista externa de 15 puntos verificada contra el código: **#1–#15 hechos, #4 descartado** (falso positivo). Detalles en los PR fusionados y el archivo.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).

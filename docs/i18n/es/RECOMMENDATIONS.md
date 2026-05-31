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

## Estado actual (2026, revisión «admiring-mayer»)

Revisión de una lista de recomendaciones enviada externamente (15 hallazgos) contra el código real. Resultado: **14 confirmados, 1 falso positivo** (#4). Los hallazgos confirmados se agrupan abajo en **seis paquetes de implementación**; el orden de los paquetes es también el orden de trabajo recomendado. Cada entrada conserva el hallazgo original, la evidencia (`archivo:línea`) y la dirección de la corrección; la tabla siguiente rige el estado actual de implementación. La numeración (#1–#15) corresponde a la lista de revisión original.

Hallazgos históricos y registros de trabajo completos (rondas 1–5): [../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).

### Estado de finalización (comprobado el 2026-05-31)

| Estado | Puntos |
|--------|--------|
| ✅ Hecho | #1, #2, #8, #10, #11, #14, #15 |
| 🟡 Hecho parcialmente | #13 – están cubiertas cinco de las seis áreas de tests dinámicos solicitadas; aún falta el test del presupuesto tras restaurar |
| ⬜ Abierto | #3, #5, #6, #7, #12 |
| ➖ Descartado | #4 – falso positivo |

---

## Paquetes de recomendaciones

**Paquete 1 — Hacer de inmediato** 🔴

- **#1 La cancelación de la IA debe finalizar el hilo.** `AIWorker._work` (`bgremover/workers.py:74`) retorna al cancelar sin emitir señal; `quit_on=(finished, error)` (`bgremover/worker_controller.py:152`) entonces nunca se dispara → el QThread sigue corriendo, `ai_thread`/`ai_worker` quedan fijados y el botón de IA queda desactivado el resto de la sesión (disparador: «cargar una imagen mientras la IA está procesando»). Solución: emitir una señal `done` sin parámetros en el bloque `finally` (`_always_finished`) e incluirla en `quit_on`; la infraestructura ya existe (worker de warmup). **Implementado en este PR, incl. test del ciclo de cancelación.**

**Paquete 2 — Victorias rápidas y seguras (hecho)** 🟠 🟡

- **#2 Restablecer el estado transitorio del canvas de forma central.** `apply_loaded_image` (`canvas.py:234`) llama a `cancel_overlay_only()` sin `cropModeChanged(False)` y no cancela el lazo → la secuencia de señal de recorte queda en `[True]` y sobreviven puntos de lazo antiguos. Introducir un método `_reset_transient_state()`.
- **#11 Configurar el logging con independencia de handlers ajenos.** `logging.basicConfig()` (`logging_config.py:61`) es un no-op si el logger raíz ya tiene handlers → la ruta de log mostrada ≠ la que realmente se escribe. Configurar explícitamente el logger nombrado `BgRemover` (más limpio que `force=True`).
- **#10 Apuntar el script de diagnóstico a la ruta de log actual.** `diagnose_mac.sh:178` aún lee `~/.bgremover.log`; el logger escribe realmente en `~/Library/Application Support/BgRemover/bgremover.log` (QStandardPaths). Alinear la ruta.
- **#8 Normalizar el formato de exportación de forma robusta.** `_save_as` (`main_window.py:304`) descarta el filtro elegido en el diálogo; `save_image_file` (`image_ops.py:46`) guarda silenciosamente como PNG cuando falta la extensión. Modelo de formato central con sufijo por defecto; unificar los dicts de formato duplicados (diálogo vs. MainWindow). *(El `KeyError` de EXR reportado solo es alcanzable con ajustes manipulados/deriva de dicts; el caso de extensión faltante es el núcleo visible para el usuario.)*
- **#14 Sincronizar CI y comprobaciones de documentación.** `RESOURCES.md:102` y `TESTING.md:10` aún dicen «3.10/3.12» (en realidad 3.10–3.13); `ui-nightly.yml` falta en las listas de workflows y en `test_resource_docs.py:35`. Comprobar también la lista de workflows y la matriz de Python.
- **#15 Convertir la CI de release en una verdadera puerta.** `ci.yml` ejecuta la matriz completa solo en `release: published` (demasiado tarde como puerta); `ui-nightly.yml:18` `continue-on-error: true` enmascara fallos. Añadir una ejecución candidata por tag/pre-release y dejar que los fallos nocturnos escalen de forma visible.

**Paquete 3 — Sustancia con medición** 🟠

- **#5 No reasignar el overlay en cada movimiento del pincel.** `_refresh_overlay` (`canvas.py:263`) → `mask_to_overlay` construye un overlay RGBA completo (40 MP ≈ 160 MiB), incluso con máscara vacía y en cada movimiento del ratón. Crearlo de forma diferida, actualizar una región sucia o agrupar eventos.
- **#6 Acotar la varita mágica, hacerla cancelable, medirla.** `flood_fill` (`image_utils.py:48`) hace crecer la región en Python; medido ≈ 3,3 s a 2,25 MP (→ segundos de dos cifras a 40 MP). Añadir una implementación scanline/nativa (p. ej. `scipy.ndimage.label`) y una ruta de cancelación.
- **#7 Serializar el warmup de rembg y la llamada de IA.** `_on_warmup_done` (`main_window.py:270`) muestra «IA lista» incluso tras errores de warmup; el botón de IA sigue usable durante el warmup → init de modelo en paralelo. Separar éxito/error y bloquear el botón hasta terminar el warmup.
- **#3 Aplicar el presupuesto de memoria del historial.** `restore` (`canvas_history.py:81`) y `redo` (`:47`) añaden a la pila de deshacer pero saltan la expulsión de `push` → restaurar repetidamente crece sin límite. Usar un helper de recorte común y testear el presupuesto total.

**Paquete 4 — Seguridad** 🟡

- **#12 Endurecer el staging temporal de plugins de Qt.** `qt_plugins.py` (líneas 26/29/48) usa en macOS una ruta predecible en `/private/tmp`, archivos `.tmp` fijos y solo una comparación de tamaño. Como ahí se cargan plugins de Qt ejecutables, el pre-sembrado es un vector local de inyección de código. Usar un directorio `0700` específico de usuario, archivos temporales únicos y comprobación de contenido/hash.

**Paquete 5 — Tests y metodología** 🟡

- **#13 Orientar los tests al comportamiento, no al texto fuente.** Las comprobaciones AST en `test_static_checks.py` solo verifican apariciones de cadenas y no detectan el fallo de cancelación de IA (#1). Añadir tests dinámicos para el ciclo de cancelación, cargar durante recorte/lazo, error de warmup, formato de exportación desconocido, logging con un handler existente y el presupuesto de memoria tras restaurar.

**Paquete 6 — Descartar / reorientar** 🟢

- **#4 Resta con Cmd en macOS — falso positivo.** Sin `AA_MacDontSwapCtrlAndMeta` (no se fija en ningún sitio), Qt mapea Cmd→`ControlModifier` en macOS; la comprobación en `canvas.py:80` ya responde a Cmd+clic y el texto de la UI es correcto. Aceptar además `MetaModifier` ligaría erróneamente la tecla Control física a «restar». **Descartar el cambio de código**; como mucho, añadir un test de plataforma que fije el mapeo de Qt.

[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-08-31, v2.9.0 publicado, inventario abierto auditado por completo)

**Auditoría diaria 2026-08-31:** Se revisaron los doce PR fusionados hoy
(#927–#932, #935–#938, #940 y #941) y las incidencias que cerraron
(#918–#923, #933 y #934), contrastando diffs de fusión, correcciones de revisión
y pruebas asociadas. La automatización de publicación mantiene un diseño
fail-closed; quedan cubiertos, en particular, la referencia de publicación,
los reintentos, el informe de seguridad, el heartbeat/dry run de runners, el
andamiaje preparatorio y el preflight Qt/GL real con procedencia también en
caso de éxito. Cada hallazgo de revisión se cerró con cobertura de regresión
antes de fusionar. La evidencia de fusión registra 2.908 pruebas pytest; Ruff
pasa localmente, mientras pytest no está disponible por faltar `libGL.so.1` y
mypy por estar activo Python 3.14 en vez de una versión admitida. No queda ningún
hallazgo residual demostrable, por lo que no se necesita una incidencia de
seguimiento. El inventario abierto y las tres recomendaciones siguientes no
cambian.

**Revisión rutinaria 2026-08-30 (delta tras la auditoría completa):** Las 39
incidencias abiertas comprobadas por completo y de forma adversarial contra
`main` (estado de producto `411d47c`) el 2026-08-29 no han cambiado; HEAD
`1d31f2a` solo añade documentación. Las descripciones corregidas de
#681/#882/#905/#906 y las carencias de fixtures/celdas de las pruebas reales
EufyMake #688–#690 siguen visibles correctamente. El nuevo #912 se contrastó
por separado con el aviso de Qt y el artefacto fijado: CVSS 4.0 es 6,3, no
6,8, y no se distribuye el `QtCore5Compat` vulnerable. #912 se corrigió y
cerró como «no afectado»; sin falso riesgo aceptado ni nuevo hallazgo 🔴.

**Adenda 2026-08-29:** v2.9.0 está publicado. La aceptación en hardware pasó
en macOS arm64 y Linux arm64 con renderizadores de GPU reales, la etiqueta y la
publicación se verificaron byte a byte contra el manifiesto de aprobación, y
`PUBLIC-DOWNLOAD-01` y `UPDATE-01` están cumplidos. #881 queda cerrado; los
criterios de Linux x86_64 pausados a propósito siguen visiblemente `PENDING`.
#878 se implementó mediante el PR #908; esta sincronización de cierre cierra
el issue y lo retira de las seis tablas de triaje actuales.

**Revisión rutinaria 2026-08-28:** La comparación en vivo con GitHub añade
los issues abiertos **#878**, **#881**, **#882** y los nuevos sub-issues MAS
**#883–#907**, que faltaban. En aquel momento, #878 debía cerrar la brecha
entre la interfaz estándar/experta y la guía, incluidas capturas y PDF
actuales; la implementación se completó después mediante el PR #908. #881 es
el registro vinculante de aceptación y publicación de 2.9.0;
el build candidato y la revisión previa están en verde, pero faltan la
aceptación en hardware y las aprobaciones humanas. #882 agrupa la vía Mac App
Store como epic bloqueado; #883–#907 concretan sus fases de licencia, cuenta,
sandbox y modelo de IA. La estrategia de licencia debe decidirse antes del
trabajo técnico. No hay nuevos hallazgos 🔴.

**Revisión rutinaria 2026-08-26:** El estado en vivo es ahora de 16 incidencias abiertas (antes 15). Se registró y evaluó de nuevo **#869** (auditoría automatizada de la suite de pruebas: un duplicado en `test_workers.py`, varios accesos a campos/widgets privados, seis aserciones débiles – sin error de producción, `make coverage` se mantiene en verde con 93 %). **#828** (automatización de revisión) se ha cerrado entretanto mediante el PR #876; la serie de mediciones está en 10/10 (adenda más abajo). No hay hallazgos 🔴 abiertos. **Adenda 2026-08-26:** Dos correcciones a esta ronda. Primera: figuraba **#866** (Rosetta/x86_64 en Apple Silicon) como abierta aunque [PR #870](https://github.com/NikolayDA/picture_helper/pull/870) ya la había cerrado a las 07:56 UTC – la ronda trabajó contra una instantánea compuesta localmente (el acceso a la API en vivo está bloqueado desde el sandbox del agente, véase el historial de #752) y ya estaba desfasada al fusionarse a las 13:05 UTC. Segunda: **#869** se ha completado por entero mediante [PR #873](https://github.com/NikolayDA/picture_helper/pull/873). Ambas filas se han retirado, así que el estado en vivo era **14**; tras cerrarse #828 mediante el PR #876 son **13**. Por causa de #866, `recommendations-live-check.yml` estuvo en rojo durante cuatro ejecuciones desde la #67 (2026-08-25, 21:56 UTC): primero como fila ausente y luego como fila cerrada pero listada. **Adenda 2026-08-26 (#828):** con la ejecución de revisión de la PR #870 la muestra pasiva de diez ejecuciones está completa – **10/10**, 6 en verde y 4 en rojo. El contador de rechazos es 0 en las diez ejecuciones (las ejecuciones que abortaban al inicio registraban 6–10 cada una) y todas publicaron resumen y hallazgos en línea; las cuatro rojas fallan únicamente por el tope de 25 turnos (26–30 turnos). El owner subió el tope a 40 ese mismo día (timeout 20 minutos).

**Revisión del alcance de release 2026-08-26:** Desde v2.8.0 (2026-08-17) se han fusionado 37 commits en `main`. A diferencia de lo que sugerían las últimas rondas, desde la adenda del 2026-08-24 ha llegado más que trabajo de gobernanza/documentación: `CHANGELOG.md` ya trae una sección `[Unreleased]` con una función real (#863, la píldora de zoom ahora también aparece en la vista previa de relieve 3D) y cuatro correcciones/cambios de UX (#839/#846 descartan la vista previa en vivo de altura al cambiar al modo estándar; #864/#865 icono de proceso incorrecto en el selector de apps/barra de Stage Manager en macOS; #867 mueve el aviso de modo estándar/experto de una etiqueta permanente a un tooltip; #868 traslada el botón principal «Generar mapa de altura desde la imagen» a la parte superior del paso 5). Todavía no existe un documento de congelación para la próxima versión (`docs/history/RELEASE-*-scope-freeze.md` termina en 2.8.0). Como la píldora de zoom 3D es una función nueva, SemVer exige una **versión menor, v2.9.0**, que ya toca pero aún no está preparada. #866 y #869 se han cerrado desde entonces y en ningún caso bloqueaban dicho release. **Adenda (este corte):** la preparación está hecha: `pyproject.toml` está en 2.9.0, el [documento de congelación](../../history/RELEASE-2.9.0-scope-freeze.md) existe (base v2.8.0, política de rutas 6) y CHANGELOG y AppStream están fechados el 2026-08-26. Los 37 commits citados arriba eran el recuento en el momento de la comprobación; el conjunto de commits determinante lo deriva el freeze-gate dinámicamente del historial first-parent y no se fija aquí a propósito.

**Revisión rutinaria 2026-08-22:** `scripts/recommendations_live_check.py --write` sincronizó las seis tablas con GitHub: #837 se cerró mediante PR #838 y fue retirada; se añadieron #839 y #841. Desde v2.8.0, PR #840 actualizó documentación y PR #842 actualizó documentación de procesos, un detalle menor del workflow de auditoría de dependencias y pruebas contra deriva, sin función de producto publicada. No procede una nueva versión y no hay hallazgos 🔴 abiertos. **Adenda 2026-08-23:** #836 y #839 están cerradas; los PR que las cierran figuran en la enumeración de abajo. El cierre de #841 por el PR #843, dedicado solo a documentación, fue prematuro: tres ejecuciones de PR posteriores volvieron a fallar, por lo que la incidencia se reabrió. Solo se considera resuelta tras corregir allowlist/prompt y obtener tres revisiones verdes consecutivas. Por eso la tabla volvió a incluir #841: el PR de corrección #850 está fusionado, pero **no** cierra la incidencia – solo habilita la serie de mediciones. La versión anterior había retirado la fila de forma anticipada; de ahí venía el live check rojo de #849, que esta ronda cierra. Se añadió y evaluó #847. **Adenda 2026-08-24:** el owner cerró #841 el 2026-08-23 sin la serie de mediciones y #847 se completó mediante el PR #852 – ambas filas vuelven a estar fuera de la tabla; los criterios de #841 están en [../../history/ISSUE-841-VERIFIKATION.md](../../history/ISSUE-841-VERIFIKATION.md) y el resto se sigue en #828. La regla de las tres ejecuciones allí registrada fue sustituida el 2026-08-24, con la desescalada de los bucles de revisión, por la medición pasiva de diez ejecuciones sin reinicios (punto 1 del archivo de criterios).

**Auditoría completa (instantánea de la revisión rutinaria, antes de las dos adendas; #836/#839 están completadas y #841 quedó cerrada entretanto):** cada descripción, criterio de aceptación, comentario y etiqueta se comprobó contra `main`. #839 registra una discrepancia limitada pero real entre la vista previa de altura y el modelo guardado/exportado al pasar al modo Estándar. #841 convierte las mediciones de #828 en un defecto concreto del workflow. #836 abarca ahora los seis idiomas de la guía más la regeneración del PDF; #694 contempla modo Estándar/Experto y vistas previas COLOR activas.

**#828/#841 y PR #842:** la muestra 3/3 de #828 está completa y su hipótesis inicial queda refutada. La ejecución final de revisión de PR #842 ([32572985972](https://github.com/NikolayDA/picture_helper/actions/runs/32572985972)) aporta otra línea base: `error_max_turns`, 31 turnos y 9 denegaciones. Precisa el arreglo de #841 con `git show-ref` como herramienta de solo lectura y una prohibición explícita en el prompt de `git fetch`, pruebas locales y atajos genéricos mediante `gh api`; no cuenta para las tres verificaciones posteriores al arreglo. La corrección se fusionó entretanto mediante el PR #850; #828 conservaba las cuestiones generales y está cerrado mediante el PR #876.

**EufyMake #681/#687–#691:** los 31 fixtures, las plantillas de protocolo y la gobernanza aprobada ya constan en las incidencias. #687 está en 16/18 criterios; solo faltan I-06 (carpeta/manifiesto) y la revisión final tras las pruebas reales. Para la ruta Spot UV separada, la hipótesis respaldada por el fabricante es negro = gloss y blanco = sin gloss. El uso completo de 16 bits, la prioridad de `pHYs`, el mapeo de gris a mm y la intensidad gloss siguen siendo preguntas de hardware en #688–#690.

Sin cambios y cerrado: **N1/N2/N4/N5/N6/N7/N8**, **O1–O8**, todo lo completado desde **2026-06-25**, las versiones v2.7.0 a v2.8.0, además de la épica #741 con sus once sub-incidencias, la épica #805 con #806–#811, #817 y #821; cerradas desde la última sincronización: #836 (PR #844), #837 (PR #838), #839 (PR #846), #849 (PR #851), #841 (cerrada por el owner), #847 (PR #852), #866 (PR #870/#871), #869 (PR #873), #881 (cerrada por el owner) y #878 (PR #908/#910) (detalles: Rondas anteriores).

Bandeja abierta: una fila por incidencia en la tabla de clasificación de abajo. Desde #821 no se mantienen a mano ni el recuento ni las filas: `scripts/recommendations_live_check.py --write` actualiza las seis versiones desde el estado en vivo de GitHub, mientras que las columnas de valoración siguen siendo trabajo editorial.

## Incidencias abiertas de GitHub — Clasificación

| # | Título | Relevancia | Complejidad | Modelo recomendado (esfuerzo) | Próximo paso |
|---|--------|------------|-------------|--------------------------------|--------------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Épica] Perfil objetivo EufyMake – validar Height/Gloss/mm-DPI | 🟠 Alta (corrección del principal objetivo de exportación) | 🔴 Alta (5 sub-incidencias, requiere hardware físico) | – (épica) | Preparación de #687 en 16/18 CA; quedan I-06 y la revisión final, y la integración #691 espera las pruebas reales #688–#690 |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | Inventario de suposiciones, fuentes del fabricante, matriz de pruebas | 🟠 Alta (base vinculante para #688–#691) | 🔴 Alta (entregables propios listos; lagunas de fixtures/celdas de #688–#690 abiertas, el resto requiere hardware real) | – (sin agente; requiere hardware EufyMake real) | Bloqueada (externa) – 16/18 criterios cumplidos; pendientes I-06 para carpeta/manifiesto y la revisión final tras #688–#690 |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | Validar profundidad de bits/semántica HEIGHT en hardware real | 🟠 Alta (afecta directamente a la altura del relieve) | 🔴 Alta (impresora física, fixtures, registro de medición) | – (sin agente; requiere hardware EufyMake real) | Bloqueada (externa) + trabajo previo pendiente – los fixtures/plantillas de protocolo de #687 ya están listos, pero alfa/cobertura no tiene ni fixture ni celda de prueba (todos los fixtures COLOR son opacos) y falta un par COLOR/HEIGHT con las mismas dimensiones en píxeles (I-02/I-08 confundidos); completar antes del día de pruebas |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | Validar contrato de mm/DPI, tamaño objetivo y posicionamiento | 🟠 Alta (tamaño de impresión/registro) | 🔴 Alta (mediciones físicas, motivos de control) | – (sin agente; requiere hardware real) | Bloqueada (externa) + trabajo previo pendiente – si el diálogo de importación de Studio deriva el tamaño inicial de `pHYs`/DPI no está demostrado (N10, EM-F04); además, la celda I-06 referencia el manifiesto de los fixtures en lugar de uno de exportación real, y los DPI no cuadrados ni se prueban ni se descartan de forma justificada |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | Validar semántica de gloss/barniz | 🟡 Media (gloss ya está marcado como "experimental" en el código) | 🔴 Alta (impresiones físicas, consumo de material) | – (sin agente; requiere hardware real) | Bloqueada (externa) + trabajo previo pendiente – el trabajo previo de #687 solo está hecho en parte: exactamente una celda de gloss (I-10), sin fixtures de alfa/cobertura, sin una dimensión de gloss divergente y gloss × HEIGHT sin cruzar |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | Integrar el perfil objetivo versionado en validador/writer/diálogo/documentación | 🟠 Alta (endurece la ruta de exportación de producción) | 🟠 Alta (transversal a eufymake_export/_validate/_writer + UI) | Opus, alto | Bloqueada – espera a #688–#690 |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Épica] Motor de tono/escala de grises COLOR | 🟡 Media-alta (fundamento de la hoja de ruta para láser, no un bug activo) | 🔴 Alta (5 sub-incidencias, ADR→núcleo→UI→integración→aceptación) | – (épica) | En curso – iniciar primero #692 |
| [#692](https://github.com/NikolayDA/picture_helper/issues/692) | ADR + contrato de datos para tono/histograma/escala de grises | 🟠 Alta (fija el contrato para toda la épica) | 🟡 Media (decisión de arquitectura, sin implementación) | Opus, alto | Lista para iniciar |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | Núcleo libre de Qt: histograma/escala de grises/niveles/gamma | 🟡 Media-alta | 🟡 Media (extiende `color_ops.py`, bien aislado y comprobable) | Sonnet, alto | Bloqueada – espera al ADR #692 |
| [#694](https://github.com/NikolayDA/picture_helper/issues/694) | Vista previa en vivo + interfaz para histograma/niveles/gamma | 🟡 Media | 🟡 Media-alta (UI de Qt, protección de debounce/generación similar a la vista previa de altura) | Sonnet, alto | Bloqueada – espera al núcleo #693 |
| [#695](https://github.com/NikolayDA/picture_helper/issues/695) | Integración de capas/selección/historial/proyecto | 🟡 Media | 🟠 Alta (muchas transiciones de estado: deshacer/rehacer, selección, estado sucio) | Opus, alto | Bloqueada – espera a #693/#694 |
| [#696](https://github.com/NikolayDA/picture_helper/issues/696) | Aceptación de rendimiento/E2E/documentación/interfaz láser | 🟡 Media (gate de cierre, no una función nueva) | 🟠 Alta (suite de benchmarks, E2E, documentación, contrato del adaptador) | Opus, alto | Bloqueada – incidencia de cierre tras #695 |
| [#882](https://github.com/NikolayDA/picture_helper/issues/882) | [Epic] BgRemover en la Mac App Store | 🟡 Media-alta (nuevo canal, no defecto actual) | 🔴 Alta (licencia, sandbox, empaquetado, tienda y gobernanza) | – (Epic) | Bloqueada – crear y decidir primero la estrategia de licencia como subtarea concreta de fase 0 |
| [#883](https://github.com/NikolayDA/picture_helper/issues/883) | [MAS] Estrategia de licencia: PySide6 vs. Riverbank y relicenciamiento | 🟠 Alta (bloqueo duro para todo trabajo técnico MAS) | 🔴 Alta (decisión legal/del propietario, posible port Qt, riesgo residual) | Opus, alto + revisión del propietario/legal | Lista – redactar ADR y decisión; crear issue de port separado si se elige PySide6 |
| [#884](https://github.com/NikolayDA/picture_helper/issues/884) | [MAS] Inscripción en Apple Developer Program | 🟠 Alta (bloquea certificados y acceso a la tienda) | 🟢 Baja (paso manual de cuenta/pago) | – (sin agente; titular de cuenta) | Bloqueada (externa) – elegir tipo de cuenta, completar inscripción/2FA y asignar renovación |
| [#885](https://github.com/NikolayDA/picture_helper/issues/885) | [MAS] Identidades de firma, App ID y perfil de aprovisionamiento | 🟠 Alta (requisito del build firmado) | 🟡 Media (secretos del propietario y contrato bundle-ID/packaging) | – (sin agente; titular/admin) | Bloqueada – espera #884; crear certificados, App ID/perfil explícitos y fijar bundle ID |
| [#886](https://github.com/NikolayDA/picture_helper/issues/886) | [MAS] Definir y aplicar entitlements de App Sandbox | 🟠 Alta (requisito obligatorio de tienda y ejecución) | 🟠 Alta (todos los Mach-O, packaging y evidencia en hardware) | Opus, alto | Bloqueada – espera la decisión #883; implementar entitlements mínimos y pruebas de artefacto/hardware |
| [#887](https://github.com/NikolayDA/picture_helper/issues/887) | [MAS] Proceso hijo de inferencia compatible con sandbox | 🟠 Alta (la IA central debe funcionar en la tienda) | 🔴 Alta (spawn/firma del helper, regla de dos claves, sandbox real) | Opus, alto | Bloqueada – espera #886; decidir re-exec/helper y probar el self-check de IA en hardware |
| [#888](https://github.com/NikolayDA/picture_helper/issues/888) | [MAS] Bookmarks security-scoped para archivos y directorios | 🟠 Alta (Recientes y guardado rápido fallan tras reinicio) | 🟠 Alta (grants persistentes, imágenes/proyectos/directorios, gating) | Opus, alto | Bloqueada – espera #886; implementar contrato de bookmarks y probar reinicio sandboxed |
| [#889](https://github.com/NikolayDA/picture_helper/issues/889) | [MAS] Escrituras sandbox-safe y exportación EufyMake | 🟠 Alta (guardado/exportación e integridad de datos) | 🔴 Alta (atomicidad en varias rutas y grants Powerbox) | Opus, alto | Bloqueada – espera #886; diseñar escritura/extensión/destino dentro del grant y probar en hardware |
| [#890](https://github.com/NikolayDA/picture_helper/issues/890) | [MAS] Caché del modelo de IA en el contenedor sandbox | 🟡 Media (ruta determinista del modelo) | 🟡 Media (contrato de ruta aislado y decisión de migración) | Sonnet, alto | Bloqueada – espera #886 y se coordina con #893; fijar `U2NET_HOME` y decidir migración |
| [#891](https://github.com/NikolayDA/picture_helper/issues/891) | [MAS] Bandera de canal y gating del comprobador de actualizaciones | 🟠 Alta (regla 2.4.5, sin autoactualización) | 🟠 Media-alta (bandera central en menú, settings, workers y hooks) | Sonnet, alto | Bloqueada – espera #883; introducir contrato de canal y pruebas negativas de red/UI MAS |
| [#892](https://github.com/NikolayDA/picture_helper/issues/892) | [MAS] Retirar AiInstallDialog y empaquetar el backend IA | 🟠 Alta (no instalar código ejecutable en la tienda) | 🟡 Media (gating y prueba vinculante de packaging) | Sonnet, alto | Bloqueada – espera #891; ocultar diálogo/menú y demostrar rembg/onnxruntime incluidos |
| [#893](https://github.com/NikolayDA/picture_helper/issues/893) | [MAS] Incluir u2net o descargarlo en el primer inicio | 🟠 Alta (riesgo de review y función IA) | 🟠 Alta (decisión de producto/review, packaging o nuevo flujo i18n) | Opus, alto | Bloqueada – espera #890/#891 y #883; documentar, implementar y verificar la variante en sandbox |
| [#894](https://github.com/NikolayDA/picture_helper/issues/894) | [MAS] Elegir empaquetado Briefcase vs. py2app | 🟠 Alta (determina la viabilidad técnica) | 🟠 Alta (spike sandbox/firma/upload abierto) | Opus, alto | Bloqueada – espera #883; probar Briefcase, validar fallback py2app y registrar ADR |
| [#895](https://github.com/NikolayDA/picture_helper/issues/895) | [MAS] App onedir, firma inside-out y limpieza Qt | 🟠 Alta (build ejecutable central) | 🔴 Alta (binarios, Qt, provisioning, validación upload) | Opus, alto | Bloqueada – espera #885/#886/#894; implementar y validar sin errores ITMS |
| [#896](https://github.com/NikolayDA/picture_helper/issues/896) | [MAS] Info.plist e iconos completos | 🟡 Media-alta (metadatos y contrato de plataforma) | 🟡 Media (campos, arquitectura, assets deterministas) | Sonnet, alto | Bloqueada – espera #895; decidir SO/arquitectura/tipos y añadir pruebas |
| [#897](https://github.com/NikolayDA/picture_helper/issues/897) | [MAS] PKG productbuild firmado y subida Transporter | 🟠 Alta (artefacto enviable) | 🟠 Alta (segunda firma, automatización, primera subida manual) | Opus, alto + titular | Bloqueada – espera #885/#895/#896; crear PKG reproducible y registrar delivery |
| [#898](https://github.com/NikolayDA/picture_helper/issues/898) | [MAS] CI, contrato de seis artefactos y escaneo PKG | 🟠 Alta (integridad fail-closed) | 🔴 Alta (secretos, contrato, extractor, malware/rutas) | Opus, alto | Bloqueada – espera #895/#897; ampliar leg, contrato, escaneo payload y pruebas |
| [#899](https://github.com/NikolayDA/picture_helper/issues/899) | [MAS] Smokes sandboxed en hardware real | 🟠 Alta (evidencia vinculante de runtime) | 🔴 Alta (PKG, spawn IA, Powerbox, 3D, esquema) | Opus, alto + hardware macOS | Bloqueada (externa) – espera #898; implementar y ejecutar en ARM64 self-hosted |
| [#900](https://github.com/NikolayDA/picture_helper/issues/900) | [MAS] Beta TestFlight para macOS | 🟠 Alta (evidencia temprana de review/dispositivo externo) | 🟡 Media (coordinación manual ASC/tester) | – (sin agente; titular y tester) | Bloqueada – espera #897/#901; probar IA, archivos y 3D en otro dispositivo |
| [#901](https://github.com/NikolayDA/picture_helper/issues/901) | [MAS] Registro ASC y metadatos en seis idiomas | 🟠 Alta (nombre, listing y requisito de envío) | 🟠 Media-alta (owner y seis juegos localizados) | Sonnet, alto + titular | Bloqueada – espera #884/#885; reservar nombre, versionar/cargar textos, rating/storefronts |
| [#902](https://github.com/NikolayDA/picture_helper/issues/902) | [MAS] Capturas de tienda 16:10 | 🟡 Media-alta (material obligatorio) | 🟡 Media (formatos, alfa, decisión de idiomas) | Sonnet, alto | Bloqueada – espera build #895; ampliar automatización y verificar el juego |
| [#903](https://github.com/NikolayDA/picture_helper/issues/903) | [MAS] Política de privacidad y App Privacy | 🟠 Alta (obligatoria en tienda y app) | 🟡 Media (política, hosting, enlace i18n, cuestionario) | Sonnet, alto + owner | Bloqueada – espera #891/#893; publicar/enlazar y demostrar «Data Not Collected» |
| [#904](https://github.com/NikolayDA/picture_helper/issues/904) | [MAS] Estado DSA UE, aviso legal y GPSR | 🟠 Alta (storefronts UE y deberes legales) | 🟠 Media-alta (clasificación, verificación, riesgo legal) | – (sin agente; owner/legal) | Bloqueada – espera #884; declarar trader y documentar DDG/GPSR con owner/revisión |
| [#905](https://github.com/NikolayDA/picture_helper/issues/905) | [MAS] Extender la gobernanza de release | 🟠 Alta (evita canal fuera del contrato fail-closed) | 🟠 Alta (runbook, checklist, contrato, policy, seis changelogs) | Opus, alto | Bloqueada – acompaña #898/#899; llevar contratos/pruebas a seis artefactos |
| [#906](https://github.com/NikolayDA/picture_helper/issues/906) | [MAS] Primer envío y ronda de review | 🟠 Alta (puerta manual de publicación) | 🔴 Alta (dependencias, riesgos, comunicación Apple) | – (sin agente; release owner) | Bloqueada – tras #896/#897/#899/#901–#905 revisar, enviar y registrar resultado/issues |
| [#907](https://github.com/NikolayDA/picture_helper/issues/907) | [MAS] Operación: renovación, actualizaciones y canales | 🟡 Media-alta (disponibilidad y separación a largo plazo) | 🟡 Media (runbook, responsables, recordatorios, matriz) | Opus, alto + owner | Bloqueada – adelantar concepto y cerrar tras #906; fijar rutinas de renovación/updates/web |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurar la cuota de OpenAI para la comprobación manual de Codex Security | 🟢 Baja (solo bloquea un escaneo manual opcional) | 🟢 Baja (puramente operativo, sin código) | – (sin agente; propietario del repo: facturación) | Bloqueada (externa) – la última ejecución (29233060507, 2026-07-13) no demuestra un escaneo exitoso; facturación/cuota sigue sin resolver |

### Recomendado a continuación

1. **#692** (ADR) abre la épica COLOR #682.
2. Antes de la próxima sesión de Studio/impresora, cerrar primero las lagunas de fixtures/celdas
   documentadas en #688–#690 (alfa/cobertura, un par COLOR/HEIGHT del mismo tamaño, celdas de
   gloss, un manifiesto de exportación real para I-06); después ejecutar #687 (resto), #688,
   #689 y #690 en una sola sesión conjunta.
3. **#883** (estrategia de licencia MAS) decide la vía Mac App Store #882: sin
   esa decisión del owner toda la cadena #884–#907 sigue bloqueada.

## Rondas anteriores

Protocolos detallados desde v2.2: [RECOMMENDATIONS-2026-v2.2-v2.9.es.md](../../history/RECOMMENDATIONS-2026-v2.2-v2.9.es.md).

Hallazgos históricos y registros de trabajo (rondas 1–5): [RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).

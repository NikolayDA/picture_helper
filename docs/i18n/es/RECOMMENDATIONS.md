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

**Auditoría diaria 2026-08-31 (estado `551d055`):** Se revisaron los doce PR
fusionados hoy (#927–#932, #935–#938, #940 y #941) y las incidencias que
cerraron (#918–#923, #933 y #934): los diffs de fusión completos, las
correcciones de revisión y, donde existen, sus pruebas de regresión. La
referencia de publicación, el informe de seguridad, el heartbeat/dry run, el
andamiaje preparatorio y el preflight Qt/GL son coherentes. Sin embargo, la
re-revisión adversarial del PR #942 halló cinco hallazgos residuales concretos
en los scripts de proceso, verificados y agrupados en la incidencia #943.

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
| [#943](https://github.com/NikolayDA/picture_helper/issues/943) | Relectura de revisión 2026-08-31: cinco hallazgos de robustez en scripts de proceso | 🟠 Alta (el heartbeat informa PASS sin preparación demostrada) | 🟡 Media (cuatro scripts, arreglos aislados con pruebas de regresión) | Sonnet, alto | Lista – primero las conclusiones del heartbeat, luego el marcador de dispatch, prepare_release (downgrade/orden de escritura) y el OSError del escáner |
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

[Deutsch](../../../RECOMMENDATIONS.md) · [English](../en/RECOMMENDATIONS.md) · **Español** · [Français](../fr/RECOMMENDATIONS.md) · [Українська](../uk/RECOMMENDATIONS.md) · [简体中文](../zh/RECOMMENDATIONS.md)

# Análisis de código y recomendaciones priorizadas: BgRemover

## Escala de valoración

| Símbolo | Prioridad | Significado |
|---------|-----------|-------------|
| 🔴 | Crítica | Errores, cierres inesperados o pérdida de datos |
| 🟠 | Alta | Impacto claro en la fiabilidad o el mantenimiento |
| 🟡 | Media | Mejora útil de calidad, legibilidad o testabilidad |
| 🟢 | Baja | Pulido opcional o mejora de proceso |

## Estado actual (2026-09-03, v2.9.0 publicado, inventario abierto auditado por completo)

**Auditoría diaria 2026-09-02 (estado `91b32b4`):** se contrastaron las 42
incidencias abiertas con código, fusiones, comentarios y, para la épica Mac App
Store, fuentes primarias actuales. Las correcciones de estado constan ahora en
#681, #688, #691, #682/#693, #914/#918 y #949. Hallazgos nuevos: el artefacto
separado `u2net.onnx` no tiene Apache-2.0 demostrado (#883/#893), Apple puede
pedir datos de cuenta de pago a traders incluso para una app gratuita
(#884/#904), y #895/#899/#906 deben decidir y probar la validación de descarga.
Ningún defecto de producto ni hallazgo 🔴 nuevo.

**Revisión 2026-09-03 (estado `e7c379d`):** se contrastaron los PR nuevos
#955–#957 con los puntos abiertos. El PR #956 corrigió deliberadamente la
referencia de evidencia dentro de la v1 aún no publicada y añadió guardas de
snapshot/paquetes; con ello queda resuelto el punto crítico de #691. #955 solo
afecta a la documentación de pruebas y #957 a los scripts de publicación.

**Valoración de publicación: aún no se ha lanzado ningún candidato.** Desde
`v2.9.0` (2026-08-29) hay 34 commits en la rama principal en el estado auditado `e7c379d`. Con el PR #953 (perfil
de destino EufyMake versionado, HEIGHT por defecto en 16 bits, perfil y DPI X/Y
en el diálogo, procedencia del manifiesto) `[Unreleased]` contiene por primera
vez una entrada visible para las personas usuarias; el resto es automatización
de publicación, documentación y gobernanza. Que **v2.10.0** salga solo con #953
o junto con el motor de tono COLOR (#693/#694 de la épica #682, ADR #692) es una
decisión del owner. El PR #956 corrigió la referencia con una decisión explícita
de mantener v1 y guardas golden/de paquetes. #691 ya no añade un bloqueo de
publicación; sigue mandando la puerta normal de release.

**EufyMake #681/#687–#691:** los PR #948, #951–#953, #956 y #959–#961 están fusionados. El esquema 5 contiene 42 fixtures individuales y siete paquetes reales de exportación sin cambios. Las 29 celdas obligatorias de importación sin impresión están completas en Studio 4.2.2. Además de HEIGHT nativo de 8/16 bits, el recorte COLOR/HEIGHT y `Gloss Varnish`, queda probado que se aceptan dimensiones de píxel distintas con la misma relación de aspecto, mientras que una relación HEIGHT diferente se rechaza con `Depth image ratio does not match the original image`. I-14 añade un par borde/impulso de 256/128 píxeles generado directamente y sin prefiltrado; ambas variantes superaron el preflight de importación. I-09 (`.empf`) sigue sin bloquear. Solo faltan las mediciones físicas E1 de #688–#690 y la revisión final de #687.

Sin cambios y cerrado: **N1/N2/N4/N5/N6/N7/N8**, **O1–O8**, todo lo completado desde **2026-06-25**, las versiones v2.7.0 a v2.9.0, además de la épica #741 con sus once sub-incidencias, la épica #805 con #806–#811, #817 y #821; cerradas desde la última sincronización: #943 (PR #944) y #692 (PR #947) (detalles: Rondas anteriores).

Bandeja abierta: una fila por incidencia en la tabla de clasificación de abajo. Desde #821 no se mantienen a mano ni el recuento ni las filas: `scripts/recommendations_live_check.py --write` actualiza las seis versiones desde el estado en vivo de GitHub, mientras que las columnas de valoración siguen siendo trabajo editorial.

## Incidencias abiertas de GitHub — Clasificación

| # | Título | Relevancia | Complejidad | Modelo recomendado (esfuerzo) | Próximo paso |
|---|--------|------------|-------------|--------------------------------|--------------|
| [#681](https://github.com/NikolayDA/picture_helper/issues/681) | [Épica] Perfil objetivo EufyMake – validar Height/Gloss/mm-DPI | 🟠 Alta (corrección del principal objetivo de exportación) | 🔴 Alta (5 sub-incidencias, requiere hardware físico) | – (épica) | Integración y las 29 celdas obligatorias sin impresión completadas; I-09 no bloquea. Faltan #688–#690 y la revisión final |
| [#687](https://github.com/NikolayDA/picture_helper/issues/687) | Inventario de suposiciones, fuentes del fabricante, matriz de pruebas | 🟠 Alta (base vinculante para #688–#691) | 🔴 Alta (material de repositorio completo; el resto requiere hardware real) | – (sin agente; requiere hardware EufyMake real) | Bloqueada (externa) – 17/18 criterios y las 29 celdas obligatorias de importación completados. Solo falta la revisión tras #688–#690 |
| [#688](https://github.com/NikolayDA/picture_helper/issues/688) | Validar profundidad de bits/semántica HEIGHT en hardware real | 🟠 Alta (afecta directamente a la altura del relieve) | 🔴 Alta (impresora física, fixtures, registro de medición) | – (sin agente; requiere hardware EufyMake real) | Bloqueada (externa) – incluidos los preflights del par directo I-14 para filtrado/normalización, todos están completos; faltan mediciones físicas de precisión, filtrado, relieve y mm |
| [#689](https://github.com/NikolayDA/picture_helper/issues/689) | Validar contrato de mm/DPI, tamaño objetivo y posicionamiento | 🟠 Alta (tamaño de impresión/registro) | 🔴 Alta (mediciones físicas, motivos de control) | – (sin agente; requiere hardware real) | Bloqueada (externa) – contrato de Studio incluido recorte y relación HEIGHT demostrado. Solo faltan registro físico, mediciones y tolerancias |
| [#690](https://github.com/NikolayDA/picture_helper/issues/690) | Validar semántica de gloss/barniz | 🟡 Media (gloss ya está marcado como "experimental" en el código) | 🔴 Alta (impresiones físicas, consumo de material) | – (sin agente; requiere hardware real) | Bloqueada (externa) – Ink Mode nativo `Gloss Varnish` precomprobado; faltan registro por celda, polaridad, intensidad y efecto físico |
| [#691](https://github.com/NikolayDA/picture_helper/issues/691) | Integrar el perfil objetivo versionado en validador/writer/diálogo/documentación | 🟠 Alta (endurece la ruta de exportación de producción) | 🟢 Baja para el resto crítico; 🔴 hardware para cerrar | Sonnet, medio + hardware después | Implementación lista para release – #953 integra v1 y #956 corrige la referencia con decisión v1 y guardas; solo queda la promoción posterior a #688–#690 |
| [#682](https://github.com/NikolayDA/picture_helper/issues/682) | [Épica] Motor de tono/escala de grises COLOR | 🟡 Medio-alto (base de hoja de ruta para láser, sin fallo activo) | 🔴 Alto (4 sub-incidencias restantes: núcleo→UI→integración→aceptación) | – (épica) | En curso: el ADR #692 está aprobado; a continuación el núcleo #693 |
| [#693](https://github.com/NikolayDA/picture_helper/issues/693) | Núcleo libre de Qt: histograma/escala de grises/niveles/gamma | 🟡 Medio-alto | 🟡 Medio (amplía `color_ops.py`, bien aislado y comprobable) | Sonnet, alto | Listo para empezar: el ADR #692 (PR #947) aporta el contrato de datos; implementar y probar el núcleo contra sus fórmulas |
| [#694](https://github.com/NikolayDA/picture_helper/issues/694) | Vista previa en vivo + interfaz para histograma/niveles/gamma | 🟡 Media | 🟡 Media-alta (UI de Qt, protección de debounce/generación similar a la vista previa de altura) | Sonnet, alto | Bloqueada – espera al núcleo #693 |
| [#695](https://github.com/NikolayDA/picture_helper/issues/695) | Integración de capas/selección/historial/proyecto | 🟡 Media | 🟠 Alta (muchas transiciones de estado: deshacer/rehacer, selección, estado sucio) | Opus, alto | Bloqueada – espera a #693/#694 |
| [#696](https://github.com/NikolayDA/picture_helper/issues/696) | Aceptación de rendimiento/E2E/documentación/interfaz láser | 🟡 Media (gate de cierre, no una función nueva) | 🟠 Alta (suite de benchmarks, E2E, documentación, contrato del adaptador) | Opus, alto | Bloqueada – incidencia de cierre tras #695 |
| [#882](https://github.com/NikolayDA/picture_helper/issues/882) | [Epic] BgRemover en la Mac App Store | 🟡 Media-alta (nuevo canal, no defecto actual) | 🔴 Alta (licencia, sandbox, empaquetado, tienda y gobernanza) | – (Epic) | Bloqueada – decidir primero #883, separando licencia Qt/código de procedencia y derechos no resueltos del modelo |
| [#883](https://github.com/NikolayDA/picture_helper/issues/883) | [MAS] Estrategia de licencia: PySide6 vs. Riverbank y relicenciamiento | 🟠 Alta (bloqueo duro para todo trabajo técnico MAS) | 🔴 Alta (decisión legal/del propietario, posible port Qt, riesgo residual) | Opus, alto + revisión del propietario/legal | Lista – ADR/decisión y prueba de origen, licencia y redistribución del `u2net.onnx` exacto, o elegir modelo sustituto |
| [#884](https://github.com/NikolayDA/picture_helper/issues/884) | [MAS] Inscripción en Apple Developer Program | 🟠 Alta (bloquea certificados y acceso a la tienda) | 🟢 Baja (paso manual de cuenta/pago) | – (sin agente; titular de cuenta) | Bloqueada – resolver cuenta, inscripción/2FA y renovación; app gratis no exige Paid Apps Agreement, pero un trader puede necesitar datos de pago (#904) |
| [#885](https://github.com/NikolayDA/picture_helper/issues/885) | [MAS] Identidades de firma, App ID y perfil de aprovisionamiento | 🟠 Alta (requisito del build firmado) | 🟡 Media (secretos del propietario y contrato bundle-ID/packaging) | – (sin agente; titular/admin) | Bloqueada – espera #884; crear certificados, App ID/perfil explícitos y fijar bundle ID |
| [#886](https://github.com/NikolayDA/picture_helper/issues/886) | [MAS] Definir y aplicar entitlements de App Sandbox | 🟠 Alta (requisito obligatorio de tienda y ejecución) | 🟠 Alta (todos los Mach-O, packaging y evidencia en hardware) | Opus, alto | Bloqueada – espera la decisión #883; implementar entitlements mínimos y pruebas de artefacto/hardware |
| [#887](https://github.com/NikolayDA/picture_helper/issues/887) | [MAS] Proceso hijo de inferencia compatible con sandbox | 🟠 Alta (la IA central debe funcionar en la tienda) | 🔴 Alta (spawn/firma del helper, regla de dos claves, sandbox real) | Opus, alto | Bloqueada – espera #886; decidir re-exec/helper y probar el self-check de IA en hardware |
| [#888](https://github.com/NikolayDA/picture_helper/issues/888) | [MAS] Bookmarks security-scoped para archivos y directorios | 🟠 Alta (Recientes y guardado rápido fallan tras reinicio) | 🟠 Alta (grants persistentes, imágenes/proyectos/directorios, gating) | Opus, alto | Bloqueada – espera #886; implementar contrato de bookmarks y probar reinicio sandboxed |
| [#889](https://github.com/NikolayDA/picture_helper/issues/889) | [MAS] Escrituras sandbox-safe y exportación EufyMake | 🟠 Alta (guardado/exportación e integridad de datos) | 🔴 Alta (atomicidad en varias rutas y grants Powerbox) | Opus, alto | Bloqueada – espera #886; diseñar escritura/extensión/destino dentro del grant y probar en hardware |
| [#890](https://github.com/NikolayDA/picture_helper/issues/890) | [MAS] Caché del modelo de IA en el contenedor sandbox | 🟡 Media (ruta determinista del modelo) | 🟡 Media (contrato de ruta aislado y decisión de migración) | Sonnet, alto | Bloqueada – espera #886 y se coordina con #893; fijar `U2NET_HOME` y decidir migración |
| [#891](https://github.com/NikolayDA/picture_helper/issues/891) | [MAS] Bandera de canal y gating del comprobador de actualizaciones | 🟠 Alta (regla 2.4.5, sin autoactualización) | 🟠 Media-alta (bandera central en menú, settings, workers y hooks) | Sonnet, alto | Bloqueada – espera #883; introducir contrato de canal y pruebas negativas de red/UI MAS |
| [#892](https://github.com/NikolayDA/picture_helper/issues/892) | [MAS] Retirar AiInstallDialog y empaquetar el backend IA | 🟠 Alta (no instalar código ejecutable en la tienda) | 🟡 Media (gating y prueba vinculante de packaging) | Sonnet, alto | Bloqueada – espera #891; ocultar diálogo/menú y demostrar rembg/onnxruntime incluidos |
| [#893](https://github.com/NikolayDA/picture_helper/issues/893) | [MAS] Incluir u2net o descargarlo en el primer inicio | 🟠 Alta (riesgo de review y función IA) | 🟠 Alta (decisión de producto/review, packaging o nuevo flujo i18n) | Opus, alto | Bloqueada – antes de elegir variante, probar origen/licencia/redistribución mediante #883 o cambiar de modelo; luego #890/#891 y sandbox |
| [#894](https://github.com/NikolayDA/picture_helper/issues/894) | [MAS] Elegir empaquetado Briefcase vs. py2app | 🟠 Alta (determina la viabilidad técnica) | 🟠 Alta (spike sandbox/firma/upload abierto) | Opus, alto | Bloqueada – espera #883; probar Briefcase, validar fallback py2app y registrar ADR |
| [#895](https://github.com/NikolayDA/picture_helper/issues/895) | [MAS] App onedir, firma inside-out y limpieza Qt | 🟠 Alta (build ejecutable central) | 🔴 Alta (binarios, Qt, provisioning, validación upload) | Opus, alto | Bloqueada – tras #885/#886/#894 implementar, elegir `AppTransaction` o recibo fail-closed y validar sin errores ITMS |
| [#896](https://github.com/NikolayDA/picture_helper/issues/896) | [MAS] Info.plist e iconos completos | 🟡 Media-alta (metadatos y contrato de plataforma) | 🟡 Media (campos, arquitectura, assets deterministas) | Sonnet, alto | Bloqueada – espera #895; decidir SO/arquitectura/tipos y añadir pruebas |
| [#897](https://github.com/NikolayDA/picture_helper/issues/897) | [MAS] PKG productbuild firmado y subida Transporter | 🟠 Alta (artefacto enviable) | 🟠 Alta (segunda firma, automatización, primera subida manual) | Opus, alto + titular | Bloqueada – espera #885/#895/#896; crear PKG reproducible y registrar delivery |
| [#898](https://github.com/NikolayDA/picture_helper/issues/898) | [MAS] CI, contrato de seis artefactos y escaneo PKG | 🟠 Alta (integridad fail-closed) | 🔴 Alta (secretos, contrato, extractor, malware/rutas) | Opus, alto | Bloqueada – espera #895/#897; ampliar leg, contrato, escaneo payload y pruebas |
| [#899](https://github.com/NikolayDA/picture_helper/issues/899) | [MAS] Smokes sandboxed en hardware real | 🟠 Alta (evidencia vinculante de runtime) | 🔴 Alta (PKG, spawn IA, Powerbox, 3D, esquema) | Opus, alto + hardware macOS | Bloqueada – tras #898 ejecutar en ARM64 self-hosted e incluir evidencia válida y, si es reproducible, inválida de descarga |
| [#900](https://github.com/NikolayDA/picture_helper/issues/900) | [MAS] Beta TestFlight para macOS | 🟠 Alta (evidencia temprana de review/dispositivo externo) | 🟡 Media (coordinación manual ASC/tester) | – (sin agente; titular y tester) | Bloqueada – espera #897/#901; probar IA, archivos y 3D en otro dispositivo |
| [#901](https://github.com/NikolayDA/picture_helper/issues/901) | [MAS] Registro ASC y metadatos en seis idiomas | 🟠 Alta (nombre, listing y requisito de envío) | 🟠 Media-alta (owner y seis juegos localizados) | Sonnet, alto + titular | Bloqueada – espera #884/#885; reservar nombre, versionar/cargar textos, rating/storefronts |
| [#902](https://github.com/NikolayDA/picture_helper/issues/902) | [MAS] Capturas de tienda 16:10 | 🟡 Media-alta (material obligatorio) | 🟡 Media (formatos, alfa, decisión de idiomas) | Sonnet, alto | Bloqueada – espera build #895; ampliar automatización y verificar el juego |
| [#903](https://github.com/NikolayDA/picture_helper/issues/903) | [MAS] Política de privacidad y App Privacy | 🟠 Alta (obligatoria en tienda y app) | 🟡 Media (política, hosting, enlace i18n, cuestionario) | Sonnet, alto + owner | Bloqueada – espera #891/#893; publicar/enlazar y demostrar «Data Not Collected» |
| [#904](https://github.com/NikolayDA/picture_helper/issues/904) | [MAS] Estado DSA UE, aviso legal y GPSR | 🟠 Alta (storefronts UE y deberes legales) | 🟠 Media-alta (clasificación, verificación, riesgo legal) | – (sin agente; owner/legal) | Bloqueada – tras #884 documentar trader, contacto público, datos de cuenta si aplican y DDG/GPSR con owner/revisión |
| [#905](https://github.com/NikolayDA/picture_helper/issues/905) | [MAS] Extender la gobernanza de release | 🟠 Alta (evita canal fuera del contrato fail-closed) | 🟠 Alta (runbook, checklist, contrato, policy, seis changelogs) | Opus, alto | Bloqueada – acompaña #898/#899; llevar contratos/pruebas a seis artefactos |
| [#906](https://github.com/NikolayDA/picture_helper/issues/906) | [MAS] Primer envío y ronda de review | 🟠 Alta (puerta manual de publicación) | 🔴 Alta (dependencias, riesgos, comunicación Apple) | – (sin agente; release owner) | Bloqueada – tras #896/#897/#899/#901–#905 prevalidar incluida la descarga, enviar y registrar resultado/issues |
| [#907](https://github.com/NikolayDA/picture_helper/issues/907) | [MAS] Operación: renovación, actualizaciones y canales | 🟡 Media-alta (disponibilidad y separación a largo plazo) | 🟡 Media (runbook, responsables, recordatorios, matriz) | Opus, alto + owner | Bloqueada – adelantar concepto y cerrar tras #906; fijar rutinas de renovación/updates/web |
| [#914](https://github.com/NikolayDA/picture_helper/issues/914) | [Épica] Proceso de publicación: runners, evidencias automatizadas, congelación de main | 🟠 Alto (operación; implementación casi lista) | 🟢 Bajo (dos pruebas temporales/eventuales) | – (épica) | Casi terminada: faltan el primer dry-run programado del 2026-09-03 04:40 UTC y la evidencia E2E con #918 en el próximo release real |
| [#918](https://github.com/NikolayDA/picture_helper/issues/918) | Referencia de publicación en lugar de congelar main (ADR + salvaguardas fail-closed) | 🟠 Alto (`main` sigue fusionable durante una publicación) | 🟢 Bajo (código, documentación y ruleset están listos) | – (sin agente; próxima publicación) | Bloqueado (externo): reabierto el 2026-08-31 tras su comprobación final; el PR #936 y el ruleset activo 21941216 están documentados, solo falta una ejecución cuya aceptación posterior arrancara demostrablemente en `release/vX.Y.Z` |
| [#939](https://github.com/NikolayDA/picture_helper/issues/939) | Operación: runners autoalojados (canal de alerta del heartbeat) | 🟡 Medio (canal operativo, sin código de producto) | 🟢 Bajo (solo observación) | – (sin agente; owner del repositorio) | Permanentemente abierto: no cerrar (`RUNNER_HEARTBEAT_ISSUE`); el FAIL del 2026-08-31 fue la prueba planificada del canal y el paso de limpieza está hecho (ejecución programada 33496675995 en verde, x86_64 omitido, Mac y Pi superados) |
| [#949](https://github.com/NikolayDA/picture_helper/issues/949) | Auditoría de la suite de pruebas 2026-09-02 (deriva de RESOURCES, CropOverlay, lagunas de cobertura) | 🟡 Medio (calidad de pruebas y protección frente a deriva, sin defecto de producción) | 🟢 Bajo-medio (cuatro cambios de prueba bien acotados, sin cambio de producción) | Sonnet, medio | Lista – cuatro cambios; baseline anterior a PR #948–#954 y dependiente del entorno, repetir con plataforma y dependencias |
| [#245](https://github.com/NikolayDA/picture_helper/issues/245) | Restaurar la cuota de OpenAI para la comprobación manual de Codex Security | 🟢 Baja (solo bloquea un escaneo manual opcional) | 🟢 Baja (puramente operativo, sin código) | – (sin agente; propietario del repo: facturación) | Bloqueada (externa) – la última ejecución (29233060507, 2026-07-13) no demuestra un escaneo exitoso; facturación/cuota sigue sin resolver |
| [#958](https://github.com/NikolayDA/picture_helper/issues/958) | Heartbeat: escalado offline en 7/14/21 días (avisos por correo, retirada) y guardia de plazos | 🟡 Media (operación y avisos de runners, no un fallo de producto) | 🟠 Alta (historial, etapas idempotentes, permisos de workflow, pruebas y documentación) | Opus, alto + decisión del owner | Decisión necesaria – fijar E1 comentarios diarios, E2 retirada automática/manual y E3 días de etapa; después implementar fail-safe y validar en una incidencia de prueba |

### Recomendado a continuación

1. **#693**: ADR #692 está aprobado; después siguen #694, #695 y #696.
2. **#949**: hacer los cuatro cambios y medir la baseline con plataforma y dependencias opcionales.
3. **#883**: decidir licencia Qt/código y probar derechos/procedencia de `u2net.onnx`, o elegir
   un modelo sustituto con licencia clara.
4. Tras aprobar dispositivo y material, realizar las mediciones físicas pendientes de **#689**
   junto con el resto de #687, #688 y #690; las rutas nativas HEIGHT/Gloss e I-08 están precomprobadas. Después cerrar #691:
   promover el perfil v1 o crear v2 si los resultados lo contradicen.

## Rondas anteriores

Protocolos detallados desde v2.2: [RECOMMENDATIONS-2026-v2.2-v2.9.es.md](../../history/RECOMMENDATIONS-2026-v2.2-v2.9.es.md).

Hallazgos históricos y registros de trabajo (rondas 1–5): [RECOMMENDATIONS-2026-pre-v2.2.es.md](../../history/RECOMMENDATIONS-2026-pre-v2.2.es.md).

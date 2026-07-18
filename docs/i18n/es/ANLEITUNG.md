# BgRemover – Guía de uso

**Deutsch** · [English](../en/ANLEITUNG.md) · **Español** · [Français](../fr/ANLEITUNG.md) · [Українська](../uk/ANLEITUNG.md) · [简体中文](../zh/ANLEITUNG.md)

Esta guía explica paso a paso cómo se maneja el programa **BgRemover** —
desde la primera apertura de una imagen hasta guardar el resultado
final. Está dirigida a usuarias y usuarios sin conocimientos previos de
edición de imágenes.

> Las indicaciones sobre la **instalación** no están aquí a propósito,
> sino en [INSTALL_MAC.md](../../../INSTALL_MAC.md) (macOS) o
> [INSTALL_LINUX.md](../../../INSTALL_LINUX.md) (Linux). Esta guía
> asume que el programa ya puede iniciarse.

---

## Índice

1. [¿Qué puede hacer BgRemover?](#1-qué-puede-hacer-bgremover)
2. [La interfaz del programa de un vistazo](#2-la-interfaz-del-programa-de-un-vistazo)
3. [Inicio rápido en 5 pasos](#3-inicio-rápido-en-5-pasos)
4. [Paso 1 – Abrir imagen](#4-paso-1--abrir-imagen)
5. [La barra de herramientas (izquierda)](#5-la-barra-de-herramientas-izquierda)
6. [Hacer una selección](#6-hacer-una-selección)
7. [Paso 2 – Quitar fondo](#7-paso-2--quitar-fondo)
8. [Paso 3 – Ajustar (corrección de color)](#8-paso-3--ajustar-corrección-de-color)
9. [Paso 4 – Forma y medidas](#9-paso-4--forma-y-medidas)
10. [Cambiar tamaño y medidas físicas](#10-cambiar-tamaño-y-medidas-físicas)
11. [Paso 5 – Relieve y capas](#11-paso-5--relieve-y-capas)
12. [Paso 6 – Exportar](#12-paso-6--exportar)
13. [Configuración](#13-configuración)
14. [Atajos de teclado](#14-atajos-de-teclado)
15. [Flujos de trabajo típicos](#15-flujos-de-trabajo-típicos)
16. [Consejos y trucos](#16-consejos-y-trucos)
17. [Limitaciones conocidas](#17-limitaciones-conocidas)
18. [Solución de problemas y archivo de registro](#18-solución-de-problemas-y-archivo-de-registro)
19. [Licencia](#19-licencia)

---

## 1. ¿Qué puede hacer BgRemover?

BgRemover es una herramienta de edición de imágenes para **eliminar,
reemplazar y editar fondos** — con funciones adicionales para
optimización sencilla de imágenes, capas/proyectos y la preparación de
activos para impresión UV. Un **flujo guiado de 6 pasos** (Abrir →
Quitar fondo → Ajustar → Forma y medidas → Relieve y capas → Exportar)
te acompaña durante la edición. Las funciones principales:

- **Eliminación de fondo con IA** – recorta el fondo automáticamente
  con un solo clic.
- **Selección manual** con varita mágica, pincel, borrador y lazo
  poligonal.
- **Reemplazar fondo** – hacer la selección transparente o rellenarla
  con cualquier color.
- **Transformar** – rotar (en pasos de 90° o ángulo libre) y voltear.
- **Forma y recorte** – redondear esquinas, recortar en círculo o con
  una relación de aspecto fija.
- **Optimización de imagen** – ajustar brillo, contraste y saturación,
  y suavizar el borde alfa (feather).
- **Tamaño y medidas físicas** – cambiar el tamaño en píxeles o definir
  un tamaño de impresión mediante milímetros y DPI (con aviso de área
  de impresión).
- **Capas y proyectos** – gestionar varias capas (color/altura/gloss/
  genérica) y guardar y abrir todo como un proyecto `.bgrproj`.
- **Mapas de altura** – generar un mapa de altura a partir de una
  imagen, editarlo mediante controles o directamente con el pincel, y
  optimizarlo.
- **Vista previa 2D** – comprobar color, relieve, altura y gloss en
  pantalla.
- **Exportación a EufyMake Studio** – generar activos de importación
  para impresión UV.
- **Historial** con deshacer/rehacer y salto a cualquier paso anterior
  de edición.
- **Guardar** como PNG, JPEG, WebP o TIFF.

---

## 2. La interfaz del programa de un vistazo

![BgRemover – ventana principal tras el inicio](../../../app_screenshots/bgremover_complete_20260711_094027/01_main_empty.png)

*La ventana principal justo tras el inicio: la barra de menú arriba, la
barra de herramientas a la izquierda, el lienzo con el tablero de
transparencia en el centro, la barra de pasos sobre el lienzo, el
inspector de tarjetas a la derecha (aquí el paso 1 "Abrir") y la barra
de estado abajo.*

La ventana está dividida en cinco áreas:

```
┌─────────────────────────────────────────────────────────────┐
│ Barra de menú                                                 │
├──────────┬───────────────────────────────┬──────────────────┤
│          │      Barra de pasos (6 pasos)                     │
│ Barra de ├───────────────────────────────┼──────────────────┤
│ herra-   │                               │  Inspector       │
│ mientas  │        Lienzo                 │  de tarjetas     │
│ (izq.)   │      (imagen + selección)     │  (derecha)       │
│          │                               │                  │
├──────────┴───────────────────────────────┴──────────────────┤
│ Barra de estado (sugerencias y mensajes)                     │
└──────────────────────────────────────────────────────────────┘
```

| Área | Función |
|---|---|
| **Barra de menú** (arriba) | Archivo, Proyecto, Edición, Ver, Herramientas |
| **Barra de pasos** (sobre el lienzo) | Seis pasos: Abrir, Quitar fondo, Ajustar, Forma y medidas, Relieve y capas, Exportar |
| **Barra de herramientas** (izquierda) | Mover/Zoom, herramientas contextuales de selección/altura, deshacer/rehacer/tema |
| **Lienzo** (centro) | Muestra la imagen y la selección actual; la píldora de zoom abajo a la derecha muestra y controla el nivel de ampliación |
| **Inspector de tarjetas** (derecha) | Cabecera con título/descripción del paso, las tarjetas del paso activo, pie con "Atrás"/"Siguiente" |
| **Barra de estado** (abajo) | Sugerencias y respuestas del programa |

### Menús "Edición", "Ver", "Proyecto" y "Herramientas"

Muchas acciones también están disponibles desde la barra de menú:

- **Edición** – deshacer/rehacer, rotar (90° izquierda/derecha/180°),
  voltear horizontal/verticalmente, *Cambiar tamaño…*, así como anular/
  invertir selección y *Restaurar original*. Práctico si prefieres
  invocar una función desde el menú en lugar de la barra de
  herramientas o el inspector de tarjetas.
- **Ver** – *Ajustar a la vista* (⌘0), *Historial* (abre el mismo
  historial de cambios que antes el botón de la barra de
  herramientas), el submenú *Modo de vista previa* (consulta la
  [sección 12](#12-paso-6--exportar)) y *Tema claro* para alternar el
  esquema de color.
- **Proyecto** – *Nuevo proyecto*, *Abrir proyecto…*, *Guardar
  proyecto* / *…como…* (`.bgrproj`) y *Exportar assets para EufyMake
  Studio…* (consulta la [sección 11](#11-paso-5--relieve-y-capas) y la
  [sección 12](#12-paso-6--exportar)).
- **Herramientas** – *Ajustes…* (consulta la
  [sección 13](#13-configuración)), *Buscar actualizaciones…*, *Gestionar
  modelo de IA…* e *Instalar eliminación de fondo con IA…* (consulta la
  [sección 7](#7-paso-2--quitar-fondo) y la
  [sección 18](#18-solución-de-problemas-y-archivo-de-registro)).

![Menú "Edición"](../../../app_screenshots/bgremover_complete_20260711_094027/23_menu_edit.png)

*El menú "Edición" reúne deshacer/rehacer, rotar, voltear y las
acciones de selección.*

### La barra de pasos

Sobre el lienzo, la **barra de pasos** guía a través de seis estaciones:
**Abrir → Quitar fondo → Ajustar → Forma y medidas → Relieve y capas →
Exportar**. Un clic sobre un paso ya alcanzado o habilitado salta
directamente a él; sin una imagen cargada, los pasos 2–6 permanecen
bloqueados (solo el paso 1 está disponible). Los pasos completados
muestran una marca de verificación, y el paso activo aparece resaltado.
En el borde inferior del inspector de tarjetas, **"← Atrás"** y
**"Siguiente: …"** guían el proceso; en el último paso, el botón activa
en su lugar **"Exportar ✓"** (guardar).

### Zoom y vista

- **Zoom:** con la **rueda del ratón** sobre el lienzo acercas o alejas
  la vista, o utiliza la **píldora de zoom** flotante abajo a la
  derecha del lienzo (**−** / valor en porcentaje / **+** / candado
  para fijar el nivel de zoom).
- **Desplazar:** si la imagen es mayor que la ventana, desplázala con
  la herramienta **Mover/Zoom** (arrastrar con clic izquierdo) o
  mediante las barras de desplazamiento.
- **Ajustar:** `Ver → Ajustar a la vista` (⌘0) vuelve a encajar la
  imagen por completo en la ventana. Al cargar una imagen esto ocurre
  automáticamente.

---

## 3. Inicio rápido en 5 pasos

Así eliminas un fondo en menos de un minuto:

1. **Abrir imagen** – en el paso *Abrir*, arrastra la imagen al campo
   de depósito, usa `Archivo → Abrir` (⌘O / Ctrl+O) o arrástrala
   directamente al lienzo.
2. **Iniciar IA** – en el paso *Quitar fondo*, haz clic arriba en
   **"Eliminar fondo (IA)"**. El fondo se elimina automáticamente.
3. **Retocar (opcional)** – elimina restos de la selección con el
   **borrador** o añade con el **pincel**.
4. **Revisar** – si hace falta, retrocede un paso con **Deshacer**
   (⌘Z).
5. **Guardar** – en el paso *Exportar*, elige el formato **PNG**
   (conserva la transparencia) y haz clic en **Guardar**, o usa
   `Archivo → Guardar` (⌘S).

![Resultado de la eliminación de fondo con IA](../../../app_screenshots/bgremover_complete_20260711_094027/55_function_ai_result.png)

*Tras un clic en "Eliminar fondo (IA)", el fondo queda recortado
automáticamente — la barra de estado informa "Eliminación de fondo con
IA completada" y las áreas libres se muestran con el patrón de
cuadros.*

Los siguientes capítulos explican cada paso en detalle.

---

## 4. Paso 1 – Abrir imagen

Hay varias formas de cargar una imagen:

- **Campo de depósito (paso 1):** arrastra una imagen desde el gestor
  de archivos directamente al campo punteado del inspector de
  tarjetas, o haz clic en él para abrir el diálogo de archivos.
- **Menú:** `Archivo → Abrir…` (⌘O / Ctrl+O).
- **Arrastrar y soltar en el lienzo:** arrastra un archivo de imagen
  directamente al lienzo. Si arrastras varios archivos, solo se carga
  la primera imagen.
- **Abiertos recientemente:** `Archivo → Abiertos recientemente` y la
  tarjeta "Abiertos recientemente" en el paso *Abrir* (hasta tres
  entradas con miniatura) listan las entradas usadas más recientemente.
  Son tanto imágenes como **proyectos** `.bgrproj` (consulta la
  [sección 11](#11-paso-5--relieve-y-capas)); al hacer clic, el
  programa detecta el tipo y lo abre en consecuencia.
- **Iniciar con una ruta de imagen:** cuando el programa se inicia con
  una ruta de imagen — mediante la **línea de comandos**
  (`bgremover imagen.png`) o un **lanzador de escritorio de Linux**
  (asociación de archivos) —, carga esa imagen directamente al
  arrancar.
- **Abrir desde el Finder de macOS:** en macOS también puedes entregar
  una imagen a BgRemover mediante **doble clic**, "Abrir con…" o una
  **asociación de archivos** en el Finder.

Todas estas vías utilizan la misma **ruta de carga validada y
asíncrona**: se aplican las mismas comprobaciones de formato y tamaño,
y las imágenes grandes se cargan en segundo plano — la barra de estado
muestra el progreso. Tras la carga, la barra de pasos habilita
automáticamente el paso siguiente.

![El menú "Archivo"](../../../app_screenshots/bgremover_complete_20260711_094027/20_menu_file.png)

*El menú "Archivo" agrupa Abrir (⌘O), "Abiertos recientemente", Guardar
(⌘S) y Guardar como… (⇧⌘S).*

**Los formatos de entrada admitidos** son, de forma vinculante, **PNG,
JPEG, WebP, TIFF, BMP y GIF**. Esta lista es el contrato de entrada
actual, no un ejemplo: otros formatos se rechazan de forma controlada.
En particular, **HEIC/HEIF no se admite actualmente a propósito** — un
archivo HEIC/HEIF se rechaza como formato no admitido. El guardado se
hace en PNG, JPEG, WebP o TIFF (consulta la
[sección 12](#12-paso-6--exportar)).

> **Tamaño máximo de imagen: 40 megapíxeles.** Las imágenes más grandes
> se rechazan con un mensaje en la barra de estado.

---

## 5. La barra de herramientas (izquierda)

La barra vertical en el borde izquierdo es **contextual**: solo muestra
las herramientas del paso actualmente activo. De arriba abajo:

### Mover / Zoom (siempre disponible)

| Ícono | Herramienta | Función |
|---|---|---|
| ✥ | **Mover / Zoom** | Arrastrar con clic izquierdo desplaza el encuadre de la imagen, la rueda del ratón hace zoom. Activa en todos los pasos excepto *Quitar fondo* y *Relieve y capas*. |

### Herramientas de selección (solo en el paso "Quitar fondo")

| Ícono | Herramienta | Función |
|---|---|---|
| 🪄 | **Varita mágica** | Selecciona con un clic un área de color contigua (relleno por inundación). Ajustable mediante la *Tolerancia*. |
| 🖌 | **Pincel** | "Pintar" la selección manualmente. |
| 🧽 | **Borrador** | Eliminar la selección pintada. |
| ⬡ | **Lazo poligonal** | Haz clic en los puntos uno tras otro; **doble clic** cierra el polígono. **Esc** cancela. |

Cambio rápido con teclado: **W** varita mágica, **B** pincel,
**E** borrador, **L** lazo — estos atajos solo funcionan mientras el
paso *Quitar fondo* está activo.

En todas las herramientas de selección se aplica:

- **Shift + clic** → **añadir** a la selección
- **Ctrl/Cmd + clic** → **sustraer** de la selección

### Herramientas de altura (solo en el paso "Relieve y capas")

| Ícono | Herramienta | Función |
|---|---|---|
| ▲ | **Aclarar (más alto)** | La pincelada eleva la altura de la capa de altura activa. |
| ▼ | **Oscurecer (más bajo)** | La pincelada reduce la altura de la capa de altura activa. |

Ambas herramientas están desactivadas mientras no haya una capa de
altura activa (consulta la [sección 11](#11-paso-5--relieve-y-capas));
el tooltip indica entonces el motivo. Complementan las acciones de
aclarar/oscurecer basadas en controles del inspector de tarjetas con
una herramienta de pintura a mano alzada.

### Pie de la barra: deshacer, rehacer, tema

Abajo en la barra de herramientas quedan visibles — de forma
independiente del paso — tres botones:

| Ícono | Función |
|---|---|
| ↩ | **Deshacer** (⌘Z) – revertir el último paso |
| ↪ | **Rehacer** (⇧⌘Z) – volver a aplicar el paso deshecho |
| ◐ | **Alternar tema claro/oscuro** – cambia el esquema de color (misma acción que `Ver → Tema claro`) |

> La eliminación de fondo con IA, el historial de cambios y abrir/
> guardar imagen ya no están en la barra de herramientas: se accede a
> ellos desde el inspector de tarjetas del paso correspondiente, el
> menú o sus atajos de teclado (consulta la
> [sección 7](#7-paso-2--quitar-fondo) y la
> [sección 12](#12-paso-6--exportar)).

> **Consejo:** pasa el ratón sobre un ícono para mostrar un breve texto
> de ayuda (tooltip).

---

## 6. Hacer una selección

Casi todas las ediciones (hacer transparente, reemplazar color) actúan
sobre el **área actualmente seleccionada**. La selección se resalta en
color sobre la imagen. Las herramientas de selección están activas en
el paso *Quitar fondo*.

![Imagen cargada con una selección activa](../../../app_screenshots/bgremover_complete_20260711_094027/02_main_loaded_selection.png)

*Una imagen cargada con una selección activa: el área de fondo
seleccionada se resalta en color sobre el lienzo.*

### Con la varita mágica (recomendada para fondos de un solo color)

1. Elige la varita mágica en la barra de herramientas.
2. Haz clic en el fondo – se seleccionan todos los colores similares y
   contiguos.
3. ¿No es suficiente? Usa **Shift+clic** para añadir más áreas o
   aumenta la **Tolerancia** (tarjeta *Ajustes de herramienta* en el
   paso *Quitar fondo*).

### Con pincel y borrador (para correcciones finas)

- **Pincel:** pinta sobre el área deseada para añadirla a la
  selección.
- **Borrador:** pinta sobre áreas seleccionadas incorrectamente para
  eliminarlas.
- El **tamaño del pincel** se ajusta en la tarjeta *Ajustes de
  herramienta*.

### Con el lazo poligonal (para bordes rectos)

1. Elige el lazo.
2. Haz clic vértice por vértice alrededor del objeto.
3. **Doble clic** cierra el polígono y crea la selección.
4. **Esc** cancela la operación.

---

## 7. Paso 2 – Quitar fondo

En el paso *Quitar fondo* separas el motivo del fondo — automáticamente
mediante IA o a mano. El inspector de tarjetas agrupa para ello cuatro
tarjetas.

![El paso "Quitar fondo"](../../../app_screenshots/bgremover_complete_20260711_094027/11_step_2_cutout.png)

*Paso 2 "Quitar fondo": arriba el botón de IA, debajo los ajustes de
herramienta, las acciones de selección y "Editar fondo".*

### Eliminación de fondo con IA

Arriba en el inspector de tarjetas, el botón **"Eliminar fondo (IA)"**
elimina el fondo de forma totalmente automática. En la primera llamada
se carga el modelo de IA, lo que puede tardar un momento.

> Si el componente de IA (`rembg`) no está instalado, el botón aparece
> en gris. `Herramientas → Instalar eliminación de fondo con IA…` muestra
> directamente en la app el comando de instalación adecuado para tu
> plataforma (con botón de copiar); alternativamente, consulta la guía de
> instalación para configurar la función de IA.

A través de `Herramientas → Gestionar modelo de IA…` puedes comprobar en
cualquier momento si el modelo de IA ya se ha descargado, e iniciar o
cancelar la descarga allí.

### Ajustes de herramienta (tolerancia y tamaño de pincel)

| Control deslizante | Rango | Efecto |
|---|---|---|
| **Tolerancia (varita mágica)** | 0 – 255 (predeterminado: 30) | Qué tan similares deben ser los colores para seleccionarse juntos con la varita mágica. **Bajo** = solo colores muy similares · **Alto** = muchos tonos. |
| **Tamaño del pincel** | 4 – 200 px (predeterminado: 30 px) | Diámetro del pincel y del borrador. |

### Acciones de selección

- **Anular selección** – anula la selección actual. **Esc** cancela
  primero un recorte activo o un lazo poligonal iniciado, y solo anula
  la selección si ninguna de esas interacciones está activa.
- **Invertir selección** (⌘⇧I) – intercambia las áreas seleccionadas y
  no seleccionadas. Práctico: primero selecciona el *objeto* y luego
  invierte para editar el *fondo*.
- **Expandir / Contraer** – agranda o reduce la selección según el
  radio ajustado al lado (1 – 20 px, predeterminado: 2 px). Útil para
  eliminar un fino borde de color tras el recorte.

### Editar fondo

| Acción | Descripción |
|---|---|
| **Eliminar (transparente)** | Hace completamente transparente el área seleccionada. Consejo: primero selecciona el fondo con la varita mágica. |
| **Elegir color** | Abre un selector de color. El pequeño botón de color muestra el color de reemplazo elegido actualmente. |
| **Reemplazar color** | Rellena el área seleccionada con el color elegido. |

![Diálogo selector de color](../../../app_screenshots/bgremover_complete_20260711_094027/31_dialog_color_picker.png)

*Mediante "Elegir color" se abre el selector de color; el color
elegido aparece en el campo de color y se aplica a la selección con
"Reemplazar color".*

**Flujo típico:** seleccionar el fondo con la varita mágica/IA →
*Eliminar (transparente)* para obtener un PNG recortado, **o** elegir
un color y *Reemplazar color* para un fondo de un solo color (p. ej.
blanco para fotos de identidad).

### Suavizar borde (feather)

En la sección *Suavizar borde* de la misma tarjeta puedes dibujar el
**borde alfa** de forma más suave — útil contra bordes duros con
aspecto "recortado" tras un recorte.

- **Radio:** 0 – 20 px (predeterminado: 2 px) ajusta el ancho de la
  transición suave.
- **Suavizar borde** aplica el suavizado. Afecta solo al **canal de
  transparencia** (los colores permanecen sin cambios) y — si hay una
  selección activa — actúa solo dentro de la selección.

---

## 8. Paso 3 – Ajustar (corrección de color)

El paso *Ajustar* contiene una sencilla **corrección de color**. Actúa
sobre la **capa de color activa** (consulta la
[sección 11](#11-paso-5--relieve-y-capas)) y deja la transparencia sin
cambios.

| Control deslizante | Rango | Efecto |
|---|---|---|
| **Brillo** | 0 – 200 % (predeterminado: 100 %) | Aclarar u oscurecer la imagen. |
| **Contraste** | 0 – 200 % (predeterminado: 100 %) | Diferencia entre áreas claras y oscuras. |
| **Saturación** | 0 – 200 % (predeterminado: 100 %) | Intensidad del color; 0 % produce escala de grises. |

- Mientras arrastras los controles, el lienzo muestra una **vista
  previa en vivo**.
- **Aplicar** confirma la corrección (con deshacer/rehacer en el
  historial).
- **Restablecer** devuelve los tres controles a 100 % y descarta la
  vista previa.

---

## 9. Paso 4 – Forma y medidas

El paso *Forma y medidas* agrupa rotar/voltear, redondear esquinas,
recorte y un cambio rápido de tamaño en píxeles.

![El paso "Forma y medidas"](../../../app_screenshots/bgremover_complete_20260711_094027/13_step_4_shape.png)

*Paso 4 "Forma y medidas": rotación (rápida/ángulo libre), voltear,
redondear esquinas y, abajo, los formatos de recorte.*

### Rotar

- **Rotación rápida:** botones para *90° izquierda*, *90° derecha*,
  *180°* y *270°*.
- **Ángulo libre:** control deslizante o campo de entrada de **−180° a
  +180°**, luego **Aplicar ángulo**. Los ángulos oblicuos generan
  esquinas transparentes.

> La rotación rápida también funciona con teclado: ⌘← (90° izquierda)
> y ⌘→ (90° derecha).

### Voltear

- **Horizontal** – voltear izquierda ↔ derecha.
- **Vertical** – voltear arriba ↕ abajo.

### Redondear esquinas

1. Con el control deslizante **Radio** ajusta el grado de redondeo
   (0 = sin redondeo, hasta 500 px = máximo redondeo).
2. Haz clic en **Redondear esquinas**.

El resultado se guarda con esquinas transparentes — lo mejor es
hacerlo como PNG.

### Cambiar tamaño (píxeles, directamente en el paso)

La tarjeta "Cambiar tamaño" ofrece **Anchura × Altura en píxeles**
directamente en el paso: introduce los valores y haz clic en
**Aplicar**. Para la relación de aspecto vinculada, el método de
remuestreo y las medidas físicas (mm/DPI), usa el diálogo completo de
la [sección 10](#10-cambiar-tamaño-y-medidas-físicas).

### Formato de salida y recorte

1. Elige un formato – aparece un **marco** sobre la imagen:
   - **Formato especial:** ⬤ Círculo
   - **Cuadrado:** 1:1
   - **Horizontal:** 16:9, 4:3
   - **Vertical:** 9:16, 3:4
2. **Mover el marco:** haz clic en el centro y arrastra.
3. **Cambiar tamaño:** arrastra las esquinas – la relación de aspecto
   se conserva.
4. Encima del lienzo aparece una barra:
   - **✓ Aplicar recorte** – recorta la imagen.
   - **✗ Cancelar** – descarta el marco.

![Recorte circular activo con barra de confirmación](../../../app_screenshots/bgremover_complete_20260711_094027/63_crop_circle_overlay.png)

*Ejemplo "Círculo": el marco de recorte se sitúa sobre la imagen con
tiradores. Con "✓ Aplicar recorte" se recorta y "✗ Cancelar" descarta
el marco.*

---

## 10. Cambiar tamaño y medidas físicas

Mediante `Edición → Cambiar tamaño…` (Ctrl+R) abres el diálogo completo
de cambio de tamaño — con relación de aspecto vinculada, método de
remuestreo y medidas físicas. Para un cambio rápido de tamaño en
píxeles sin diálogo, el paso *Forma y medidas* ofrece la tarjeta en
línea de la [sección 9](#9-paso-4--forma-y-medidas). El diálogo conoce
dos unidades de medida:

### Cambiar el tamaño en píxeles

En el modo **Píxeles** indicas **Anchura** y **Altura** directamente en
píxeles. Con **Vincular relación de aspecto** se conserva la
proporción. El método de remuestreo determina la calidad:

| Método | Idoneidad |
|---|---|
| **Lanczos** | Mejor calidad (predeterminado), ideal para reducir. |
| **Bicúbico** | Resultados suaves, buen todoterreno. |
| **Bilineal** | Más rápido, algo más suave. |
| **Vecino más cercano** | Conserva bordes/píxeles duros, sin suavizado. |

El diálogo muestra el número de megapíxeles resultante y respeta el
límite de **40 megapíxeles**.

### Medidas físicas (mm/DPI) y área de impresión

En el modo **Milímetros (mm + DPI)** defines **anchura/altura en
milímetros** y una **resolución (DPI)**; de ahí resulta el tamaño en
píxeles. Este tamaño físico es el tamaño de impresión de referencia y
se guarda en el proyecto `.bgrproj`.

Mediante **Medio de destino** eliges un medio de impresión habitual
(p. ej. A4 o A3). Si el motivo cabe, el diálogo lo confirma; si es
mayor que el medio, un aviso indica que se supera el área de
impresión.

---

## 11. Paso 5 – Relieve y capas

El paso *Relieve y capas* agrupa la gestión de capas y el espacio de
trabajo del mapa de altura en dos tarjetas.

### Tipos y roles de capa

BgRemover puede gestionar varias **capas** en un **proyecto** y guardar
todo como un archivo `.bgrproj`. Para la edición clásica de fondo no
necesitas ocuparte de esto — una sola imagen se comporta como una
única capa de color. Cada capa tiene un **tipo** y, opcionalmente, un
**rol**. Solo las **capas de color** contribuyen a la imagen de color
visible; los demás tipos son capas de datos para la preparación de
impresión.

| Tipo / rol | Significado |
|---|---|
| **Color** (motivo de color) | La imagen visible. Varias capas de color forman juntas el composite, que también se exporta. |
| **Altura** (mapa de altura) | Un mapa de altura en escala de grises para relieve/impresión UV. |
| **Gloss** (máscara de gloss) | Una máscara para efectos de brillo (experimental). |
| **Genérica** | Una capa de datos neutra sin rol fijo. |

### Gestionar capas

En la tarjeta *Capas* gestionas la lista de capas:

| Acción | Descripción |
|---|---|
| **Nueva capa / Duplicar / Eliminar** | Añadir una capa, copiar la capa activa o eliminarla. |
| **Subir / Bajar** | Cambiar el orden de apilamiento de las capas. |
| **Renombrar** | Renombrar la capa activa. |
| **Rol** | Asignar un rol a la capa activa (solo se permiten combinaciones compatibles). |
| **Visibilidad** | Mostrar u ocultar una capa. |
| **Seleccionar** | Elegir una capa como capa **activa** – las herramientas actúan sobre ella. |
| **Opacidad** | Opacidad de la capa (se aplica al soltar). |

### Archivos de proyecto (.bgrproj)

A través del menú **Proyecto** trabajas con archivos de proyecto:

- **Nuevo proyecto** (Ctrl+N), **Abrir proyecto…** (Ctrl+Mayús+O).
- **Guardar proyecto** (Ctrl+Alt+S) y **Guardar proyecto como…**
  (Ctrl+Alt+Mayús+S).

Un archivo `.bgrproj` es un archivo comprimido con un **manifiesto**
(orden, tipos, roles, nombres, medidas físicas) y **un PNG por capa**;
las capas de altura guardan además sus valores de altura de 16 bits en
un archivo propio (versión de formato 2). Así se conservan todas las
capas sin pérdidas, incluida la transparencia y las alturas con toda su
precisión. Los proyectos antiguos se adoptan automáticamente al abrirlos
y se convierten al nuevo formato al guardarlos. Las versiones antiguas
de BgRemover (hasta 2.6.0) no pueden abrir archivos de proyecto v2 e
informan de una entrada inesperada; el archivo queda intacto. Los
proyectos aparecen además en
"Abiertos recientemente" (consulta la
[sección 4](#4-paso-1--abrir-imagen)).

### Mapas de altura: obtener

Un **mapa de altura** es una capa en escala de grises en la que el
brillo representa una altura: **claro = alto, oscuro = bajo**. Es la
base del relieve y de la impresión UV. La tarjeta *Altura* trabaja
sobre la **capa de altura** activa; las secciones Editar y Optimizar
solo están activas cuando hay una capa de altura activa.

- **Generar desde imagen** – convierte de forma determinista la imagen
  de color actual en un mapa de altura y lo crea como una nueva capa
  de altura.
- **Importar escala de grises…** – carga una imagen en escala de
  grises como mapa de altura y la escala al tamaño del proyecto. Los
  archivos en escala de grises de 16 bits (PNG/TIFF) se importan de forma
  **nativa con los 65536 niveles**; las imágenes en color y de 8 bits se
  convierten según su brillo. Las imágenes de 16 bits con canal alfa y las
  imágenes float no pueden leerse sin pérdidas y se rechazan con un
  mensaje. Al exportar para EufyMake, BgRemover avisa cuando un destino de
  8 bits cuantizaría las alturas internas de 16 bits.

### Mapas de altura: editar

- **Aclarar / Oscurecer** – eleva o reduce la altura; la **Intensidad**
  controla cuánto. Para pintar a mano alzada, el paso *Relieve y
  capas* ofrece además las herramientas de pincel homónimas en la
  barra de herramientas (consulta la
  [sección 5](#5-la-barra-de-herramientas-izquierda)).
- **Establecer altura** – fija la altura a un **valor** determinado.
- **Invertir** – intercambia alto y bajo.

Si hay una selección activa, las acciones basadas en controles actúan
solo dentro de la selección; si no, sobre toda la capa.

### Mapas de altura: optimizar

Las operaciones de optimización muestran una **vista previa en vivo**;
**Aplicar** las confirma (con deshacer/rehacer), **Descartar vista
previa** las descarta.

| Operación | Efecto |
|---|---|
| **Tono (negro/blanco)** | Establecer el punto negro y blanco de la altura. |
| **Gamma** | Llevar las alturas medias hacia más claro/oscuro. |
| **Desenfoque gaussiano (radio)** | Suavizado suave y uniforme. |
| **Desenfoque de mediana (radio)** | Suaviza preservando los bordes. |
| **Umbral** | Dividir la altura en dos niveles. |
| **Escalones** | Cuantizar la altura a una cantidad de escalones. |
| **Rango (mín/máx)** | Limitar la altura a un rango de valores. |

### Vista previa de relieve 3D

Además de la vista previa de relieve 2D, puedes ver el mapa de altura activo
como una **superficie 3D real y giratoria**. En la parte superior de la tarjeta
*Altura*, la fila **Visualización** alterna entre **2D** y **3D** (o mediante
«Ver → Mostrar relieve 3D»). El segmento 3D solo está activo cuando existe un
mapa de altura con datos válidos y tu entorno gráfico ofrece OpenGL 2.1.

La vista 3D es **solo de visualización**: permite girar e inspeccionar la
superficie desde distintos ángulos, pero **no cambia ni los datos de altura ni
la imagen guardada o la exportación**. En el viewport, arrastra con el botón
izquierdo para orbitar, usa el botón central o Alt+arrastrar para desplazar y
la rueda para acercar. Con el teclado, las flechas orbitan, Mayús+flechas
desplazan, `+`/`−` acercan, `Inicio` ajusta la vista y `Mayús+Inicio` restablece
cámara, exageración y luz a los valores predeterminados.

Los controles 3D ajustan la **exageración** (cuánto se amplifica visualmente el
relieve plano – solo la visualización, nunca los datos de altura), el **azimut
y la elevación de la luz** y la **calidad** (Reducida / Estándar / Alta). Las
imágenes muy grandes se simplifican de forma automática y determinista para la
vista 3D; un aviso «Vista simplificada 1:N» en la esquina superior izquierda del
viewport lo indica. La referencia exacta a nivel de píxel sigue siendo la vista
previa 2D.

Si el entorno no ofrece OpenGL 2.1 o se produce un error gráfico, la app sigue
siendo totalmente utilizable: el segmento 3D se desactiva, o el visor muestra un
aviso claro con las acciones «Mostrar relieve 2D» y «Reintentar»; la probada
vista previa de relieve 2D está siempre disponible como respaldo seguro.

---

## 12. Paso 6 – Exportar

El último paso, *Exportar*, agrupa la vista previa 2D, el guardado de
la imagen y la exportación para impresión UV en tres tarjetas.

### Vista previa 2D (color, relieve, altura, gloss, combinado)

La **vista previa 2D** muestra distintas vistas del mismo motivo
directamente en el lienzo. Es una **visualización en pantalla pura** y
no cambia ni la imagen ni la exportación. La tarjeta *Vista previa*
ofrece un control segmentado con cuatro modos; el quinto modo,
"Combinado", se alcanza mediante `Ver → Modo de vista previa`.

| Modo | Visualización |
|---|---|
| **Color** | La imagen de color normal. |
| **Relieve** | Un relieve sombreado a partir del mapa de altura, superpuesto de forma multiplicativa sobre la imagen de color. |
| **Altura** | El mapa de altura como imagen en escala de grises. |
| **Gloss** | La máscara de gloss como un brillo satinado. |
| **Combinado** (solo mediante `Ver → Modo de vista previa`) | Color, relieve y gloss juntos. |

- Con **Intensidad del relieve** (0 – 100 %, predeterminado 70 %)
  ajustas la intensidad del relieve; al 0 % se omite el relieve.
- **Mostrar gloss** activa o desactiva el componente de brillo.

La tarjeta de vista previa y el submenú Ver se mantienen sincronizados.
Las capas de datos ocultas se ignoran en la vista previa.

### Guardar

La tarjeta *Guardar* ofrece una selección de formato (PNG/JPEG/WebP/
TIFF) y el botón de guardado directamente en el paso; como alternativa,
guarda a través del menú:

- **Guardar:** `Archivo → Guardar` (⌘S / Ctrl+S)
- **Guardar como…:** `Archivo → Guardar como…` (⇧⌘S)

Al guardar siempre se escribe el **composite de color** (con
independencia de qué capa esté activa o qué modo de vista previa esté
establecido).

| Formato | Propiedades | Recomendación |
|---|---|---|
| **PNG** | Con transparencia | Para objetos recortados – **recomendación predeterminada** |
| **JPEG** | Sin canal de transparencia, las áreas transparentes se vuelven blancas | Para fotos con fondo opaco |
| **WebP** | Formato web moderno, transparencia posible | Para uso en la web |
| **TIFF** | Sin pérdida, transparencia posible | Para archivado/impresión |

> Si quieres conservar el recorte, elige **siempre PNG, WebP o TIFF**
> — JPEG rellena de blanco las zonas transparentes.

### Exportar para EufyMake Studio

A través de la tarjeta *Impresión UV* en el paso *Exportar* o de
`Proyecto → Exportar assets para EufyMake Studio…` (Ctrl+Alt+E),
BgRemover escribe **activos de importación** para EufyMake Studio —
**no** un archivo `.empf` terminado:

- **Motivo de color** (obligatorio) como PNG RGBA – de una capa con el
  rol *Motivo de color* o, si no hay ninguna, del composite de color.
- **Mapa de altura** (opcional) en escala de grises con **claro = alto,
  oscuro = bajo** – disponible solo si una capa tiene el rol *Mapa de
  altura* (p. ej. una capa de altura creada con "Generar desde
  imagen"; una simple capa de altura sin ese rol no se exporta).
- **Máscara de gloss** (opcional, experimental) como activo auxiliar –
  disponible solo si una capa tiene el rol *Gloss*.

En el diálogo eliges la carpeta de exportación, los activos opcionales
y la **profundidad de bits** del mapa de altura (8 bits predeterminado,
16 bits experimental). Una **comprobación previa a la exportación** se
ejecuta de forma continua e informa de los hallazgos según su
gravedad:

- **Errores** (⛔) bloquean la exportación hasta que se corrigen – p.
  ej. un motivo de color ausente o tamaños que no coinciden.
- **Advertencias** (⚠️) deben confirmarse de forma deliberada – p. ej.
  datos de altura/gloss vacíos o la salida de 16 bits sin confirmar.

Después, importa y posiciona los activos en EufyMake Studio, asigna
allí los modos de tinta/capas y guarda el proyecto de Studio tú mismo
como `.empf`.

---

## 13. Configuración

A través de `Herramientas → Ajustes…` (⌘, / Ctrl+,) puedes gestionar
los siguientes ajustes:

![El diálogo de ajustes](../../../app_screenshots/bgremover_complete_20260711_094027/30_dialog_settings.png)

*El diálogo de ajustes: idioma, directorios predeterminados para abrir
y guardar, formato de imagen preferido, así como la ruta al archivo de
registro con el botón "Abrir carpeta".*

| Ajuste | Descripción |
|---|---|
| **Directorio predeterminado para abrir** | Carpeta de inicio del diálogo de abrir (vacío = último usado) |
| **Directorio predeterminado para exportar/guardar** | Carpeta de inicio del diálogo de guardar (vacío = último usado) |
| **Formato de imagen preferido** | PNG, JPEG, WebP o TIFF – aparece como primera opción en el diálogo de guardar |
| **Idioma** | Alemán, inglés, español, francés, ucraniano o chino; el cambio surte efecto tras reiniciar |
| **Archivo de registro** | Muestra la ruta del archivo de registro; el botón "Abrir carpeta" abre el directorio en el gestor de archivos |
| **Buscar actualizaciones automáticamente al iniciar** | Casilla, desactivada por defecto; comprueba en segundo plano y solo muestra un aviso discreto y clicable en la barra de estado si hay una actualización disponible |

Los directorios, el formato preferido, el idioma y la opción de búsqueda
automática de actualizaciones se conservan entre inicios del programa.

A través de `Herramientas → Buscar actualizaciones…` también puedes
lanzar la comprobación manualmente en cualquier momento; el resultado se
muestra como un diálogo con un enlace a la página de la versión (si hay
una actualización disponible).

---

## 14. Atajos de teclado

En macOS la tecla modificadora es **⌘ (Cmd)**, en Linux/Windows
**Ctrl**. Los atajos de herramienta (W/B/E/L) solo funcionan mientras
el paso *Quitar fondo* está activo; las acciones sin atajo en la tabla
solo se alcanzan mediante el menú o el inspector de tarjetas.

| Acción | Atajo |
|---|---|
| Elegir varita mágica (solo en el paso "Quitar fondo") | W |
| Elegir pincel (solo en el paso "Quitar fondo") | B |
| Elegir borrador (solo en el paso "Quitar fondo") | E |
| Elegir lazo poligonal (solo en el paso "Quitar fondo") | L |
| Abrir imagen | ⌘O |
| Guardar imagen | ⌘S |
| Guardar imagen como… | ⇧⌘S |
| Nuevo proyecto | ⌘N |
| Abrir proyecto… | ⇧⌘O |
| Guardar proyecto | ⌥⌘S |
| Guardar proyecto como… | ⇧⌥⌘S |
| Exportar assets para EufyMake Studio… | ⌥⌘E |
| Deshacer | ⌘Z |
| Rehacer | ⇧⌘Z |
| Cambiar tamaño… | ⌘R |
| Rotar 90° a la izquierda | ⌘← |
| Rotar 90° a la derecha | ⌘→ |
| Anular selección (si no hay recorte/lazo activo) | Esc |
| Invertir selección | ⌘⇧I |
| Ajustar a la vista (Fit to View) | ⌘0 |
| Abrir ajustes | ⌘, |

---

## 15. Flujos de trabajo típicos

### A) Recortar foto de producto (fondo transparente)

1. Abrir la imagen.
2. En el paso *Quitar fondo*, hacer clic en **"Eliminar fondo (IA)"**.
3. Retocar los bordes con **borrador**/**pincel**.
4. Si hace falta, **Contraer** (1–2 px) para eliminar el borde de
   color.
5. En el paso *Exportar*, guardar como **PNG**.

### B) Foto de identidad con fondo blanco

1. Abrir la imagen.
2. En el paso *Quitar fondo*, hacer clic con la **varita mágica** en el
   fondo (ajustar la tolerancia).
3. **Elegir color** (blanco) → **Reemplazar color**.
4. En el paso *Forma y medidas*, elegir el formato **1:1**, posicionar
   el marco y **✓ Aplicar recorte**.
5. En el paso *Exportar*, guardar como **JPEG** o **PNG**.

### C) Foto de perfil redonda

1. Abrir la imagen.
2. Eliminar el fondo con **IA** (opcional).
3. En el paso *Forma y medidas*, elegir **⬤ Círculo** y arrastrar el
   marco sobre el rostro.
4. **✓ Aplicar recorte**.
5. En el paso *Exportar*, guardar como **PNG** (transparencia fuera
   del círculo).

### D) Conservar el objeto, solo cambiar el fondo

1. Abrir la imagen, en el paso *Quitar fondo* hacer clic con la
   **varita mágica** sobre el **objeto**.
2. **Invertir selección** (⌘⇧I) → ahora el fondo queda seleccionado.
3. Elegir un color → **Reemplazar color**.
4. En el paso *Exportar*, guardar.

### E) Activo de relieve de altura para EufyMake Studio

1. Abrir la imagen y recortarla.
2. En el paso *Relieve y capas*, **Generar desde imagen**.
3. Afinar la altura en la sección *Optimizar* (p. ej. *Tono*,
   *Desenfoque*) y **Aplicar**.
4. En el paso *Exportar*, elegir el modo de vista previa **Relieve** o,
   mediante `Ver → Modo de vista previa`, **Combinado** para
   comprobar.
5. Tarjeta *Impresión UV* → revisar los hallazgos y exportar.

---

## 16. Consejos y trucos

- **Primero grueso, luego fino:** recorta groseramente con IA o varita
  mágica, luego corrige con pincel/borrador.
- **Ajustar la tolerancia:** ¿se selecciona demasiado? → reduce la
  tolerancia. ¿se selecciona muy poco? → aumenta la tolerancia o usa
  Shift+clic.
- **Eliminar el borde de color:** tras el recorte, en el paso *Quitar
  fondo* aplica "Contraer" 1–2 px antes de eliminar el fondo.
- **Bordes suaves:** con *Suavizar borde* (paso *Quitar fondo*), los
  bordes recortados se ven menos duros.
- **Retroceder un paso:** cada paso queda registrado en el historial —
  con `Ver → Historial` puedes hacer doble clic para volver a
  cualquier estado anterior.
- **¿Nada funciona?** `Edición → Restaurar original` restablece la
  imagen a su estado de carga.

---

## 17. Limitaciones conocidas

- **Tamaño máximo de imagen: 40 megapíxeles.** Las imágenes más
  grandes se rechazan.
- **Formatos de entrada:** se admiten PNG, JPEG, WebP, TIFF, BMP y GIF.
  **HEIC/HEIF no se admite actualmente** y se rechaza de forma
  controlada.
- La **función de IA** requiere el componente opcional `rembg`. Sin
  él, el botón de IA está desactivado; todas las herramientas
  manuales siguen funcionando.
- La **vista previa 2D** es una visualización en pantalla pura; la
  exportación de imagen escribe sin cambios el composite de color.
- La **exportación a EufyMake** solo genera activos de importación,
  **no** un archivo `.empf` nativo; la salida de altura de 16 bits es
  experimental.
- El **paquete de aplicación** (`BgRemover.app`) es específico de
  macOS; en Linux la aplicación se ejecuta mediante el inicio directo
  del programa. Windows no forma parte actualmente de la matriz
  probada oficialmente.

---

## 18. Solución de problemas y archivo de registro

Ante cualquier problema conviene revisar el **archivo de registro**
interno `bgremover.log`. Se encuentra en el directorio de datos de la
aplicación determinado por Qt y se crea con la primera entrada de
registro. La ruta exacta puede variar según la plataforma y la
configuración de Qt:

- **macOS (configuración actual):**
  `~/Library/Application Support/BgRemover/BgRemover/bgremover.log`
- **Linux:** bajo `~/.local/share/`

El lanzador del paquete de aplicación de macOS escribe además
diagnósticos de arranque en
`~/Library/Application Support/BgRemover/bgremover.log`.

El archivo interno contiene mensajes de ejecución y detalles de
errores (trazas de pila) y es el primer punto de contacto para
solicitudes de soporte.

La forma más fácil de encontrar el archivo es a través de
`Herramientas → Ajustes… → Archivo de registro`: allí se muestra la
ruta completa, y el botón **"Abrir carpeta"** abre el directorio
directamente en el gestor de archivos — ideal para adjuntar el archivo
de registro a un correo de soporte.

| Problema | Posible solución |
|---|---|
| Botón de IA en gris | `rembg` no está instalado – `Herramientas → Instalar eliminación de fondo con IA…` muestra el comando de instalación, o consulta la guía de instalación |
| La imagen no se puede abrir | ¿Más de 40 megapíxeles? ¿Formato admitido (sin HEIC/HEIF)? Lee la barra de estado |
| La IA tarda mucho | La primera llamada carga el modelo – solo una vez, luego es más rápida |
| Transparencia perdida tras guardar | Guardado como JPEG → elige PNG/WebP/TIFF en su lugar |
| El proyecto no se puede abrir | ¿Archivo `.bgrproj` dañado/incompleto? Lee la barra de estado |

---

## 19. Licencia

BgRemover se distribuye bajo la **GNU General Public License v3.0 o
posterior** (`GPL-3.0-or-later`) – consulta [LICENSE](../../../LICENSE).
Una lista completa de todas las bibliotecas utilizadas y sus licencias
está en [RESOURCES.md](RESOURCES.md).

---

*Esta guía forma parte del proyecto BgRemover. Si tienes preguntas o
sugerencias de mejora, crea un issue en el repositorio de GitHub.*

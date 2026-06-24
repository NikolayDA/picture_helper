[Deutsch](../../../ANLEITUNG.md) · [English](../en/ANLEITUNG.md) · **Español** · [Français](../fr/ANLEITUNG.md) · [Українська](../uk/ANLEITUNG.md) · [简体中文](../zh/ANLEITUNG.md)

> **Nota:** La versión PDF de esta guía solo se genera para el original en alemán
> (`ANLEITUNG.pdf`). No se produce ningún PDF para esta traducción.

# BgRemover – Guía de usuario

Esta guía explica paso a paso cómo utilizar **BgRemover** — desde abrir la
primera imagen hasta guardar el resultado final. Está dirigida a usuarios sin
experiencia previa en edición de imágenes.

> Las notas sobre la **instalación** no se incluyen aquí deliberadamente; consulte
> [INSTALL_MAC.md](INSTALL_MAC.md) (macOS) o
> [INSTALL_LINUX.md](INSTALL_LINUX.md) (Linux). Esta guía asume que la
> aplicación ya puede iniciarse.

---

## Tabla de contenidos

1. [¿Qué puede hacer BgRemover?](#1-qué-puede-hacer-bgremover)
2. [La ventana de la aplicación de un vistazo](#2-la-ventana-de-la-aplicación-de-un-vistazo)
3. [Inicio rápido en 5 pasos](#3-inicio-rápido-en-5-pasos)
4. [Abrir una imagen](#4-abrir-una-imagen)
5. [La barra de herramientas (izquierda)](#5-la-barra-de-herramientas-izquierda)
6. [Hacer una selección](#6-hacer-una-selección)
7. [Pestaña "Selección"](#7-pestaña-selección)
8. [Pestaña "Fondo"](#8-pestaña-fondo)
9. [Pestaña "Ajustar" – Corrección de color](#9-pestaña-ajustar--corrección-de-color)
10. [Pestaña "Rotar/Voltear"](#10-pestaña-rotarvoltear)
11. [Pestaña "Forma" – Esquinas y recorte](#11-pestaña-forma--esquinas-y-recorte)
12. [Redimensionar y dimensiones físicas](#12-redimensionar-y-dimensiones-físicas)
13. [Capas y proyectos](#13-capas-y-proyectos)
14. [Espacio de trabajo de mapa de altura](#14-espacio-de-trabajo-de-mapa-de-altura)
15. [Vista previa 2D (color, relieve, altura, brillo)](#15-vista-previa-2d-color-relieve-altura-brillo)
16. [Guardar y exportar](#16-guardar-y-exportar)
17. [Configuración](#17-configuración)
18. [Atajos de teclado](#18-atajos-de-teclado)
19. [Flujos de trabajo típicos](#19-flujos-de-trabajo-típicos)
20. [Consejos y trucos](#20-consejos-y-trucos)
21. [Limitaciones conocidas](#21-limitaciones-conocidas)
22. [Solución de problemas y archivo de registro](#22-solución-de-problemas-y-archivo-de-registro)
23. [Licencia](#23-licencia)

---

## 1. ¿Qué puede hacer BgRemover?

BgRemover es una herramienta de edición de imágenes para **eliminar, reemplazar
y editar fondos** — con funciones adicionales para optimización sencilla de
imágenes, capas/proyectos y la preparación de activos para impresión UV. Las
funciones principales:

- **Eliminación de fondo con IA** – elimina el fondo automáticamente con un
  solo clic.
- **Selección manual** con varita mágica, pincel, goma y lazo poligonal.
- **Reemplazar fondo** – hacer la selección transparente o rellenarla con
  cualquier color.
- **Transformar** – rotar (en pasos de 90° o ángulo libre) y voltear.
- **Forma y recorte** – redondear esquinas, recortar en círculo o relación de
  aspecto fija.
- **Optimización de imagen** – ajustar brillo, contraste y saturación, y
  suavizar el borde alfa (feather).
- **Tamaño y dimensiones físicas** – cambiar el tamaño en píxeles o definir un
  tamaño de impresión mediante milímetros y DPI (con aviso de área de impresión).
- **Capas y proyectos** – gestionar varias capas (color/altura/brillo/genérica)
  y guardar y abrir todo como un proyecto `.bgrproj`.
- **Mapas de altura** – generar un mapa de altura a partir de una imagen, luego
  editarlo y optimizarlo.
- **Vista previa 2D** – comprobar color, relieve, altura y brillo en pantalla.
- **Exportación a EufyMake Studio** – generar activos de importación para
  impresión UV.
- **Historial** con deshacer/rehacer y salto a cualquier paso anterior.
- **Guardar** como PNG, JPEG, WebP o TIFF.

---

## 2. La ventana de la aplicación de un vistazo

![BgRemover – ventana principal tras el inicio](../../../app_screenshots/bgremover_complete_20260528_214013/01_main_empty.png)

*La ventana principal justo tras el inicio: la barra de herramientas a la
izquierda, el lienzo con el tablero de transparencia en el centro, el panel de
pestañas a la derecha (aquí la pestaña "Selección") y la barra de estado abajo.
Las capturas muestran la interfaz en alemán; las etiquetas se corresponden con
los términos usados en esta guía.*

La ventana está dividida en cuatro áreas:

```
┌──────────┬───────────────────────────────┬──────────────────┐
│          │                               │                  │
│  Barra   │         Lienzo                │  Panel de        │
│  de he-  │     (imagen + selección)      │  pestañas        │
│  rram.   │                               │  (configuración) │
│          │                               │                  │
├──────────┴───────────────────────────────┴──────────────────┤
│ Barra de estado (sugerencias y mensajes)                     │
└──────────────────────────────────────────────────────────────┘
```

| Área | Función |
|---|---|
| **Barra de menú** (arriba) | Archivo, Proyecto, Editar, Ver, Extras |
| **Barra de herramientas** (izquierda) | Herramientas de selección, IA, historial, abrir/guardar |
| **Lienzo** (centro) | Muestra la imagen y la selección actual |
| **Panel de pestañas** (derecha) | Ocho pestañas: Vista previa, Selección, Fondo, Ajustar, Rotar/Voltear, Forma, Capas, Altura |
| **Barra de estado** (abajo) | Sugerencias y respuestas de la aplicación |

### Menús "Editar", "Ver" y "Proyecto"

Muchas acciones también están disponibles desde la barra de menú:

- **Editar** – deshacer/rehacer, rotar (90° izquierda/derecha), voltear
  horizontal/verticalmente, *Redimensionar…*, así como deseleccionar/invertir
  selección y *Restaurar original*. Útil si prefieres el menú a la barra de
  herramientas o a una pestaña.
- **Ver** – *Ajustar a la vista* (⌘0) y el submenú *Modo de vista previa* (consulta
  la [sección 15](#15-vista-previa-2d-color-relieve-altura-brillo)); consulta
  también "Zoom y vista" abajo.
- **Proyecto** – *Nuevo proyecto*, *Abrir proyecto…*, *Guardar proyecto* /
  *…como…* (`.bgrproj`) y *Exportar activos para EufyMake Studio…* (consulta la
  [sección 13](#13-capas-y-proyectos) y la [sección 16](#16-guardar-y-exportar)).

![El menú "Editar"](../../../app_screenshots/bgremover_complete_20260528_214013/22_menu_edit.png)

*El menú "Editar" reúne deshacer/rehacer, rotar, voltear y las acciones de
selección.*

### Zoom y vista

- **Zoom:** usa la **rueda del ratón** sobre el lienzo para acercar o
  alejar.
- **Desplazar:** si la imagen es mayor que la ventana, navega con las
  **barras de desplazamiento** de los bordes derecho e inferior.
- **Ajustar:** `Ver → Ajustar a la vista` (⌘0) vuelve a escalar la imagen
  por completo dentro de la ventana. También ocurre automáticamente al
  cargar una imagen.

---

## 3. Inicio rápido en 5 pasos

Elimina un fondo en menos de un minuto:

1. **Abrir imagen** – `Archivo → Abrir` (⌘O / Ctrl+O) o arrastrar y soltar
   la imagen en la ventana.
2. **Ejecutar IA** – haz clic en el **ícono de IA** en la barra de
   herramientas izquierda. El fondo se elimina automáticamente.
3. **Retocar (opcional)** – usa la **goma** para eliminar restos de la
   selección o el **pincel** para añadir.
4. **Revisar** – si es necesario, pulsa **Deshacer** (⌘Z) para retroceder
   un paso.
5. **Guardar** – `Archivo → Guardar` (⌘S), elige el formato **PNG** (conserva
   la transparencia).

![Resultado de la eliminación de fondo con IA](../../../app_screenshots/bgremover_complete_20260528_214013/54_function_ai_result.png)

*Tras un clic en el ícono de IA, el fondo queda recortado automáticamente; la
barra de estado confirma que la eliminación de fondo con IA ha finalizado y el
patrón de cuadros marca las áreas transparentes.*

Las siguientes secciones explican cada paso en detalle.

---

## 4. Abrir una imagen

Hay varias formas de cargar una imagen:

- **Menú:** `Archivo → Abrir…` (⌘O / Ctrl+O).
- **Arrastrar y soltar:** arrastra un archivo de imagen desde el gestor de
  archivos directamente al lienzo. Si arrastras varios archivos, solo se
  carga la primera imagen.
- **Archivos recientes:** `Archivo → Archivos recientes` lista las últimas
  10 entradas abiertas. Son tanto imágenes como **proyectos** `.bgrproj`
  (consulta la [sección 13](#13-capas-y-proyectos)); al hacer clic, la
  aplicación detecta el tipo y lo abre en consecuencia.
- **Iniciar con una ruta de imagen:** cuando el programa se inicia con una ruta
  de imagen — mediante la **línea de comandos** (`bgremover imagen.png`) o un
  **lanzador de escritorio de Linux** (asociación de archivos) — carga esa
  imagen directamente al arrancar.
- **Abrir desde el Finder de macOS:** en macOS también puedes entregar una
  imagen a BgRemover mediante **doble clic**, "Abrir con…" o una **asociación de
  archivos** en el Finder.

Todas estas vías utilizan la misma **ruta de carga validada y asíncrona**: se
aplican las mismas comprobaciones de formato y tamaño, y las imágenes grandes se
cargan en segundo plano — la barra de estado muestra el progreso.

![El menú "Archivo"](../../../app_screenshots/bgremover_complete_20260528_214013/20_menu_file.png)

*El menú "Archivo" agrupa Abrir (⌘O), "Archivos recientes", Guardar (⌘S) y
Guardar como… (⇧⌘S).*

**Los formatos de entrada admitidos** son, de forma vinculante, **PNG, JPEG,
WebP, TIFF, BMP y GIF**. Esta lista es el contrato de entrada actual, no un
ejemplo: otros formatos se rechazan de forma controlada. En particular,
**HEIC/HEIF no es compatible actualmente por diseño** — un archivo HEIC/HEIF se
rechaza como formato no admitido. El guardado es en PNG, JPEG, WebP o TIFF
(consulta la [sección 16](#16-guardar-y-exportar)).

> **Tamaño máximo de imagen: 40 megapíxeles.** Las imágenes más grandes se
> rechazan con un mensaje en la barra de estado.

---

## 5. La barra de herramientas (izquierda)

La barra vertical en el borde izquierdo contiene, de arriba a abajo:

### Herramientas de selección

| Ícono | Herramienta | Función |
|---|---|---|
| 🪄 | **Varita mágica** | Selecciona un área continua de color similar con un clic (relleno por inundación). Ajustable mediante *Tolerancia*. |
| 🖌 | **Pincel** | Pintar una selección manualmente. |
| 🧽 | **Goma** | Eliminar la selección pintada. |
| ⬡ | **Lazo poligonal** | Haz clic en los puntos uno a uno; **doble clic** cierra el polígono. **Esc** cancela. |

Cambio rápido con teclado: **W** varita, **B** pincel,
**E** borrador, **L** lazo.

Para todas las herramientas de selección:

- **Shift + clic** → **añadir** a la selección
- **Ctrl/Cmd + clic** → **sustraer** de la selección

### Eliminación de fondo con IA

| Ícono | Función |
|---|---|
| ✨ | **IA** – elimina el fondo completamente de forma automática. El modelo de IA se carga en el primer uso, lo que puede tardar un momento. |

> Si el componente de IA (`rembg`) no está instalado, el botón aparece
> desactivado. Consulta la guía de instalación para configurar la función IA.

### Historial

| Ícono | Función |
|---|---|
| ↩ | **Deshacer** (⌘Z) – revertir el último paso |
| ↪ | **Rehacer** (⇧⌘Z) – volver a aplicar el paso deshecho |
| ⟲ | **Restaurar original** – descartar todas las ediciones |
| 🕘 | **Historial de ediciones** – lista de todos los pasos; **doble clic** en una entrada para saltar a ese estado |

![Ventana emergente "Historial de ediciones"](../../../app_screenshots/bgremover_complete_20260528_214013/40_popup_history.png)

*El historial de ediciones lista cada paso de edición; un doble clic en una
entrada vuelve exactamente a ese estado.*

### Archivo

| Ícono | Función |
|---|---|
| 📂 | **Abrir imagen** (⌘O) |
| 💾 | **Guardar imagen** (⌘S) |

> **Consejo:** Pasa el ratón sobre un ícono para mostrar un breve texto de
> ayuda (tooltip).

---

## 6. Hacer una selección

Casi todas las ediciones (hacer transparente, reemplazar color) actúan sobre
el **área actualmente seleccionada**. La selección se resalta en color sobre
la imagen.

![Imagen cargada con una selección activa](../../../app_screenshots/bgremover_complete_20260528_214013/02_main_loaded_selection.png)

*Una imagen cargada con una selección activa: el área de fondo seleccionada se
resalta en color sobre el lienzo.*

### Con la varita mágica (recomendado para fondos de color sólido)

1. Elige la varita mágica en la barra de herramientas.
2. Haz clic en el fondo – se seleccionan todos los colores similares y
   contiguos.
3. ¿No es suficiente? Usa **Shift+clic** para añadir más áreas o aumenta la
   **Tolerancia** (pestaña *Selección*).

### Con pincel y goma (para correcciones finas)

- **Pincel:** pinta sobre el área deseada para añadirla a la selección.
- **Goma:** pinta sobre áreas seleccionadas incorrectamente para eliminarlas.
- Ajusta el **tamaño del pincel** en la pestaña *Selección*.

### Con el lazo poligonal (para bordes rectos)

1. Elige el lazo.
2. Haz clic esquina por esquina alrededor del objeto.
3. **Doble clic** cierra el polígono y crea la selección.
4. **Esc** cancela la operación.

---

## 7. Pestaña "Selección"

La primera pestaña de edición del panel derecho controla el comportamiento de la
selección; ya aparece en la vista general de arriba ([sección 2](#2-la-ventana-de-la-aplicación-de-un-vistazo)) y en la figura
de la [sección 6](#6-hacer-una-selección).

### Sugerencias de herramientas

En la parte superior se listan las cuatro herramientas de selección con una
breve descripción y las teclas modificadoras (Shift = añadir,
Ctrl/Cmd = sustraer).

### Configuración

| Control deslizante | Rango | Efecto |
|---|---|---|
| **Tolerancia (varita mágica)** | 0 – 255 (predeterminado: 30) | Qué tan similares deben ser los colores para seleccionarse juntos. **Bajo** = solo colores muy similares · **Alto** = muchos tonos. |
| **Tamaño del pincel** | 4 – 200 px (predeterminado: 30 px) | Diámetro del pincel y la goma. |

### Acciones de selección

- **Deseleccionar** – borra la selección actual. **Esc** cancela primero un
  recorte activo o un lazo poligonal iniciado y solo borra la selección si
  ninguno está activo.
- **Invertir selección** (⌘⇧I) – intercambia áreas seleccionadas y no
  seleccionadas. Útil: primero selecciona el *objeto*, luego invierte para
  editar el *fondo*.
- **Expandir / Contraer** – agranda o reduce la selección por el radio
  adyacente (1 – 20 px, predeterminado: 2 px). Útil para eliminar un fino borde de color tras el
  recorte.

---

## 8. Pestaña "Fondo"

Aquí se modifica realmente la selección actual.

![La pestaña "Fondo"](../../../app_screenshots/bgremover_complete_20260528_214013/11_tab_background.png)

*La pestaña "Fondo": "Eliminar (transparente)" hace transparente la selección;
el cuadro de color y "Reemplazar color" la rellenan con un color.*

| Acción | Descripción |
|---|---|
| **Eliminar (transparente)** | Hace el área seleccionada completamente transparente. Consejo: primero selecciona el fondo con la varita mágica. |
| **Elegir color** | Abre un selector de color. El pequeño botón de color muestra el color de reemplazo elegido actualmente. |
| **Reemplazar color** | Rellena el área seleccionada con el color elegido. |

![Diálogo selector de color](../../../app_screenshots/bgremover_complete_20260528_214013/31_dialog_color_picker.png)

*"Elegir color" abre el selector de color; el color elegido aparece en el
cuadro y se aplica a la selección con "Reemplazar color".*

**Flujo de trabajo típico:** seleccionar fondo con varita mágica/IA →
*Eliminar (transparente)* para un PNG recortado, **o** elegir un color y
*Reemplazar color* para un fondo sólido (p. ej. blanco para fotos de
identidad).

### Suavizar borde (feather)

En la sección *Suavizar borde* de la misma pestaña puedes suavizar el **borde
alfa** — útil contra bordes duros con aspecto "recortado" tras una eliminación.

- **Radio:** 0 – 20 px (predeterminado: 2 px) define el ancho de la transición
  suave.
- **Suavizar borde** aplica el suavizado. Afecta solo al **canal de
  transparencia** (los colores no cambian) y — cuando hay una selección activa —
  solo dentro de la selección.

---

## 9. Pestaña "Ajustar" – Corrección de color

La pestaña *Ajustar* contiene una sencilla **corrección de color**. Actúa sobre
la **capa de color activa** (consulta la [sección 13](#13-capas-y-proyectos)) y
deja la transparencia sin cambios.

| Control deslizante | Rango | Efecto |
|---|---|---|
| **Brillo** | 0 – 200 % (predeterminado: 100 %) | Aclarar u oscurecer la imagen. |
| **Contraste** | 0 – 200 % (predeterminado: 100 %) | Diferencia entre áreas claras y oscuras. |
| **Saturación** | 0 – 200 % (predeterminado: 100 %) | Intensidad del color; 0 % da escala de grises. |

- Mientras arrastras los controles, el lienzo muestra una **vista previa en
  vivo**.
- **Aplicar** confirma la corrección (con deshacer/rehacer en el historial).
- **Restablecer** devuelve los tres controles a 100 % y descarta la vista
  previa.

---

## 10. Pestaña "Rotar/Voltear"

![La pestaña "Rotar/Voltear"](../../../app_screenshots/bgremover_complete_20260528_214013/12_tab_transform.png)

*La pestaña "Rotar/Voltear" con rotación rápida (90°/180°/270°), ángulo libre y
los botones para voltear horizontal y verticalmente.*

### Rotar

- **Rotación rápida:** botones para *90° izquierda*, *90° derecha*, *180°* y
  *270°*.
- **Ángulo libre:** control deslizante o campo de entrada de **−180° a
  +180°**, luego haz clic en **Aplicar ángulo**. Los ángulos oblicuos
  producen esquinas transparentes.

### Voltear

- **Horizontal** – voltear izquierda ↔ derecha.
- **Vertical** – voltear arriba ↕ abajo.

> La rotación rápida también está disponible mediante teclado: ⌘← (90°
> izquierda) y ⌘→ (90° derecha). Al final de la pestaña, **Redimensionar…**
> lleva al diálogo de la [sección 12](#12-redimensionar-y-dimensiones-físicas).

---

## 11. Pestaña "Forma" – Esquinas y recorte

![La pestaña "Forma"](../../../app_screenshots/bgremover_complete_20260528_214013/13_tab_shape_crop.png)

*La pestaña "Forma": arriba "Redondear esquinas" con control deslizante de
radio; debajo, los formatos de recorte (especiales, horizontal y vertical).*

### Redondear esquinas

1. Usa el control deslizante **Radio** para ajustar el redondeo (0 = sin
   redondeo, hasta 500 px = máximo).
2. Haz clic en **Redondear esquinas**.

El resultado se guarda con esquinas transparentes — mejor como PNG.

### Formato de salida y recorte

1. Elige un formato – aparece un **marco** en la imagen:
   - **Formatos especiales:** ⬤ Círculo, ■ 1:1 (cuadrado)
   - **Horizontal:** 16:9, 4:3, 3:2, 2:1, 7:4.5 (14:9)
   - **Vertical:** 9:16, 3:4
2. **Mover marco:** haz clic en el centro y arrastra.
3. **Redimensionar:** arrastra las esquinas – se preserva la relación de
   aspecto.
4. Aparece una barra encima del lienzo:
   - **✓ Aplicar recorte** – recorta la imagen.
   - **✗ Cancelar** – descarta el marco.

![Recorte circular activo con barra de confirmación](../../../app_screenshots/bgremover_complete_20260528_214013/61_crop_circle_overlay.png)

*Ejemplo "Círculo": el marco de recorte se sitúa sobre la imagen con tiradores.
"✓ Aplicar recorte" recorta la imagen y "✗ Cancelar" descarta el marco.*

---

## 12. Redimensionar y dimensiones físicas

Mediante `Editar → Redimensionar…` (Ctrl+R) o el botón **Redimensionar…** de la
pestaña *Rotar/Voltear*, escalas la imagen a un nuevo tamaño objetivo. El
diálogo admite dos unidades:

### Redimensionar en píxeles

En el modo **Píxeles** introduces **Anchura** y **Altura** directamente en
píxeles. Con **Vincular relación de aspecto** se conserva la proporción. El
método de remuestreo determina la calidad:

| Método | Idoneidad |
|---|---|
| **Lanczos** | Mejor calidad (predeterminado), ideal para reducir. |
| **Bicúbico** | Resultados suaves, buen todoterreno. |
| **Bilineal** | Más rápido, algo más suave. |
| **Vecino más cercano** | Mantiene bordes/píxeles duros, sin suavizado. |

El diálogo muestra el recuento de megapíxeles resultante y respeta el límite de
**40 megapíxeles**.

### Dimensiones físicas (mm/DPI) y área de impresión

En el modo **Milímetros (mm + DPI)** defines **anchura/altura en milímetros** y
una **resolución (DPI)**; de ahí resulta el tamaño en píxeles. Este tamaño
físico es el tamaño de impresión de referencia y se guarda en el proyecto
`.bgrproj`.

Mediante **Medio objetivo** eliges un medio de impresión común (p. ej. A4 o A3).
Si el motivo cabe, el diálogo lo confirma; si es mayor que el medio, un aviso
señala que se supera el área de impresión.

---

## 13. Capas y proyectos

BgRemover puede gestionar varias **capas** en un **proyecto** y guardar todo
como un archivo `.bgrproj`. Para la edición de fondo clásica no necesitas
ocuparte de esto — una sola imagen se comporta como una única capa de color.

### Tipos y roles de capa

Cada capa tiene un **tipo** y, opcionalmente, un **rol**. Solo las **capas de
color** alimentan la imagen de color visible; los demás tipos son capas de datos
para la preparación de impresión.

| Tipo / rol | Significado |
|---|---|
| **Color** (motivo de color) | La imagen visible. Varias capas de color forman juntas el composite, que también se exporta. |
| **Altura** (mapa de altura) | Un mapa de altura en escala de grises para relieve/impresión UV (consulta la [sección 14](#14-espacio-de-trabajo-de-mapa-de-altura)). |
| **Brillo** (máscara de brillo) | Una máscara para efectos de brillo (experimental). |
| **Genérica** | Una capa de datos neutra sin rol fijo. |

### La pestaña "Capas"

En la pestaña *Capas* gestionas la lista de capas:

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

Un archivo `.bgrproj` es un archivo comprimido con un **manifiesto** (orden,
tipos, roles, nombres, dimensiones físicas) y **un PNG por capa**. Así se
conservan todas las capas sin pérdidas, incluida la transparencia. Los proyectos
también aparecen en "Archivos recientes" (consulta la [sección 4](#4-abrir-una-imagen)).

---

## 14. Espacio de trabajo de mapa de altura

Un **mapa de altura** es una capa en escala de grises en la que el brillo
representa una altura: **claro = alto, oscuro = bajo**. Es la base del relieve y
la impresión UV. La pestaña *Altura* se divide en tres secciones y trabaja sobre
la **capa de altura** activa; las funciones de edición y optimización solo están
activas cuando hay una capa de altura activa.

### Adquirir

- **Generar desde imagen** – convierte de forma determinista la imagen de color
  actual en un mapa de altura y lo crea como una nueva capa de altura.
- **Importar escala de grises…** – carga una imagen en escala de grises como
  mapa de altura y la escala al tamaño del proyecto.

### Editar

- **Aclarar / Oscurecer** – sube o baja la altura; la **Intensidad** controla
  cuánto.
- **Establecer altura** – fija la altura a un **valor** fijo.
- **Invertir** – intercambia alto y bajo.

Cuando hay una selección activa, estas acciones afectan solo dentro de la
selección; de lo contrario, a toda la capa.

### Optimizar

Las operaciones de optimización muestran una **vista previa en vivo**;
**Aplicar** la confirma (con deshacer/rehacer) y **Descartar vista previa** la
descarta.

| Operación | Efecto |
|---|---|
| **Niveles (negro/blanco)** | Establecer el punto negro y blanco de la altura. |
| **Gamma** | Llevar las alturas medias hacia más claro/oscuro. |
| **Desenfoque gaussiano (radio)** | Suavizado suave y uniforme. |
| **Desenfoque de mediana (radio)** | Suaviza preservando los bordes. |
| **Umbral** | Dividir la altura en dos niveles. |
| **Pasos** | Cuantizar la altura a un número de niveles. |
| **Rango (mín/máx)** | Limitar la altura a un rango de valores. |

---

## 15. Vista previa 2D (color, relieve, altura, brillo)

La **vista previa 2D** muestra distintas vistas del mismo motivo directamente
en el lienzo. Es una **visualización en pantalla pura** y no cambia ni la imagen
ni la exportación. Elige el modo en la pestaña *Vista previa* o mediante
`Ver → Modo de vista previa`.

| Modo | Visualización |
|---|---|
| **Color** | La imagen de color normal. |
| **Relieve sobre color** | Un relieve sombreado a partir del mapa de altura, multiplicado sobre la imagen de color. |
| **Altura (escala de grises)** | El mapa de altura como imagen en escala de grises. |
| **Brillo** | La máscara de brillo como un brillo satinado. |
| **Combinado** | Color, relieve y brillo juntos. |

- Con **Intensidad del relieve** ajustas la intensidad del relieve; a 0 % se
  omite el relieve.
- **Mostrar brillo** activa o desactiva la capa de brillo.

La pestaña de vista previa y el submenú Ver se mantienen sincronizados. Las
capas de datos ocultas se ignoran en la vista previa.

---

## 16. Guardar y exportar

- **Guardar:** `Archivo → Guardar` (⌘S / Ctrl+S)
- **Guardar como…:** `Archivo → Guardar como…` (⇧⌘S)

Al guardar siempre se escribe el **composite de color** (independientemente de
qué capa esté activa o qué modo de vista previa esté establecido). Elige el
**formato de archivo** deseado en el diálogo:

| Formato | Propiedades | Recomendación |
|---|---|---|
| **PNG** | Con transparencia | Para objetos recortados – **recomendación predeterminada** |
| **JPEG** | Sin canal alfa; las áreas transparentes se vuelven blancas | Para fotos con fondo opaco |
| **WebP** | Formato web moderno, transparencia compatible | Para uso en la web |
| **TIFF** | Sin pérdida, transparencia compatible | Para archivado/impresión |

> Para conservar el recorte, **elige siempre PNG, WebP o TIFF** — JPEG rellena
> las áreas transparentes de blanco.

### Exportar para EufyMake Studio

Desde `Proyecto → Exportar activos para EufyMake Studio…` (Ctrl+Alt+E), BgRemover
escribe **activos de importación** para EufyMake Studio, **no** un archivo `.empf`
terminado:

- **Motivo de color** (obligatorio) como PNG RGBA – de una capa con el rol
  *Motivo de color* o, si no hay ninguna, del composite de color.
- **Mapa de altura** (opcional) en escala de grises con **claro = alto,
  oscuro = bajo** – disponible solo cuando una capa tiene el rol *Mapa de altura*
  (p. ej. una capa de altura creada con "Generar desde imagen"; una mera capa de
  altura sin ese rol no se exporta).
- **Máscara de brillo** (opcional, experimental) como activo auxiliar – disponible
  solo cuando una capa tiene el rol *Brillo*.

En el diálogo eliges la carpeta de exportación, los activos opcionales y la
**profundidad de bits** del mapa de altura (8 bits predeterminado, 16 bits
experimental). Una **comprobación previa a la exportación** se ejecuta de forma
continua e informa de los hallazgos por gravedad:

- **Errores** (⛔) bloquean la exportación hasta que se corrigen – p. ej. un
  motivo de color ausente o tamaños que no coinciden.
- **Advertencias** (⚠️) deben confirmarse de forma deliberada – p. ej. datos de
  altura/brillo vacíos o la salida de 16 bits sin confirmar.

Después, importa y posiciona los activos en EufyMake Studio, asigna allí los
modos de tinta/capas y guarda el proyecto de Studio como `.empf`.

---

## 17. Configuración

A través de `Extras → Configuración…` (⌘, / Ctrl+,) puedes gestionar los
siguientes ajustes:

![El diálogo de configuración](../../../app_screenshots/bgremover_complete_20260528_214013/30_dialog_settings.png)

*El diálogo de configuración: idioma, directorios predeterminados de apertura y
guardado, formato de imagen preferido y ruta del archivo de registro con el
botón "Abrir carpeta".*

| Ajuste | Descripción |
|---|---|
| **Directorio de apertura predeterminado** | Carpeta de inicio del diálogo de apertura (vacío = último usado) |
| **Directorio de exportación/guardado predeterminado** | Carpeta de inicio del diálogo de guardado (vacío = último usado) |
| **Formato de imagen preferido** | PNG, JPEG, WebP o TIFF – aparece como primera opción en el diálogo de guardado |
| **Idioma** | Alemán o inglés; el cambio se aplica después de reiniciar |
| **Archivo de registro** | Muestra la ruta del archivo de registro; el botón "Abrir carpeta" abre el directorio en el gestor de archivos |

Los directorios, el formato preferido y el idioma se conservan entre reinicios
de la aplicación.

---

## 18. Atajos de teclado

En macOS la tecla modificadora es **⌘ (Cmd)**, en Linux/Windows **Ctrl**.

| Acción | Atajo |
|---|---|
| Seleccionar varita mágica | W |
| Seleccionar pincel | B |
| Seleccionar borrador | E |
| Seleccionar lazo poligonal | L |
| Abrir imagen | ⌘O |
| Guardar imagen | ⌘S |
| Guardar imagen como… | ⇧⌘S |
| Nuevo proyecto | ⌘N |
| Abrir proyecto… | ⇧⌘O |
| Guardar proyecto | ⌥⌘S |
| Guardar proyecto como… | ⇧⌥⌘S |
| Exportar activos para EufyMake Studio… | ⌥⌘E |
| Deshacer | ⌘Z |
| Rehacer | ⇧⌘Z |
| Redimensionar… | ⌘R |
| Rotar 90° izquierda | ⌘← |
| Rotar 90° derecha | ⌘→ |
| Deseleccionar (si no hay recorte/lazo activo) | Esc |
| Invertir selección | ⌘⇧I |
| Ajustar a la vista | ⌘0 |
| Abrir configuración | ⌘, |

---

## 19. Flujos de trabajo típicos

### A) Recortar foto de producto (fondo transparente)

1. Abre la imagen.
2. Haz clic en **IA** en la barra de herramientas.
3. Refina los bordes con **goma**/**pincel**.
4. En la pestaña *Selección*, opcionalmente **Contraer** (1–2 px) para
   eliminar el borde de color.
5. Guarda como **PNG**.

### B) Foto de identidad con fondo blanco

1. Abre la imagen.
2. Haz clic con la **varita mágica** en el fondo (ajusta la tolerancia).
3. Pestaña *Fondo* → **Elegir color** (blanco) → **Reemplazar color**.
4. Pestaña *Forma* → elige formato **1:1**, posiciona el marco, haz clic en
   **✓ Aplicar recorte**.
5. Guarda como **JPEG** o **PNG**.

### C) Foto de perfil redonda

1. Abre la imagen.
2. Elimina el fondo con **IA** (opcional).
3. Pestaña *Forma* → elige **⬤ Círculo**, arrastra el marco sobre el rostro.
4. Haz clic en **✓ Aplicar recorte**.
5. Guarda como **PNG** (transparente fuera del círculo).

### D) Conservar objeto, solo reemplazar el fondo

1. Abre la imagen, haz clic con la **varita mágica** sobre el **objeto**.
2. Pestaña *Selección* → **Invertir selección** (⌘⇧I) → el fondo queda
   seleccionado.
3. Pestaña *Fondo* → elige un color → **Reemplazar color**.
4. Guarda.

### E) Activo de relieve de altura para EufyMake Studio

1. Abre y recorta la imagen.
2. Pestaña *Altura* → **Generar desde imagen**.
3. Afina la altura en la sección *Optimizar* (p. ej. *Niveles*, *Desenfoque*) y
   pulsa **Aplicar**.
4. En la *vista previa 2D*, elige el modo **Relieve sobre color** o
   **Combinado** para comprobar.
5. `Proyecto → Exportar activos para EufyMake Studio…`, revisa los hallazgos y
   exporta.

---

## 20. Consejos y trucos

- **Primero grueso, luego fino:** recorta groseramente con IA o varita mágica,
  luego corrige con pincel/goma.
- **Ajusta la tolerancia:** si se selecciona demasiado → reduce la tolerancia.
  Si se selecciona muy poco → aumenta la tolerancia o usa Shift+clic.
- **Eliminar borde de color:** tras el recorte, aplica "Contraer" 1–2 px en la
  pestaña *Selección* antes de eliminar el fondo.
- **Bordes suaves:** con *Suavizar borde* (pestaña *Fondo*), los bordes
  recortados se ven menos duros.
- **Retroceder:** cada paso queda registrado en el historial — haz doble clic
  en cualquier entrada del **Historial de ediciones** (🕘) para volver a ese
  estado.
- **¿Sin salida?** **Restaurar original** restablece la imagen a su estado de
  carga.

---

## 21. Limitaciones conocidas

- **Tamaño máximo de imagen: 40 megapíxeles.** Las imágenes más grandes se
  rechazan.
- **Formatos de entrada:** se admiten PNG, JPEG, WebP, TIFF, BMP y GIF.
  **HEIC/HEIF no es compatible actualmente** y se rechaza de forma controlada.
- La **función IA** requiere el componente opcional `rembg`. Sin él, el botón
  de IA está desactivado; todas las herramientas manuales siguen funcionando.
- La **vista previa 2D** es una visualización en pantalla pura; la exportación
  de imagen escribe sin cambios el composite de color.
- La **exportación a EufyMake** solo produce activos de importación, **no** un
  archivo `.empf` nativo; la salida de altura de 16 bits es experimental.
- El **paquete de aplicación** (`BgRemover.app`) es específico de macOS; en
  Linux la aplicación se inicia directamente. Windows no forma parte
  actualmente de la matriz probada oficialmente.

---

## 22. Solución de problemas y archivo de registro

Si surgen problemas, consulta el **archivo de registro** interno
`bgremover.log`. Se guarda en el directorio de datos determinado por Qt y se
crea con la primera entrada de registro. La ruta exacta puede variar según la
plataforma y la configuración de Qt:

- **macOS (configuración actual):**
  `~/Library/Application Support/BgRemover/BgRemover/bgremover.log`
- **Linux:** bajo `~/.local/share/`

El launcher del paquete de aplicación para macOS escribe además diagnósticos
de arranque en `~/Library/Application Support/BgRemover/bgremover.log`.

El archivo interno contiene mensajes de ejecución y detalles de errores
(trazas de pila) y es el primer punto de contacto para solicitudes de soporte.

La forma más fácil de encontrar el archivo es a través de
`Extras → Configuración… → Archivo de registro`: allí se muestra la ruta
completa, y el botón **"Abrir carpeta"** abre el directorio directamente en
el gestor de archivos — ideal para adjuntar el archivo de registro a un
correo de soporte.

| Problema | Posible solución |
|---|---|
| Botón de IA desactivado | `rembg` no está instalado – consulta la guía de instalación |
| La imagen no se puede abrir | ¿Más de 40 megapíxeles? ¿Formato compatible (sin HEIC/HEIF)? Lee la barra de estado |
| La IA tarda mucho | La primera llamada carga el modelo – solo una vez, más rápido después |
| Transparencia perdida tras guardar | Guardado como JPEG → elige PNG/WebP/TIFF en su lugar |
| El proyecto no se puede abrir | ¿Archivo `.bgrproj` dañado/incompleto? Lee la barra de estado |

---

## 23. Licencia

BgRemover se distribuye bajo la **Licencia Pública General GNU v3.0 o
posterior** (`GPL-3.0-or-later`) – consulta [LICENSE](../../../LICENSE). Una
lista completa de todas las bibliotecas utilizadas y sus licencias está en
[RESOURCES.md](RESOURCES.md).

---

*Esta guía forma parte del proyecto BgRemover. Para preguntas o sugerencias,
abre un issue en el repositorio de GitHub.*

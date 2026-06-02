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
9. [Pestaña "Rotar/Voltear"](#9-pestaña-rotarvoltear)
10. [Pestaña "Forma" – Esquinas y recorte](#10-pestaña-forma--esquinas-y-recorte)
11. [Guardar una imagen](#11-guardar-una-imagen)
12. [Configuración](#12-configuración)
13. [Atajos de teclado](#13-atajos-de-teclado)
14. [Flujos de trabajo típicos](#14-flujos-de-trabajo-típicos)
15. [Consejos y trucos](#15-consejos-y-trucos)
16. [Limitaciones conocidas](#16-limitaciones-conocidas)
17. [Solución de problemas y archivo de registro](#17-solución-de-problemas-y-archivo-de-registro)
18. [Licencia](#18-licencia)

---

## 1. ¿Qué puede hacer BgRemover?

BgRemover es una herramienta de edición de imágenes para **eliminar, reemplazar
y editar fondos**. Las funciones principales:

- **Eliminación de fondo con IA** – elimina el fondo automáticamente con un
  solo clic.
- **Selección manual** con varita mágica, pincel, goma y lazo poligonal.
- **Reemplazar fondo** – hacer la selección transparente o rellenarla con
  cualquier color.
- **Transformar** – rotar (en pasos de 90° o ángulo libre) y voltear.
- **Forma y recorte** – redondear esquinas, recortar en círculo o relación de
  aspecto fija.
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
| **Barra de menú** (arriba) | Archivo, Editar, Ver, Extras |
| **Barra de herramientas** (izquierda) | Herramientas de selección, IA, historial, abrir/guardar |
| **Lienzo** (centro) | Muestra la imagen y la selección actual |
| **Panel de pestañas** (derecha) | Cuatro pestañas: Selección, Fondo, Rotar/Voltear, Forma |
| **Barra de estado** (abajo) | Sugerencias y respuestas de la aplicación |

### Menús "Editar" y "Ver"

Muchas acciones también están disponibles desde la barra de menú:

- **Editar** – deshacer/rehacer, rotar (90° izquierda/derecha), voltear
  horizontal/verticalmente, así como deseleccionar/invertir selección y
  *Restaurar original*. Útil si prefieres el menú a la barra de herramientas
  o a una pestaña.
- **Ver** – *Ajustar a la vista* (⌘0); consulta "Zoom y vista" abajo.

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

Hay tres formas de cargar una imagen:

- **Menú:** `Archivo → Abrir…` (⌘O / Ctrl+O).
- **Arrastrar y soltar:** arrastra un archivo de imagen desde el gestor de
  archivos directamente al lienzo. Si arrastras varios archivos, solo se
  carga la primera imagen.
- **Archivos recientes:** `Archivo → Archivos recientes` lista las últimas
  10 imágenes abiertas.

![El menú "Archivo"](../../../app_screenshots/bgremover_complete_20260528_214013/20_menu_file.png)

*El menú "Archivo" agrupa Abrir (⌘O), "Archivos recientes", Guardar (⌘S) y
Guardar como… (⇧⌘S).*

Al abrir se admiten formatos comunes como PNG, JPEG, WebP, TIFF, BMP y GIF;
el guardado es en PNG, JPEG, WebP o TIFF. Las imágenes
grandes se cargan en segundo plano — la barra de estado muestra el progreso.

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

La primera pestaña del panel derecho controla el comportamiento de la
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

- **Deseleccionar** – borra la selección actual (también con la tecla **Esc**).
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

---

## 9. Pestaña "Rotar/Voltear"

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
> izquierda) y ⌘→ (90° derecha).

---

## 10. Pestaña "Forma" – Esquinas y recorte

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

## 11. Guardar una imagen

- **Guardar:** `Archivo → Guardar` (⌘S / Ctrl+S)
- **Guardar como…:** `Archivo → Guardar como…` (⇧⌘S)

Elige el **formato de archivo** deseado en el diálogo:

| Formato | Propiedades | Recomendación |
|---|---|---|
| **PNG** | Con transparencia | Para objetos recortados – **recomendación predeterminada** |
| **JPEG** | Sin canal alfa; las áreas transparentes se vuelven blancas | Para fotos con fondo opaco |
| **WebP** | Formato web moderno, transparencia compatible | Para uso en la web |
| **TIFF** | Sin pérdida, transparencia compatible | Para archivado/impresión |

> Para conservar el recorte, **elige siempre PNG, WebP o TIFF** — JPEG rellena
> las áreas transparentes de blanco.

---

## 12. Configuración

A través de `Extras → Configuración…` (⌘, / Ctrl+,) puedes gestionar los
siguientes ajustes:

![El diálogo de configuración](../../../app_screenshots/bgremover_complete_20260528_214013/30_dialog_settings.png)

*El diálogo de configuración: los directorios predeterminados de apertura y
guardado, el formato de imagen preferido y la ruta del archivo de registro con
el botón "Abrir carpeta".*

| Ajuste | Descripción |
|---|---|
| **Directorio de apertura predeterminado** | Carpeta de inicio del diálogo de apertura (vacío = último usado) |
| **Directorio de exportación/guardado predeterminado** | Carpeta de inicio del diálogo de guardado (vacío = último usado) |
| **Formato de imagen preferido** | PNG, JPEG, WebP o TIFF – aparece como primera opción en el diálogo de guardado |
| **Archivo de registro** | Muestra la ruta del archivo de registro; el botón "Abrir carpeta" abre el directorio en el gestor de archivos |

Los primeros tres ajustes se conservan entre reinicios de la aplicación.

---

## 13. Atajos de teclado

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
| Deshacer | ⌘Z |
| Rehacer | ⇧⌘Z |
| Rotar 90° izquierda | ⌘← |
| Rotar 90° derecha | ⌘→ |
| Deseleccionar | Esc |
| Invertir selección | ⌘⇧I |
| Ajustar a la vista | ⌘0 |
| Abrir configuración | ⌘, |

---

## 14. Flujos de trabajo típicos

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

---

## 15. Consejos y trucos

- **Primero grueso, luego fino:** recorta groseramente con IA o varita mágica,
  luego corrige con pincel/goma.
- **Ajusta la tolerancia:** si se selecciona demasiado → reduce la tolerancia.
  Si se selecciona muy poco → aumenta la tolerancia o usa Shift+clic.
- **Eliminar borde de color:** tras el recorte, aplica "Contraer" 1–2 px en la
  pestaña *Selección* antes de eliminar el fondo.
- **Retroceder:** cada paso queda registrado en el historial — haz doble clic
  en cualquier entrada del **Historial de ediciones** (🕘) para volver a ese
  estado.
- **¿Sin salida?** **Restaurar original** restablece la imagen a su estado de
  carga.

---

## 16. Limitaciones conocidas

- **Tamaño máximo de imagen: 40 megapíxeles.** Las imágenes más grandes se
  rechazan.
- La **función IA** requiere el componente opcional `rembg`. Sin él, el botón
  de IA está desactivado; todas las herramientas manuales siguen funcionando.
- El **paquete de aplicación** (`BgRemover.app`) es específico de macOS; en
  Linux la aplicación se inicia directamente. Windows no forma parte
  actualmente de la matriz probada oficialmente.

---

## 17. Solución de problemas y archivo de registro

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
| La imagen no se puede abrir | ¿Más de 40 megapíxeles? ¿Formato compatible? Lee la barra de estado |
| La IA tarda mucho | La primera llamada carga el modelo – solo una vez, más rápido después |
| Transparencia perdida tras guardar | Guardado como JPEG → elige PNG/WebP/TIFF en su lugar |

---

## 18. Licencia

BgRemover se distribuye bajo la **Licencia Pública General GNU v3.0 o
posterior** (`GPL-3.0-or-later`) – consulta [LICENSE](../../../LICENSE). Una
lista completa de todas las bibliotecas utilizadas y sus licencias está en
[RESOURCES.md](RESOURCES.md).

---

*Esta guía forma parte del proyecto BgRemover. Para preguntas o sugerencias,
abre un issue en el repositorio de GitHub.*

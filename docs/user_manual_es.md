# Lossless Crop

## Caso de uso
Esta aplicación es útil para recortar rápidamente varias imágenes en un directorio una tras otra.

## FormatOS compatibles
- **JPEG**: Modos de recorte sin pérdida (lossless) o con pérdida (lossy)
- **PNG**: Sin pérdida
- **BMP**: Sin pérdida
- **WebP**: Con pérdida

## Nota sobre el recorte sin pérdida
Se requiere el ajuste a la cuadrícula (grid snapping) para realizar un recorte sin pérdida en una imagen *JPEG*, debido a que las imágenes JPEG agrupan los píxeles en bloques llamados Unidades Mínimas Codificadas (MCUs). Los límites del recorte deben alinearse con estos bloques para realizar el recorte sin recompresión y sin pérdida de calidad.
Esa es la razón por la cual, al seleccionar el motor sin pérdida (lossless) en una imagen JPEG, el área seleccionada para recortar saltará para ajustarse a los bloques MCU más cercanos. Si no desea esto, puede utilizar el motor pixel-perfect, el cual tiene pérdida pero le permite elegir su área de recorte libremente.
El recorte de *PNG* o *BMP* siempre es sin pérdida y no requiere ajuste a la cuadrícula.
*WebP* en esta aplicación se maneja como recorte con pérdida.

## Flujo de trabajo básico
1. Abra un directorio con imágenes
2. Dibuje la selección sobre la imagen
3. Recorte y pase a la siguiente imagen

## Zoom con la vista previa flotante de HUD (Zoom HUD)
Puede activar la vista previa flotante presionando `P` o `Q` o desde el panel de configuración (Settings Drawer).
Esta vista previa se puede redimensionar arrastrando en los bordes con el clic izquierdo y mover manteniendo presionado el clic derecho, de forma coherente con el área de selección.
Si la opción `Preview HUD` está marcada en 'Layout Memory', el tamaño y la posición del HUD de vista previa actual se guardarán y restaurarán la próxima vez que abra la aplicación.

### Flujo de trabajo A ("No me gusta el zoom flotante")
Una forma sencilla de obtener otro zoom es trabajar con `Overwrite` (Sobrescribir) activo y presionar `S` para recortar alrededor del área en la que desea hacer zoom. Cada vez que recorte, la imagen actual cambiará y se recargará mostrando únicamente la parte recortada.
Tenga en cuenta que esto sobrescribe sus archivos originales.

### Flujo de trabajo B ("No me gusta el zoom flotante")
¿Qué pasa si necesita recortar diferentes partes pequeñas de una imagen grande? Entonces puede desactivar `Overwrite`, recortar todas las partes que necesite de todas las imágenes que desee, abrir la subcarpeta 'cropped' donde se ubicarán estas partes más pequeñas y volver a recortarlas con mayor precisión.

## Opciones de la barra de herramientas
### Motor (Engine)
- **Lossless**: Utiliza el motor jpegtran para realizar el recorte sin pérdida de imágenes JPEG; si la imagen no es un *JPEG* válido, esta opción se ignora.
- **Pixel-Perfect**: Utiliza el motor Pillow para recortar, ya sea con una pérdida menor de calidad para *JPEG* y *WebP* o sin pérdida para *PNG* y *BMP*.

### Relación de aspecto forzada (Forced Ratio)
Esta opción impone una relación de aspecto en el cuadro de recorte; opciones disponibles:
- Libre (Freeform)
- Relación de origen (Source Ratio)
- Cuadrado 1:1 (1:1 Square)
- Pantalla panorámica 16:9 (16:9 Widescreen)
- Estándar 4:3 (4:3 Standard)

### Comentarios de ajuste (Snapping Feedback)
Cambia la forma en que se muestra el ajuste a la cuadrícula al usuario.
Esto solo se aplica al recorte sin pérdida, lo que significa que el motor Lossless debe estar seleccionado junto con una imagen JPEG válida.
Hay 3 opciones:
- **Real Time Snap:** El ajuste se adapta en tiempo real mientras el usuario dibuja el área de recorte.
- **Post Release Snap**: El ajuste solo se muestra cuando el usuario termina de dibujar.
- **Ghosting**: Se dibuja otro cuadro mientras el usuario dibuja para mostrar la cuadrícula ajustada.

### Entradas manuales del área de recorte
Los controles numéricos (spinboxes) se pueden utilizar para ingresar el tamaño deseado del área de recorte.
*Importante*: Para que los valores se registren, el usuario debe presionar Enter o salir de los campos de edición de los spinboxes.

### Mantener selección (Keep selection)
Útil para conservar el cuadro de selección de una imagen a otra si se espera que los tamaños de recorte sean similares.

### Sobrescribir (Overwrite)
Activar esta opción sobrescribe el archivo original después de recortar.

### Engranaje de configuración (Settings Gear)
Abre el panel deslizante de configuración.

## Panel de configuración (Settings drawer)
Proporciona numerosas opciones de visibilidad y persistencia.
### Configuración general
- Guardar configuración (Save settings): persiste la configuración del usuario y la recarga la próxima vez que se use la aplicación.
- Apertura automática de la última carpeta (Auto-open last folder): abre el último directorio de trabajo utilizado al iniciar la aplicación.
- Ajustar vista previa (Fit preview): cambia cómo se muestra la imagen en el HUD de vista previa. Al activarlo, se muestra el área seleccionada completa.
- Tema oscuro (Dark Theme): habilita el tema oscuro. De lo contrario, se aplica el tema claro.

### Mostrar / Visualizar (Show / Display)
Afecta lo que se muestra u oculta en la interfaz de usuario.

### Memoria de diseño (Layout Memory)
- Ventana principal (Main Window): recarga el tamaño y la posición de la ventana principal de la aplicación al iniciar.
- HUD de vista previa (Preview HUD): recarga el tamaño y la posición del HUD de vista previa al iniciar.

## Barra de menús
La barra de menús se puede alternar con la tecla *Alt*.
Los comandos habituales se explican en la sección de comandos; aquí solo se explican las acciones especiales.

- Archivo -> Ver registros (File -> See Logs): Abre la carpeta con los registros de aplicación para que el usuario los lea si es necesario.
- Recientes -> Directorio (Recent -> Directory): Abre el directorio seleccionado de la lista de recientes.
- Ayuda -> Manual de usuario (Help -> User Manual): Muestra este manual de usuario.
- Help -> Acerca de (Help -> About): Muestra la ventana "Acerca de".

## Atajos globales de teclado y controles del ratón

| Acciones de teclado | Teclas | Acciones de ratón | Control |
| :--- | :--- | :--- | :--- |
| **Recortar y Siguiente** | <kbd>Espacio</kbd> | **Dibujar cuadro** | <kbd>Clic Izquierdo</kbd> + Arrastrar |
| **Recortar** | <kbd>S</kbd> o <kbd>Clic Central</kbd> | **Mover cuadro** | <kbd>Clic Derecho</kbd> + Arrastrar |
| **Abrir Directorio** | <kbd>O</kbd> | **Navegar** | <kbd>Rueda del Ratón</kbd> |
| **Abrir Imagen** | <kbd>I</kbd> | **Recortar** | <kbd>Clic Central</kbd> |
| **Avanzar** | <kbd>F</kbd> o <kbd>D</kbd> | | |
| **Retroceder** | <kbd>B</kbd> o <kbd>A</kbd> | | |
| **Girar en Sentido Horario** | <kbd>R</kbd> | | |
| **Alternar Vista Previa** | <kbd>P</kbd> o <kbd>Q</kbd> | | |
| **Alternar Menú** | <kbd>Alt</kbd> | | |
| **Salir de la App** | <kbd>Esc</kbd> | | |

## Comandos
Existen varias formas de realizar las mismas acciones en la aplicación; elija la que mejor se adapte a sus necesidades:
- *Abrir Directorio*: Abre una carpeta con imágenes y la carga en la aplicación. Debe contener imágenes válidas.
- *Abrir Imagen*: Permite elegir una imagen individual para abrir el directorio en esa imagen específica.
- *Avanzar*: Mueve a la siguiente imagen.
- *Retroceder*: Mueve a la imagen anterior.
- *Recortar*: Recorta el área seleccionada.
- *Recortar y Siguiente*: Recorta y avanza a la siguiente imagen.
- *Girar*: Gira la imagen en sentido horario.
- *Salir*: Cierra la aplicación.

## Soporte de arrastrar y soltar (Drag and Drop)
- Arrastrar un directorio a la aplicación equivale al comando Abrir Directorio.
- Arrastrar una imagen a la aplicación equivale al comando Abrir Imagen.

## Iconos de la barra de herramientas
A la izquierda de la barra de herramientas, los iconos se pueden utilizar para activar Abrir Directorio, Abrir Imagen, Recortar, Recortar y Siguiente y Girar, en ese orden de aparición.

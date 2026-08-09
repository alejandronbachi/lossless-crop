<p align="center">
  <img src="../../assets/screenshots/banner.png" width="100%" alt="Lossless Crop">
</p>
<p align="center">
<img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python">
<img src="https://img.shields.io/badge/Windows-Supported-blue?logo=windows" alt="WindowsSupport">
<img src="https://img.shields.io/badge/macOS-Supported-lighgrey?logo=apple" alt="macOSSupport">
<img src="https://img.shields.io/badge/Linux-Supported-orange?logo=linux" alt="LinuxSupport">
</p>


**Una aplicación multiplataforma de recorte de imágenes sin pérdida (lossless) con numerosas características y opciones de configuración.**

## Caso de uso
Útil para recortar rápidamente varias imágenes en un directorio una tras otra.

## Características

- Flujo de trabajo de recorte rápido
- Vista previa de zoom flotante configurable
- Soporte para recorte **sin pérdida (lossless)** en formatos de imagen *JPEG*, *PNG* y *BMP*
- Soporte para recorte **con pérdida (lossy)** en formatos *JPEG* y *WebP*
- Conservación de datos Exif y perfiles ICC
- Aplicación, conservación y redimensionamiento de la relación de aspecto (aspect ratio) del área de recorte
- Multiplataforma: compatible con **Windows**, **Linux** y **macOS**
- Temas oscuro y claro
- Atajos de teclado globales
- Entrada manual del área de recorte
- Soporte para arrastrar y soltar (drag and drop)
- Menú de directorios recientes
- Interfaz de usuario configurable
- Persistencia opcional de la configuración

## Demostración
<p align="center">
  <img src="../../assets/screenshots/demo.webp" width="850" alt="Demostración">
</p>

## Formatos Soportados
- **JPEG**: Modos de recorte sin pérdida o con pérdida
- **PNG**: Sin pérdida
- **BMP**: Sin pérdida
- **WebP**: Con pérdida

## Instalación

### Opción 1: Binarios
Descarga el binario apropiado desde la [Página de Lanzamientos (Releases)](https://github.com/alejandronbachi/lossless-crop/releases):
- **Windows** (`LosslessCrop-Windows.exe`)
- **Linux** (`LosslessCrop-Linux`)
- **macOS** (`LosslessCrop-macOS.tar.gz`)

[![GitHubRelease](https://img.shields.io/github/v/release/alejandronbachi/lossless-crop?color=blue)](https://github.com/alejandronbachi/lossless-crop/releases)

## Guía de Inicio Rápido / Uso
1. Abre un directorio con imágenes
2. Dibuja la selección sobre la imagen
3. Presiona `space` para recortar y pasar a la siguiente imagen

## Manual de Usuario
Por favor, lee el [Manual de Usuario](/docs/user_manual_es.md) para más instrucciones, especialmente si necesitas saber cómo funciona el recorte sin pérdida; de lo contrario, el ajuste (snapping) del área de selección podría parecer un comportamiento inesperado.

## Atajos de Teclado Globales y Controles del Mouse

| Acciones de Teclado | Teclas | Acciones del Mouse | Control |
| :--- | :--- | :--- | :--- |
| **Recortar y Siguiente** | <kbd>Space</kbd> | **Dibujar Cuadro** | <kbd>Clic Izquierdo</kbd> + Arrastrar |
| **Recortar** | <kbd>S</kbd> o <kbd>Middle-Click</kbd> | **Mover Cuadro** | <kbd>Clic Derecho</kbd> + Arrastrar |
| **Abrir Directorio** | <kbd>O</kbd> | **Navegar** | <kbd>Rueda del Mouse</kbd> |
| **Abrir Imagen** | <kbd>I</kbd> | **Recortar** | <kbd>Clic Central</kbd> |
| **Avanzar** | <kbd>F</kbd> o <kbd>D</kbd> | | |
| **Retroceder** | <kbd>B</kbd> o <kbd>A</kbd> | | |
| **Rotar en sentido horario** | <kbd>R</kbd> | | |
| **Alternar Vista Previa** | <kbd>P</kbd> o <kbd>Q</kbd> | | |
| **Alternar Menú** | <kbd>Alt</kbd> | | |
| **Salir de la App** | <kbd>Esc</kbd> | | |


## Demostración visual: tema claro, comandos, HUD de zoom, opciones y un capibara
  <br>
  <p align="center">
    <img src="../../assets/screenshots/showcase_1.webp" alt="Primera Pantalla" width="70%">
    <img src="../../assets/screenshots/showcase_2.webp" alt="Segunda Pantalla" width="20%">
  </p>


## Desarrollo y Contribución
Próximamente actualizaré la documentación para facilitar la colaboración en el proyecto. Avísame si estás interesado en ayudar.
El proyecto fue construido en Python con las bibliotecas PyQt6 y Pillow. Es posible que pruebe cambiar a PySide6 en breve.
Como lo estoy publicando como software libre (FOSS) y también en la tienda de Windows (Windows Marketplace) en un intento de obtener financiación, los colaboradores deberán firmar un CLA; automatizaré esto pronto.

Prerrequisitos:
```
PyQt6==6.7.1
Pillow==10.4.0
```

## Hoja de Ruta (Roadmap)
Dependiendo del tiempo disponible, el uso de la aplicación y las peticiones de los usuarios.
- Internacionalización
- Redimensionamiento sin pérdida
- Operaciones por lotes

## Licencia
Este proyecto está bajo la Licencia GNU GPL 3. Consulta el archivo [`LICENSE`](../../LICENSE) para más detalles.
<a href="https://github.com/alejandronbachi/lossless-crop/blob/main/LICENSE"> <img src="https://img.shields.io/github/license/alejandronbachi/lossless-crop?color=green" alt="Licencia"></a>


## Apoya mi trabajo

Si encuentras útil este proyecto, ¡puedes apoyar su desarrollo a través de Binance Pay!

**Mi ID de Binance Pay:** `1228818247`

*Escanea el código QR a continuación usando tu aplicación móvil de Binance para donar al instante con 0% de comisiones por gas de red (Compatible con USDT, BTC, ETH y BNB).*

<img src="../../assets/screenshots/binance_qr.jpg" width="220" alt="Código QR de Binance Pay">

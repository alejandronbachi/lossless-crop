
<p align="center">
  <img src="assets/screenshots/banner.png" width="100%" alt="Lossless Crop">
</p>
<p align="center">
<img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python">
<img src="https://img.shields.io/badge/Windows-Supported-blue?logo=windows" alt="WindowsSupport">
<img src="https://img.shields.io/badge/macOS-Supported-lighgrey?logo=apple" alt="macOSSupport">
<img src="https://img.shields.io/badge/Linux-Supported-orange?logo=linux" alt="LinuxSupport">
</p>
<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/Language-English-blue" alt="English"></a>
  <a href="docs/readmes/README.es.md"><img src="https://img.shields.io/badge/Idioma-Español-orange" alt="Español"></a>
  <a href="docs/readmes/README.fr.md"><img src="https://img.shields.io/badge/Language-Français-red" alt="Français"></a>
  <a href="docs/readmes/README.pt.md"><img src="https://img.shields.io/badge/Idioma-Português-green" alt="Português"></a>
</p>

**A cross-platform lossless image cropping application with many features and configuration options.**

## Use case
Useful to quickly crop several images in a directory one after the other.

## Features

- Fast cropping workflow
- Floating configurable zoom preview
- **Lossless** cropping support for *JPEG*, *PNG* and *BMP* image format
- **Lossy** cropping support for *JPEG* and *WebP* format
- Exif data and ICC profiles conservation
- Crop area aspect ratio enforcing, conservation and re-sizing
- Crossplatform: **Windows**, **Linux** and **macOS** compatible
- Dark and Light Themes
- Global keyboard shorcuts
- Manual cropping area input
- Drag and drop support
- Recent directories menu
- Configurable user interface
- Optional settings persistence

## Demo
<p align="center">
  <img src="assets/screenshots/demo.webp" width="850" alt="Demo">
</p>

## Supported Formats
- **JPEG**: Lossless or Lossy cropping modes
- **PNG**: Lossless 
- **BMP**: Lossless
- **WebP**: Lossy

## Installation

### Option 1: Binaries
Download the appropiate binary from the  [Releases Page](https://github.com/alejandronbachi/lossless-crop/releases)

 page:
- **Windows** (`LosslessCrop-Windows.exe`)
- **Linux** (`LosslessCrop-Linux`) and (`LosslessCrop-Linux.AppImage`)
- **macOS** (`LosslessCrop-macOS.tar.gz`)

[![GitHubRelease](https://img.shields.io/github/v/release/alejandronbachi/lossless-crop?color=blue)](https://github.com/alejandronbachi/lossless-crop/releases)

## Quick Start / Usage Guide
1. Open a directory with images 
2. Draw selection over the image
3. Press `space` to crop and move to the next image

## User Manual
Please read the [User Manual](/docs/user_manual.md) for more instructions, specially if you need to know how lossless cropping works, otherwise the selection area snapping could be an unexpected issue.

## Keyboard Global Shorcuts & Mouse Controls

| Keyboard Actions | Keys | Mouse Actions | Control |
| :--- | :--- | :--- | :--- |
| **Crop & Next** | <kbd>Space</kbd> | **Draw Box** | <kbd>Left-Click</kbd> + Drag |
| **Crop** | <kbd>S</kbd> or <kbd>Middle-Click</kbd> | **Move Box** | <kbd>Right-Click</kbd> + Drag |
| **Open Directory** | <kbd>O</kbd> | **Navigate** | <kbd>Scroll Wheel</kbd> |
| **Open Image** | <kbd>I</kbd> | **Crop** | <kbd>Middle-Click</kbd> |
| **Skip Forward** | <kbd>F</kbd> or <kbd>D</kbd> | | |
| **Skip Backward** | <kbd>B</kbd> or <kbd>A</kbd> | | |
| **Rotate Clockwise** | <kbd>R</kbd> | | |
| **Toggle Preview** | <kbd>P</kbd> or <kbd>Q</kbd> | | |
| **Toggle Menu** | <kbd>Alt</kbd> | | |
| **Exit App** | <kbd>Esc</kbd> | | |


## Showcase: light theme, commands, zoom hud, options and a capybara
  <br>
  <p align="center">
    <img src="assets/screenshots/showcase_1.webp" alt="First Screen" width="70%">
    <img src="assets/screenshots/showcase_2.webp" alt="Second Screen" width="20%">
  </p>


## Development & Contributing
I'll be updating the documentation to make it easier to collaborate with the project soon, let me know if you are insterested in helping out.
The project was built with python with PyQt6 and Pillow libraries. I might be testing switching to Pyside6 shortly.
As im releasing as FOSS but also on the windows marketplace in an attempt to get some funding, collaborators will need to sign a cla, i will automate that shortly.

Prerequisites:
```
PyQt6==6.7.1
Pillow==10.4.0
```

## Roadmap
Depending on available time, application usage and user requests.
- Internationalization
- Lossless resize
- Batch operations

## License
This project is licensed under the GNU GPL 3 License - see the [LICENSE](LICENSE) file for details.

##  Support My Work

If you find this project useful, you can support its development via Binance Pay!

**My Binance Pay ID:** `1228818247`

*Scan the QR code below using your Binance Mobile App to donate instantly with 0% network gas fees (Supports USDT, BTC, ETH, and BNB).*

<img src="assets/screenshots/binance_qr.jpg" width="220" alt="Binance Pay QR Code">

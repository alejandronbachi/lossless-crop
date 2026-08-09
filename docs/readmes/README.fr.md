
<p align="center">
  <img src="../../assets/screenshots/banner.png" width="100%" alt="Lossless Crop">
</p>
<p align="center">
<img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python">
<img src="https://img.shields.io/badge/Windows-Supported-blue?logo=windows" alt="WindowsSupport">
<img src="https://img.shields.io/badge/macOS-Supported-lighgrey?logo=apple" alt="macOSSupport">
<img src="https://img.shields.io/badge/Linux-Supported-orange?logo=linux" alt="LinuxSupport">
</p>
<p align="center">
  <a href="../../README.md"><img src="https://img.shields.io/badge/Language-English-blue" alt="English"></a>
</p>

**Une application de recadrage d'images sans perte (lossless) multiplateforme dotée de nombreuses fonctionnalités et options de configuration.**

## Cas d'utilisation
Utile pour recadrer rapidement plusieurs images dans un dossier les unes après les autres.

## Fonctionnalités

- Flux de travail de recadrage rapide
- Aperçu zoom flottant configurable
- Prise en charge du recadrage **sans perte (lossless)** pour les formats d'image *JPEG*, *PNG* et *BMP*
- Prise en charge du recadrage **avec perte (lossy)** pour les formats *JPEG* et *WebP*
- Conservation des métadonnées Exif et des profils ICC
- Application, conservation et redimensionnement du ratio d'aspect (aspect ratio) de la zone de recadrage
- Multiplateforme : compatible **Windows**, **Linux** et **macOS**
- Thèmes sombre et clair
- Raccourcis clavier globaux
- Saisie manuelle de la zone de recadrage
- Prise en charge du glisser-déposer (drag and drop)
- Menu des dossiers récents
- Interface utilisateur configurable
- Persistance optionnelle des paramètres

## Démonstration
<p align="center">
  <img src="../../assets/screenshots/demo.webp" width="850" alt="Démonstration">
</p>

## Formats pris en charge
- **JPEG** : Modes de recadrage sans perte ou avec perte
- **PNG** : Sans perte
- **BMP** : Sans perte
- **WebP** : Avec perte

## Installation

### Option 1 : Binaires
Téléchargez le binaire approprié depuis la [Page des Releases](https://github.com/alejandronbachi/lossless-crop/releases) :
- **Windows** (`LosslessCrop-Windows.exe`)
- **Linux** (`LosslessCrop-Linux`) , (`LosslessCrop-Linux.AppImage`)
- **macOS** (`LosslessCrop-macOS.tar.gz`)

[![GitHubRelease](https://img.shields.io/github/v/release/alejandronbachi/lossless-crop?color=blue)](https://github.com/alejandronbachi/lossless-crop/releases)

## Démarrage rapide / Guide d'utilisation
1. Ouvrez un dossier contenant des images
2. Dessinez une sélection sur l'image
3. Appuyez sur `space` pour recadrer et passer à l'image suivante

## Manuel de l'utilisateur
Veuillez lire le [Manuel de l'utilisateur](/docs/user_manual_fr.md) pour plus d'instructions, en particulier si vous avez besoin de savoir comment fonctionne le recadrage sans perte, sinon le magnétisme (snapping) de la zone de sélection pourrait sembler inattendu.

## Raccourcis clavier globaux et contrôles de la souris

| Actions Clavier | Touches | Actions Souris | Contrôle |
| :--- | :--- | :--- | :--- |
| **Recadrer & Suivant** | <kbd>Space</kbd> | **Dessiner le cadre** | <kbd>Clic gauche</kbd> + Glisser |
| **Recadrer** | <kbd>S</kbd> ou <kbd>Middle-Click</kbd> | **Déplacer le cadre** | <kbd>Clic droit</kbd> + Glisser |
| **Ouvrir un dossier** | <kbd>O</kbd> | **Naviguer** | <kbd>Molette de la souris</kbd> |
| **Ouvrir une image** | <kbd>I</kbd> | **Recadrer** | <kbd>Clic du milieu</kbd> |
| **Avancer** | <kbd>F</kbd> ou <kbd>D</kbd> | | |
| **Reculer** | <kbd>B</kbd> ou <kbd>A</kbd> | | |
| **Pivoter dans le sens horaire** | <kbd>R</kbd> | | |
| **Basculer l'aperçu** | <kbd>P</kbd> ou <kbd>Q</kbd> | | |
| **Basculer le menu** | <kbd>Alt</kbd> | | |
| **Quitter l'application** | <kbd>Esc</kbd> | | |


## Vitrine : thème clair, commandes, HUD de zoom, options et un capybara
  <br>
  <p align="center">
    <img src="../../assets/screenshots/showcase_1.webp" alt="Premier écran" width="70%">
    <img src="../../assets/screenshots/showcase_2.webp" alt="Deuxième écran" width="20%">
  </p>


## Développement et Contribution
Je mettrai bientôt à jour la documentation pour faciliter la collaboration sur le projet, faites-moi savoir si vous souhaitez aider.
Le projet a été développé en Python avec les bibliothèques PyQt6 et Pillow. Je pourrais tester le passage à PySide6 prochainement.
Étant donné que le projet est publié en open source (FOSS) et également sur le Windows Marketplace pour tenter d'obtenir un financement, les contributeurs devront signer un CLA (accord de licence contributeur), que j'automatiserai bientôt.

Prérequis :
```
PyQt6==6.7.1
Pillow==10.4.0
```

## Feuille de route (Roadmap)
Selon le temps disponible, l'utilisation de l'application et les demandes des utilisateurs.
- Internationalisation
- Redimensionnement sans perte
- Opérations par lots

## Licence
Ce projet est sous licence GNU GPL 3 - voir le fichier [`LICENSE`](../../LICENSE) pour plus de détails.
<a href="https://github.com/alejandronbachi/lossless-crop/blob/main/LICENSE"> <img src="https://img.shields.io/github/license/alejandronbachi/lossless-crop?color=green" alt="Licence"></a>


## Soutenir mon travail

Si vous trouvez ce projet utile, vous pouvez soutenir son développement via Binance Pay !

**Mon ID Binance Pay :** `1228818247`

*Scannez le code QR ci-dessous à l'aide de votre application mobile Binance pour faire un don instantané avec 0 % de frais de réseau (prend en charge USDT, BTC, ETH et BNB).*

<img src="../../assets/screenshots/binance_qr.jpg" width="220" alt="Code QR Binance Pay">

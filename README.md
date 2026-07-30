# Lossless Crop

A PyQt6-based lossless image cropping and management application supporting Windows, Linux, and macOS.

## Building Executables Locally

To build standalone executables locally using PyInstaller:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt pyinstaller
   ```
2. Run PyInstaller with the spec file:
   ```bash
   pyinstaller lossless_crop.spec
   ```
   The output executable will be available in the `dist/LosslessCrop` directory.

## CI/CD Pipeline & GitHub Actions

The repository includes a GitHub Actions workflow at [`.github/workflows/build.yml`](.github/workflows/build.yml:1) which automatically builds executables for:
- **Windows** (`LosslessCrop-Windows.zip`)
- **Linux** (`LosslessCrop-Linux.tar.gz`)
- **macOS** (`LosslessCrop-macOS.tar.gz`)

## Key Architecture & Packaging Details

- **Resource Paths & PyInstaller**: [`config/app_constants.py`](config/app_constants.py:1) checks `sys.frozen` and `sys._MEIPASS` to ensure assets (`styles/`, `templates/`, `config/`, `icon.png`) and platform-specific `jpegtran` binaries (`binaries/`) are correctly resolved at runtime.
- **Lossless Binaries**: [`managers/image_manager.py`](managers/image_manager.py:14) dynamically locates `jpegtran.exe` (Windows), `jpegtran_linux` (Linux), or `jpegtran_mac` (macOS).

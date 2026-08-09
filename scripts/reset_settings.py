from PyQt6.QtCore import QSettings

# Alternative: Manual Deletion via PowerShell
#
# Remove-Item -Path "HKCU:\Software\LossLessCropTeam\LossLessCrop" -Recurse -Force
#


def wipe_all_application_settings():
    """Locates and permanently deletes the QSettings database for Lossless Crop."""
    # 1. Initialize QSettings matching your production configuration credentials exactly
    settings = QSettings("LossLessCropTeam", "LossLessCrop")

    # 2. Extract the physical disk/registry file path location for logging visibility
    storage_path = settings.fileName()
    print(f"Target storage location identified at: {storage_path}")

    # 3. Purge all internal keys, values, and organizational groups natively
    settings.clear()

    # 4. Force a hardware sync to flush the deletion immediately to disk channels
    settings.sync()
    print(
        "Successfully flushed and wiped all persistent application configuration states!"
    )


if __name__ == "__main__":
    wipe_all_application_settings()

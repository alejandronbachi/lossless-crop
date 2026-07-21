# Refactoring Plan for FastCrop

## Goals
- Decouple GUI logic from image processing and I/O.
- Improve maintainability and readability.
- Facilitate easier feature addition (e.g., new engine support, better UI controls).

## Proposed Architecture

1. **`ImageProcessor` class**: Handles all Pillow/jpegtran operations, file I/O, and cropping logic.
2. **`SettingsManager` class**: Manages application settings, persistence, and state.
3. **`FastCropApp` class (GUI)**: Handles only layout, user interaction, and event routing.
4. **`FloatingZoomPreview` class**: Already present; can be slightly refined to use the new `ImageProcessor`.

## Refactoring Steps

### 1. Extract Image Processing Logic
- Create `ImageProcessor` in a new file or as a separate class.
- Move Pillow-related operations (open, crop, rotate, save) from `FastCropApp` to `ImageProcessor`.
- Move binary (jpegtran) management to `ImageProcessor`.

### 2. Extract Settings Management
- Create `SettingsManager`.
- Consolidate all `QSettings` read/write calls from `FastCropApp` to this class.

### 3. Refine `FastCropApp`
- Remove all low-level image processing calls from `FastCropApp`.
- `FastCropApp` should hold an instance of `ImageProcessor` and `SettingsManager`.

## New Class Definitions

### `ImageProcessor`
- `__init__(self, settings)`: Initialize processing engine.
- `load_image(self, path)`: Load image into memory.
- `execute_crop(self, rect, engine, overwrite)`: Perform crop and save.
- `rotate_image(self, angle)`: Rotate image.

### `SettingsManager`
- `__init__(self, app_name)`: Initialize settings.
- `get(key, default)`: Retrieve setting.
- `set(key, value)`: Store setting.
- `persist_all_states()`: Save all application states.

## Next Steps
- Implement `SettingsManager` and test integration.
- Migrate processing logic to `ImageProcessor`.
- Cleanup `FastCropApp`.

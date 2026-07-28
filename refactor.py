# refactor.py

# =================================================================
# 1. ADD THIS IMPORT TO THE TOP OF LossLessCropApp.py
# =================================================================

# =================================================================
# 2. INITIALIZE IN LossLessCropApp.__init__ (LossLessCropApp.py)
# =================================================================
# Inside the __init__ method of LossLessCropApp, add:
# self.processor = ImageProcessor()

# =================================================================
# 3. REPLACE PILLOW/JPEGTRAN CALLS
# =================================================================

# Example 1: Loading an image
# Old: self.current_pil_image = Image.open(file_path)
# New: self.current_pil_image = self.processor.load_image(file_path)

# Example 2: Checking lossless
# Old: if self.combo_engine.currentText() == "Lossless" and ... (manual checks)
# New: if self.processor.is_lossless_supported(file_path):

# Example 3: Executing a crop
# Replace the entire block in `process_and_execute_crop` (approx line 1283) with:
# self.processor.execute_crop(
#     current_filepath,
#     output_filepath,
#     (crop_left, crop_top, crop_right, crop_bottom),
#     use_lossless
# )

# Example 4: Rotating
# Old: self.current_pil_image = self.current_pil_image.rotate(-90, expand=True)
# New: self.current_pil_image = self.processor.rotate_image(self.current_pil_image, -90)

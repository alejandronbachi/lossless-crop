# EXIF preservation implementation
#### pillow
def save_cropped_image(
    self, cropped_image, original_img, output_path, format_type="JPEG", quality=95
):
    """Saves a cropped image while safely transferring applicable format metadata."""
    fmt = format_type.upper()
    save_kwargs = {}

    # 1. Handle compression/quality properties based on format
    if fmt in ["JPEG", "MPO", "WEBP"]:
        save_kwargs["quality"] = quality

    try:
        # 2. Safely extract available source metadata profiles
        exif_data = original_img.info.get("exif")
        icc_profile = original_img.info.get("icc_profile")

        # 3. Dynamically map parameters to corresponding formats
        if fmt in ["JPEG", "MPO", "WEBP", "TIFF"]:
            if exif_data:
                save_kwargs["exif"] = exif_data
            if icc_profile:
                save_kwargs["icc_profile"] = icc_profile

        elif fmt == "PNG":
            if exif_data:
                save_kwargs["exif"] = exif_data
            if icc_profile:
                save_kwargs["icc_profile"] = icc_profile

        # Note: BMP skips this entire block as it doesn't support metadata fields

        # 4. Save the finalized crop payload cleanly
        cropped_image.save(output_path, format=fmt, **save_kwargs)
        logger.info("[EXPORT] Successfully saved %s to %s", fmt, output_path)

    except Exception as e:
        print(f"[EXPORT WARNING] Metadata injection failed for {fmt}: {e}")
        # Fallback path: Drop metadata injections and write the plain image matrix
        try:
            fallback_kwargs = (
                {"quality": quality} if fmt in ["JPEG", "MPO", "WEBP"] else {}
            )
            cropped_image.save(output_path, format=fmt, **fallback_kwargs)
        except Exception as critical_err:
            print(f"[CRITICAL FAIL] Total asset export write block: {critical_err}")


# example call
self.save_cropped_image(crop, src, "output.png", format_type="PNG")
self.save_cropped_image(crop, src, "output.jpg")


# another method signature
def save_cropped_image(
    self, cropped_image, original_img, output_path, format_type, quality
):

    # preserving quality with keep
    def save_cropped_image(
        self, cropped_image, original_img, output_path, format_type="JPEG", quality=95
    ):
        """Saves a cropped image while safely transferring all metadata, supporting lossless configurations."""
        fmt = format_type.upper()
        save_kwargs = {}

        # 1. 🌟 Handle Lossless JPEG Quality Rules
        if fmt in ["JPEG", "MPO"]:
            if quality == "keep":
                save_kwargs["quality"] = "keep"
                save_kwargs["subsampling"] = "keep"
                save_kwargs["qtables"] = "keep"
            else:
                save_kwargs["quality"] = quality
        elif fmt == "WEBP":
            save_kwargs["quality"] = quality

        try:
            # 2. Extract the source metadata chunks
            exif_data = original_img.info.get("exif")
            icc_profile = original_img.info.get("icc_profile")

            # 3. Inject EXIF / Color data blocks to protect them from being deleted
            if fmt in ["JPEG", "MPO", "WEBP", "TIFF", "PNG"]:
                if exif_data:
                    save_kwargs["exif"] = exif_data
                if icc_profile:
                    save_kwargs["icc_profile"] = icc_profile

            # 4. Save the file cleanly
            cropped_image.save(output_path, format=fmt, **save_kwargs)
            print(f"[EXPORT] Successfully saved {fmt} to {output_path}")

        except Exception as e:
            print(f"[EXPORT WARNING] Metadata injection failed for {fmt}: {e}")
            try:
                # Fallback to normal compression array if custom options break
                fallback_kwargs = (
                    {"quality": 95} if fmt in ["JPEG", "MPO", "WEBP"] else {}
                )
                cropped_image.save(output_path, format=fmt, **fallback_kwargs)
            except Exception as critical_err:
                print(f"[CRITICAL FAIL] Total asset export write block: {critical_err}")


# example method call
self.save_cropped_image(
    cropped_image=self.cached_crop_slice,
    original_img=self.loaded_pil_image,
    output_path="lossless_photo.jpg",
    format_type="JPEG",
    quality="keep",  # 🌟 Triggers the lossless compression parameters
)
##########
####jpegtran
#change commands to include flags "-copy", "all"
            binary_path = os.path.join(current_dir, "binaries", bin_name)

            crop_argument = f"{crop_width}x{crop_height}+{crop_left}+{crop_top}"
            command = [
                binary_path,
                "-crop",
                crop_argument,
                "-copy", "all",  # 🌟 FIX: Preserves all EXIF data and ICC profiles
                "-optimize",     # 💡 OPTIONAL: Optimizes Huffman tables for a smaller file size
                "-outfile",
                output_filepath,
                current_filepath,
            ]
# the optimize flag
#The Optimization Bonus: Adding "-optimize" instructs jpegtran to compress the final file structures slightly tighter without altering a single pixel value
#may confuse the user if they see smaller picture size give an option for it.
#EXIF Data Survival: Camera tags, creation timestamps, and orientation values will copy over to the cropped file cleanly.True Colors: Any custom embedded ICC color profile is carried over, meaning your cropped image won't look washed out or color-shifted when viewed in image viewers.

import subprocess

def save_lossless_rotate_and_crop(image_path, output_path, angle, crop_x, crop_y, crop_w, crop_h):
    """
    Applies rotation and cropping losslessly via jpegtran.
    Coordinates must be based on the VISUAL ROTATED image layout.
    """
    # 1. Enforce the 8x8 block alignment rule for a perfect lossless cut
    # This snaps the X and Y coordinates down to the nearest multiple of 8
    lossless_x = (crop_x // 8) * 8
    lossless_y = (crop_y // 8) * 8
    
    # 2. Translate your UI angle to jpegtran format (90, 180, 270)
    jpegtran_angle = str(angle % 360)
    
    # 3. Construct the geometry string: WidthxHeight+X+Y
    crop_geometry = f"{crop_w}x{crop_h}+{lossless_x}+{lossless_y}"
    
    # 4. Execute single optimized command (Internal Order: Rotate then Crop)
    cmd = [
        "jpegtran",
        "-rotate", jpegtran_angle,
        "-crop", crop_geometry,
        "-copy", "all",
        image_path,
        output_path
    ]
    
    subprocess.run(cmd)

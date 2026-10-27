import os
import uuid
import logging

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageChops, ImageEnhance, ImageStat
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False
    logger.warning("Pillow is not installed. Error-Level Analysis (ELA) will be disabled.")

ELA_WARNING = "ELA is a heuristic indicator only; anomaly does not confirm tampering."


def run_ela(image_path: str, output_dir: str, quality: int = 90) -> dict:
    """
    Perform Error-Level Analysis (ELA) on an image:
    1. Resave the image at specified JPEG quality (default 90).
    2. Compute the pixel difference between original and recompressed image.
    3. Scale up difference 10x to amplify compression artifacts.
    4. Save the difference image to output_dir.
    5. Compute mean error; if > threshold (15.0), flag as an anomaly.

    Returns:
        dict: {
            "ela_image_path": str,
            "mean_error": float,
            "anomaly_detected": bool,
            "warning": str
        }
    """
    if not HAVE_PIL:
        return {
            "ela_image_path": "",
            "mean_error": 0.0,
            "anomaly_detected": False,
            "warning": ELA_WARNING,
            "error": "PIL/Pillow is not available in environment"
        }

    if not os.path.exists(image_path):
        return {
            "ela_image_path": "",
            "mean_error": 0.0,
            "anomaly_detected": False,
            "warning": ELA_WARNING,
            "error": f"Image file not found: {image_path}"
        }

    try:
        os.makedirs(output_dir, exist_ok=True)
        unique_id = uuid.uuid4().hex[:10]
        temp_recompressed_path = os.path.join(output_dir, f"_temp_ela_{unique_id}.jpg")
        output_ela_path = os.path.join(output_dir, f"ela_{unique_id}.jpg")

        # 1. Open original and resave at target quality
        with Image.open(image_path) as orig_img:
            # Convert to RGB to ensure uniform channels
            rgb_orig = orig_img.convert("RGB")
            rgb_orig.save(temp_recompressed_path, "JPEG", quality=quality)

        # 2. Re-open recompressed and compute difference
        with Image.open(temp_recompressed_path) as recomp_img:
            diff = ImageChops.difference(rgb_orig, recomp_img)

        # 3. Clean up temp recompressed file
        if os.path.exists(temp_recompressed_path):
            os.remove(temp_recompressed_path)

        # 4. Compute statistics on difference
        stat = ImageStat.Stat(diff)
        # Average channel mean error
        mean_error = sum(stat.mean) / len(stat.mean) if stat.mean else 0.0

        # 5. Amplify difference by 10x for visual clarity
        enhancer = ImageEnhance.Brightness(diff)
        amplified = enhancer.enhance(10.0)
        amplified.save(output_ela_path, "JPEG", quality=95)

        anomaly_detected = bool(mean_error > 15.0)

        return {
            "ela_image_path": output_ela_path,
            "mean_error": round(float(mean_error), 2),
            "anomaly_detected": anomaly_detected,
            "warning": ELA_WARNING
        }
    except Exception as e:
        logger.error(f"Failed to execute ELA on {image_path}: {e}")
        return {
            "ela_image_path": "",
            "mean_error": 0.0,
            "anomaly_detected": False,
            "warning": ELA_WARNING,
            "error": str(e)
        }

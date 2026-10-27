import os
import io
import logging

logger = logging.getLogger(__name__)

# Check for PyMuPDF (fitz) with dual-import fallback
try:
    import pymupdf as fitz  # PyMuPDF modern import
    HAVE_FITZ = True
except ImportError:
    try:
        import fitz  # PyMuPDF classic import
        HAVE_FITZ = True
    except ImportError:
        HAVE_FITZ = False
        logger.warning("PyMuPDF (fitz) is not installed. PDF text extraction will be limited.")

# Check for PIL / Pillow
try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False
    logger.warning("Pillow is not installed. Image processing will be limited.")

# Check for pytesseract and local executable discovery
try:
    import pytesseract
    HAVE_TESSERACT = True
    # Allow custom path via env var
    tess_cmd = os.getenv("TESSERACT_CMD")
    if tess_cmd:
        pytesseract.pytesseract.tesseract_cmd = tess_cmd
    else:
        # Autodiscover standard Windows install paths if present
        for candidate in [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]:
            if os.path.exists(candidate):
                pytesseract.pytesseract.tesseract_cmd = candidate
                break
except ImportError:
    HAVE_TESSERACT = False
    logger.warning("pytesseract is not installed. OCR will not be available.")


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Extract text from a PDF file page by page using PyMuPDF.
    If a page's extracted text is empty or very sparse (< 50 chars),
    attempt fallback to pytesseract OCR on rendered page image.
    Returns: list of dicts: [{"page": 1, "text": "...", "method": "pdf_native|tesseract"}]
    """
    results: list[dict] = []
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return results

    if not HAVE_FITZ:
        return [{"page": 1, "text": "[Warning: PyMuPDF not available]", "method": "error"}]

    try:
        doc = fitz.open(file_path)
        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page = doc.load_page(page_idx)
            page_text = page.get_text("text") or ""
            method = "pdf_native"

            # Fallback to OCR if native text is too short and pytesseract & PIL are available
            if len(page_text.strip()) < 50 and HAVE_PIL and HAVE_TESSERACT:
                try:
                    pix = page.get_pixmap(dpi=150)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = pytesseract.image_to_string(img, config="--oem 3 --psm 3")
                    if len(ocr_text.strip()) > len(page_text.strip()):
                        page_text = ocr_text
                        method = "tesseract"
                except Exception as ocr_err:
                    logger.warning(f"OCR fallback failed on page {page_num} of {file_path}: {ocr_err}")

            results.append({
                "page": page_num,
                "text": page_text.strip(),
                "method": method
            })
        doc.close()
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        results.append({
            "page": 1,
            "text": f"[Error reading PDF: {str(e)}]",
            "method": "error"
        })

    return results


def extract_text_from_image(file_path: str) -> list[dict]:
    """
    Extract text from an image using pytesseract.
    Returns: list of dicts: [{"page": 1, "text": "...", "method": "tesseract"}]
    """
    if not os.path.exists(file_path):
        return []

    if not HAVE_PIL or not HAVE_TESSERACT:
        warning_msg = "[pytesseract/Pillow not installed - image OCR skipped]"
        return [{"page": 1, "text": warning_msg, "method": "skipped"}]

    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img, config="--oem 3 --psm 3")
        return [{
            "page": 1,
            "text": text.strip(),
            "method": "tesseract"
        }]
    except Exception as e:
        logger.warning(f"Tesseract OCR failed on image {file_path}: {e}")
        return [{
            "page": 1,
            "text": f"[OCR execution note: {str(e)}]",
            "method": "tesseract_failed"
        }]


def extract_text(file_path: str, mime_type: str = "") -> list[dict]:
    """
    Route to the appropriate text extraction function based on MIME type or file extension.
    """
    lower_path = file_path.lower()
    lower_mime = mime_type.lower() if mime_type else ""

    if "pdf" in lower_mime or lower_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif any(img_type in lower_mime for img_type in ["image", "jpeg", "jpg", "png", "tiff", "bmp"]) or \
            any(lower_path.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]):
        return extract_text_from_image(file_path)
    else:
        # Default fallback: try PDF first, then image
        try:
            return extract_text_from_pdf(file_path)
        except Exception:
            return extract_text_from_image(file_path)


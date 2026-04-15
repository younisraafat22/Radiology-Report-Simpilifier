import os
from io import BytesIO

from PIL import Image
import pytesseract


class VLMServiceError(RuntimeError):
    pass


def extract_text_from_image(
    image_bytes: bytes,
    _content_type: str,
) -> tuple[str, str]:
    ocr_lang = os.getenv("OCR_LANG", "eng").strip() or "eng"

    if not image_bytes:
        raise VLMServiceError("Image payload is empty.")

    try:
        image = Image.open(BytesIO(image_bytes))
    except Exception as exc:  # noqa: BLE001
        raise VLMServiceError("Failed to decode image data.") from exc

    if image.mode != "RGB":
        image = image.convert("RGB")

    text = pytesseract.image_to_string(image, lang=ocr_lang).strip()
    if not text:
        raise VLMServiceError("OCR returned empty text. Try a clearer image.")

    return text, f"tesseract:{ocr_lang}"

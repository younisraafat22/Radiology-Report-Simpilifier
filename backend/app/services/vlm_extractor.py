import os
from io import BytesIO

from PIL import Image
import pytesseract
from pytesseract import TesseractError


class VLMServiceError(RuntimeError):
    pass


def extract_text_from_image(
    image_bytes: bytes,
    _content_type: str,
) -> tuple[str, str]:
    ocr_lang = os.getenv("OCR_LANG", "eng").strip() or "eng"
    max_side = int(os.getenv("OCR_MAX_SIDE", "2200"))

    if not image_bytes:
        raise VLMServiceError("Image payload is empty.")

    try:
        image = Image.open(BytesIO(image_bytes))
    except Exception as exc:  # noqa: BLE001
        raise VLMServiceError("Failed to decode image data.") from exc

    if image.mode != "RGB":
        image = image.convert("RGB")

    image = _resize_if_large(image, max_side=max_side)
    image = _normalize_to_png(image)

    try:
        text = pytesseract.image_to_string(image, lang=ocr_lang).strip()
    except (TesseractError, TypeError, OSError) as exc:
        raise VLMServiceError("OCR failed to process this image format. Try PNG/JPG screenshot.") from exc

    if not text:
        raise VLMServiceError("OCR returned empty text. Try a clearer image.")

    return text, f"tesseract:{ocr_lang}"


def _resize_if_large(image: Image.Image, max_side: int) -> Image.Image:
    if max_side <= 0:
        return image

    width, height = image.size
    longest = max(width, height)
    if longest <= max_side:
        return image

    scale = max_side / float(longest)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def _normalize_to_png(image: Image.Image) -> Image.Image:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    normalized = Image.open(buffer)
    normalized.load()
    return normalized

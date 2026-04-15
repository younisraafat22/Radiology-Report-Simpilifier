import os
from urllib.parse import quote

import httpx


class VLMServiceError(RuntimeError):
    pass


def extract_text_from_image(
    image_bytes: bytes,
    content_type: str,
) -> tuple[str, str]:
    token = os.getenv("HF_API_TOKEN", "").strip()
    model_id = os.getenv("HF_IMAGE_TO_TEXT_MODEL_ID", "microsoft/trocr-base-printed").strip()

    if not token:
        raise VLMServiceError("HF_API_TOKEN is required for image text extraction.")

    if not image_bytes:
        raise VLMServiceError("Image payload is empty.")

    if not model_id:
        raise VLMServiceError("HF_IMAGE_TO_TEXT_MODEL_ID is required.")

    model_path = quote(model_id, safe="")
    url = f"https://api-inference.huggingface.co/models/{model_path}"
    with httpx.Client(timeout=75.0) as client:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
        }
        response = client.post(url, headers=headers, content=image_bytes)

    if response.status_code >= 400:
        raise VLMServiceError(
            f"Image-to-text request failed ({model_id}) with status {response.status_code}: {response.text[:300]}"
        )

    parsed = response.json()
    text = _extract_text_from_inference_payload(parsed)
    if not text:
        raise VLMServiceError(f"Image-to-text model returned empty text ({model_id}).")

    return text, f"huggingface-image-to-text:{model_id}"


def _extract_text_from_inference_payload(payload: object) -> str:
    if isinstance(payload, list):
        parts = []
        for item in payload:
            if isinstance(item, dict):
                text = str(item.get("generated_text", "")).strip()
                if text:
                    parts.append(text)
        return "\n".join(parts).strip()

    if isinstance(payload, dict):
        generated = str(payload.get("generated_text", "")).strip()
        if generated:
            return generated

    return ""

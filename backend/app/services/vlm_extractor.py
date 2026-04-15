import base64
import json
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

    if not token:
        raise VLMServiceError("HF_API_TOKEN is required for VLM extraction.")

    if not image_bytes:
        raise VLMServiceError("Image payload is empty.")

    with httpx.Client(timeout=75.0) as client:
        router_result, router_error = _try_router_vlm(client, token, image_bytes, content_type)
        if router_result:
            return router_result

        ocr_result, ocr_error = _try_hf_image_to_text(client, token, image_bytes, content_type)
        if ocr_result:
            return ocr_result

    combined = "; ".join(part for part in [router_error, ocr_error] if part)
    if not combined:
        combined = "No extraction backend returned a valid response."
    raise VLMServiceError(combined)


def _try_router_vlm(
    client: httpx.Client,
    token: str,
    image_bytes: bytes,
    content_type: str,
) -> tuple[tuple[str, str] | None, str]:
    model_candidates = _get_model_candidates()
    max_tokens = int(os.getenv("HF_VLM_MAX_TOKENS", "900"))
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{content_type};base64,{image_b64}"

    prompt = (
        "Extract all visible text from this medical report image. "
        "Return plain text only. Preserve line breaks where possible. "
        "Do not add, infer, or correct medical facts."
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    url = "https://router.huggingface.co/v1/chat/completions"

    last_error = "Router VLM request failed."
    for model_id in model_candidates:
        payload = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            "temperature": 0.0,
            "max_tokens": max_tokens,
        }

        response = client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            if _is_router_model_unavailable(response):
                last_error = (
                    f"Router model unavailable/restricted for {model_id}. "
                    "Trying next backend."
                )
                continue
            raise VLMServiceError(f"VLM router returned {response.status_code}: {response.text[:400]}")

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise VLMServiceError("VLM response missing choices.")

        content = choices[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            text = "\n".join(
                str(item.get("text", "")).strip()
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            ).strip()
        else:
            text = str(content).strip()

        if not text:
            raise VLMServiceError("VLM returned empty extracted text.")

        return (text, f"huggingface-vlm:{model_id}"), ""

    return None, last_error


def _try_hf_image_to_text(
    client: httpx.Client,
    token: str,
    image_bytes: bytes,
    content_type: str,
) -> tuple[tuple[str, str] | None, str]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": content_type,
    }

    last_error = "HF image-to-text request failed."
    for model_id in _get_image_to_text_candidates():
        model_path = quote(model_id, safe="")
        url = f"https://api-inference.huggingface.co/models/{model_path}"
        response = client.post(url, headers=headers, content=image_bytes)

        if response.status_code >= 400:
            last_error = f"Image-to-text model failed ({model_id}): {response.status_code}"
            continue

        parsed = response.json()
        text = _extract_text_from_inference_payload(parsed)
        if not text:
            last_error = f"Image-to-text model returned empty text ({model_id})."
            continue

        return (text, f"huggingface-image-to-text:{model_id}"), ""

    return None, last_error


def _get_model_candidates() -> list[str]:
    configured = os.getenv("HF_VLM_MODEL_ID", "").strip()
    candidates = []
    if configured:
        candidates.append(configured)

    # Ordered by likely availability/cost profile for shared providers.
    defaults = [
        "meta-llama/Llama-3.2-11B-Vision-Instruct",
        "google/gemma-3-12b-it",
        "Qwen/Qwen2.5-VL-7B-Instruct",
    ]

    for model in defaults:
        if model not in candidates:
            candidates.append(model)

    return candidates


def _get_image_to_text_candidates() -> list[str]:
    configured = os.getenv("HF_IMAGE_TO_TEXT_MODEL_ID", "").strip()
    candidates = []
    if configured:
        candidates.append(configured)

    defaults = [
        "microsoft/trocr-base-printed",
        "microsoft/trocr-large-printed",
    ]

    for model in defaults:
        if model not in candidates:
            candidates.append(model)

    return candidates


def _is_router_model_unavailable(response: httpx.Response) -> bool:
    if response.status_code != 400:
        return False

    try:
        payload = response.json()
    except json.JSONDecodeError:
        return False

    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    code = str(error.get("code", "")).strip()
    message = str(error.get("message", "")).lower()
    return (
        code in {"model_not_supported", "40301"}
        or "not supported by any provider" in message
        or "only " in message and " allowed now" in message
    )


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

import base64
import json
import os

import httpx


class VLMServiceError(RuntimeError):
    pass


def extract_text_from_image(
    image_bytes: bytes,
    content_type: str,
) -> tuple[str, str]:
    token = os.getenv("HF_API_TOKEN", "").strip()
    model_candidates = _get_model_candidates()
    max_tokens = int(os.getenv("HF_VLM_MAX_TOKENS", "900"))

    if not token:
        raise VLMServiceError("HF_API_TOKEN is required for VLM extraction.")

    if not image_bytes:
        raise VLMServiceError("Image payload is empty.")

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

    last_error = "VLM request failed."
    with httpx.Client(timeout=75.0) as client:
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
                if _is_model_not_supported(response):
                    last_error = (
                        f"Model not supported by enabled providers: {model_id}. "
                        "Trying fallback model."
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

            return text, f"huggingface-vlm:{model_id}"

    raise VLMServiceError(last_error)


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


def _is_model_not_supported(response: httpx.Response) -> bool:
    if response.status_code != 400:
        return False

    try:
        payload = response.json()
    except json.JSONDecodeError:
        return False

    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    code = str(error.get("code", "")).strip()
    message = str(error.get("message", "")).lower()
    return code == "model_not_supported" or "not supported by any provider" in message

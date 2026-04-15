import base64
import os

import httpx


class VLMServiceError(RuntimeError):
    pass


def extract_text_from_image(
    image_bytes: bytes,
    content_type: str,
) -> tuple[str, str]:
    token = os.getenv("HF_API_TOKEN", "").strip()
    model_id = os.getenv("HF_VLM_MODEL_ID", "Qwen/Qwen2.5-VL-3B-Instruct")
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

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = "https://router.huggingface.co/v1/chat/completions"

    with httpx.Client(timeout=75.0) as client:
        response = client.post(url, headers=headers, json=payload)

    if response.status_code >= 400:
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

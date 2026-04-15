import json
import os
import re

from huggingface_hub import InferenceClient


def simplify_report(report_text: str) -> tuple[str, list[str], dict[str, str], float, str]:
    """Generate patient-friendly simplification with model-first, fallback-safe behavior."""
    use_hf = os.getenv("USE_HF_INFERENCE", "false").lower() == "true"

    if not use_hf:
        text, points, glossary, confidence = _deterministic_simplify(report_text)
        return text, points, glossary, confidence, "deterministic-fallback"

    token = os.getenv("HF_API_TOKEN", "").strip()
    model_id = os.getenv("HF_MODEL_ID", "google/flan-t5-large")
    max_new_tokens = int(os.getenv("HF_MAX_NEW_TOKENS", "400"))
    temperature = float(os.getenv("HF_TEMPERATURE", "0.2"))

    if not token:
        text, points, glossary, confidence = _deterministic_simplify(report_text)
        return text, points, glossary, confidence, "deterministic-fallback"

    try:
        client = InferenceClient(model=model_id, token=token)
        prompt = _build_prompt(report_text)

        generated = client.text_generation(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            return_full_text=False,
        )

        text, points, glossary, confidence = _parse_model_output(generated, report_text)
        return text, points, glossary, confidence, f"huggingface:{model_id}"
    except Exception:
        # Always keep endpoint resilient, even if model/API fails.
        text, points, glossary, confidence = _deterministic_simplify(report_text)
        return text, points, glossary, confidence, "deterministic-fallback"


def _build_prompt(report_text: str) -> str:
    return (
        "You are a medical language simplification assistant. "
        "Convert the radiology report into patient-friendly language without adding findings. "
        "Preserve uncertainty words like 'possible' or 'cannot exclude'. "
        "Return only valid JSON with this schema: "
        "{\"simplified_report\": string, \"summary_bullet_points\": [string], "
        "\"defined_terms\": {string: string}, \"confidence_score\": number}. "
        "Confidence score must be between 0 and 1.\n\n"
        f"Radiology report:\n{report_text}\n"
    )


def _parse_model_output(
    model_text: str,
    source_report: str,
) -> tuple[str, list[str], dict[str, str], float]:
    json_blob = _extract_first_json_object(model_text)

    if not json_blob:
        return _deterministic_simplify(source_report)

    try:
        payload = json.loads(json_blob)
    except json.JSONDecodeError:
        return _deterministic_simplify(source_report)

    simplified_report = str(payload.get("simplified_report", "")).strip()
    bullet_points = payload.get("summary_bullet_points", [])
    defined_terms = payload.get("defined_terms", {})
    confidence_score = payload.get("confidence_score", 0.68)

    if not simplified_report:
        return _deterministic_simplify(source_report)

    if not isinstance(bullet_points, list):
        bullet_points = []
    bullet_points = [str(item).strip() for item in bullet_points if str(item).strip()]

    if not isinstance(defined_terms, dict):
        defined_terms = {}
    defined_terms = {
        str(term).strip(): str(definition).strip()
        for term, definition in defined_terms.items()
        if str(term).strip() and str(definition).strip()
    }

    try:
        confidence = float(confidence_score)
    except (TypeError, ValueError):
        confidence = 0.68

    confidence = max(0.0, min(1.0, confidence))

    if not bullet_points:
        bullet_points = _derive_bullet_points(simplified_report)

    if not defined_terms:
        defined_terms = _default_glossary()

    return simplified_report, bullet_points[:5], defined_terms, confidence


def _extract_first_json_object(text: str) -> str | None:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    return match.group(0) if match else None


def _derive_bullet_points(text: str) -> list[str]:
    chunks = [chunk.strip() for chunk in re.split(r"[.!?]", text) if chunk.strip()]
    points = [f"{chunk}." for chunk in chunks[:3]]
    return points or ["No key points were produced."]


def _default_glossary() -> dict[str, str]:
    return {
        "pleural effusion": "Fluid collected around the lungs.",
        "cardiomegaly": "The heart appears larger than normal.",
        "atelectasis": "Part of the lung is not fully expanded.",
    }


def _deterministic_simplify(report_text: str) -> tuple[str, list[str], dict[str, str], float]:
    sentences = [s.strip() for s in report_text.split(".") if s.strip()]
    first_two = sentences[:2] if sentences else ["No clear findings were provided."]

    simplified_report = " ".join(first_two)
    bullet_points = [f"{line}." for line in first_two[:3]]

    return simplified_report, bullet_points, _default_glossary(), 0.72

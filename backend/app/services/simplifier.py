import json
import os
import re

from huggingface_hub import InferenceClient


class LLMServiceError(RuntimeError):
    pass


def simplify_report(report_text: str) -> tuple[str, list[str], dict[str, str], float, str]:
    """Generate patient-friendly simplification using an LLM only."""

    token = os.getenv("HF_API_TOKEN", "").strip()
    model_id = os.getenv("HF_MODEL_ID", "google/flan-t5-large")
    max_new_tokens = int(os.getenv("HF_MAX_NEW_TOKENS", "400"))
    temperature = float(os.getenv("HF_TEMPERATURE", "0.2"))

    if not token:
        raise LLMServiceError("HF_API_TOKEN is required for LLM inference.")

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
    except LLMServiceError:
        raise
    except Exception as exc:
        raise LLMServiceError("LLM inference request failed.") from exc


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
        raise LLMServiceError("Model did not return valid JSON.")

    try:
        payload = json.loads(json_blob)
    except json.JSONDecodeError:
        raise LLMServiceError("Model returned invalid JSON format.")

    simplified_report = str(payload.get("simplified_report", "")).strip()
    bullet_points = payload.get("summary_bullet_points", [])
    defined_terms = payload.get("defined_terms", {})
    confidence_score = payload.get("confidence_score", 0.68)

    if not simplified_report:
        raise LLMServiceError("Model output missing simplified_report.")

    if not isinstance(bullet_points, list):
        raise LLMServiceError("Model output summary_bullet_points must be a list.")
    bullet_points = [str(item).strip() for item in bullet_points if str(item).strip()]

    if not isinstance(defined_terms, dict):
        raise LLMServiceError("Model output defined_terms must be an object.")
    defined_terms = {
        str(term).strip(): str(definition).strip()
        for term, definition in defined_terms.items()
        if str(term).strip() and str(definition).strip()
    }

    try:
        confidence = float(confidence_score)
    except (TypeError, ValueError):
        raise LLMServiceError("Model output confidence_score must be numeric.")

    confidence = max(0.0, min(1.0, confidence))

    if not bullet_points:
        raise LLMServiceError("Model output summary_bullet_points is empty.")

    if not defined_terms:
        raise LLMServiceError("Model output defined_terms is empty.")

    return simplified_report, bullet_points[:5], defined_terms, confidence


def _extract_first_json_object(text: str) -> str | None:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    return match.group(0) if match else None

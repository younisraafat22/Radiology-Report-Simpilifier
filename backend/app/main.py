from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import SimplifyRequest, SimplifyResponse
from app.services.quality import evaluate_output_quality
from app.services.safety import sanitize_report_text, validate_report_text
from app.services.simplifier import LLMServiceError, simplify_report

app = FastAPI(title=settings.api_title, version="0.1.0")

raw_origins = [origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()]
allow_all = "*" in raw_origins
origin_regex = settings.cors_allow_origin_regex.strip() or None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else raw_origins,
    allow_origin_regex=None if allow_all else origin_regex,
    allow_credentials=False if allow_all else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/simplify", response_model=SimplifyResponse)
def simplify(payload: SimplifyRequest) -> SimplifyResponse:
    is_valid, reason = validate_report_text(payload.report_text)
    if not is_valid:
        raise HTTPException(status_code=400, detail=reason)

    sanitized_text = sanitize_report_text(payload.report_text)
    try:
        simplified_text, bullet_points, glossary, confidence, model_source = simplify_report(sanitized_text)
    except LLMServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    quality = evaluate_output_quality(sanitized_text, simplified_text)

    return SimplifyResponse(
        simplified_report=simplified_text,
        summary_bullet_points=bullet_points,
        defined_terms=glossary,
        confidence_score=confidence,
        readability_grade_level=quality.readability_grade_level,
        warnings=quality.warnings,
        model_source=model_source,
        disclaimer=(
            "This simplified summary is for education only and is not medical advice. "
            "Please discuss your report with your clinician."
        ),
    )

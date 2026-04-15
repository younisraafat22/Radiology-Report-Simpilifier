from pydantic import BaseModel, Field

from app.config import settings


class SimplifyRequest(BaseModel):
    report_text: str = Field(..., min_length=20, max_length=settings.max_report_chars)


class SimplifyResponse(BaseModel):
    simplified_report: str
    summary_bullet_points: list[str]
    defined_terms: dict[str, str]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    readability_grade_level: float = Field(..., ge=0.0)
    warnings: list[str]
    model_source: str
    disclaimer: str

import re

from app.config import settings

MIN_CHARS = 20
MAX_CHARS = settings.max_report_chars

# Lightweight PHI-like patterns for MVP; this will be expanded later.
PHI_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b\d{10}\b"),
    re.compile(r"\bMRN[:\s]*\w+\b", re.IGNORECASE),
]


def validate_report_text(report_text: str) -> tuple[bool, str]:
    cleaned = report_text.strip()

    if len(cleaned) < MIN_CHARS:
        return False, "Report text is too short."

    if len(cleaned) > MAX_CHARS:
        return False, "Report text is too long."

    return True, "ok"


def sanitize_report_text(report_text: str) -> str:
    sanitized = report_text

    for pattern in PHI_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)

    return sanitized

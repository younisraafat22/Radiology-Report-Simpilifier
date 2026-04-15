import re
from dataclasses import dataclass

import textstat

UNCERTAINTY_TERMS = {
    "possible",
    "possibly",
    "cannot exclude",
    "may represent",
    "likely",
    "suggestive",
}

MEDICAL_KEYWORDS = {
    "effusion",
    "atelectasis",
    "cardiomegaly",
    "edema",
    "consolidation",
    "pneumothorax",
    "opacity",
    "nodule",
}


@dataclass
class QualityReport:
    readability_grade_level: float
    warnings: list[str]


def evaluate_output_quality(source_report: str, simplified_report: str) -> QualityReport:
    warnings: list[str] = []

    readability_grade = _readability_grade(simplified_report)

    if _lost_uncertainty(source_report, simplified_report):
        warnings.append(
            "The source report included uncertainty terms that may not be fully reflected in the simplified output."
        )

    if _possible_added_finding(source_report, simplified_report):
        warnings.append(
            "The simplified output may include terms that were not explicit in the source report."
        )

    return QualityReport(readability_grade_level=readability_grade, warnings=warnings)


def _readability_grade(text: str) -> float:
    try:
        score = float(textstat.flesch_kincaid_grade(text))
        return round(max(0.0, score), 2)
    except Exception:
        return 0.0


def _lost_uncertainty(source_report: str, simplified_report: str) -> bool:
    source_lower = source_report.lower()
    simplified_lower = simplified_report.lower()

    has_source_uncertainty = any(term in source_lower for term in UNCERTAINTY_TERMS)
    if not has_source_uncertainty:
        return False

    has_simplified_uncertainty = any(term in simplified_lower for term in UNCERTAINTY_TERMS)
    return not has_simplified_uncertainty


def _possible_added_finding(source_report: str, simplified_report: str) -> bool:
    source_tokens = set(_tokens(source_report))
    simplified_tokens = set(_tokens(simplified_report))

    source_medical = source_tokens.intersection(MEDICAL_KEYWORDS)
    simplified_medical = simplified_tokens.intersection(MEDICAL_KEYWORDS)

    return len(simplified_medical - source_medical) > 0


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]+", text.lower())

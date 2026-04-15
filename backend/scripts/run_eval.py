import json
from pathlib import Path

from backend.app.services.quality import evaluate_output_quality
from backend.app.services.simplifier import simplify_report


def run() -> None:
    project_root = Path(__file__).resolve().parents[2]
    eval_path = project_root / "data" / "eval" / "eval_cases.jsonl"
    report_path = project_root / "data" / "eval" / "eval_report.json"

    total = 0
    warning_count = 0
    readability_scores: list[float] = []

    rows = []
    with eval_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))

    for row in rows:
        total += 1
        source = row["report_text"]

        simplified_report, bullet_points, defined_terms, confidence, model_source = simplify_report(source)
        quality = evaluate_output_quality(source, simplified_report)

        warning_count += len(quality.warnings)
        readability_scores.append(quality.readability_grade_level)

        row["output_preview"] = {
            "simplified_report": simplified_report,
            "summary_bullet_points": bullet_points,
            "defined_terms": defined_terms,
            "confidence_score": confidence,
            "model_source": model_source,
            "readability_grade_level": quality.readability_grade_level,
            "warnings": quality.warnings,
        }

    average_readability = round(sum(readability_scores) / len(readability_scores), 2) if readability_scores else 0.0

    report_payload = {
        "cases": total,
        "average_readability_grade": average_readability,
        "total_warnings": warning_count,
        "results": rows,
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report_payload, handle, indent=2)

    print(f"Evaluation complete. Report written to: {report_path}")


if __name__ == "__main__":
    run()

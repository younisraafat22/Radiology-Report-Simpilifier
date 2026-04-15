from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_simplify_endpoint_success() -> None:
    payload = {
        "report_text": "FINDINGS: Small left pleural effusion. Mild bibasilar atelectatic changes are present.",
    }

    response = client.post("/api/v1/simplify", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "simplified_report" in data
    assert "summary_bullet_points" in data
    assert "defined_terms" in data
    assert "confidence_score" in data
    assert "readability_grade_level" in data


def test_simplify_endpoint_rejects_short_text() -> None:
    response = client.post("/api/v1/simplify", json={"report_text": "too short"})
    assert response.status_code == 400

from fastapi.testclient import TestClient

from app.main import app
from app.services.simplifier import LLMServiceError
from app.services.vlm_extractor import VLMServiceError

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_simplify_endpoint_success(monkeypatch) -> None:
    def fake_simplifier(_report_text: str):
        return (
            "Plain explanation.",
            ["Key point 1.", "Key point 2."],
            {"atelectasis": "Part of the lung is not fully expanded."},
            0.88,
            "huggingface:test-model",
        )

    monkeypatch.setattr("app.main.simplify_report", fake_simplifier)

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
    assert data["model_source"].startswith("huggingface:")


def test_simplify_endpoint_rejects_short_text() -> None:
    response = client.post("/api/v1/simplify", json={"report_text": "too short"})
    assert response.status_code == 422


def test_simplify_endpoint_returns_503_on_llm_failure(monkeypatch) -> None:
    def fake_failure(_report_text: str):
        raise LLMServiceError("HF_API_TOKEN is required for LLM inference.")

    monkeypatch.setattr("app.main.simplify_report", fake_failure)

    payload = {
        "report_text": "FINDINGS: Possible left basilar infiltrate. Cannot exclude early pneumonia.",
    }

    response = client.post("/api/v1/simplify", json=payload)
    assert response.status_code == 503


def test_extract_text_endpoint_success(monkeypatch) -> None:
    def fake_extract_text(_image_bytes: bytes, _content_type: str):
        return "EXAM: CT SINUS WO CONTRAST", "huggingface-vlm:test-model"

    monkeypatch.setattr("app.main.extract_text_from_image", fake_extract_text)

    files = {"file": ("report.jpg", b"fake-image-bytes", "image/jpeg")}
    response = client.post("/api/v1/extract-text", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["extracted_text"].startswith("EXAM")
    assert data["model_source"].startswith("huggingface-vlm:")


def test_extract_text_endpoint_rejects_non_image() -> None:
    files = {"file": ("report.txt", b"not-image", "text/plain")}
    response = client.post("/api/v1/extract-text", files=files)
    assert response.status_code == 400


def test_extract_text_endpoint_returns_503_on_vlm_failure(monkeypatch) -> None:
    def fake_extract_failure(_image_bytes: bytes, _content_type: str):
        raise VLMServiceError("HF_API_TOKEN is required for VLM extraction.")

    monkeypatch.setattr("app.main.extract_text_from_image", fake_extract_failure)

    files = {"file": ("report.jpg", b"fake-image-bytes", "image/jpeg")}
    response = client.post("/api/v1/extract-text", files=files)
    assert response.status_code == 503

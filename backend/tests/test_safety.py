from app.services.safety import sanitize_report_text, validate_report_text


def test_validate_report_text_rejects_short_input() -> None:
    is_valid, reason = validate_report_text("short")
    assert is_valid is False
    assert reason == "Report text is too short."


def test_validate_report_text_accepts_normal_input() -> None:
    text = "FINDINGS: Mild bibasilar atelectatic changes. No focal consolidation present."
    is_valid, reason = validate_report_text(text)
    assert is_valid is True
    assert reason == "ok"


def test_sanitize_report_text_redacts_mrn() -> None:
    raw = "Patient MRN: 12345 has possible left pleural effusion."
    redacted = sanitize_report_text(raw)
    assert "MRN" not in redacted.upper()
    assert "[REDACTED]" in redacted

from fastapi.testclient import TestClient
from benefitflow_beta.app import MAX_TEXT_CHARS, app

client = TestClient(app)


def test_health_reports_alpha_round1_closed_and_live_integrations_blocked():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == "0.4.0"
    assert body["project"] == "benefitflow"
    assert body["rnd_status"] == "ROUND1_CLOSED_P0_HARDENING_ACTIVE"
    assert body["demo_mode"] is True
    assert body["live_integrations_allowed"] is False


def test_providers_are_synthetic():
    r = client.get("/api/providers")
    assert r.status_code == 200
    assert r.json()["synthetic"] is True


def test_provider_evidence_is_field_level_and_synthetic():
    r = client.get("/api/providers/demo-physio-1/evidence")
    assert r.status_code == 200
    body = r.json()
    assert body["synthetic"] is True
    fields = {item["field"] for item in body["assertions"]}
    assert {"identity", "service", "availability", "direct_billing"}.issubset(fields)


def test_parse_text_rejects_oversized_input():
    r = client.post("/api/parse-text", data={"text": "x" * (MAX_TEXT_CHARS + 1)})
    assert r.status_code == 413

from fastapi.testclient import TestClient
from benefitflow_beta.app import app

client = TestClient(app)


def test_health_reports_rnd_blocked():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == "0.3.0"
    assert body["project"] == "benefitflow"
    assert body["rnd_status"] == "BLOCKED_PENDING_USER_START"


def test_providers_are_synthetic():
    r = client.get("/api/providers")
    assert r.status_code == 200
    assert r.json()["synthetic"] is True

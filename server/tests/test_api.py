from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_policy_schema_without_market_network():
    r = client.get("/api/v1/stocks/ARM/policy")
    assert r.status_code == 200
    body = r.json()
    assert body["symbol"] == "ARM"
    assert any(x["key"] == "export_control" for x in body["categories"])

import os
import time
from contextlib import ExitStack
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import security
from app.main import SAMPLE, create_app, database
from app.models import Base
from app.security import COOKIE, Demo, demo_from_env

ORIGIN = "https://invoiceiq.example"
HEADERS = {"Origin": ORIGIN}
SECRET = b"test-only-session-signing-key-long-enough"


@pytest.fixture
def demo_clients(tmp_path):
    url = os.environ.get("INVOICEIQ_TEST_DATABASE_URL")
    engine = create_engine(url or f"sqlite:///{(tmp_path / 'demo.db').as_posix()}")
    if not url:
        Base.metadata.create_all(engine)
    app = create_app(Demo(ORIGIN, SECRET, SAMPLE))

    def test_database():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[database] = test_database
    try:
        with ExitStack() as stack:
            yield [stack.enter_context(TestClient(app, base_url=ORIGIN)) for _ in range(2)]
    finally:
        engine.dispose()


def start(client):
    response = client.post("/api/session", headers=HEADERS)
    assert response.json() == {"public_demo": True}
    cookie = response.headers["set-cookie"]
    for flag in ("__Host-invoiceiq=", "HttpOnly", "Secure", "SameSite=strict", "Path=/", "Max-Age=86400"):
        assert flag in cookie
    assert "domain=" not in cookie.lower()
    return response


def test_demo_workflow_and_owner_isolation(demo_clients):
    first, second = demo_clients
    assert first.get("/api/health").status_code == 200
    assert first.get("/api/invoices").status_code == 401
    assert first.post("/api/session").status_code == 403
    start(first)
    start(second)
    assert first.cookies.get(COOKIE) != second.cookies.get(COOKIE)
    assert first.post("/api/session", headers=HEADERS).headers.get("set-cookie") is None
    assert first.get("/docs").status_code == 404

    sample = first.get("/api/sample")
    assert sample.content == SAMPLE
    assert sample.headers["cache-control"] == "no-store"
    extracted = first.post("/api/extract", content=sample.content, headers=HEADERS)
    assert extracted.status_code == 200
    invoice = extracted.json()["fields"]
    assert invoice["total"] == "129.60"

    spoofed = {**invoice, "owner": second.cookies.get(COOKIE).split(".")[0]}
    assert first.post("/api/invoices", json=invoice, headers={"Origin": "https://other.example"}).status_code == 403
    created = first.post("/api/invoices", json=spoofed, headers=HEADERS)
    assert created.status_code == 201
    assert "owner" not in created.json()
    invoice_id = created.json()["id"]
    path = f"/api/invoices/{invoice_id}"
    assert first.get(path).status_code == 200
    assert first.get("/api/invoices?q=JS-1042").json()["total"] == 1
    assert first.get("/api/analytics").json()["currencies"]["USD"]["total"] == "129.60"
    assert first.post("/api/invoices/duplicates", json=invoice, headers=HEADERS).json()[0]["id"] == invoice_id
    assert "JS-1042" in first.get("/api/invoices.csv").text

    assert second.get(path).status_code == 404
    assert second.put(path, json=invoice, headers=HEADERS).status_code == 404
    assert second.delete(path, headers=HEADERS).status_code == 404
    assert second.get("/api/invoices").json()["total"] == 0
    assert second.get("/api/analytics").json()["count"] == 0
    assert "JS-1042" not in second.get("/api/invoices.csv").text
    assert second.post("/api/invoices/duplicates", json=invoice, headers=HEADERS).json() == []
    assert first.put(path, json={**invoice, "total": "130.25"}, headers=HEADERS).json()["total"] == "130.25"
    assert first.delete(path, headers=HEADERS).status_code == 204

    token = first.cookies.get(COOKIE)
    first.cookies.clear()
    first.cookies.set(COOKIE, token[:-1] + ("1" if token[-1] == "0" else "0"))
    assert first.get("/api/invoices").status_code == 401


def test_demo_request_limits_and_cors(demo_clients, monkeypatch):
    monkeypatch.setattr(security, "time", SimpleNamespace(monotonic=lambda: 0, time=time.time))
    first, second = demo_clients
    start(first)
    preflight = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"}
    assert first.options("/api/extract", headers={**HEADERS, **preflight}).headers["access-control-allow-origin"] == ORIGIN
    denied = first.options("/api/extract", headers={**preflight, "Origin": "https://other.example"})
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers
    assert first.post("/api/extract", content=b"%PDF-arbitrary", headers=HEADERS).status_code == 422
    assert first.post("/api/extract", content=SAMPLE + b"x", headers=HEADERS).status_code == 413
    assert first.post("/api/extract", content=iter([SAMPLE, b"x"]), headers=HEADERS).status_code == 413
    assert first.post("/api/invoices", content=iter([b"x" * 8192] * 3), headers=HEADERS).status_code == 413
    for _ in range(5):
        assert first.post("/api/extract", content=SAMPLE, headers=HEADERS).status_code == 200
    limited = first.post("/api/extract", content=SAMPLE, headers=HEADERS)
    assert limited.status_code == 429
    assert "retry-after" in limited.headers

    start(second)
    for _ in range(90):
        assert second.get("/api/invoices").status_code == 200
    assert second.get("/api/invoices").status_code == 429

    demo = Demo(ORIGIN, SECRET, SAMPLE)
    expired = f"{'0' * 32}.1"
    assert demo.owner(f"{expired}.{demo.signature(expired)}") is None


def test_production_configuration_fails_closed(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("INVOICEIQ_PUBLIC_DEMO", raising=False)
    with pytest.raises(RuntimeError, match="requires INVOICEIQ_PUBLIC_DEMO"):
        demo_from_env(SAMPLE)
    monkeypatch.setenv("INVOICEIQ_PUBLIC_DEMO", "1")
    monkeypatch.setenv("INVOICEIQ_DEMO_ORIGIN", ORIGIN)
    monkeypatch.setenv("INVOICEIQ_SESSION_SECRET", SECRET.decode())
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:password@example.test/db?sslmode=require")
    with pytest.raises(RuntimeError, match="sslmode=verify-full"):
        demo_from_env(SAMPLE)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:password@example.test/db?sslmode=verify-full")
    assert demo_from_env(SAMPLE).origin == ORIGIN

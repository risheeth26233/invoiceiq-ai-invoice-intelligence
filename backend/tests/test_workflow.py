import runpy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.main import app, database
from app.models import Base

sample = runpy.run_path(str(Path(__file__).resolve().parents[2] / "sample-data/make_invoice.py"))


@pytest.fixture
def client(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    Base.metadata.create_all(engine)

    def test_database():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[database] = test_database
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_invoice_workflow(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    response = client.post("/api/extract", content=sample["create_invoice"]())
    assert response.status_code == 200
    data = response.json()["fields"]
    assert data == {
        "vendor": "Juniper Studio", "number": "JS-1042", "invoice_date": "2026-10-06",
        "due_date": "2026-11-06", "currency": "USD", "subtotal": "120.00", "tax": "9.60", "total": "129.60",
    }
    assert client.get("/api/invoices").json()["total"] == 0
    response = client.post("/api/invoices", json={**data, "total": "130.25"})
    assert response.status_code == 201
    invoice_id = response.json()["id"]
    assert client.get("/api/invoices", params={"q": "JS-1042"}).json()["total"] == 1
    assert client.get("/api/invoices", params={"q": "%"}).json()["total"] == 0
    assert client.get("/api/analytics").json()["currencies"]["USD"]["total"] == "130.25"
    response = client.post("/api/invoices/duplicates", json={**data, "vendor": "juniper-studio", "number": "js1042"})
    assert response.json() == [{"id": invoice_id, "reason": "Same vendor and invoice number"}]
    response = client.put(f"/api/invoices/{invoice_id}", json={**data, "vendor": "=Example", "currency": "eur"})
    assert response.json()["currency"] == "EUR"
    assert "'=Example" in client.get("/api/invoices.csv").text
    assert client.get("/api/analytics").json()["currencies"]["EUR"]["total"] == "129.60"
    assert client.delete(f"/api/invoices/{invoice_id}").status_code == 204
    assert client.get(f"/api/invoices/{invoice_id}").status_code == 404
    assert client.get("/api/analytics").json() == {"count": 0, "currencies": {}}


@pytest.mark.parametrize(("data", "status"), [
    (b"plain text", 422),
    (b"%PDF-1.7\nbroken", 422),
    (b"0" * (10 * 1024 * 1024 + 1), 413),
])
def test_rejects_invalid_uploads(client, data, status):
    assert client.post("/api/extract", content=data).status_code == status


@pytest.mark.parametrize("kind", ["png", "jpeg", "pdf"])
def test_ocr(client, kind):
    import os

    import pymupdf

    if not os.environ.get("TESSDATA_PREFIX"):
        pytest.skip("Set TESSDATA_PREFIX to run OCR tests.")
    with pymupdf.open(stream=sample["create_invoice"](), filetype="pdf") as document:
        image = document[0].get_pixmap(dpi=180)
        data = image.tobytes("png" if kind == "pdf" else kind)
        if kind == "pdf":
            with pymupdf.open() as scanned:
                page = scanned.new_page(width=612, height=792)
                page.insert_image(page.rect, stream=data, keep_proportion=True)
                data = scanned.tobytes()
    response = client.post("/api/extract", content=data)
    assert response.status_code == 200
    body = response.json()
    assert body["fields"]["number"] == "JS-1042"
    assert body["fields"]["total"] == "129.60"
    assert body["confidence"]["number"] == "review"

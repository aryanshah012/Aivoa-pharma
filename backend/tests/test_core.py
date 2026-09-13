"""Pragmatic backend tests: health, schemas, deterministic completeness, CRUD, uploads."""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ.setdefault("GROQ_API_KEY", "test-key")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.db.init_db import init_db  # noqa: E402

init_db()
client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_extraction_schema_accepts_nulls():
    from app.schemas.complaint import ExtractedData
    e = ExtractedData(customer_name="X", product_name="Y",
                      complaint_type="Physical Defect", description="d")
    assert e.batch_number is None


def test_extraction_schema_rejects_bad_enum():
    from pydantic import ValidationError
    from app.schemas.complaint import ExtractedData
    try:
        ExtractedData(customer_name="X", product_name="Y", complaint_type="T", description="d",
                      product_type="NotAType")
        assert False, "should have raised"
    except ValidationError:
        pass


def test_completeness_is_deterministic():
    from app.agents.completeness_agent import check_required_fields
    present, missing, _ = check_required_fields(
        {"customer_name": "A", "product_name": "P", "complaint_type": "T",
         "description": "d", "batch_number": "B1"})
    assert "Customer name" in present and "Batch number" in present
    assert "Expiry date" in missing


def test_complaint_crud():
    payload = {
        "customer_name": "Test Customer", "product_name": "Paracetamol Tablets",
        "complaint_type": "Physical Defect", "description": "Broken tablets observed.",
        "batch_number": "TST001",
    }
    r = client.post("/api/complaints", json=payload)
    assert r.status_code == 201
    cid = r.json()["id"]
    assert r.json()["complaint_number"].startswith("CC-")
    assert client.get(f"/api/complaints/{cid}").status_code == 200
    assert client.put(f"/api/complaints/{cid}", json={"status": "Open"}).json()["status"] == "Open"
    assert client.delete(f"/api/complaints/{cid}").status_code == 204


def test_complaint_number_sequence():
    p1 = {"customer_name": "A", "product_name": "P", "complaint_type": "T", "description": "d"}
    p2 = {"customer_name": "B", "product_name": "P", "complaint_type": "T", "description": "d"}
    n1 = client.post("/api/complaints", json=p1).json()["complaint_number"]
    n2 = client.post("/api/complaints", json=p2).json()["complaint_number"]
    assert n1 != n2 and n1.split("-")[-1].isdigit()


def test_invalid_upload_rejected():
    r = client.post("/api/complaints/analyze-document",
                    files={"file": ("virus.exe", b"MZ...", "application/octet-stream")})
    assert r.status_code == 400


def test_empty_txt_rejected():
    r = client.post("/api/complaints/analyze-document",
                    files={"file": ("empty.txt", b"", "text/plain")})
    assert r.status_code == 400


def test_short_txt_rejected():
    r = client.post("/api/complaints/analyze-document",
                    files={"file": ("tiny.txt", b"hi", "text/plain")})
    assert r.status_code == 400


def test_dashboard_stats():
    r = client.get("/api/dashboard/stats")
    assert r.status_code == 200
    body = r.json()
    for k in ["total_complaints", "open_complaints", "under_investigation",
              "critical_high_risk", "closed_complaints"]:
        assert k in body

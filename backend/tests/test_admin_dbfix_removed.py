from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_admin_dbfix_endpoint_removed():
    r = client.post("/admin/db_fix_pix_desc_trigger")
    assert r.status_code == 404, r.text

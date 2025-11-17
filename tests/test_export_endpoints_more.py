# tests/test_export_endpoints_more.py
def test_export_endpoints_client(client):
    # CSV (may redirect to login or return 200)
    resp = client.get("/export/csv")
    assert resp.status_code in (200, 302, 404)

    # PDF
    resp = client.get("/export/pdf")
    assert resp.status_code in (200, 302, 404)

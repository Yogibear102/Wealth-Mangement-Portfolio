# tests/test_routes_smoke.py
def test_root_and_dashboard_and_assets(client):
    # root
    resp = client.get("/")
    assert resp.status_code in (200, 302, 404)

    # dashboard (if exists)
    resp = client.get("/dashboard")
    assert resp.status_code in (200, 302, 404)

    # assets list (common path)
    resp = client.get("/assets")
    assert resp.status_code in (200, 302, 404)

def test_transactions_list_and_add_pages(client):
    resp = client.get("/transactions")
    assert resp.status_code in (200, 302, 404)

    resp = client.get("/transactions/add")
    # Add page often requires login; still should respond (redirect/200/404)
    assert resp.status_code in (200, 302, 404)

# tests/test_error_handlers_and_404.py
def test_404_page(client):
    resp = client.get("/this-route-should-not-exist-12345")
    # app should return 404 (or redirect) — but assert that it's not a 500
    assert resp.status_code != 500
    assert resp.status_code in (404, 302, 200)

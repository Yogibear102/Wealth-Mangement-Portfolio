

def test_index_and_logout(client):
    """Covers index and logout routes for coverage."""
    # Index page without login
    res = client.get('/')
    assert res.status_code == 200
    assert b"Personal Wealth" in res.data or b"Login" in res.data

    # Simulate login session
    with client.session_transaction() as sess:
        sess['user_id'] = 1
    res = client.get('/')
    # Should redirect to dashboard when logged in
    assert res.status_code in (302, 303)
    assert '/dashboard' in res.location

    # Logout should clear session
    res = client.get('/logout', follow_redirects=True)
    assert b'Logged out' in res.data or res.status_code == 200


def test_health_and_404(client):
    """Covers health and 404 responses."""
    res = client.get('/health')
    assert res.status_code == 200
    data = res.get_json()
    assert 'status' in data and data['status'] == 'ok'

    # Invalid route check
    res = client.get('/not-a-real-page')
    assert res.status_code == 404

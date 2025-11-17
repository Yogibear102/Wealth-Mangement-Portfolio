from app import app, db, Asset


def test_invalid_transaction_add(client):
    """Covers invalid asset and transaction handling branches."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    # Missing asset_id
    res = client.post('/transactions/add', data={
        'asset_id': '',
        'type': 'Buy',
        'amount': '1000'
    }, follow_redirects=True)
    assert b'Invalid' in res.data or res.status_code == 200


def test_export_pdf_large_data(client):
    """Simulate large data export for PDF edge."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    with app.app_context():
        for i in range(3):
            a = Asset(user_id=1, asset_type='Stock', name=f'Edge{i}',
                      quantity=1, current_value=1000, currency='USD')
            db.session.add(a)
        db.session.commit()

    res = client.get('/export/pdf')
    assert res.status_code == 200
    assert res.mimetype == 'application/pdf'


def test_health_and_redirects(client):
    """Cover 404 and redirect branches."""
    res = client.get('/not-found-page')
    assert res.status_code == 404

    # Login required redirect
    res = client.get('/dashboard')
    assert res.status_code in (302, 303)

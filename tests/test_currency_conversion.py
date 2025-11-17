from app import load_rates


def test_rates_loaded():
    rates = load_rates()
    assert 'USD' in rates
    assert rates['USD'] == 1.0

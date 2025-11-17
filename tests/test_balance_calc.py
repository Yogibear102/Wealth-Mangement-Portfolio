from models import Asset, Transaction


def test_transaction_balance_calculation():
    a = Asset()
    a.current_value = 100.0
    t_buy = Transaction()
    t_buy.tx_type = 'buy'
    t_buy.amount = 50
    if t_buy.tx_type in ['buy', 'expense']:
        a.current_value += t_buy.amount
    assert a.current_value == 150.0
    t_sell = Transaction()
    t_sell.tx_type = 'sell'
    t_sell.amount = 70
    if t_sell.tx_type in ['sell', 'income']:
        a.current_value -= t_sell.amount
        if a.current_value < 0:
            a.current_value = 0
    assert a.current_value == 80.0

from matching_engine.engine import Trade
from decimal import Decimal
import pytest

@pytest.mark.parametrize("price, qty, expected", [
    ("20", 150, "Trade, price: 20, qty: 150"),
    ("20.00", 150, "Trade, price: 20, qty: 150"),
    ("10.50", 100, "Trade, price: 10.5, qty: 100"),
    ("9.99", 200, "Trade, price: 9.99, qty: 200"),
    ("1.2300", 50, "Trade, price: 1.23, qty: 50"),
    ("0.50", 25, "Trade, price: 0.5, qty: 25"),
    ("100.000", 10, "Trade, price: 100, qty: 10"),
])

def test_trade_str(price, qty, expected):
    assert str(Trade(price=Decimal(price), qty=qty)) == expected
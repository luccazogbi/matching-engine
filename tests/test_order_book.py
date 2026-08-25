from decimal import Decimal

from matching_engine.order import Side
from matching_engine.order_book import OrderBook

def test_get_or_create_bid_level():
    ob = OrderBook()

    level = ob.get_or_create_level(
        Side.BUY,
        Decimal("10.50")
    )
from decimal import Decimal

from matching_engine.order import Side
from matching_engine.order_book import OrderBook

def test_get_or_create_bid_level():
    ob = OrderBook()

    level = ob.get_or_create_level(
        Side.BUY,
        Decimal("10.50")
    )

    # Tests
    assert Decimal("10.50") in ob.bids
    assert ob.bids[Decimal("10.50")] is level
    assert ob.bid_prices[0] == -Decimal("10.50")

def test_reuse_existing_bid_level():
    ob = OrderBook()


    level1 = ob.get_or_create_level(
        Side.BUY,
        Decimal("10.50")
    )

    level2 = ob.get_or_create_level(
        Side.BUY,
        Decimal("10.50")
    )

    # Tests
    assert level1 is level2
    assert len(ob.bid_prices) == 1
    
def test_create_offer_level():
    ob = OrderBook()

    level = ob.get_or_create_level(
        Side.SELL,
        Decimal("10.50")
    )

    assert Decimal("10.50") in ob.offers
    assert ob.offers[Decimal("10.50")] is level
    assert ob.offer_prices[0] == Decimal("10.50")  
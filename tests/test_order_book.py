import pytest

from decimal import Decimal

from matching_engine.order import Side, Order, OrderType, PegReference
from matching_engine.order_book import OrderBook

# Tests for the get_or_create_level method of order_book.py
#-----------------------------------------------------\\-----------------------------------------------------# 

def test_get_or_create_bid_level():
    ob = OrderBook()

    level = ob.get_or_create_level(
        Side.BUY,
        Decimal("10.50")
    )

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

def test_reuse_existing_offer_level():
    ob = OrderBook()

    level1 = ob.get_or_create_level(
        Side.SELL,
        Decimal("10.50")
    )

    level2 = ob.get_or_create_level(
        Side.SELL,
        Decimal("10.50")
    )

    assert level1 is level2
    assert len(ob.offer_prices) == 1

def test_invalid_side():
    ob = OrderBook()

    with pytest.raises(ValueError):
        ob.get_or_create_level(
            "invalid",
            Decimal("10.50")
        )

# Tests for best_bid() & best_offer() method
#-----------------------------------------------------\\-----------------------------------------------------# 

def test_best_bid():
    ob = OrderBook()

    ob.get_or_create_level(Side.BUY, Decimal("10.20"))
    ob.get_or_create_level(Side.BUY, Decimal("10.80"))
    ob.get_or_create_level(Side.BUY, Decimal("10.50"))

    assert ob.best_bid() == Decimal("10.80")


def test_best_offer():
    ob = OrderBook()

    ob.get_or_create_level(Side.SELL, Decimal("10.90"))
    ob.get_or_create_level(Side.SELL, Decimal("10.60"))
    ob.get_or_create_level(Side.SELL, Decimal("10.70"))

    assert ob.best_offer() == Decimal("10.60")

def test_best_prices_when_empty():
    ob = OrderBook()

    assert ob.best_bid() is None
    assert ob.best_offer() is None

def test_best_bid_removes_stale_price():
    # Tests lazy deletion of a stale bid price from the heap.
    ob = OrderBook()

    ob.get_or_create_level(Side.BUY, Decimal("10.00"))
    ob.get_or_create_level(Side.BUY, Decimal("9.99"))
    ob.get_or_create_level(Side.BUY, Decimal("9.98"))

    assert ob.best_bid() == Decimal("10.00")
    assert Decimal("10.00") in ob.bids

    ob.remove_empty_level(
        Side.BUY,
        Decimal("10.00")
    )

    assert Decimal("10.00") not in ob.bids
    assert ob.best_bid() == Decimal("9.99")
    assert -Decimal("10.00") not in ob.bid_prices


def test_best_offer_removes_stale_price():
    # Tests lazy deletion of a stale offer price from the heap.
    ob = OrderBook()

    ob.get_or_create_level(Side.SELL, Decimal("10.00"))
    ob.get_or_create_level(Side.SELL, Decimal("10.01"))
    ob.get_or_create_level(Side.SELL, Decimal("10.02"))

    assert ob.best_offer() == Decimal("10.00")
    assert Decimal("10.00") in ob.offers

    ob.remove_empty_level(
        Side.SELL,
        Decimal("10.00")
    )

    assert Decimal("10.00") not in ob.offers
    assert ob.best_offer() == Decimal("10.01")
    assert Decimal("10.00") not in ob.offer_prices

def test_best_price_when_empty():
    ob = OrderBook()

    assert ob.best_price(Side.BUY) is None
    assert ob.best_price(Side.SELL) is None


def test_best_price_dispatches_to_correct_side():
    ob = OrderBook()

    ob.get_or_create_level(
        Side.BUY,
        Decimal("10.00")
    )

    ob.get_or_create_level(
        Side.SELL,
        Decimal("10.50")
    )

    assert ob.best_price(Side.BUY) == ob.best_bid()
    assert ob.best_price(Side.SELL) == ob.best_offer()

    assert ob.best_price(Side.BUY) == Decimal("10.00")
    assert ob.best_price(Side.SELL) == Decimal("10.50")

# ------------------------------------------- Peg orders (reference_price method) ------------------------------------------- #
# Future Review

def make_order(side, price, qty, peg_reference=None):
    """Build a resting order directly, without going through the engine.

    The book stores orders but never creates them, so a test that needs a level holding only
    pegged orders — a state submit_limit cannot produce — has to assemble it by hand.
    """
    return Order(
        side=side,
        order_type=OrderType.LIMIT,
        qty=qty,
        price=price,
        peg_reference=peg_reference,
    )

def test_reference_price_matches_best_price_without_pegged():

    ob = OrderBook()
    
    best_order = Order(
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=150,
        price=Decimal("10"),
    )

    ob.get_or_create_level(Side.BUY, Decimal("10")).last_insert(best_order)

    unpegged_price = ob.reference_price(peg_reference=PegReference.BID)

    assert ob.best_price(Side.BUY) == Decimal("10")
    assert unpegged_price == Decimal("10")

def test_reference_price_picks_the_best_of_several_levels():
    ob = OrderBook()

    ob.get_or_create_level(Side.BUY, Decimal("10")).last_insert(
        make_order(Side.BUY, Decimal("10"), 200)
    )
    ob.get_or_create_level(Side.BUY, Decimal("9.99")).last_insert(
        make_order(Side.BUY, Decimal("9.99"), 100)
    )

    assert ob.reference_price(PegReference.BID) == Decimal("10")
    assert ob.reference_price(PegReference.BID) == ob.best_price(Side.BUY)

def test_reference_price_returns_none_on_empty_side():
    ob = OrderBook()

    assert ob.reference_price(PegReference.BID) is None
    assert ob.reference_price(PegReference.OFFER) is None

def test_reference_price_skips_level_with_only_pegged():
    ob = OrderBook()

    ob.get_or_create_level(Side.BUY, Decimal("9.99")).last_insert(
        make_order(Side.BUY, Decimal("9.99"), 100)
    )
    ob.get_or_create_level(Side.BUY, Decimal("10")).last_insert(
        make_order(Side.BUY, Decimal("10"), 150, PegReference.BID)
    )

    # The two disagree, and that disagreement is the whole reason reference_price exists.
    assert ob.best_price(Side.BUY) == Decimal("10")
    assert ob.reference_price(PegReference.BID) == Decimal("9.99")

def test_reference_price_accepts_mixed_level():
    ob = OrderBook()

    level = ob.get_or_create_level(Side.BUY, Decimal("10"))
    level.last_insert(make_order(Side.BUY, Decimal("10"), 200))
    level.last_insert(make_order(Side.BUY, Decimal("10"), 150, PegReference.BID))

    # One non-pegged order is enough to make the level usable as a reference.
    assert ob.reference_price(PegReference.BID) == Decimal("10")

def test_reference_price_returns_none_when_only_pegged():
    ob = OrderBook()

    ob.get_or_create_level(Side.BUY, Decimal("10")).last_insert(
        make_order(Side.BUY, Decimal("10"), 150, PegReference.BID)
    )

    # A pegged order alone on the side cannot serve as its own reference.
    assert ob.best_price(Side.BUY) == Decimal("10")
    assert ob.reference_price(PegReference.BID) is None

def test_reference_price_offer_side():
    ob = OrderBook()

    ob.get_or_create_level(Side.BUY, Decimal("10")).last_insert(
        make_order(Side.BUY, Decimal("10"), 200)
    )
    ob.get_or_create_level(Side.SELL, Decimal("10.5")).last_insert(
        make_order(Side.SELL, Decimal("10.5"), 100)
    )

    assert ob.reference_price(PegReference.OFFER) == Decimal("10.5")
    assert ob.reference_price(PegReference.BID) == Decimal("10")

def test_reference_price_skips_pegged_on_offer_side():
    ob = OrderBook()

    ob.get_or_create_level(Side.SELL, Decimal("10.5")).last_insert(
        make_order(Side.SELL, Decimal("10.5"), 100, PegReference.OFFER)
    )
    ob.get_or_create_level(Side.SELL, Decimal("11")).last_insert(
        make_order(Side.SELL, Decimal("11"), 100)
    )

    # The sell side walks upwards, so skipping means going to the higher price.
    assert ob.best_price(Side.SELL) == Decimal("10.5")
    assert ob.reference_price(PegReference.OFFER) == Decimal("11")

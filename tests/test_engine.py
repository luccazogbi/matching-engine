from matching_engine.engine import Trade, MatchingEngine
from decimal import Decimal
from matching_engine.price_level import PriceLevel
from matching_engine.order import Side, OrderType, Order
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


def test_submit_limit_order():

    # first instance of my project (already have the book inside of it)
    engine = MatchingEngine()

    # Creating the first SELL order 
    sell_order = Order(Side.SELL,
        OrderType.LIMIT,
        100,
        Decimal("10")
    )

    # Creating the first sell level
    level_sell = engine.book.get_or_create_level(
        Side.SELL,
        Decimal("10")
    )

    level_sell.last_insert(sell_order)

    # Placing it in the engine.book.orders
    engine.book.orders[sell_order.order_id] = sell_order 

    # Creating the first BUY Order
    trades = engine.submit_limit(
        Side.BUY,
        Decimal("10"),
        100
    )

    assert [str(t) for t in trades] == [
        "Trade, price: 10, qty: 100"
    ]

    assert engine.book.best_price(Side.BUY) is None
    assert engine.book.best_price(Side.SELL) is None

    assert len(engine.book.orders) == 0

def test_submit_limit_without_match():
    engine = MatchingEngine()

    trades = engine.submit_limit(
        Side.BUY,
        Decimal("10"),
        100
    )

    assert trades == []

    assert engine.book.best_price(Side.BUY) == Decimal("10")
    assert len(engine.book.orders) == 1

def test_submit_limit_partial_match():
    engine = MatchingEngine()

    engine.submit_limit(
        Side.SELL,
        Decimal("10"),
        200
    )

    trades = engine.submit_limit(
        Side.BUY,
        Decimal("10"),
        100
    )

    assert [str(t) for t in trades] == [
        "Trade, price: 10, qty: 100"
    ]

    level = engine.book.offers[Decimal("10")]

    assert level.total_qty == 100
    assert level.first.qty == 100





def test_submit_limit_aggressive_order_rests_remaining_qty():
    engine = MatchingEngine()

    engine.submit_limit(
        Side.SELL,
        Decimal("10"),
        100
    )

    trades = engine.submit_limit(
        Side.BUY,
        Decimal("10"),
        200
    )

    assert [str(t) for t in trades] == [
        "Trade, price: 10, qty: 100"
    ]

    assert engine.book.best_price(Side.BUY) == Decimal("10")
    assert engine.book.bids[Decimal("10")].total_qty == 100

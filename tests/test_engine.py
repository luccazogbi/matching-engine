from matching_engine.engine import Trade, MatchingEngine
from decimal import Decimal
from matching_engine.price_level import PriceLevel
from matching_engine.order import Side, OrderType, Order
import pytest

def assert_book_invariants(engine):
    """Structural checks that must hold after any operation, whatever it was.

    Called at the end of each test so that a bug in one operation is caught by every test
    that exercises it, not only by the test written for that operation.
    """
    book = engine.book

    # 1. The book is never crossed: the best bid must sit strictly below the best offer.
    best_bid = book.best_price(Side.BUY)
    best_offer = book.best_price(Side.SELL)

    if best_bid is not None and best_offer is not None:
        assert best_bid < best_offer, (
            f"crossed book: best bid {best_bid} is not below best offer {best_offer}"
        )

    for side in (Side.BUY, Side.SELL):
        for price, level in book.levels_for(side).items(): # visiting every level of "side". As it's inside for side in (Side.BUY, Side.SELL), it'll
            # visit every level of both sides

            # It'll cross every order inside a level and stop when it reaches None. It's storing order objects inside queued
            queued = []
            current = level.first
            while current is not None:
                queued.append(current)
                current = current.next_order

            # 2. A level that lost its last order must have been removed from the book (An empty list is False)
            assert queued, f"empty level left behind at {price} on the {side.value} side"

            # 3. The aggregate must agree with the queue it summarises.
            queue_total = sum(order.qty for order in queued)
            assert level.total_qty == queue_total, (
                f"level {price}: total_qty is {level.total_qty}, queue sums to {queue_total}"
            )

            # 4. Position in the queue must agree with arrival order.
            sequences = [order.seq for order in queued]
            assert sequences == sorted(sequences), (
                f"level {price}: queue order disagrees with arrival order, seqs are {sequences}"
            )

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


def test_submit_limit_respects_fifo():
    engine = MatchingEngine()

    engine.submit_limit(Side.SELL, Decimal("10"), 100)
    engine.submit_limit(Side.SELL, Decimal("10"), 200)

    trades = engine.submit_limit(
        Side.BUY,
        Decimal("10"),
        150
    )

    # str(t) is transforming a Trade object in string. It'll be formated by its method "__str__"
    assert [str(t) for t in trades] == [
        "Trade, price: 10, qty: 150"
    ]

    level = engine.book.offers[Decimal("10")]

    assert level.first.qty == 150

def test_limit_sweeps_multiple_levels():

    engine = MatchingEngine()

    engine.submit_limit(Side.SELL, Decimal("20"), 100)
    engine.submit_limit(Side.SELL, Decimal("22"), 100)
    engine.submit_limit(Side.SELL, Decimal("26"), 100)

    trades = engine.submit_limit(Side.BUY, Decimal("25"), 250)

    assert [str(t) for t in trades] == [
            "Trade, price: 20, qty: 100",
            "Trade, price: 22, qty: 100"
    ]

    level = engine.book.bids[Decimal("25")] 
    assert level.first.qty == 50
    assert level.total_qty == 50

    level = engine.book.offers[Decimal("26")]
    assert level.first.qty == 100
    assert level.total_qty == 100

    assert engine.book.best_price(Side.BUY) == Decimal("25")

def test_limit_order_matching_passive_price():

    engine = MatchingEngine()

    engine.submit_limit(Side.SELL, Decimal("20"), 100)

    trades = engine.submit_limit(
        Side.BUY,
        Decimal("25"),
        100
    )

    assert [str(t) for t in trades] == [
                "Trade, price: 20, qty: 100"
    ]

def test_limit_does_not_cross_when_price_unacceptable():

    engine = MatchingEngine()
    
    engine.submit_limit(Side.SELL, Decimal("20"), 100)

    trades = engine.submit_limit(
        Side.BUY,
        Decimal("19"),
        100
    )

    assert [str(t) for t in trades] == []

# ---------------------------------------------- Market Order ---------------------------------------------- #

def test_market_sweeps_multiple_levels():

    engine = MatchingEngine()
         
    engine.submit_limit(Side.SELL, Decimal("20"), 100)
    engine.submit_limit(Side.SELL, Decimal("22"), 100)
    engine.submit_limit(Side.SELL, Decimal("26"), 100)

    trades = engine.submit_market(
        Side.BUY,
        250
    )

    assert [str(t) for t in trades] == [
        "Trade, price: 20, qty: 100",
        "Trade, price: 22, qty: 100",
        "Trade, price: 26, qty: 50"
    ]

    level = engine.book.offers[Decimal("26")]
    assert level.first.qty == 50
    assert level.total_qty == 50

def test_market_without_liquidity():

    engine = MatchingEngine()

    trades = engine.submit_market(
        Side.BUY,
        100
    )

    assert [str(t) for t in trades] == []
    assert engine.book.bids == {}

def test_market_partial_liquidity_discards_remainder():

    engine = MatchingEngine()
            
    engine.submit_limit(Side.SELL, Decimal("20"), 50)

    trades = engine.submit_market(
        Side.BUY,
        300
    )

    assert [str(t) for t in trades] == [
        "Trade, price: 20, qty: 50"
    ]

    assert engine.book.bids == {}

def test_market_consumes_in_arrival_order():

    engine = MatchingEngine()
                
    engine.submit_limit(Side.SELL, Decimal("20"), 100)
    engine.submit_limit(Side.SELL, Decimal("20"), 200)

    level = engine.book.offers[Decimal("20")]
    assert level.first.qty == 100
    assert level.total_qty == 300
    first_seq = level.first.seq

    trades = engine.submit_market(
        Side.BUY,
        150
    )

    second_seq = level.first.seq
    assert level.first.qty == 150
    assert second_seq > first_seq
    assert [str(t) for t in trades] == [
            "Trade, price: 20, qty: 150"
    ]

def test_problem_statement_sequence():

    engine = MatchingEngine()

    trade = engine.submit_limit(Side.BUY, Decimal("10"), 100)
    assert [str(t) for t in trade] == []

    trade = engine.submit_limit(Side.SELL, Decimal("20"), 100)
    assert [str(t) for t in trade] == []

    trade = engine.submit_limit(Side.SELL, Decimal("20"), 200)
    assert [str(t) for t in trade] == []

    trade = engine.submit_market(Side.BUY, 150)
    assert [str(t) for t in trade] == [
        "Trade, price: 20, qty: 150"
    ]

    trade = engine.submit_market(Side.BUY, 200)
    assert [str(t) for t in trade] == [
        "Trade, price: 20, qty: 150"
    ]

    trade = engine.submit_market(Side.SELL, 200)
    assert [str(t) for t in trade] == [
        "Trade, price: 10, qty: 100"
    ]

    assert engine.book.offers == {}
    assert engine.book.bids == {}
    assert engine.book.orders == {}

# ---------------------------------------------- Order cancellation ---------------------------------------------- #

def test_cancel_removes_order_from_book():
    eng = MatchingEngine()
    eng.submit_limit(Side.BUY, Decimal("10"), 100)
    oid = next(iter(eng.book.orders)) # iter(eng.book.order) create an iterator before the first element, so that's why we apply next()

    eng.cancel(oid)

    assert eng.book.best_price(Side.BUY) is None # It's taking from the eng.book.bid_prices
    assert len(eng.book.orders) == 0
    assert Decimal("10") not in eng.book.bids
    assert eng.book.bid_prices == []

def test_cancel_middle_of_queue():
    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 100)
    eng.submit_limit(Side.BUY, Decimal("10"), 200)
    eng.submit_limit(Side.BUY, Decimal("10"), 50)


    level = eng.book.levels_for(Side.BUY)[Decimal("10")]
    first, middle, last = level.first, level.first.next_order, level.last
    eng.cancel(middle.order_id)   

    assert first.previous_order is None
    assert first.next_order is last

    assert last.previous_order is first
    assert last.next_order is None
    assert level.total_qty == 150

def test_cancel_keeps_level_when_not_empty():
    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 100)
    eng.submit_limit(Side.BUY, Decimal("10"), 200)

    oid = next(iter(eng.book.orders))
    eng.cancel(oid)

    assert eng.book.bids[Decimal("10")] is not None
    assert eng.book.best_price(Side.BUY) == Decimal("10")
    assert eng.book.bids[Decimal("10")].total_qty == 200

def test_cancel_unknown_id():
    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 100)

    oid = 1
    unknown_id = eng.cancel(oid)

    assert unknown_id is None
    assert eng.book.best_price(Side.BUY) == Decimal("10")

def test_cancelled_order_does_not_match():

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 100)

    oid = next(iter(eng.book.orders))
    eng.cancel(oid)

    trade = eng.submit_limit(Side.SELL, Decimal("10"), 100)
    trade_market = eng.submit_market(Side.SELL, 100)

    assert [str(t) for t in trade] == []
    assert [str(t) for t in trade_market] == []
    print(eng.book.__str__())
        
# ---------------------------------------------- Order modification ---------------------------------------------- #

def test_modify_price_reprices_and_loses_priority():

    eng = MatchingEngine()
    
    eng.submit_limit(Side.BUY, Decimal("10"), 200)
    eng.submit_limit(Side.BUY, Decimal("9.99"), 100)
    eng.submit_limit(Side.SELL, Decimal("10.5"), 100)

    first_id = next(iter(eng.book.orders))

    eng.modify(first_id, new_price=Decimal("9.98"))

    assert [line.rstrip() for line in str(eng.book).split("\n")] == [
    "Ordens de Compra     | Ordens de Venda",
    "---------------------|-----------------",
    "100 @ 9.99           | 100 @ 10.5",
    "200 @ 9.98           |",
    ]

    assert_book_invariants(eng)

def test_modify_renews_seq_on_priority_loss():

    eng = MatchingEngine()
        
    eng.submit_limit(Side.BUY, Decimal("10"), 100)
    eng.submit_limit(Side.BUY, Decimal("10"), 200)

    id = eng.book.bids[Decimal("10")].first.order_id
    seq = eng.book.bids[Decimal("10")].first.order_id

    eng.modify(id, new_qty=300)

    assert eng.book.bids[Decimal("10")].last.order_id == id
    assert eng.book.bids[Decimal("10")].last.seq > seq
    assert eng.book.bids[Decimal("10")].first.seq < eng.book.bids[Decimal("10")].last.seq

    assert_book_invariants(eng)

def test_modify_qty_increase_moves_to_tail():

    eng = MatchingEngine()
            
    eng.submit_limit(Side.BUY, Decimal("10"), 100)
    eng.submit_limit(Side.BUY, Decimal("10"), 200)

    id = eng.book.bids[Decimal("10")].first.order_id
    eng.modify(id, new_qty=300)

    assert eng.book.bids[Decimal("10")].first.qty == 200
    assert eng.book.bids[Decimal("10")].last.qty == 300
    assert eng.book.bids[Decimal("10")].total_qty == 500

    assert_book_invariants(eng)
from matching_engine.engine import Trade, MatchingEngine
from decimal import Decimal
from matching_engine.price_level import PriceLevel
from matching_engine.order import Side, OrderType, Order, PegReference
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

            if any(order.peg_reference is not None for order in queued):
                assert any(order.peg_reference is None for order in queued), (
                    f"level {price} on the {side.value} side holds only pegged orders"
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
    seq = eng.book.bids[Decimal("10")].first.seq

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

# ------------------------------------------ > Future review
def test_modify_qty_decrease_keeps_position():

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 100)
    eng.submit_limit(Side.BUY, Decimal("10"), 200)

    order_id = eng.book.bids[Decimal("10")].first.order_id
    seq_before = eng.book.bids[Decimal("10")].first.seq

    assert eng.modify(order_id, new_qty=50) == []

    # Reducing does not harm anyone behind, so the order keeps its place and its sequence.
    assert eng.book.bids[Decimal("10")].first.order_id == order_id
    assert eng.book.bids[Decimal("10")].first.seq == seq_before
    assert eng.book.bids[Decimal("10")].first.qty == 50
    assert eng.book.bids[Decimal("10")].total_qty == 250

    assert_book_invariants(eng)

def test_modify_crossing_price_executes():

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 100)
    eng.submit_limit(Side.SELL, Decimal("10.5"), 100)

    order_id = eng.book.bids[Decimal("10")].first.order_id

    # Raising the bid above the best offer makes the order marketable (D08).
    trades = eng.modify(order_id, new_price=Decimal("10.6"))

    assert [str(t) for t in trades] == ["Trade, price: 10.5, qty: 100"]
    assert eng.book.best_price(Side.BUY) is None
    assert eng.book.best_price(Side.SELL) is None
    assert eng.book.orders == {}

    assert_book_invariants(eng)

def test_modify_empties_old_level():

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 100)
    order_id = eng.book.bids[Decimal("10")].first.order_id

    eng.modify(order_id, new_price=Decimal("9"))

    assert Decimal("10") not in eng.book.bids
    assert Decimal("9") in eng.book.bids
    assert eng.book.bids[Decimal("9")].total_qty == 100

    assert_book_invariants(eng)

def test_modify_to_zero_cancels():

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 100)
    eng.submit_limit(Side.BUY, Decimal("9.99"), 200)

    order_id = eng.book.bids[Decimal("10")].first.order_id

    # D10: asking for zero quantity says the order is no longer wanted.
    assert eng.modify(order_id, new_qty=0) == []

    assert order_id not in eng.book.orders
    assert Decimal("10") not in eng.book.bids
    assert eng.book.bids[Decimal("9.99")].total_qty == 200

    assert_book_invariants(eng)

def test_modify_to_zero_with_new_price_cancels():

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 100)
    eng.submit_limit(Side.BUY, Decimal("9.99"), 200)

    order_id = eng.book.bids[Decimal("10")].first.order_id

    assert eng.modify(order_id, new_price=Decimal("9"), new_qty=0) == []

    assert order_id not in eng.book.orders
    assert Decimal("10") not in eng.book.bids

    # The price is ignored because there is no order left to reprice: no ghost level.
    assert Decimal("9") not in eng.book.bids

    assert_book_invariants(eng)

def test_modify_unknown_id_returns_none():

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 100)

    # None means "no such order", as opposed to [] which would mean "no trades".
    assert eng.modify(9999, new_qty=50) is None

    assert eng.book.bids[Decimal("10")].total_qty == 100

    assert_book_invariants(eng)

def test_modify_without_terms_raises():

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 100)
    order_id = eng.book.bids[Decimal("10")].first.order_id

    with pytest.raises(ValueError):
        eng.modify(order_id)

    assert_book_invariants(eng)

@pytest.mark.parametrize("invalid_price", ["0", "-3"])
def test_modify_rejects_invalid_price(invalid_price):

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 100)
    order_id = eng.book.bids[Decimal("10")].first.order_id

    with pytest.raises(ValueError):
        eng.modify(order_id, new_price=Decimal(invalid_price))

    # A rejected modification must leave the book exactly as it was.
    assert eng.book.bids[Decimal("10")].total_qty == 100
    assert order_id in eng.book.orders

    assert_book_invariants(eng)

def test_modify_rejects_negative_qty():

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 100)
    order_id = eng.book.bids[Decimal("10")].first.order_id

    with pytest.raises(ValueError):
        eng.modify(order_id, new_qty=-5)

    assert eng.book.bids[Decimal("10")].total_qty == 100

    assert_book_invariants(eng)


# Tests for submit_pegged
#-----------------------------------------------------\-----------------------------------------------------#

def test_submit_pegged_rests_at_reference():

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 200)
    eng.submit_limit(Side.BUY, Decimal("9.99"), 100)
    eng.submit_limit(Side.SELL, Decimal("10.5"), 100)

    # A passive peg never crosses, so it can only ever return an empty list.
    assert eng.submit_pegged(Side.BUY, PegReference.BID, 150) == []

    assert [line.rstrip() for line in str(eng.book).split("\n")] == [
        "Ordens de Compra     | Ordens de Venda",
        "---------------------|-----------------",
        "200 @ 10             | 100 @ 10.5",
        "150 @ 10             |",
        "100 @ 9.99           |",
    ]

    peg_id = max(eng.pegged_orders)

    # Registered in both indices: the book one makes it cancellable and lets _match delete it.
    assert peg_id in eng.book.orders
    assert eng.pegged_orders[peg_id] is eng.book.orders[peg_id]

    assert_book_invariants(eng)

def test_submit_pegged_on_offer_side():

    eng = MatchingEngine()

    eng.submit_limit(Side.SELL, Decimal("10.5"), 100)

    assert eng.submit_pegged(Side.SELL, PegReference.OFFER, 50) == []

    level = eng.book.offers[Decimal("10.5")]

    # The statement closes requirement 5 by saying a peg to the offer works the same way.
    assert level.first.qty == 100
    assert level.last.qty == 50
    assert level.last.peg_reference is PegReference.OFFER
    assert level.total_qty == 150

    assert_book_invariants(eng)

@pytest.mark.parametrize(
    "side, peg_reference",
    [
        (Side.BUY, PegReference.OFFER),
        (Side.SELL, PegReference.BID),
    ],
) # Run the same method (below) for the each tuple of the list above 

def test_submit_pegged_rejects_mismatched_reference(side, peg_reference):

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 200)
    eng.submit_limit(Side.SELL, Decimal("10.5"), 100)

    before = str(eng.book)

    # D12: only passive pegs exist. The rejection comes from Order.__post_init__.
    with pytest.raises(ValueError):
        eng.submit_pegged(side, peg_reference, 150)

    assert str(eng.book) == before
    assert eng.pegged_orders == {}

    assert_book_invariants(eng)

def test_submit_pegged_rejects_without_reference():

    eng = MatchingEngine()

    eng.submit_limit(Side.SELL, Decimal("10.5"), 100)

    # D13: nothing to derive a price from, so the order cannot exist.
    with pytest.raises(ValueError):
        eng.submit_pegged(Side.BUY, PegReference.BID, 150)

    assert eng.book.bids == {}
    assert eng.pegged_orders == {}

    assert_book_invariants(eng)

def test_submit_pegged_ignores_other_pegged_as_reference():

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 200)
    eng.submit_limit(Side.BUY, Decimal("9.99"), 100)
    eng.submit_pegged(Side.BUY, PegReference.BID, 150)

    # Cancelling the limit leaves level 10 holding nothing but the first pegged order. That
    # level is the one the reference must refuse to use. Without the repricing trigger the
    # stranded order stays at 10, which is what makes the state reachable in this test.
    limit_at_ten = eng.book.bids[Decimal("10")].first.order_id
    eng.cancel(limit_at_ten)

    eng.submit_pegged(Side.BUY, PegReference.BID, 50)

    first_peg, second_peg = (eng.pegged_orders[i] for i in sorted(eng.pegged_orders))

    # Both pegs sit at 9.99: the first followed the reference down when the limit at 10 was
    # cancelled, and the second read that same limit — never the peg already resting there.
    assert first_peg.price == Decimal("9.99")
    assert second_peg.price == Decimal("9.99")
    assert list(eng.book.bids) == [Decimal("9.99")]
    assert eng.book.bids[Decimal("9.99")].total_qty == 300

    assert_book_invariants(eng)

def test_pegged_is_consumed_like_any_order():

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 200)
    eng.submit_pegged(Side.BUY, PegReference.BID, 150)

    peg_id = max(eng.pegged_orders)

    # Once resting, a pegged order is an ordinary order: _match never reads peg_reference.
    assert [str(t) for t in eng.submit_market(Side.SELL, 350)] == [
        "Trade, price: 10, qty: 350"
    ]

    assert peg_id not in eng.book.orders
    assert eng.book.bids == {}

    assert_book_invariants(eng)

def test_pegged_follows_new_best_bid():

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 200)
    eng.submit_limit(Side.BUY, Decimal("9.99"), 100)
    eng.submit_limit(Side.SELL, Decimal("10.5"), 100)

    eng.submit_pegged(Side.BUY, PegReference.BID, 150)

    eng.submit_limit(Side.BUY, Decimal("10.1"), 300)

    assert [line.rstrip() for line in str(eng.book).split("\n")] == [
            "Ordens de Compra     | Ordens de Venda",
            "---------------------|-----------------",
            "150 @ 10.1           | 100 @ 10.5",
            "300 @ 10.1           |",
            "200 @ 10             |",
            "100 @ 9.99           |"
    ]

    assert_book_invariants(eng)

def test_pegged_keeps_seq_on_reprice():

    eng = MatchingEngine()

    eng.submit_limit(Side.BUY, Decimal("10"), 200)
    eng.submit_limit(Side.BUY, Decimal("9.99"), 100)
    eng.submit_limit(Side.SELL, Decimal("10.5"), 100)

    eng.submit_pegged(Side.BUY, PegReference.BID, 150)
    first_seqPeg = next(iter(eng.pegged_orders.values())).seq

    eng.submit_limit(Side.BUY, Decimal("10.1"), 300)
    seq_last = eng.book.bids[Decimal("10.1")].last.seq

    second_seqPeg = next(iter(eng.pegged_orders.values())).seq

    assert first_seqPeg == second_seqPeg 
    assert (seq_last > second_seqPeg and seq_last > first_seqPeg) == True

    assert_book_invariants(eng)

def test_pegged_follows_down_on_cancel():

    eng = MatchingEngine()
    
    eng.submit_limit(Side.BUY, Decimal("10"), 200)
    eng.submit_limit(Side.BUY, Decimal("9.99"), 100)
    eng.submit_limit(Side.SELL, Decimal("10.5"), 100)

    eng.submit_pegged(Side.BUY, PegReference.BID, 150)

    eng.submit_limit(Side.BUY, Decimal("10.1"), 300)
    id_cancel = eng.book.bids[Decimal("10.1")].last.order_id
    eng.cancel(id_cancel)

    assert [line.rstrip() for line in str(eng.book).split("\n")] == [
                "Ordens de Compra     | Ordens de Venda",
                "---------------------|-----------------",
                "200 @ 10             | 100 @ 10.5",
                "150 @ 10             |",
                "100 @ 9.99           |",
    ]

    assert Decimal("10.1") not in eng.book.bids 

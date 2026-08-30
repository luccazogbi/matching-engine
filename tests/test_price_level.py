from decimal import Decimal

from matching_engine.order import Order, Side, OrderType
from matching_engine.price_level import PriceLevel

def test_insert_orders(): 
    level = PriceLevel(Decimal(10.50))
    a = Order(side=Side.BUY, order_type=OrderType.LIMIT, qty=100, price=Decimal(10.50))
    b = Order(side=Side.BUY, order_type=OrderType.LIMIT, qty=200, price=Decimal(10.50))
    c = Order(side=Side.BUY, order_type=OrderType.LIMIT, qty=50, price=Decimal(10.50))

    level.last_insert(a)
    level.last_insert(b)
    level.last_insert(c)

    assert level.first is a
    assert level.last is c
    assert level.total_qty == 350

    assert a.next_order is b
    assert b.previous_order is a
    assert b.next_order is c
    assert c.previous_order is b

def test_remove_first():
    level = PriceLevel(Decimal(10.50))
    a = Order(side=Side.BUY, order_type=OrderType.LIMIT, qty=100, price=Decimal(10.50))
    b = Order(side=Side.BUY, order_type=OrderType.LIMIT, qty=200, price=Decimal(10.50))
    c = Order(side=Side.BUY, order_type=OrderType.LIMIT, qty=50, price=Decimal(10.50))
    level.last_insert(a)
    level.last_insert(b)
    level.last_insert(c)

    removed = level.remove_first()

    assert removed is a

    assert level.first is b
    assert level.last is c

    assert b.previous_order is None
    assert b.next_order is c
    assert c.previous_order is b

    assert a.previous_order is None
    assert a.next_order is None

    assert level.total_qty == 250

def test_remove_middle():
    level = PriceLevel(Decimal(10.50))
    a = Order(side=Side.BUY, order_type=OrderType.LIMIT, qty=100, price=Decimal(10.50))
    b = Order(side=Side.BUY, order_type=OrderType.LIMIT, qty=200, price=Decimal(10.50))
    c = Order(side=Side.BUY, order_type=OrderType.LIMIT, qty=50, price=Decimal(10.50))
    level.last_insert(a)
    level.last_insert(b)
    level.last_insert(c)

    removed = level.remove_order(b)

    assert removed is b

    assert level.first is a
    assert level.last is c

    assert a.next_order is c
    assert c.previous_order is a

    assert b.previous_order is None
    assert b.next_order is None

    assert level.total_qty == 150

def test_remove_last():
    level = PriceLevel(Decimal(10.50))
    a = Order(side=Side.BUY, order_type=OrderType.LIMIT, qty=100, price=Decimal(10.50))
    b = Order(side=Side.BUY, order_type=OrderType.LIMIT, qty=200, price=Decimal(10.50))
    c = Order(side=Side.BUY, order_type=OrderType.LIMIT, qty=50, price=Decimal(10.50))
    level.last_insert(a)
    level.last_insert(b)
    level.last_insert(c)

    removed = level.remove_order(c)

    assert removed is c

    assert level.first is a
    assert level.last is b

    assert a.next_order is b
    assert b.previous_order is a
    assert b.next_order is None

    assert c.previous_order is None
    assert c.next_order is None

    assert level.total_qty == 300

def test_remove_only_order():
    level = PriceLevel(Decimal(10.50))
    a = Order(side=Side.BUY, order_type=OrderType.LIMIT, qty=100, price=Decimal(10.50))
    level.last_insert(a)

    removed = level.remove_order(a)

    assert removed is a

    assert level.first is None
    assert level.last is None

    assert a.previous_order is None
    assert a.next_order is None

    assert level.total_qty == 0

def test_remove_from_empty_level():
    level = PriceLevel(Decimal(10.50))
    removed = level.remove_first()

    assert removed is None
    assert level.first is None
    assert level.last is None
    assert level.total_qty == 0

def test_fill_first_partial():

    level = PriceLevel(Decimal("10.00"))

    first_order = Order(Side.SELL, OrderType.LIMIT, 100, Decimal("10.00"))
    second_order = Order(Side.SELL, OrderType.LIMIT, 200, Decimal("10.00"))

    level.last_insert(first_order)
    level.last_insert(second_order)

    removed = level.fill_first(50)

    assert removed is None
    assert level.first is first_order
    assert first_order.qty == 50
    assert level.total_qty == 250
    assert level.last is second_order

def test_fill_first_removes_fully_filled_order():
    level = PriceLevel(Decimal("10.00"))

    first_order = Order(
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        qty=100,
        price=Decimal("10.00")
    )

    second_order = Order(
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        qty=200,
        price=Decimal("10.00")
    )

    level.last_insert(first_order)
    level.last_insert(second_order)

    removed = level.fill_first(100)

    assert removed is first_order
    assert level.first is second_order
    assert second_order.previous_order is None
    assert level.total_qty == 200
    assert first_order.previous_order is None
    assert first_order.next_order is None

def test_fill_first_removes_only_order():
    level = PriceLevel(Decimal("10.00"))

    order = Order(
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        qty=100,
        price=Decimal("10.00")
    )

    level.last_insert(order)

    removed = level.fill_first(100)

    assert removed is order
    assert level.first is None
    assert level.last is None
    assert level.total_qty == 0

def make_orders(how_many):
    
    return [
        Order(side=Side.BUY, order_type=OrderType.LIMIT, qty=100, price=Decimal("10"))
        for _ in range(how_many)
    ]

def queued(level):
    
    out = []
    current = level.first

    while current is not None:
        out.append(current)
        current = current.next_order

    return out

def test_insert_by_seq_into_empty_level():
    level = PriceLevel(Decimal("10"))
    a, = make_orders(1)

    level.insert_by_seq(a)

    assert level.first is a
    assert level.last is a
    assert a.previous_order is None
    assert a.next_order is None
    assert level.total_qty == 100

def test_insert_by_seq_as_new_head():
    level = PriceLevel(Decimal("10"))
    a, b = make_orders(2)

    level.insert_by_seq(b)
    level.insert_by_seq(a)

    assert queued(level) == [a, b]
    assert level.first is a
    assert level.last is b
    assert a.previous_order is None
    assert b.previous_order is a
    assert level.total_qty == 200

def test_insert_by_seq_in_the_middle():
    level = PriceLevel(Decimal("10"))
    a, b, c = make_orders(3)

    level.insert_by_seq(a)
    level.insert_by_seq(c)
    level.insert_by_seq(b)

    assert queued(level) == [a, b, c]
    assert level.first is a
    assert level.last is c
    assert a.next_order is b
    assert c.previous_order is b
    assert level.total_qty == 300

def test_insert_by_seq_at_tail():
    level = PriceLevel(Decimal("10"))
    a, b = make_orders(2)

    level.insert_by_seq(a)
    level.insert_by_seq(b)

    assert queued(level) == [a, b]
    assert level.last is b
    assert b.next_order is None
    assert level.total_qty == 200

def test_insert_by_seq_keeps_queue_sorted():
    level = PriceLevel(Decimal("10"))
    a, b, c, d = make_orders(4)

    for order in (c, a, d, b):
        level.insert_by_seq(order)

    assert queued(level) == [a, b, c, d]

    walked_back = []
    current = level.last

    while current is not None:
        walked_back.append(current)
        current = current.previous_order

    assert walked_back == [d, c, b, a]
    assert level.total_qty == 400

def test_insert_by_seq_matches_last_insert_when_in_order():
    by_seq = PriceLevel(Decimal("10"))
    by_tail = PriceLevel(Decimal("10"))
    a, b, c = make_orders(3)

    for order in (a, b, c):
        by_seq.insert_by_seq(order)

    d, e, f = make_orders(3)

    for order in (d, e, f):
        by_tail.last_insert(order)

    assert [o.qty for o in queued(by_seq)] == [o.qty for o in queued(by_tail)]
    assert by_seq.total_qty == by_tail.total_qty

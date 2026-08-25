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

    # Tests
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

    # Tests 
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

    # Tests
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

    # Tests 
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

    # Tests 
    assert removed is a

    assert level.first is None
    assert level.last is None

    assert a.previous_order is None
    assert a.next_order is None

    assert level.total_qty == 0
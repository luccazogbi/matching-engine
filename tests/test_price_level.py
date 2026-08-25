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




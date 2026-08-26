from decimal import Decimal

from matching_engine.order import Order, OrderType, Side


def test_side_opposite():
    assert Side.BUY.opposite is Side.SELL
    assert Side.SELL.opposite is Side.BUY
    assert Side.BUY.opposite.opposite is Side.BUY


def test_limit_order_initial_state():
    order = Order(
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=100,
        price=Decimal("10.50")
    )

    assert order.price == Decimal("10.50")
    assert order.previous_order is None
    assert order.next_order is None


def test_order_arrival_sequence():
    first_order = Order(
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=100,
        price=Decimal("10.50")
    )

    second_order = Order(
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=200,
        price=Decimal("10.50")
    )

    assert first_order.seq < second_order.seq
    assert first_order.order_id != second_order.order_id
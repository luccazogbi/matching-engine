from decimal import Decimal
from itertools import count

from matching_engine.cli import execute_command
from matching_engine.engine import MatchingEngine
from matching_engine import order as order_module
import pytest


@pytest.fixture(autouse=True)
def reset_counters():
   
    order_module._id_counter = count(1)
    order_module._seq_counter = count(1)


def run(engine, *commands):

    lines = []

    for command in commands:
        lines += execute_command(engine, command)

    return lines


def test_limit_reports_creation_with_identifier():
    eng = MatchingEngine()

    assert run(eng, "limit buy 10 100") == ["Order created: buy 100 @ 10 1"]


def test_creation_line_reports_submitted_quantity():
    eng = MatchingEngine()

    lines = run(eng, "limit sell 10 100", "limit buy 10 100")

    assert lines[1] == "Order created: buy 100 @ 10 2"
    assert lines[2] == "Trade, price: 10, qty: 100"


def test_market_reports_only_trades():
    eng = MatchingEngine()

    assert run(eng, "limit sell 20 100", "market buy 150") == [
        "Order created: sell 100 @ 20 1",
        "Trade, price: 20, qty: 100",
    ]


def test_print_book():
    eng = MatchingEngine()

    lines = run(eng, "limit buy 10 200", "limit sell 10.5 100", "print book")

    assert [line.rstrip() for line in lines[2:]] == [
        "Ordens de Compra     | Ordens de Venda",
        "---------------------|-----------------",
        "200 @ 10             | 100 @ 10.5",
    ]


def test_requirement_five_sequence():
    eng = MatchingEngine()

    run(eng, "limit buy 10 200", "limit buy 9.99 100", "limit sell 10.5 100")

    assert run(eng, "peg bid buy 150")[0] == "Order created: buy 150 @ 10 4"

    assert [line.rstrip() for line in run(eng, "print book")] == [
        "Ordens de Compra     | Ordens de Venda",
        "---------------------|-----------------",
        "200 @ 10             | 100 @ 10.5",
        "150 @ 10             |",
        "100 @ 9.99           |",
    ]

    run(eng, "limit buy 10.1 300")

    assert [line.rstrip() for line in run(eng, "print book")] == [
        "Ordens de Compra     | Ordens de Venda",
        "---------------------|-----------------",
        "150 @ 10.1           | 100 @ 10.5",
        "300 @ 10.1           |",
        "200 @ 10             |",
        "100 @ 9.99           |",
    ]


def test_cancel_reports_and_removes():
    eng = MatchingEngine()

    assert run(eng, "limit buy 10 100", "cancel order 1") == [
        "Order created: buy 100 @ 10 1",
        "Order cancelled",
    ]
    assert eng.book.bids == {}


def test_cancel_unknown_id_is_an_error():
    eng = MatchingEngine()

    assert run(eng, "cancel order 99") == ["Error: no order with id 99"]


def test_modify_changes_price_and_reports():
    eng = MatchingEngine()

    lines = run(eng, "limit buy 10 200", "modify order 1 price 9.98", "print book")

    assert lines[1] == "Order modified"
    assert [line.rstrip() for line in lines[2:]] == [
        "Ordens de Compra     | Ordens de Venda",
        "---------------------|-----------------",
        "200 @ 9.98           |",
    ]


def test_modify_quantity_only():
    eng = MatchingEngine()

    run(eng, "limit buy 10 200", "modify order 1 qty 50")

    assert eng.book.bids[Decimal("10")].total_qty == 50


@pytest.mark.parametrize("command, expected", [
    ("dance buy 10 100", "Error: unknown command: dance"),
    ("limit up 10 100", "Error: side must be buy or sell, got up"),
    ("limit buy dez 100", "Error: price must be a number, got dez"),
    ("limit buy 10 muitas", "Error: quantity must be a whole number, got muitas"),
    ("limit buy 10", "Error: usage: limit <buy|sell> <price> <qty>"),
    ("peg middle buy 100", "Error: peg reference must be bid or offer, got middle"),
    ("cancel 1", "Error: usage: cancel order <id>"),
    ("print trades", "Error: usage: print book | print orders"),
    ("print", "Error: usage: print book | print orders"),
])
def test_malformed_input_never_raises(command, expected):
    eng = MatchingEngine()

    assert execute_command(eng, command) == [expected]


def test_empty_line_is_ignored():
    eng = MatchingEngine()

    assert execute_command(eng, "   ") == []


def test_engine_rejection_becomes_an_error_line():
    eng = MatchingEngine()

    assert run(eng, "peg bid buy 150") == [
        "Error: no reference price available for the bid"
    ]
    assert run(eng, "limit buy 10 100") == ["Order created: buy 100 @ 10 1"]


def test_print_orders_lists_identifiers():
    eng = MatchingEngine()

    run(eng, "limit buy 10 200", "limit sell 10.5 100", "peg bid buy 150")

    assert run(eng, "print orders") == [
        "1 | buy 200 @ 10",
        "2 | sell 100 @ 10.5",
        "3 | buy 150 @ 10 (pegged to the bid)",
    ]


def test_print_orders_reflects_cancellation():
    eng = MatchingEngine()

    run(eng, "limit buy 10 200", "limit buy 9.99 100", "cancel order 1")

    assert run(eng, "print orders") == ["2 | buy 100 @ 9.99"]


def test_print_orders_on_an_empty_book():
    eng = MatchingEngine()

    assert run(eng, "print orders") == ["No resting orders."]


def test_clear_wipes_the_screen_but_not_the_book():
    eng = MatchingEngine()

    run(eng, "limit buy 10 200")

    assert execute_command(eng, "clear") == ["\033[H\033[2J\033[3J"]

    assert run(eng, "print orders") == ["1 | buy 200 @ 10"]


def test_clear_takes_no_arguments():
    eng = MatchingEngine()

    assert execute_command(eng, "clear all") == ["Error: usage: clear"]

"""Text interface for the matching engine.

The engine knows nothing about text: it takes enums and Decimal values and returns objects.
This module is the only place that parses input and formats output, which is what allows the
two to be tested and changed independently.

execute_command runs one command and returns the lines to print instead of printing them, so
a test can assert on the output without capturing standard output. main() is the only function
that touches input() and print().
"""

from decimal import Decimal, InvalidOperation

from .engine import MatchingEngine
from .order import Side, PegReference, format_price


def execute_command(engine: MatchingEngine, command: str) -> list[str]:
    """Run one command line and return what should be printed.

    Never raises. A malformed command, an unknown verb or a rejection from the engine all
    come back as an error line, so the read loop survives any input.
    """

    tokens = command.split()

    if not tokens:
        return []

    try:
        return _dispatch(engine, tokens)

    except ValueError as error:
        return [f"Error: {error}"]


def _dispatch(engine: MatchingEngine, tokens: list[str]) -> list[str]:

    verb = tokens[0].lower()

    if verb == "limit":
        return _limit(engine, tokens)

    if verb == "market":
        return _market(engine, tokens)

    if verb == "peg":
        return _pegged(engine, tokens)

    if verb == "cancel":
        return _cancel(engine, tokens)

    if verb == "modify":
        return _modify(engine, tokens)

    if verb == "print":
        return _print(engine, tokens)

    if verb == "clear":
        return _clear(tokens)

    raise ValueError(f"unknown command: {verb}")


# ------------------------------------------------------------------ commands

def _limit(engine: MatchingEngine, tokens: list[str]) -> list[str]:

    _expect(tokens, 4, "limit <buy|sell> <price> <qty>")

    side = _read_side(tokens[1])
    price = _read_price(tokens[2])
    qty = _read_qty(tokens[3])

    trades = engine.submit_limit(side, price, qty)

    return _created_line(engine, qty) + _trade_lines(trades)


def _market(engine: MatchingEngine, tokens: list[str]) -> list[str]:

    _expect(tokens, 3, "market <buy|sell> <qty>")

    side = _read_side(tokens[1])
    qty = _read_qty(tokens[2])

    # No creation line: a market order has no price to report and never rests, so there is
    # nothing to refer to afterwards. Its whole visible effect is the trades it produces.
    return _trade_lines(engine.submit_market(side, qty))


def _pegged(engine: MatchingEngine, tokens: list[str]) -> list[str]:

    _expect(tokens, 4, "peg <bid|offer> <buy|sell> <qty>")

    peg_reference = _read_peg_reference(tokens[1])
    side = _read_side(tokens[2])
    qty = _read_qty(tokens[3])

    trades = engine.submit_pegged(side, peg_reference, qty)

    # The price shown is the reference the engine derived, which is the only way the user
    # learns where the order landed without printing the book.
    return _created_line(engine, qty) + _trade_lines(trades)


def _cancel(engine: MatchingEngine, tokens: list[str]) -> list[str]:

    _expect(tokens, 3, "cancel order <id>")

    if tokens[1].lower() != "order":
        raise ValueError("usage: cancel order <id>")

    order_id = _read_order_id(tokens[2])

    if engine.cancel(order_id) is None:
        raise ValueError(f"no order with id {order_id}")

    return ["Order cancelled"]


def _modify(engine: MatchingEngine, tokens: list[str]) -> list[str]:

    usage = "modify order <id> [price <price>] [qty <qty>]"

    # The statement does not specify a syntax for this command. Named pairs were chosen so
    # that changing only the quantity does not require a placeholder for the price.
    if len(tokens) < 5 or tokens[1].lower() != "order" or len(tokens[3:]) % 2 != 0:
        raise ValueError(f"usage: {usage}")

    order_id = _read_order_id(tokens[2])
    new_price = None
    new_qty = None

    terms = tokens[3:]

    for key, value in zip(terms[::2], terms[1::2]):

        if key.lower() == "price":
            new_price = _read_price(value)

        elif key.lower() == "qty":
            new_qty = _read_qty(value)

        else:
            raise ValueError(f"usage: {usage}")

    trades = engine.modify(order_id, new_price, new_qty)

    # None means the identifier does not exist; an empty list means it does and no trade came
    # out of the change. The two cannot be collapsed into one message.
    if trades is None:
        raise ValueError(f"no order with id {order_id}")

    return ["Order modified"] + _trade_lines(trades)


def _print(engine: MatchingEngine, tokens: list[str]) -> list[str]:

    _expect(tokens, 2, "print book | print orders")

    what = tokens[1].lower()

    if what == "book":
        return str(engine.book).split("\n")

    if what == "orders":
        return _order_lines(engine)

    raise ValueError("usage: print book | print orders")


def _clear(tokens: list[str]) -> list[str]:
    """Wipe the screen without touching the book.

    Returned as a line rather than done here, so execute_command stays free of side effects
    and can still be tested by comparing its output. The escape sequence moves the cursor
    home, clears the visible screen and clears the scrollback, in that order.
    """

    _expect(tokens, 1, "clear")

    return ["\033[H\033[2J\033[3J"]


def _order_lines(engine: MatchingEngine) -> list[str]:
    """List every resting order with its identifier.

    The book display shows quantity and price but no identifiers, because its format is the
    one fixed by the statement and comparing against it is how conformance is checked. Yet
    the identifier is announced only once, when the order is created, and it is what cancel
    and modify take -- so without this command the user has to have written it down.
    """

    if not engine.book.orders:
        return ["No resting orders."]

    lines = []

    for order_id in sorted(engine.book.orders):

        order = engine.book.orders[order_id]

        line = (
            f"{order_id} | {order.side.value} {order.qty} @ "
            f"{format_price(order.price)}"
        )

        if order.peg_reference is not None:
            line += f" (pegged to the {order.peg_reference.value})"

        lines.append(line)

    return lines


# ------------------------------------------------------------------ parsing

def _expect(tokens: list[str], count: int, usage: str) -> None:

    if len(tokens) != count:
        raise ValueError(f"usage: {usage}")


def _read_side(token: str) -> Side:

    # The enum values are the command words themselves, so the lookup is the validation.
    try:
        return Side(token.lower())

    except ValueError:
        raise ValueError(f"side must be buy or sell, got {token}")


def _read_peg_reference(token: str) -> PegReference:

    try:
        return PegReference(token.lower())

    except ValueError:
        raise ValueError(f"peg reference must be bid or offer, got {token}")


def _read_price(token: str) -> Decimal:

    # Built from the token as written, never through float, so 10.1 stays 10.1 (D01).
    try:
        return Decimal(token)

    except InvalidOperation:
        raise ValueError(f"price must be a number, got {token}")


def _read_qty(token: str) -> int:

    try:
        return int(token)

    except ValueError:
        raise ValueError(f"quantity must be a whole number, got {token}")


def _read_order_id(token: str) -> int:

    try:
        return int(token)

    except ValueError:
        raise ValueError(f"order id must be a whole number, got {token}")


# ------------------------------------------------------------------ output

def _created_line(engine: MatchingEngine, qty: int) -> list[str]:

    # qty is passed in rather than read from the order: by the time the call returns, the
    # order's own qty is what is left after matching, not what was submitted.
    order = engine.last_accepted_order

    return [
        f"Order created: {order.side.value} {qty} @ "
        f"{format_price(order.price)} {order.order_id}"
    ]


def _trade_lines(trades) -> list[str]:

    return [str(trade) for trade in trades]


def main() -> None:

    engine = MatchingEngine()

    while True:

        try:
            command = input(">> ")

        except EOFError:
            break

        if command.strip().lower() in ("quit", "exit"):
            break

        for line in execute_command(engine, command):
            print(line)


if __name__ == "__main__":
    main()

from decimal import Decimal, InvalidOperation

from .engine import MatchingEngine
from .order import Side, PegReference, format_price


def execute_command(engine: MatchingEngine, command: str) -> list[str]:
   
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

    return _trade_lines(engine.submit_market(side, qty))


def _pegged(engine: MatchingEngine, tokens: list[str]) -> list[str]:

    _expect(tokens, 4, "peg <bid|offer> <buy|sell> <qty>")

    peg_reference = _read_peg_reference(tokens[1])
    side = _read_side(tokens[2])
    qty = _read_qty(tokens[3])

    trades = engine.submit_pegged(side, peg_reference, qty)

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

    _expect(tokens, 1, "clear")

    return ["\033[H\033[2J\033[3J"]


def _order_lines(engine: MatchingEngine) -> list[str]:
   
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

def _expect(tokens: list[str], count: int, usage: str) -> None:

    if len(tokens) != count:
        raise ValueError(f"usage: {usage}")


def _read_side(token: str) -> Side:

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

def _created_line(engine: MatchingEngine, qty: int) -> list[str]:

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

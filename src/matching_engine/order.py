from __future__ import annotations

from enum import Enum 
from dataclasses import dataclass, field
from decimal import Decimal
from itertools import count

"""
    Enum: é uma classe especial usada para 
    criar um conjunto de constantes nomeadas vinculadas a valores únicos

"""
class Side(Enum):
    BUY = "buy"
    SELL = "sell"

    
    @property
    def opposite(self):

        if self is Side.BUY:
            return Side.SELL
        
        return Side.BUY
        

class OrderType(Enum):
    LIMIT = "limit"
    MARKET = "market"

class PegReference(Enum):
    BID = "bid"
    OFFER = "offer"

# Counter variables (put "_" because it indicates that belongs only to this module "order.py")
_id_counter = count(1)
_seq_counter = count(1)

# it generates some methods automatically for us (very often implemented when the class is used to store and transport data)
@dataclass 
class Order:

    order_id: int = field(init=False) # Don't receive data from the constructor
    seq: int = field(init=False)
    side: Side
    order_type: OrderType 
    qty: int
    price: Decimal | None = None
    peg_reference: PegReference | None = None
    previous_order: Order | None = None
    next_order: Order | None = None

    def __post_init__(self):
        validate_order_terms(
            self.order_type,
            self.price,
            self.qty,
            self.side,
            self.peg_reference,
        )
        self.order_id = next(_id_counter)
        self.seq = next(_seq_counter)

    def renew_seq(self):
        self.seq = next(_seq_counter)

def  validate_order_terms(
    order_type: OrderType,
    price: Decimal | None,
    qty: int,
    side: Side,
    peg_reference: PegReference | None,
) -> None:

    """Enforce the invariants every order must satisfy, wherever it comes from.

    Called from Order.__post_init__, which covers every creation path, and from
    MatchingEngine.modify, which is the only operation that changes these values after
    the order already exists.

    Every rule here is a property of the order by itself. Whether the book can currently
    supply a reference price for a pegged order is a property of the book, not of the order,
    so the engine checks that one — this function never looks at the book.
    """

    if qty <= 0:
        raise ValueError(f"quantity must be positive, got {qty}")

    if order_type is OrderType.LIMIT:
        if price is None:
            raise ValueError("a limit order requires a price")

        if price <= 0:
            raise ValueError(f"a limit order price must be positive, got {price}")

    elif order_type is OrderType.MARKET and price is not None:
        raise ValueError("a market order must not carry a price")

    # An ordinary order carries no peg reference and may take either side, so nothing below
    # applies to it.
    if peg_reference is None:
        return

    if order_type is OrderType.MARKET:
        raise ValueError("a market order must not carry a peg reference")

    # D12: only passive pegs exist. A buy follows the bid, a sell follows the offer. The
    # opposite pairings would rest through the other side of the book and execute on arrival.
    expected_side = Side.BUY if peg_reference is PegReference.BID else Side.SELL

    if side is not expected_side:
        raise ValueError(
            f"a peg to the {peg_reference.value} requires a {expected_side.value} order, "
            f"got {side.value}"
        )


def format_price(price: Decimal) -> str:
    return f"{price.normalize():f}"

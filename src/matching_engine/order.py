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
        validate_order_terms(self.order_type, self.price, self.qty)
        self.order_id = next(_id_counter)
        self.seq = next(_seq_counter)

    def renew_seq(self):
        self.seq = next(_seq_counter)

def  validate_order_terms(
    order_type: OrderType,
    price: Decimal | None,
    qty: int,
) -> None:

    """Enforce the two invariants every order must satisfy, wherever it comes from.

    Called from Order.__post_init__, which covers every creation path, and from
    MatchingEngine.modify, which is the only operation that changes these values after
    the order already exists.
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


def format_price(price: Decimal) -> str:
    return f"{price.normalize():f}"


# Good approach to implement in each module, because it executes a code block only when this file is executed directly
if __name__ == "__main__": 

    a = Order(
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=100,
        price=Decimal("10.50")
    )

    b = Order(
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=200,
        price=Decimal("10.50")
    )

    c = Order(
            side=Side.BUY,
            order_type=OrderType.MARKET,
            qty=200
        )
    print(a)
    print(b)
    print(c)
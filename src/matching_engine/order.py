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
        self.order_id = next(_id_counter)
        self.seq = next(_seq_counter)

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
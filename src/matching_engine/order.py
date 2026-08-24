from __future__ import annotations
from enum import Enum 
from dataclasses import dataclass
from decimal import Decimal

"""
    Enum: é uma classe especial usada para 
    criar um conjunto de constantes nomeadas vinculadas a valores únicos

"""
class Side(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    LIMIT = "limit"
    MARKET = "market"

class PegReference(Enum):
    BID = "bid"
    SELL = "sell"

@dataclass 
class Order:
    order_id: int 
    side: Side
    order_type: OrderType 
    qty: int
    seq: int 
    price: Decimal | None = None
    peg_reference: PegReference | None = None
    anterior: Order | None = None
    proxima: Order | None = None

o = Order(order_id=1, side=Side.BUY, order_type=OrderType.LIMIT, qty=100, price=Decimal("10.50"), seq=0)
print(o)

m = Order(order_id=2, side=Side.SELL, order_type=OrderType.MARKET,
          qty=150, seq=1)
print(m)

# 3 — nasce solta
print(o.anterior, o.proxima)
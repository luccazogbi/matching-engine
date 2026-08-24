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
    order_id:
    side: Side
    order_type: OrderType 
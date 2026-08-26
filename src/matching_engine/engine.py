from dataclasses import dataclass, field
from decimal import Decimal

@dataclass
class Trade:

    price: Decimal
    qty: int 

    def __str__(self) -> str:
        return f"Trade, price: {self.price.normalize():f}, qty: {self.qty}"

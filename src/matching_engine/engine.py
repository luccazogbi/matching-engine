from dataclasses import dataclass
from decimal import Decimal
from .order_book import OrderBook
from .order import Side, Order, OrderType


@dataclass
class Trade:

    price: Decimal
    qty: int 

    def __str__(self) -> str:
        return f"Trade, price: {self.price.normalize():f}, qty: {self.qty}"

class MatchingEngine:

    def __init__(self):
        self.book = OrderBook()

    # It'll submit the limit order
    def submit_limit(self,
            side: Side,
            price: Decimal,
            qty: int
    ) -> list[Trade]:

        # Create the limit order (aggresive)
        order = Order(side=side, order_type=OrderType.LIMIT, qty=qty, price=price)
        list_trades = []

        while order.qty > 0: 

            opposite_price = self.book.best_price(side.opposite)        

            if opposite_price is None:
                break

            # BUY  → match when offer <= limit price (BUY price)
            # SELL → match when bid >= limit price (SELL Price)

            if side is Side.BUY:
                price_is_acceptable = opposite_price <= price
                
            else:
                price_is_acceptable = opposite_price >= price

            if not price_is_acceptable:
                break

            # Obtain all the PriceLevels from the other side compared to the top created order
            opposite_levels = self.book.levels_for(side.opposite)

            # Level where it's going to have the match
            matching_level = opposite_levels[opposite_price]
            level_trade_qty = 0

            while order.qty > 0 and matching_level.first is not None: 

                # MatchingEngine dealing with the agressive order
                trade_qty = min(order.qty, matching_level.first.qty)
                order.qty -= trade_qty

                # PriceLevel dealing with the FIFO consumption 
                first_consumed = matching_level.fill_first(trade_qty)
                level_trade_qty += trade_qty

                if first_consumed is not None:
                    del self.book.orders[first_consumed.order_id]

            # Explained: Put condition here because I did a test putting just a PriceLevel (with no orders)
            # and it was showing "Trade, price: 20, qty: 0 ".
            if level_trade_qty > 0:
                list_trades.append(Trade(opposite_price, level_trade_qty))    

            # If the last matching level is empty
            if matching_level.first is None:
                self.book.remove_empty_level(side.opposite, opposite_price)

        # If there's any left over inside order.qty
        if order.qty > 0:

            level_after_matching = self.book.get_or_create_level(side, price)
            level_after_matching.last_insert(order)
            self.book.orders[order.order_id] = order

        return list_trades

if __name__ == "__main__": 

        
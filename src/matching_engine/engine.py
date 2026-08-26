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

            opposite_levels = self.book.levels_for(side.opposite)

            # Level where it's going to have the match
            matching_level = opposite_levels[opposite_price]
            level_trade_qty = 0

            while order.qty > 0 and matching_level.first is not None: 

                # Picking the first element
                match = matching_level.first

                trade_qty = min(order.qty, match.qty)

                # When I subtract the lowest value from trade_qty, I'll have 0
                order.qty -= trade_qty
                match.qty -= trade_qty
                matching_level.total_qty -= trade_qty

                level_trade_qty += trade_qty

                if match.qty == 0:
                    matching_level.remove_first()
                    del self.book.orders[match.order_id]

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

        

        


        
from dataclasses import dataclass
from decimal import Decimal
from .order_book import OrderBook
from .order import Side, Order, OrderType
from .price_level import PriceLevel



@dataclass
class Trade:

    price: Decimal
    qty: int 

    # It defines how Trade'll be converted into string
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

        # Create the limit order (aggresive) based on what it was given 
        limit_order = Order(side=side, order_type=OrderType.LIMIT, qty=qty, price=price)
        list_trades = self._match(limit_order)

        # If there's any left over inside order.qty (Only for OrderType.LIMIT)
        if limit_order.qty > 0:

            level_after_matching = self.book.get_or_create_level(limit_order.side, limit_order.price)
            level_after_matching.last_insert(limit_order)
            self.book.orders[limit_order.order_id] = limit_order

        return list_trades

    def submit_market(self,
        side: Side,
        qty: int 
    ) -> list[Trade]:

        market_order = Order(side=side, order_type=OrderType.MARKET, qty=qty)
        return self._match(market_order)

    def _match(self,
        order: Order
    ) -> list[Trade]:

        list_trades = []

        while order.qty > 0: 

            opposite_price = self.book.best_price(order.side.opposite)        

            if opposite_price is None:
                break

            # BUY  → match when offer <= limit price (BUY price)
            # SELL → match when bid >= limit price (SELL Price)

            if order.order_type is OrderType.LIMIT:
                # Only for OrderType.LIMIT
                if order.side is Side.BUY:
                    price_is_acceptable = opposite_price <= order.price
                    
                else:
                    price_is_acceptable = opposite_price >= order.price

                if not price_is_acceptable:
                    break

            # Obtain all the PriceLevels from the other side 
            opposite_levels = self.book.levels_for(order.side.opposite)

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
                self.book.remove_empty_level(order.side.opposite, opposite_price)

        return list_trades
         
from dataclasses import dataclass
from decimal import Decimal
from .order_book import OrderBook
from .order import Side, Order, OrderType, format_price, validate_order_terms
from .price_level import PriceLevel



@dataclass
class Trade:

    price: Decimal
    qty: int 

    # It defines how Trade'll be converted into string
    def __str__(self) -> str:
        return f"Trade, price: {format_price(self.price)}, qty: {self.qty}"

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

    # Method to detach the order of a level without destroying it
    def _detach(self,
         order: Order
    ):

        level = self.book.levels_for(order.side)[order.price]
        level.remove_order(order)

        if level.first is None:
            self.book.remove_empty_level(order.side, order.price)

        return level
        
    def cancel(self, 
        order_id: int
    ):

        # Important thign: The order is removed from the PriceLevel, book.bids/book.offers, but not from book.bid_prices or book.offer_prices. This
        # occurs because of lazy deletion and that's ok.
        order_to_remove = self.book.orders.get(order_id) # Is's returning the Order object with "order_id"

        # If It's None, there's no order. In the other case, there's and we need to take out from orders after removing it 
        if order_to_remove is None:
            return None

        self._detach(order_to_remove)
        del self.book.orders[order_to_remove.order_id] # Removing from the dict responsible for store order with its IDs

        return order_to_remove

    def modify(self,
        order_id: int,
        new_price: Decimal | None = None,
        new_qty: int | None = None
    ) -> list[Trade] | None:

        order_to_mod = self.book.orders.get(order_id)

        if order_to_mod is None:
            return None

        if new_price is None and new_qty is None:
            raise ValueError("nothing to modify: provide a price, a quantity, or both")

        # In the verification below, it doens't matter what is the new_price. If the new_qty is 0, it'll 
        # cancel the order with order_id. Don't know if it's correct from the advisor view, but I though 
        # about poiting an error because a modify() method with valid order_id, new_price being different 
        # from the original price, and a new_qty equals to zero, it's strange. In my point, it's like 
        # asking to create an order in the new price and after this, delete it. So I put in the way below:
        if new_qty == 0:
            self.cancel(order_id)
            return []

        # Kind of 
        validate_order_terms(
            order_to_mod.order_type,
            new_price if new_price is not None else order_to_mod.price,
            new_qty if new_qty is not None else order_to_mod.qty,
        )

        # Stays in the same price level
        if new_price is None:

            if new_qty < order_to_mod.qty:
                self.book.levels_for(order_to_mod.side)[order_to_mod.price].adjust_qty(order_to_mod, new_qty)
                return []

            elif new_qty > order_to_mod.qty: # new_qty is greater than old_qty
                self._detach(order_to_mod)
                order_to_mod.qty = new_qty
                level = self.book.get_or_create_level(order_to_mod.side, order_to_mod.price)
                order_to_mod.renew_seq()
                level.last_insert(order_to_mod)
                return []

            elif new_qty == order_to_mod.qty:
                return []

        # Going to another price level
        else: 

            # Remove order from initial level (returns the level, but it's not gonna to be used here) 
            self._detach(order_to_mod) 

            # Putting inside another level. Its price is updated, id maintained.  
            order_to_mod.price = new_price

            if new_qty is not None:
                order_to_mod.qty = new_qty

            trades_after_changing = self._match(order_to_mod) # Verifies if when changing the level, it could be possible to match another order.

            # With this, it creates a level if it wasn't any match
            if order_to_mod.qty > 0:

                level_after_matching = self.book.get_or_create_level(order_to_mod.side, order_to_mod.price)
                order_to_mod.renew_seq()
                level_after_matching.last_insert(order_to_mod)

            else:

                del self.book.orders[order_id]

        return trades_after_changing 

        
from dataclasses import dataclass
from decimal import Decimal
from .order_book import OrderBook
from .order import Side, Order, OrderType, format_price, validate_order_terms, PegReference
from .price_level import PriceLevel



@dataclass
class Trade:

    price: Decimal
    qty: int 

    def __str__(self) -> str:
        return f"Trade, price: {format_price(self.price)}, qty: {self.qty}"

class MatchingEngine:

    def __init__(self):
        self.book = OrderBook()
        self.pegged_orders = {}
        self.last_accepted_order = None

    def submit_limit(self,
        side: Side,
        price: Decimal,
        qty: int
    ) -> list[Trade]:

        limit_order = Order(side=side, order_type=OrderType.LIMIT, qty=qty, price=price)
        self.last_accepted_order = limit_order
        list_trades = self._match(limit_order)

        if limit_order.qty > 0:

            level_after_matching = self.book.get_or_create_level(limit_order.side, limit_order.price)
            level_after_matching.last_insert(limit_order)
            self.book.orders[limit_order.order_id] = limit_order

        self._reprice_pegged()
        return list_trades

    def submit_market(self,
        side: Side,
        qty: int 
    ) -> list[Trade]:

        market_order = Order(side=side, order_type=OrderType.MARKET, qty=qty)
        self.last_accepted_order = market_order
        trades = self._match(market_order)
        self._reprice_pegged()

        return trades

    def submit_pegged(self, 
        side: Side,
        peg_reference: PegReference, 
        qty: int,

        ) -> list[Trade]:

        reference_pri = self.book.reference_price(peg_reference)

        if reference_pri is None:
            raise ValueError(f"no reference price available for the {peg_reference.value}")

        pegged_order = Order(side=side, order_type=OrderType.LIMIT, qty=qty, price=reference_pri, peg_reference=peg_reference)

        reference_level = self.book.levels_for(side)[reference_pri]
        reference_level.last_insert(pegged_order) # 
        self.book.orders[pegged_order.order_id] = pegged_order
        self.pegged_orders[pegged_order.order_id] = pegged_order
        self.last_accepted_order = pegged_order
        self._reprice_pegged()

        return []

    def _reprice_pegged(self) -> None:

        for id, pegged in list(self.pegged_orders.items()):

            if id not in self.book.orders:
                del self.pegged_orders[id]
                continue 

            reference_price = self.book.reference_price(pegged.peg_reference) 
            if reference_price is None:
                self._detach(pegged)
                del self.book.orders[id]
                del self.pegged_orders[id]
                continue

            if reference_price == pegged.price:
                continue

            else:
                self._detach(pegged)
                new_reference = self.book.get_or_create_level(pegged.side, reference_price)
                pegged.price = reference_price
                new_reference.insert_by_seq(pegged)

        return None


    def _match(self,
        order: Order
    ) -> list[Trade]:

        list_trades = []

        while order.qty > 0: 

            opposite_price = self.book.best_price(order.side.opposite)        

            if opposite_price is None:
                break

            if order.order_type is OrderType.LIMIT:
                # Only for OrderType.LIMIT
                if order.side is Side.BUY:
                    price_is_acceptable = opposite_price <= order.price
                    
                else:
                    price_is_acceptable = opposite_price >= order.price

                if not price_is_acceptable:
                    break

            opposite_levels = self.book.levels_for(order.side.opposite)

            matching_level = opposite_levels[opposite_price]
            level_trade_qty = 0

            while order.qty > 0 and matching_level.first is not None: 

                trade_qty = min(order.qty, matching_level.first.qty)
                order.qty -= trade_qty

                first_consumed = matching_level.fill_first(trade_qty)
                level_trade_qty += trade_qty

                if first_consumed is not None:
                    del self.book.orders[first_consumed.order_id]

            if level_trade_qty > 0:
                list_trades.append(Trade(opposite_price, level_trade_qty))    

            if matching_level.first is None:
                self.book.remove_empty_level(order.side.opposite, opposite_price)

        return list_trades

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
        
        order_to_remove = self.book.orders.get(order_id) 

        if order_to_remove is None:
            return None

        self._detach(order_to_remove)
        del self.book.orders[order_to_remove.order_id] 
        self._reprice_pegged()

        return order_to_remove

    def _modify(self,
        order_id: int,
        new_price: Decimal | None = None,
        new_qty: int | None = None
    ) -> list[Trade] | None:

        order_to_mod = self.book.orders.get(order_id)

        if order_to_mod is None:
            return None

        if order_to_mod.peg_reference is not None and new_price is not None:
            raise ValueError("the price of a pegged order is derived from the book and cannot be modified")

        if new_price is None and new_qty is None:
            raise ValueError("nothing to modify: provide a price, a quantity, or both")

        if new_qty == 0:
            self.cancel(order_id)
            return []

        validate_order_terms(
            order_to_mod.order_type,
            new_price if new_price is not None else order_to_mod.price,
            new_qty if new_qty is not None else order_to_mod.qty,
            order_to_mod.side,
            order_to_mod.peg_reference,
        )

        if new_price is None:

            if new_qty < order_to_mod.qty:
                self.book.levels_for(order_to_mod.side)[order_to_mod.price].adjust_qty(order_to_mod, new_qty)
                return []

            elif new_qty > order_to_mod.qty:
                self._detach(order_to_mod)
                order_to_mod.qty = new_qty
                level = self.book.get_or_create_level(order_to_mod.side, order_to_mod.price)
                order_to_mod.renew_seq()
                level.last_insert(order_to_mod)
                return []

            elif new_qty == order_to_mod.qty:
                return []

        else: 

            self._detach(order_to_mod) 

            order_to_mod.price = new_price

            if new_qty is not None:
                order_to_mod.qty = new_qty

            trades_after_changing = self._match(order_to_mod) 

            if order_to_mod.qty > 0:

                level_after_matching = self.book.get_or_create_level(order_to_mod.side, order_to_mod.price)
                order_to_mod.renew_seq()
                level_after_matching.last_insert(order_to_mod)

            else:

                del self.book.orders[order_id]

        return trades_after_changing 

    def modify(self,
            order_id: int,
            new_price: Decimal | None = None,
            new_qty: int | None = None
    ) -> list[Trade] | None:

        trades_modify = self._modify(order_id, new_price, new_qty)

        if trades_modify is not None:
            self._reprice_pegged()
            return trades_modify

        return trades_modify
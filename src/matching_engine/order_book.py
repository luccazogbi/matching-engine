from decimal import Decimal

from .order import Order, Side, OrderType, format_price, PegReference
from .price_level import PriceLevel
from itertools import zip_longest
import heapq


class OrderBook:
    def __init__(self):
        self.bids = {} 
        self.offers = {} 

        self.orders = {}  
        
        self.bid_prices = []
        self.offer_prices = []


    def levels_for(self, side: Side):
        
        if side is Side.BUY:
            return self.bids

        if side is Side.SELL:
            return self.offers

        raise ValueError("Invalid side")


    def __str__(self) -> str:
        showing_bid_prices = sorted(self.bids.keys(), reverse=True) 
        showing_offer_prices = sorted(self.offers.keys()) 
        lines_bids = []
        lines_offers = []

        for price in showing_bid_prices:
            level = self.bids[price]
            current_order = level.first

            while current_order is not None:
                lines_bids.append(
                    f"{current_order.qty} @ {format_price(price)}"
                )

                current_order = current_order.next_order

        for price in showing_offer_prices:
            level = self.offers[price]
            current_order = level.first

            while current_order is not None:

                lines_offers.append(
                    f"{current_order.qty} @ {format_price(price)}"
                )

                current_order = current_order.next_order

        book_lines = [
            f"{'Ordens de Compra':<20} | Ordens de Venda",
            f"{'-' * 20}-|-----------------"
        ]

        for bid, offer in zip_longest(lines_bids, lines_offers, fillvalue=""):
            book_lines.append(
                f"{bid:<20} | {offer}"
            )

        return "\n".join(book_lines)
    
    def get_or_create_level(
            self, 
            side: Side,
            price: Decimal
    ) -> PriceLevel:

        levels = self.levels_for(side)

        if price in levels:
            return levels[price] 

        levels[price] = PriceLevel(price) 
        
        if side is Side.BUY:
            heapq.heappush(self.bid_prices, -price) 
            

        else:
            heapq.heappush(self.offer_prices, price)

        return levels[price]
    
    def best_bid(self) -> Decimal | None:
        while self.bid_prices:

            current_best_bid = -self.bid_prices[0]

            if current_best_bid in self.bids: 
                return current_best_bid

            heapq.heappop(self.bid_prices)  

        return None

    def best_offer(self) -> Decimal | None:
        while self.offer_prices: 

            current_best_offer = self.offer_prices[0]

            if current_best_offer in self.offers: 
                return current_best_offer

            heapq.heappop(self.offer_prices) 

        return None

    def best_price(
    self,
    side: Side
    ) -> Decimal | None:
        
        if side is Side.BUY:
            return self.best_bid()

        if side is Side.SELL:
            return self.best_offer()

        raise ValueError("Invalid side")

    def remove_empty_level(
    self,
    side: Side,
    price: Decimal
    ):  

        levels = self.levels_for(side) 

        if price in levels: 
            level = levels[price] 

            if level.first is None:
                del levels[price]

    def reference_price(self, 
        peg_reference: PegReference
    ) -> Decimal | None:
        
        if peg_reference is PegReference.BID:
            sorted_bid = sorted(self.bids.items(), reverse=True) 
            unpegged_price = self.finding_unpegged_order(sorted_bid)
            return unpegged_price
        
        else: 
            sorted_offer = sorted(self.offers.items()) 
            unpegged_price = self.finding_unpegged_order(sorted_offer)
            return unpegged_price
                    
    def finding_unpegged_order(self, 
        sorted_side: tuple
    ) -> Decimal | None:

        for price, level in sorted_side: 
            unpegged_price = price
            current = level.first

            while current is not None:

                if current.peg_reference is None:
                    return unpegged_price

                current = current.next_order       
            
        return None

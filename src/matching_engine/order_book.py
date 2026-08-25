"""
    Here, we're going to construct the structure of a OrderBook. It needs to have a dict for BUY and SELL side, as well as 
    a dict to identify an order based on the id, because we'll remove and modifiy by the id. 

    Furthermore, we're going to use heap to have access to the lowest or higher value along our OrderBook (both in SELL and BUY side)

    Something I thought: The OrderBook is responsible for managing everything. You have two sides: SELL and BUY. Inside of each one,
    you have different price levels. So, the OrderBook is responsible for having all of this. In this way, we'll have only ONE 
    OrderBook. 
"""

from decimal import Decimal

from .order import Order, Side, OrderType
from .price_level import PriceLevel
from itertools import zip_longest
import heapq


class OrderBook:
    def __init__(self):
        self.bids = {} # Key: price | Value: PriceLevel (BUY)
        self.offers = {} # Key: price | Value: PriceLevel (SELL)

        self.orders = {}  # Key: order_id | Value: Order (average O(1) lookup) 

        # It'll be used to store the best BID and best OFFER (ASK)
        self.bid_prices = []
        self.offer_prices = []

    def __str__(self) -> str:
        showing_bid_prices = sorted(self.bids.keys(), reverse=True) # descending order
        showing_offer_prices = sorted(self.offers.keys()) # ascending order
        lines_bids = []
        lines_offers = []

        for price in showing_bid_prices:
            level = self.bids[price]
            current_order = level.first

            while current_order is not None:
                lines_bids.append(
                    f"{current_order.qty} @ {price}"
                )

                current_order = current_order.next_order

        for price in showing_offer_prices:
            level = self.offers[price]
            current_order = level.first

            while current_order is not None:

                lines_offers.append(
                    f"{current_order.qty} @ {price}"
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
        
        if side is Side.BUY:

            if price in self.bids: # average O(1) lookup
                return self.bids[price] # It'll return the PriceLevel object
            else:
                self.bids[price] = PriceLevel(price)
                heapq.heappush(self.bid_prices, -price) # Add the best bid inside this specify list called "self.bid_prices"
                return self.bids[price] # Create and return the PriceLevel object

        elif side is Side.SELL:

            if price in self.offers:
                return self.offers[price]
            else:
                self.offers[price] = PriceLevel(price)
                heapq.heappush(self.offer_prices, price)
                return self.offers[price]

        else: 
            raise ValueError("Invalid side")

    def best_bid(self) -> Decimal | None:
        while self.bid_prices:

            current_best_bid = -self.bid_prices[0]

            if current_best_bid in self.bids: # If the price still exists in the dict
                return current_best_bid

            heapq.heappop(self.bid_prices)  # Lazy deletion - O(log P)

        return None

    def best_offer(self) -> Decimal | None:
        while self.offer_prices:

            current_best_offer = self.offer_prices[0]

            if current_best_offer in self.offers: # If the price still exists in the dict
                return current_best_offer

            heapq.heappop(self.offer_prices) # Lazy deletion - O(log P)

        return None

    def remove_empty_level(
    self,
    side: Side,
    price: Decimal
    ):  
        if side is Side.BUY:
            if price in self.bids: # Does the price exist in the dict?
                level = self.bids[price] # Taking the level and verifying if it's empty
                if level.first is None:
                    del self.bids[price]

        elif side is Side.SELL:
            if price in self.offers:
                level = self.offers[price]
                if level.first is None:
                    del self.offers[price]

        else:
            raise ValueError("Invalid side")


if __name__ == "__main__":
    ob = OrderBook()
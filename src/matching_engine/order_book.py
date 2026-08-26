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

    def levels_for(self, side: Side):
        if side is Side.BUY:
            return self.bids

        if side is Side.SELL:
            return self.offers

        raise ValueError("Invalid side")


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

        levels = self.levels_for(side)

        if price in levels: # average O(1) lookup
            return levels[price] # It'll return the PriceLevel object

        levels[price] = PriceLevel(price)
        
        if side is Side.BUY:
            heapq.heappush(self.bid_prices, -price)

        else:
            heapq.heappush(self.offer_prices, price)

        return levels[price]
    
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

        if price in levels: # Does the price exist in the dict?
            level = levels[price] # Taking the level and verifying if it's empty

            if level.first is None:
                del levels[price]

if __name__ == "__main__":
    ob = OrderBook()

    # BUY Orders
    buy_1 = Order(
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=300,
        price=Decimal("10.10")
    )

    buy_2 = Order(
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=300,
        price=Decimal("10.10")
    )

    buy_3 = Order(
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=200,
        price=Decimal("10.00")
    )

    # SELL Order
    
    sell_1 = Order(
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        qty=100,
        price=Decimal("10.50")
    ) 


    sell_2 = Order(
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        qty=100,
        price=Decimal("10.10")
    ) 

    # Get/Create the correct PriceLevels for BUY Side
    level = ob.get_or_create_level(Side.BUY, buy_1.price)
    level.last_insert(buy_1)
    level.last_insert(buy_2)

    level = ob.get_or_create_level(Side.BUY, buy_3.price)
    level.last_insert(buy_3)

    # Get/Create the correct PriceLevels for SELL Side
    level = ob.get_or_create_level(Side.SELL, sell_1.price)
    level.last_insert(sell_1)

    level = ob.get_or_create_level(Side.SELL, sell_2.price)
    level.last_insert(sell_2)

    print(ob)

        
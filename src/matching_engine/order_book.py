"""
    Here, we're going to construct the structure of a OrderBook. It needs to have a dict for BUY and SELL side, as well as 
    a dict to identify an order based on the id, because we'll remove and modifiy by the id. 

    Furthermore, we're going to use heap to have access to the lowest or higher value along our OrderBook (both in SELL and BUY side)
"""

from decimal import Decimal

from .order import Order, Side
from .price_level import PriceLevel
import heapq

class OrderBook:
    def __init__(self):
        self.bids = {} # price - PriceLevel (BUY)
        self.offers = {} # price - PriceLevel (SELL)

        self.orders = {}  # order_id - Order (average O(1) lookup) 

        self.bid_prices = []
        self.offer_prices = []

    def get_or_create_level(self, side, price):
        if side is Side.BUY:
            if price in self.bids: # average O(1) lookup
                return 
            else:
                self.bids[price] = PriceLevel(price)
                heapq.heappush(self.bid_prices, -Decimal(price))

        else:
            if price in self.offers:
                return
            else:
                self.offers[price] = PriceLevel(price)
                heapq.heappush(self.offer_prices, Decimal(price))

if __name__ == "__main__":
    prices = []
    ob = OrderBook()    

    heapq.heappush(ob.offer_prices, Decimal("10.50"))
    heapq.heappush(ob.offer_prices, Decimal("10.20"))
    heapq.heappush(ob.offer_prices, Decimal("10.80"))

    print(ob.offer_prices)
    print(ob.offer_prices[0])

    heapq.heappush(ob.bid_prices, -Decimal("10.50"))
    heapq.heappush(ob.bid_prices, -Decimal("10.20"))
    heapq.heappush(ob.bid_prices, -Decimal("10.80"))

    best_bid = -ob.bid_prices[0]
    print(ob.bid_prices)
    print(best_bid)
# A PriceLevel represents all the orders that exists in the same price, which means it is the doubly linked list.
# This module'll be responsible for that. 
## Furthermore, we have a certain sequence to be respected, which is a FIFO (First In, First Out)


from decimal import Decimal
from .order import Order

class PriceLevel: 

    def __init__(self, price):
        self.price = price
        self.first = None
        self.last = None 
        self.total_qty = 0

    def __repr__(self):
        return (
            f"PriceLevel(price={self.price}, "
            f"total_qty={self.total_qty})"
        )

    # It's a FIFO case, that's why i'm inserting at the end
    def last_insert(self, order):

        new_node = order
        if self.first is None: 
            self.first = new_node
            self.last = new_node

            self.total_qty += new_node.qty

        else:
            new_node.previous_order = self.last
            self.last.next_order = new_node
            self.last = new_node

            self.total_qty += new_node.qty

    def remove_first(self):

        """
        Here we have a O(1) complexity, because we already have a direct reference
        to the first element of the queue. In this way, we don't have to cross all of it 
        to find the first element. 
        """
        # Nothing in the list
        if self.first is None:
            return None

        order_removed = self.first
        
        if order_removed.next_order is None:
            self.first = None
            self.last = None
            self.total_qty -= order_removed.qty

            # Cleaning the removed order
            order_removed.previous_order = None
            order_removed.next_order = None
            return order_removed
        
        else:

            self.total_qty -= order_removed.qty
            self.first = order_removed.next_order
            self.first.previous_order = None

            # Cleaning the removed order
            order_removed.next_order = None
            order_removed.previous_order = None
            return order_removed

    def remove_order(self, order): # O(1) complexity / No loops

        # 1. case: Empty list
        if self.first is None:
            return None

        order_removed = order 
       
        # 2. case: One element list
        if order_removed is self.first and order_removed is self.last:
            self.first = None
            self.last = None

            self.total_qty -= order_removed.qty

            # Cleaning the removed order
            order_removed.next_order = None
            order_removed.previous_order = None
            return order_removed

        # 3. case: The element to be removed is the FIRST in the queue
        elif order_removed  is self.first:

            self.first = order_removed.next_order
            self.first.previous_order = None

            self.total_qty -= order_removed.qty

            # Cleaning the removed order
            order_removed.next_order = None
            order_removed.previous_order = None
            return order_removed

        # 4. case: The element to be removed is the LAST in the queue
        elif order_removed is self.last:
            self.last = order_removed.previous_order
            self.last.next_order = None

            self.total_qty -= order_removed.qty

            # Cleaning the removed order
            order_removed.next_order = None
            order_removed.previous_order = None
            return order_removed

        # 5. case: General case
        else:
            
            prev_order = order_removed.previous_order
            next_order = order_removed.next_order 

            prev_order.next_order = order_removed.next_order
            next_order.previous_order = order_removed.previous_order

            self.total_qty -= order_removed.qty

            # Cleaning the removed order
            order_removed.next_order = None
            order_removed.previous_order = None
            return order_removed

    def fill_first(self, qty):

        first_order = self.first

        first_order.qty -= qty
        self.total_qty -= qty

        if first_order.qty == 0:
            return self.remove_first()
        
        else:
            return None

    # Preserves the position, only for reduction
    def adjust_qty(self,
        order: Order,
        new_qty: int 
    ):
        self.total_qty -= order.qty
        order.qty = new_qty
        self.total_qty += order.qty

    # Inserts respecting the arrival sequence instead of at the tail
    def insert_by_seq(self,
        order: Order
    ):

        """
        Used only when a pegged order is repriced. A repriced order keeps its original seq,
        because the engine moved it — nobody asked for a new place in the queue — so the
        destination level may already hold orders that arrived after it, and the tail would
        put it behind them. Every other insertion in the project goes through last_insert.
        """

        # Walk until the first order that arrived after the one being inserted.
        successor = self.first

        while successor is not None and successor.seq < order.seq:
            successor = successor.next_order

        # No successor: everyone arrived earlier, so the tail is the right
        # place. This also covers the empty level, which last_insert already handles.
        if successor is None:
            self.last_insert(order)
            return

        # Do this if order.seq < successor.seq
        order.previous_order = successor.previous_order
        order.next_order = successor

        # The successor was the head, so the new order becomes the head.
        if successor.previous_order is None:
            self.first = order

        else:
            successor.previous_order.next_order = order

        successor.previous_order = order

        self.total_qty += order.qty

        # Great obs: successor.next_order continuous to point to its original place. Take for example the following config for a level:
        # PriceLevel = [Order 1(seq = 1), Order 2(seq = 3), Order_to_be_insert(seq=2)] ---> Easy to see that...
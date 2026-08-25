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
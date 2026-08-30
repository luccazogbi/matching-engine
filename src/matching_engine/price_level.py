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

        if self.first is None:
            return None

        order_removed = self.first
        
        if order_removed.next_order is None:
            self.first = None
            self.last = None
            self.total_qty -= order_removed.qty

            order_removed.previous_order = None
            order_removed.next_order = None
            return order_removed
        
        else:

            self.total_qty -= order_removed.qty
            self.first = order_removed.next_order
            self.first.previous_order = None

            order_removed.next_order = None
            order_removed.previous_order = None
            return order_removed

    def remove_order(self, order): 

        if self.first is None:
            return None

        order_removed = order 
       
        if order_removed is self.first and order_removed is self.last:
            self.first = None
            self.last = None

            self.total_qty -= order_removed.qty

            order_removed.next_order = None
            order_removed.previous_order = None
            return order_removed

        elif order_removed  is self.first:

            self.first = order_removed.next_order
            self.first.previous_order = None

            self.total_qty -= order_removed.qty

            order_removed.next_order = None
            order_removed.previous_order = None
            return order_removed

        elif order_removed is self.last:
            self.last = order_removed.previous_order
            self.last.next_order = None

            self.total_qty -= order_removed.qty

            order_removed.next_order = None
            order_removed.previous_order = None
            return order_removed

        else:
            
            prev_order = order_removed.previous_order
            next_order = order_removed.next_order 

            prev_order.next_order = order_removed.next_order
            next_order.previous_order = order_removed.previous_order

            self.total_qty -= order_removed.qty

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

    def adjust_qty(self,
        order: Order,
        new_qty: int 
    ):
        self.total_qty -= order.qty
        order.qty = new_qty
        self.total_qty += order.qty

    def insert_by_seq(self,
        order: Order
    ):

        successor = self.first

        while successor is not None and successor.seq < order.seq:
            successor = successor.next_order

        if successor is None:
            self.last_insert(order)
            return

        order.previous_order = successor.previous_order
        order.next_order = successor

        if successor.previous_order is None:
            self.first = order

        else:
            successor.previous_order.next_order = order

        successor.previous_order = order

        self.total_qty += order.qty

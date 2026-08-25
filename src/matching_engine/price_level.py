# A PriceLevel represents all the orders that exists in the same price. This module'll be responsible for that.
## Furthermore, we have a certain sequence to be respected, which is a FIFO (First In, First Out)


from decimal import Decimal
from order import Order

class PriceLevel: 

    def __init__(self, price):
        self.price = price
        self.first = None
        self.last = None 
        self.total_qty = 0

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



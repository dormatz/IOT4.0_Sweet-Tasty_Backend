
"""this moudle gets a list of (id, quantity) and suppose to return the
boxes (including order) in which to find those items in the fastest way"""

class Order(object):
    def __init__(self, id, q):
        self.id = id
        self.q = q



def findOrders(orders: list[Order]):
    """entry point, being called from the application by http"""
    warehouse = Warehouse
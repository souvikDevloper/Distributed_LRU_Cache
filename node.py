# node.py
# Doubly‑linked list node for use in the LRU cache

class DLinkedNode:
    def __init__(self, key=None, value=None, expiry=None):
        self.key = key
        self.value = value
        self.expiry = expiry
        self.prev = None
        self.next = None

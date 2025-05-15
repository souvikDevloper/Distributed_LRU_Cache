# lru_cache.py
import time
import threading
from node import DLinkedNode

class LRUCache:
    def __init__(self, capacity: int, default_ttl: float = None):
        """
        capacity: max number of entries
        default_ttl: default time-to-live (seconds) for each entry
        """
        self.capacity = capacity
        self.default_ttl = default_ttl
        self.cache = {}  # key -> DLinkedNode
        # Dummy head/tail for easy list operations
        self.head = DLinkedNode()
        self.tail = DLinkedNode()
        self.head.next = self.tail
        self.tail.prev = self.head
        self.lock = threading.RLock()

    def _add_node(self, node: DLinkedNode):
        """Insert node right after head."""
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _remove_node(self, node: DLinkedNode):
        """Remove node from list."""
        prev = node.prev
        nxt = node.next
        prev.next = nxt
        nxt.prev = prev

    def _move_to_head(self, node: DLinkedNode):
        """Move an accessed node to the front (most recently used)."""
        self._remove_node(node)
        self._add_node(node)

    def _pop_tail(self) -> DLinkedNode:
        """Pop the least recently used node."""
        node = self.tail.prev
        self._remove_node(node)
        return node

    def _is_expired(self, node: DLinkedNode) -> bool:
        return node.expiry is not None and node.expiry < time.time()

    def get(self, key):
        """Retrieve value and mark as recently used, or None if missing/expired."""
        with self.lock:
            node = self.cache.get(key)
            if not node:
                return None
            if self._is_expired(node):
                # Evict expired entry
                self._remove_node(node)
                del self.cache[key]
                return None
            self._move_to_head(node)
            return node.value

    def put(self, key, value, ttl: float = None):
        """Insert or update key with optional TTL."""
        with self.lock:
            node = self.cache.get(key)
            expiry = None
            effective_ttl = ttl if ttl is not None else self.default_ttl
            if effective_ttl is not None:
                expiry = time.time() + effective_ttl

            if node:
                # Update existing
                node.value = value
                node.expiry = expiry
                self._move_to_head(node)
            else:
                # Insert new
                new_node = DLinkedNode(key, value, expiry)
                self.cache[key] = new_node
                self._add_node(new_node)
                if len(self.cache) > self.capacity:
                    # Evict LRU
                    tail = self._pop_tail()
                    del self.cache[tail.key]

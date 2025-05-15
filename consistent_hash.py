# consistent_hash.py
import hashlib
import bisect

class ConsistentHashRing:
    def __init__(self, nodes=None, replicas=100):
        """
        nodes: iterable of node identifiers (e.g. "cache1", "cache2")
        replicas: number of virtual nodes per real node
        """
        self.replicas = replicas
        self.ring = dict()      # hash -> node
        self._sorted_keys = []  # sorted list of hashes
        if nodes:
            for node in nodes:
                self.add_node(node)

    def _hash(self, key: str) -> int:
        """Return a 32-bit hash of the given key."""
        h = hashlib.md5(key.encode('utf-8')).hexdigest()
        return int(h, 16)

    def add_node(self, node: str):
        """Add a real node and its replicas."""
        for i in range(self.replicas):
            virtual_key = f"{node}#{i}"
            h = self._hash(virtual_key)
            self.ring[h] = node
            bisect.insort(self._sorted_keys, h)

    def remove_node(self, node: str):
        """Remove a real node and its replicas."""
        for i in range(self.replicas):
            virtual_key = f"{node}#{i}"
            h = self._hash(virtual_key)
            del self.ring[h]
            idx = bisect.bisect_left(self._sorted_keys, h)
            self._sorted_keys.pop(idx)

    def get_node(self, key: str) -> str:
        """Given a key, return the nearest node on the ring."""
        if not self.ring:
            return None
        h = self._hash(key)
        idx = bisect.bisect_right(self._sorted_keys, h)
        if idx == len(self._sorted_keys):
            idx = 0
        return self.ring[self._sorted_keys[idx]]

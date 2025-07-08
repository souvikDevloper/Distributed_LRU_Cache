"""
consistent_hash.py
------------------
Minimal, dependency-free implementation of a consistent-hash ring.

• Each real node is represented by *replicas* virtual nodes to improve key
  distribution.
• Supports dynamic add/remove of shards.
• Thread-safe reads (writes are expected to happen rarely and require the GIL).
"""

from __future__ import annotations

import bisect
import hashlib
from typing import Any, Dict, Iterable, List, Sequence


class ConsistentHashRing:
    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #
    def __init__(self, nodes: Sequence[str] | Iterable[str] = (), replicas: int = 100):
        """
        Parameters
        ----------
        nodes
            Iterable of node identifiers (strings).
        replicas
            Number of virtual nodes per real node.
        """
        self.replicas: int = int(replicas)
        self._ring: Dict[int, str] = {}       # hash -> node_id
        self._sorted_keys: List[int] = []     # sorted list of the above hashes

        for n in nodes:
            self.add_node(n)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _hash(key: Any) -> int:
        """Return a 128-bit MD5 hash → int for *any* python object."""
        h = hashlib.md5(str(key).encode("utf-8")).hexdigest()
        return int(h, 16)

    def _reindex(self):
        """Maintain the sorted ring list after mutations."""
        self._sorted_keys = sorted(self._ring.keys())

    # ------------------------------------------------------------------ #
    # Public mutators
    # ------------------------------------------------------------------ #
    def add_node(self, node_id: str) -> None:
        """Add a node and all its replicas."""
        for i in range(self.replicas):
            h = self._hash(f"{node_id}:{i}")
            self._ring[h] = node_id
        self._reindex()

    def remove_node(self, node_id: str) -> None:
        """Remove a node (and its replicas) from the ring."""
        for i in range(self.replicas):
            h = self._hash(f"{node_id}:{i}")
            self._ring.pop(h, None)
        self._reindex()

    # ------------------------------------------------------------------ #
    # Lookup
    # ------------------------------------------------------------------ #
    def get_node(self, key: Any) -> str:
        """
        Map *key* → node_id using consistent hashing.
        Raises KeyError if the ring is empty.
        """
        if not self._ring:
            raise KeyError("Hash ring is empty – add nodes first.")

        h = self._hash(key)
        idx = bisect.bisect(self._sorted_keys, h)
        if idx == len(self._sorted_keys):     # wrap-around
            idx = 0
        return self._ring[self._sorted_keys[idx]]

    # ------------------------------------------------------------------ #
    # Convenience
    # ------------------------------------------------------------------ #
    def __contains__(self, node_id: str) -> bool:
        return node_id in self._ring.values()

    def __len__(self) -> int:
        """Number of *real* nodes on the ring."""
        return len({n for n in self._ring.values()})

    def nodes(self) -> List[str]:
        """Return the list of real nodes on the ring (order arbitrary)."""
        return list({n for n in self._ring.values()})

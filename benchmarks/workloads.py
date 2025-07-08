"""Reusable workload generators for benchmarking Distributed_LRU_Cache."""

from collections import namedtuple
import random

Request = namedtuple("Request", ("op", "key", "value"))


def uniform(keys: int, read_ratio: float, size: int):
    """Uniform key distribution with configurable read/write mix."""
    for _ in range(size):
        if random.random() < read_ratio:
            yield Request("get", random.randrange(keys), None)
        else:
            yield Request(
                "put", random.randrange(keys), random.randrange(1_000_000)
            )


def zipf(keys: int, read_ratio: float, size: int, skew: float = 1.2):
    """Zipfian distribution (approximates hotspot traffic)."""
    from bisect import bisect

    # Pre‑compute CDF for efficiency
    ranks = list(range(1, keys + 1))
    weights = [1 / (r ** skew) for r in ranks]
    total = sum(weights)
    cdf = []
    cumsum = 0.0
    for w in weights:
        cumsum += w / total
        cdf.append(cumsum)

    for _ in range(size):
        if random.random() < read_ratio:
            op = "get"
        else:
            op = "put"
        u = random.random()
        idx = bisect(cdf, u)
        key = idx % keys  # keep key in range
        val = None if op == "get" else random.randrange(1_000_000)
        yield Request(op, key, val)
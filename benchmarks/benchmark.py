#!/usr/bin/env python3
"""
benchmarks/benchmark.py
─────────────────────────────────────────────────────────────────────────────
Benchmark the Distributed-LRU-Cache project.

Modes
-----
• --mode local : call an in-process LRUCache
• --mode http  : exercise the Flask shards through ShardManager

Metrics collected
-----------------
p50 / p95 / p99 latencies (ms) and overall throughput (ops/sec).
"""

from __future__ import annotations

import argparse
import csv
import pathlib
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

import yaml
from tqdm import tqdm

# ── put the repo root on sys.path ────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from lru_cache import LRUCache
from shard_manager import ShardManager
from benchmarks.workloads import Request, uniform, zipf

# ─────────────────────────────────────────────────────────────────────────────
# worker helpers
# ─────────────────────────────────────────────────────────────────────────────


def _local_worker(cache: LRUCache, req: Request) -> float:
    """Run one op against an in-process cache; return latency in *ms*."""
    start = time.perf_counter_ns()
    cache.get(req.key) if req.op == "get" else cache.put(req.key, req.value)
    return (time.perf_counter_ns() - start) / 1e6  # → ms


def _http_worker(client: ShardManager, req: Request) -> float:
    """Run one op through ShardManager; return latency in *ms*."""
    key = str(req.key)  # hash-ring always expects strings
    start = time.perf_counter_ns()
    client.get(key) if req.op == "get" else client.put(key, req.value)
    return (time.perf_counter_ns() - start) / 1e6


# ─────────────────────────────────────────────────────────────────────────────
# one benchmark run
# ─────────────────────────────────────────────────────────────────────────────
def _load_endpoints(path: pathlib.Path) -> Dict[str, str]:
    """
    Accept any of:

    ```yaml
    endpoints:
      cache1: http://127.0.0.1:5001
      cache2: http://127.0.0.1:5002
      cache3: http://127.0.0.1:5003
    ```

    or

    ```yaml
    - http://127.0.0.1:5001
    - http://127.0.0.1:5002
    - http://127.0.0.1:5003
    ```

    or even the plain dict without the wrapper key.
    """
    with path.open() as f:
        y = yaml.safe_load(f)

    urls = y["endpoints"] if isinstance(y, dict) and "endpoints" in y else y
    if isinstance(urls, list):
        urls = {str(i): u for i, u in enumerate(urls)}
    if not isinstance(urls, dict):
        raise ValueError("Malformed endpoints.yaml")
    return urls  # {node-id: base_url}


def run_once(args: argparse.Namespace) -> dict[str, float | int | str]:
    # workload generator ------------------------------------------------------
    gen = (
        uniform(args.keys, args.read_ratio, args.ops)
        if args.workload == "uniform"
        else zipf(args.keys, args.read_ratio, args.ops, args.skew)
    )

    # execution mode ----------------------------------------------------------
    if args.mode == "local":
        cache = LRUCache(capacity=args.capacity)
        worker = lambda r: _local_worker(cache, r)
    else:
        endpoints = _load_endpoints(pathlib.Path(args.endpoint_file))
        client = ShardManager(endpoints)
        worker = lambda r: _http_worker(client, r)

    # run ---------------------------------------------------------------------
    latencies: list[float] = []
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        futures = [pool.submit(worker, r) for r in gen]
        for f in tqdm(as_completed(futures), total=args.ops, desc="running"):
            latencies.append(f.result())
    elapsed = time.perf_counter() - t0

    # stats -------------------------------------------------------------------
    p50, p95, p99 = (
        statistics.quantiles(latencies, n=100)[i] for i in (49, 94, 98)
    )
    return dict(
        mode=args.mode,
        ops=args.ops,
        threads=args.threads,
        workload=args.workload,
        read_ratio=args.read_ratio,
        elapsed_sec=round(elapsed, 3),
        p50_ms=round(p50, 3),
        p95_ms=round(p95, 3),
        p99_ms=round(p99, 3),
        throughput_ops_sec=round(args.ops / elapsed, 1),
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    p = argparse.ArgumentParser(description="Benchmark Distributed-LRU-Cache")
    p.add_argument("--mode", choices=["local", "http"], default="local")
    p.add_argument(
        "--endpoint-file",
        default="endpoints.yaml",
        help="YAML with shard URLs (http mode only)",
    )
    p.add_argument("--capacity", type=int, default=100_000)
    p.add_argument("--threads", type=int, default=32)
    p.add_argument("--ops", type=int, default=100_000)
    p.add_argument("--keys", type=int, default=50_000)
    p.add_argument("--read-ratio", type=float, default=0.9)
    p.add_argument("--workload", choices=["uniform", "zipf"], default="uniform")
    p.add_argument("--skew", type=float, default=1.2, help="Zipf skew (≥1.0)")
    p.add_argument("--outfile", help="Write CSV to benchmarks/results/<file>")
    args = p.parse_args()

    res = run_once(args)

    print("\n=== Results ===")
    for k, v in res.items():
        print(f"{k}: {v}")

    if args.outfile:
        out = pathlib.Path(__file__).parent / "results" / args.outfile
        out.parent.mkdir(exist_ok=True)
        with out.open("w", newline="") as f:
            w = csv.DictWriter(f, res.keys())
            w.writeheader()
            w.writerow(res)
        print(f"\nCSV written → {out}")


if __name__ == "__main__":
    main()

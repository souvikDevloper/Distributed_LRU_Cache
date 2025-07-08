#!/usr/bin/env python3
"""
main.py

Run a single cache shard *or* spin-up a 3-node demo cluster.

• one shard:  python main.py --port 5001
• demo:       python main.py --demo

Extra flags
-----------
--threads N     worker threads per shard (Waitress only, default 8)
--capacity N    max cache items            (default from config)
--default-ttl N seconds default TTL        (default from config)
--no-quiet      show Flask/Waitress access log
"""

from __future__ import annotations

import argparse
import logging
import multiprocessing as mp
import time
from typing import List

from flask import Flask, jsonify, request

import config
from lru_cache import LRUCache
from replication import Replicator
from shard_manager import ShardManager

# ─────────────────────────────────────────────────────────────────────────────
# Flask factory – each shard gets its *own* cache instance
# ─────────────────────────────────────────────────────────────────────────────
def create_app(capacity: int, default_ttl: int) -> Flask:
    app = Flask(__name__)
    cache = LRUCache(capacity=capacity, default_ttl=default_ttl)

    @app.route("/cache/<key>", methods=["GET"])
    def http_get(key: str):
        val = cache.get(key)
        return jsonify({"value": val}), (200 if val is not None else 404)

    @app.route("/cache/<key>", methods=["POST"])
    def http_put(key: str):
        data = request.get_json(force=True)
        cache.put(key, data["value"], ttl=data.get("ttl"))
        return jsonify(ok=True), 200

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify(status="up"), 200

    return app


# ─────────────────────────────────────────────────────────────────────────────
# Shard launcher – Waitress w/ keep-alive, falls back to Flask dev server
# ─────────────────────────────────────────────────────────────────────────────
def run_shard(
    port: int,
    capacity: int,
    default_ttl: int,
    threads: int,
    quiet: bool,
) -> None:
    if quiet:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        logging.getLogger("waitress").setLevel(logging.WARNING)

    app = create_app(capacity, default_ttl)

    try:
        from waitress import serve

        serve(
            app,
            host="127.0.0.1",
            port=port,
            threads=threads,
            connection_limit=10_000,  # plenty for local benchmarks
        )
    except ImportError:
        # ── fallback: Flask dev server (good for quick tests, not for load) ──
        app.run(
            host="127.0.0.1",
            port=port,
            threaded=True,
            use_reloader=False,  # no double-fork on Windows
        )


# ─────────────────────────────────────────────────────────────────────────────
# Demo helper – launches three shard processes, runs the original test
# ─────────────────────────────────────────────────────────────────────────────
def run_demo(
    ports: List[int],
    capacity: int,
    default_ttl: int,
    threads: int,
    quiet: bool,
) -> None:
    procs: List[mp.Process] = [
        mp.Process(
            target=run_shard,
            args=(p, capacity, default_ttl, threads, quiet),
            daemon=True,
        )
        for p in ports
    ]

    for p in procs:
        p.start()

    time.sleep(2)  # give the servers time to bind

    shard_mgr = ShardManager(config.SHARD_ENDPOINTS)
    replicator = Replicator(
        list(config.SHARD_ENDPOINTS.items()), config.REPLICATION_FACTOR
    )

    replicator.put("foo", "bar", ttl=60)
    time.sleep(0.5)
    print("GET foo:", shard_mgr.get("foo"))

    # LRU eviction
    for i in range(capacity + 5):
        shard_mgr.put(f"key{i}", f"val{i}")
    print("GET key0 (evicted):", shard_mgr.get("key0"))

    # TTL expiry
    shard_mgr.put("temp", "123", ttl=1)
    time.sleep(2)
    print("GET temp (expired):", shard_mgr.get("temp"))

    # shutdown
    for p in procs:
        p.terminate()
        p.join()


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Distributed-LRU cache shard / demo")

    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--port", type=int, help="Run a single shard on this port")
    g.add_argument("--demo", action="store_true", help="Run the 3-node demo")

    p.add_argument("--threads", type=int, default=8, help="Worker threads per shard")
    p.add_argument("--capacity", type=int, default=config.CAPACITY)
    p.add_argument("--default-ttl", type=int, default=config.DEFAULT_TTL)
    p.add_argument(
        "--no-quiet", action="store_true", help="Show access log (very noisy)"
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    quiet = not args.no_quiet

    if args.demo:
        run_demo([5001, 5002, 5003], args.capacity, args.default_ttl, args.threads, quiet)
    else:
        run_shard(args.port, args.capacity, args.default_ttl, args.threads, quiet)


if __name__ == "__main__":
    main()

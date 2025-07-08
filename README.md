<<<<<<< HEAD
Scalable In‑Memory LRU Cache (O(1) Ops) with Sharding & Auto‑Failover

Summary

This project implements a distributed, thread‑safe LRU (Least Recently Used) cache in Python that provides O(1) get/put operations, 

per‑entry TTL (time‑to‑live), horizontal sharding via consistent hashing, and replication with failover support. 

It uses a doubly‑linked list with a hashmap for constant‑time eviction and access 

, ensures thread safety with reentrant locks 

, and evenly distributes keys across cache nodes using consistent hashing 

. TTL eviction is handled lazily on access or proactively via background cleanup 

, while replication across N live nodes provides high availability and automatic failover.

Features

O(1) LRU Eviction: Combines a doubly‑linked list and hashmap for constant‑time insertions, deletions, and recency updates .



Per‑Entry TTL: Supports optional TTL on each cache entry, with expiry checks on access and periodic purge threads .



Thread‑Safety: Uses Python’s threading.RLock to guard cache mutations, allowing safe concurrent access within a process .



Horizontal Sharding: Distributes keys across multiple cache nodes using a consistent hash ring to minimize data movement on node topology changes .



Replication & Failover: Writes propagate to a configurable replication factor of nodes; health‑check threads detect node failures and reassign replicas to maintain availability .



RESTful API: Each shard exposes a simple HTTP interface (via Flask) for GET/PUT operations .



Project Structure

distributed_lru_cache/
├── config.py           # Capacity, TTL defaults, shard endpoints
├── node.py             # Doubly‑linked list node class
├── lru_cache.py        # Core LRUCache implementation
├── consistent_hash.py  # ConsistentHashRing for sharding
├── shard_manager.py    # Client‑side routing of get/put to shards
├── replication.py      # Replication and failover logic
└── main.py             # Flask servers + client demo
Installation
Clone the repo


git clone https://github.com/souvikDevloper/distributed_lru_cache.git

cd distributed_lru_cache

Install dependencies


pip install flask requests

Configuration

Edit config.py to adjust:

CAPACITY (max entries per shard)

DEFAULT_TTL (seconds; None for infinite)

SHARD_ENDPOINTS (mapping of node IDs to HTTP URLs)

REPLICATION_FACTOR (number of replicas per key)




python main.py

This spins up three Flask shards (ports 5001–5003) and a client that demonstrates:

Writing foo with TTL and reading it back

LRU eviction past capacity

TTL expiry of a temporary key

Integrate in your app


from shard_manager import ShardManager
sm = ShardManager(SHARD_ENDPOINTS)

sm.put("user:123", {"name": "Alice"}, ttl=600)
user = sm.get("user:123")

Architecture:

Core Cache

LRU Mechanism: A doubly‑linked list orders entries by recency, with a hashmap for direct node lookup .



TTL Handling: Each node stores an expiry timestamp. On get, expired nodes are purged. Optional background sweeper can remove stale items proactively .



Concurrency: A global RLock wraps get/put/evict operations to prevent race conditions in multi‑threaded environments .



Sharding & Consistent Hashing
Hash Ring: Maps virtual node hashes into a ring to evenly spread keys and reduce re‑mapping when nodes join/leave .



Client Routing: ShardManager hashes each key to select a shard’s HTTP endpoint and forwards requests accordingly.

Replication & Failover

Replication Factor: Writes go to N distinct shards (sync or async). Replicas boost availability if primary node fails .



Heartbeat Monitoring: Background threads poll /health endpoints; on failure detection, replicas are re‑distributed to maintain desired redundancy.

Extensions:

Geo‑Distributed Active‑Active: Deploy multiple regional clusters with CRDTs for conflict‑free merging and low‑latency local reads 
Python in Plain English.


Write Through vs. Write Back:

Write‑Through: Synchronously write to both cache and backing store for strong consistency.

Write‑Back: Buffer writes in cache and flush asynchronously to the store for higher throughput, at risk of data loss on failures .



Contributing:

Fork the repo

Create a feature branch (git checkout -b feature/xyz)

Commit your changes (git commit -am 'Add xyz')

Push to your branch (git push origin feature/xyz)

Open a Pull Request

License
This project is licensed under the Apache 2.0 License. See the LICENSE file for details.
=======
Distributed LRU Cache

A minimal sharded, replicated, time‑aware LRU key/value cache written 100 % in Python.

Consistent‑hash sharding – even key distribution, graceful scale‑out

Write replication – adjustable REPLICATION_FACTOR for durability

Per‑item TTL – automatic expiry without background janitors

Exact LRU eviction – O(1) get/put using a doubly‑linked list

HTTP interface – zero‑config Flask shards; portable to any WSGI/ASGI server

Batteries‑included benchmark – uniform & Zipf workloads, local or HTTP

⚠️  The bundled Flask server is for development only. For production‑grade
load, run the shards under Gunicorn/uvicorn – see Tuning.

Architecture at a Glance

┌──────────────┐        put(k,v)        ┌──────────┐
│  Benchmark   │ ─────────────────────▶ │ Primary  │
│   Client     │                       │  Shard 1 │
└──────────────┘ ◀───────────────────── │  (cache) │
    ▲    ▲         get(k) / 404        └──────────┘
    │    │                                   ▲  ▲
    │    └───────────────┐                   │  │
    │                    │   Replication     │  │
    │      ┌──────────┐  └───────────────────┘  │
    │      │ Shard 2  │<─────────────────────────┘
    │      └──────────┘
    │
  Consistent‑Hash Ring      (N nodes, R replicas)

ShardManager chooses the primary node for a key via consistent hashing

Replicator fans out writes to the next R‑1 nodes on the ring

Reads always go to the primary (read‑replicas are an easy extension)

Quick Start

1. Create and activate a virtual‑env

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

2. Run the 3‑node demo cluster

python main.py --demo

You should see:

GET foo: bar
GET key0 (evicted): None
GET temp (expired): None

3. Spin up a single shard

python main.py --port 5001 --capacity 100_000 --default-ttl 60

The shard exposes:

Method

Endpoint

Body

Notes

GET

/cache/<key>

–

404 if not found

POST

/cache/<key>

{"value": <str>, "ttl": 30}

ttl optional (s)

GET

/health

–

liveness probe

Benchmark

Run locally (no HTTP):

python benchmarks/benchmark.py --mode local --ops 100_000 --threads 32

Run through the shards:

python benchmarks/benchmark.py `
  --mode http `
  --endpoint-file endpoints.yaml `
  --threads 64 `           # load generator concurrency
  --ops 100_000 `          # total operations
  --keys 10_000 `          # distinct key space
  --read-ratio 0.9         # 90 % GET / 10 % PUT

Sample numbers on a laptop (Windows 11, Ryzen 7‑5800H)

ops

threads

p50 (ms)

p95 (ms)

p99 (ms)

throughput (ops/s)

50 k

32

2.2

18.1

21.0

1.77 k

100 k

64

37.7

42.0

47.8

1.64 k

Under the hood each logical write is replicated to 2 nodes, so the shard side handles ~3.2 k HTTP requests/s in the second run.

Tuning for Higher QPS

lever

effect

example

Production server

Faster accept + coroutine‑based IO

gunicorn main:create_app -w 8 -k gevent --bind 0.0.0.0:5001

More shard workers

Parallelism within a node

run 2–4 Gunicorn workers per port or multiple ports per shard

Batch writes

Slash HTTP overhead on replication

add /bulk that accepts a dict of key→value

Async client

Drive more load without GIL contention

replace benchmark threads with httpx.AsyncClient

Larger TIME_WAIT reuse

Windows: netsh int ipv4 set dynamicport tcp start=49152 num=16384

frees more ephemeral ports

Troubleshooting

WinError 10048 / Only one usage of each socket address … – ran out of ephemeral ports. Use keep‑alive (requests.Session, already enabled), lower --threads, or shorten TIME_WAIT.

High P99 latency – likely Python GC pauses or replication fan‑out. Try Gunicorn with gevent, which yields during IO.

Hot spots – skewed workload? Switch benchmark to --workload zipf --skew 1.4.

Contributing

Fork ✨

Create feature branch git checkout -b feat/my‑idea

poetry run pytest – tests must pass

Open a PR – we ❤️ discussions!

License

This project is released under the MIT License – see LICENSE for details.
>>>>>>> 4b405a4 (updated distributed cache)


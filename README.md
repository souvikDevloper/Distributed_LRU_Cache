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


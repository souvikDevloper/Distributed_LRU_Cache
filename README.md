# Distributed LRU Cache 

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
  <img src="https://img.shields.io/badge/Build-Passing-success" />
</p>

A **light‑weight, horizontal‑scaling key/value store** that combines:

* ⚖️ **Consistent hashing** for near‑perfect shard balance 
* 🔁 **Configurable replication** for availability / durability 
* ⏱️ **Per‑item TTL** *and* **LRU eviction** to stay memory‑bounded 
* 🌐 **HTTP API** so any language can consume it 
* 🛠️ **Pluggable storage backend** (current drop‑in LRU in‑memory) 
* 📊 **Benchmark harness** with uniform + Zipf workloads

> **Status** Demo‑ready / learning project — not production hardened (yet 😉).

---

\## 📸 Architecture

```text
┌─────────────────────────┐        ┌─────────────────────────┐
│  Client / Benchmark     │        │  Client / Application    │
│  benchmarks/benchmark.py│  ...   │  (any language)          │
└──────────┬──────────────┘        └──────────┬──────────────┘
           │HTTP GET/POST                       │HTTP GET/POST
           ▼                                   ▼
┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────────┐
│   Shard #1 (Flask)      │   │   Shard #2 (Flask)      │   │   Shard #3 (Flask)      │
│  → LRUCache instance    │   │  → LRUCache instance    │   │  → LRUCache instance    │
└──────────┬──────────────┘   └──────────┬──────────────┘   └──────────┬──────────────┘
           ▲  consistent‑hash ring        ▲                         ▲
           └───────────────Shard Manager / Replicator───────────────┘
```

* **Shard Manager** → maps keys to shards via *Ketama* consistent hashing.
* **Replicator** → applies the write to *N* successive nodes on the hash ring.
* Every shard runs the same tiny Flask app that wraps an `LRUCache`.

---

\## 🚀 Quick start

```bash
# 1) install deps (ideally in a venv)
python -m pip install -r requirements.txt

# 2) spin up a single shard on :5001
python main.py --port 5001 --capacity 100_000 --default-ttl 60

#  or run the built‑in 3‑node demo
python main.py --demo

# 3) hammer it with the benchmark harness
python benchmarks/benchmark.py \
        --mode http \
        --endpoint-file endpoints.yaml \
        --threads 32 \
        --ops 50_000 \
        --keys 5_000 \
        --read-ratio 0.9
```

<details>
<summary>🔧 Common options (click)</summary>

|  Flag           |  Default     |  What it does                    |
| --------------- | ------------ | -------------------------------- |
| `--capacity`    | `100_000`    | Max entries before LRU eviction  |
| `--default-ttl` | `60` seconds | TTL if caller omits `ttl`        |
| `--threads`     | `32`         | Parallel workers in benchmark    |
| `--workload`    | `uniform`    | `uniform` or `zipf` key dist.    |
| `--skew`        | `1.2`        | Zipf θ parameter                 |

</details>

---

\## 📑 HTTP API

|  Verb    |  Route         |  Body                         |  Meaning                              |
| -------- | -------------- | ----------------------------- | ------------------------------------- |
| **GET**  | `/cache/<key>` | –                             | Return JSON `{"value": ..}` or `404`. |
| **POST** | `/cache/<key>` | `{"value": …, "ttl": <sec?>}` | Insert/overwrite. `ttl` optional.     |
| **GET**  | `/health`      | –                             | Simple liveness probe.                |

> **Note** A write is proxied to *N consecutive* shards (see `config.REPLICATION_FACTOR`).

---

\## 📈 Sample benchmarks (2025‑07‑08, local laptop)

|  Ops      |  Threads  |  Keys    |  P50 (ms)  |  P95 (ms)  |  Throughput (ops/s)  |
| --------- | --------- | -------- | ---------- | ---------- | -------------------- |
|  50 000   |  32       |  5 000   |  2.16      |  18.0      |  1 770               |
|  100 000  |  64       |  10 000  |  37.6      |  42.0      |  1 640               |

*Flask’s built‑in server isn’t tuned for high QPS ― swap in Gunicorn / uvicorn for real deployments.*

---

\## 🗄️ Project layout

```
.
├── benchmarks/            ← load‑testing harness & workloads
├── cache_node.py          ← minimal Flask + LRU (used by main.py)
├── lru_cache.py           ← fast O(1) doubly‑linked‑list + dict impl
├── consistent_hash.py     ← Ketama ring
├── shard_manager.py       ← client‑side routing logic
├── replication.py         ← fan‑out writes to replicas
├── config.py              ← capacity, TTL, replica factor, endpoint list
└── main.py                ← CLI: run one shard or 3‑node demo
```

---

\## 🤝 Contributing

1. **Fork** the repo & create a feature branch.
2. Follow [`black`](https://black.readthedocs.io/) & [`ruff`](https://github.com/astral-sh/ruff) for lint/format.
3. Make sure `pytest` passes.
4. Open a PR — please include context & before/after benchmarks if you’re touching the hot path.

---

\## 📜 License 

Distributed LRU Cache is released under the **MIT License** — see [`LICENSE`](LICENSE).

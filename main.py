# main.py
from lru_cache import LRUCache
from shard_manager import ShardManager
from replication import Replicator
import config
import threading
import time
from flask import Flask, request, jsonify

app = Flask(__name__)
# Each process runs one shard instance:
cache = LRUCache(capacity=config.CAPACITY, default_ttl=config.DEFAULT_TTL)

@app.route("/cache/<key>", methods=["GET"])
def http_get(key):
    val = cache.get(key)
    return jsonify({"value": val}), (200 if val is not None else 404)

@app.route("/cache/<key>", methods=["POST"])
def http_put(key):
    data = request.get_json(force=True)
    ttl = data.get("ttl", None)
    cache.put(key, data["value"], ttl=ttl)
    return jsonify({"ok": True}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "up"}), 200

def start_flask(port):
    app.run(port=port)

if __name__ == "__main__":
    # 1) Launch three shard processes (in real deploy, separate machines)
    ports = [5001, 5002, 5003]
    for p in ports:
        threading.Thread(target=start_flask, args=(p,), daemon=True).start()

    time.sleep(1)  # let servers start

    # 2) Client logic
    shard_mgr = ShardManager(config.SHARD_ENDPOINTS)
    replicator = Replicator(list(config.SHARD_ENDPOINTS.items()), config.REPLICATION_FACTOR)

    # Write with replication
    replicator.put("foo", "bar", ttl=60)
    time.sleep(0.5)

    # Read via shard manager
    print("GET foo:", shard_mgr.get("foo"))

    # Demonstrate LRU eviction and TTL
    for i in range(config.CAPACITY + 5):
        shard_mgr.put(f"key{i}", f"val{i}")
    print("GET key0 (should be None if evicted):", shard_mgr.get("key0"))

    # TTL expiry
    shard_mgr.put("temp", "123", ttl=1)
    time.sleep(2)
    print("GET temp (after TTL):", shard_mgr.get("temp"))

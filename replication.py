# replication.py
import threading
import time
import requests

class Replicator:
    def __init__(self, shard_endpoints, replication_factor=3):
        """
        shard_endpoints: list of (node_id, base_url)
        replication_factor: how many replicas per key
        """
        self.endpoints = shard_endpoints
        self.replication_factor = replication_factor

    def _choose_replicas(self, key):
        # simple round-robin or consistent hash subset for replicas
        # here, just take first N for demo
        return self.endpoints[:self.replication_factor]

    def put(self, key, value, ttl=None):
        replicas = self._choose_replicas(key)
        payload = {"value": value}
        if ttl is not None:
            payload["ttl"] = ttl
        for node_id, base_url in replicas:
            url = f"{base_url}/cache/{key}"
            # fire-and-forget for async; or resp = requests.post(...) for sync
            threading.Thread(target=requests.post, args=(url,), kwargs={"json": payload}).start()

    def heartbeat_loop(self, interval=5):
        """Continuously check node health and reassign replicas as needed."""
        while True:
            for node_id, base_url in self.endpoints:
                try:
                    requests.get(f"{base_url}/health")
                except Exception:
                    # handle failover: reassign replicas, promote standby, etc.
                    print(f"[WARN] Node {node_id} down!")
            time.sleep(interval)

# shard_manager.py
from consistent_hash import ConsistentHashRing
import requests  # assumes each shard exposes HTTP API

class ShardManager:
    def __init__(self, shard_endpoints, replicas=100):
        """
        shard_endpoints: dict mapping node_id -> base_url (e.g. "cache1": "http://10.0.0.1:5000")
        """
        self.ring = ConsistentHashRing(nodes=shard_endpoints.keys(), replicas=replicas)
        self.endpoints = shard_endpoints

    def _route(self, key):
        node = self.ring.get_node(key)
        return self.endpoints[node]

    def get(self, key):
        url = f"{self._route(key)}/cache/{key}"
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json().get("value")
        return None

    def put(self, key, value, ttl=None):
        url = f"{self._route(key)}/cache/{key}"
        payload = {"value": value}
        if ttl is not None:
            payload["ttl"] = ttl
        requests.post(url, json=payload)

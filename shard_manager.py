# shard_manager.py  ── final hard-limit version
from __future__ import annotations

import threading
from typing import Dict, Any

import requests
from requests.adapters import HTTPAdapter

from consistent_hash import ConsistentHashRing


class ShardManager:
    """
    Routes keys to HTTP shards with a single shared requests.Session.
    Blocks when the per-host pool is exhausted → no more ‘address in use’.
    """

    _global_session: requests.Session | None = None
    _lock = threading.Lock()

    def __init__(
        self,
        shard_endpoints: Dict[str, str],
        *,
        replicas: int = 100,
        pool_size: int = 256,
        timeout: float = 2.0,
    ) -> None:
        self.ring = ConsistentHashRing(nodes=shard_endpoints.keys(), replicas=replicas)
        self.endpoints = shard_endpoints
        self.timeout = timeout
        self._session = self._get_or_create_session(pool_size)

    # ── session helper ─────────────────────────────────────────────────────
    @classmethod
    def _get_or_create_session(cls, pool_size: int) -> requests.Session:
        with cls._lock:
            if cls._global_session is None:
                s = requests.Session()
                adapter = HTTPAdapter(
                    pool_connections=pool_size,
                    pool_maxsize=pool_size,
                    pool_block=True,          # ← **key change**
                    max_retries=0,
                )
                s.mount("http://", adapter)
                s.mount("https://", adapter)
                s.headers.update({"Connection": "keep-alive"})
                s.trust_env = False           # ignore proxy env vars etc.
                cls._global_session = s
            return cls._global_session

    def _route(self, key: str) -> str:
        return self.endpoints[self.ring.get_node(key)]

    # ── public API ─────────────────────────────────────────────────────────
    def get(self, key: str):
        url = f"{self._route(key)}/cache/{key}"
        r = self._session.get(url, timeout=self.timeout)
        return r.json()["value"] if r.status_code == 200 else None

    def put(self, key: str, value: Any, ttl: int | None = None) -> None:
        url = f"{self._route(key)}/cache/{key}"
        payload = {"value": value}
        if ttl is not None:
            payload["ttl"] = ttl
        self._session.post(url, json=payload, timeout=self.timeout)

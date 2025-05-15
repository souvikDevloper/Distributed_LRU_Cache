# config.py
CAPACITY = 1000
DEFAULT_TTL = 300.0       # 5 minutes
SHARD_ENDPOINTS = {
    "cache1": "http://127.0.0.1:5001",
    "cache2": "http://127.0.0.1:5002",
    "cache3": "http://127.0.0.1:5003",
}
REPLICATION_FACTOR = 2

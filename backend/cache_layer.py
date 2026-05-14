"""
TRD v12.3 — Caching Layer (Redis-compatible, in-memory fallback)
Provides: Market data caching, session caching, rate store
"""
import time, json, threading, hashlib
from typing import Any, Optional
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

class TRDCache:
    """
    Thread-safe in-memory cache with TTL.
    Drop-in Redis replacement — swap to redis.Redis() in production.
    """
    def __init__(self):
        self._store  = {}
        self._lock   = threading.Lock()
        self._hits   = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            item = self._store.get(key)
            if not item:
                self._misses += 1
                return None
            if item["expires"] and time.time() > item["expires"]:
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return item["value"]
    
    def set(self, key: str, value: Any, ttl: int = 300):
        with self._lock:
            self._store[key] = {
                "value":   value,
                "expires": time.time() + ttl if ttl > 0 else None,
                "created": time.time(),
            }
    
    def delete(self, key: str):
        with self._lock:
            self._store.pop(key, None)
    
    def delete_prefix(self, prefix: str):
        with self._lock:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys: del self._store[k]
    
    def stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            return {
                "keys":      len(self._store),
                "hits":      self._hits,
                "misses":    self._misses,
                "hit_rate":  f"{(self._hits/max(total,1)*100):.1f}%",
            }
    
    def flush(self):
        with self._lock:
            self._store.clear()

# Global cache instance
cache = TRDCache()

# Cache TTL constants
TTL_MARKET_PRICE  = 30    # 30s — market prices
TTL_OPTION_CHAIN  = 60    # 1min — option chain
TTL_IV_SURFACE    = 300   # 5min — IV surface
TTL_USER_PROFILE  = 120   # 2min — user profile
TTL_STRATEGIES    = 600   # 10min — builtin strategies
TTL_AI_SIGNALS    = 180   # 3min — AI signals

def cached(key: str, ttl: int = 300):
    """Decorator for caching function results"""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            cached_val = cache.get(key)
            if cached_val is not None:
                return cached_val
            result = fn(*args, **kwargs)
            if result is not None:
                cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator

def market_cache_key(instrument: str) -> str:
    return f"market:{instrument}"

def user_cache_key(user_id: str, resource: str) -> str:
    return f"user:{user_id}:{resource}"

def chain_cache_key(instrument: str, dte: int, date: str) -> str:
    return f"chain:{instrument}:{dte}:{date}"

print("✅ cache_layer.py created")

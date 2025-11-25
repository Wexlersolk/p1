import time
from typing import Any, Dict, Optional
from .config import API_CONFIG

# In-memory cache
_cache: Dict[str, Dict[str, Any]] = {}

def get_from_cache(key: str) -> Optional[Any]:
    """Get cached data if it exists and is not expired"""
    if key in _cache and time.time() - _cache[key]["timestamp"] < API_CONFIG["cache_ttl"]:
        return _cache[key]["data"]
    return None

def save_to_cache(key: str, data: Any) -> None:
    """Save data to cache with current timestamp"""
    _cache[key] = {
        "timestamp": time.time(),
        "data": data
    }

def clear_cache() -> None:
    """Clear the entire cache"""
    _cache.clear()

def remove_from_cache(key: str) -> None:
    """Remove specific key from cache"""
    if key in _cache:
        del _cache[key]

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    current_time = time.time()
    return {
        "total_keys": len(_cache),
        "active_keys": sum(1 for k, v in _cache.items() if current_time - v["timestamp"] < API_CONFIG["cache_ttl"]),
        "expired_keys": sum(1 for k, v in _cache.items() if current_time - v["timestamp"] >= API_CONFIG["cache_ttl"]),
        "ttl": API_CONFIG["cache_ttl"]
    }
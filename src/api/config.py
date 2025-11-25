# Server configuration
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": True,
    "reload": True,
    "workers": 4,
    "cache_ttl": 300,  # 5 minutes cache TTL
}

# Endpoint prefixes
API_PREFIX = "/api/v1"
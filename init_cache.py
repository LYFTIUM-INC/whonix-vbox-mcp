#!/usr/bin/env python3
"""
Initialize persistent cache for browser automation.
This script creates the cache directory and database.
"""

import sys
sys.path.insert(0, '/home/user/browser_automation')

from persistent_cache import PersistentCache, get_cache
import json

def main():
    print("Initializing persistent cache...")

    # Initialize cache (creates directory + database)
    cache = get_cache()

    # Verify directory exists
    print(f"Cache directory: {cache.cache_dir}")
    print(f"Database path: {cache.db_path}")
    print(f"Directory exists: {cache.cache_dir.exists()}")
    print(f"Database exists: {cache.db_path.exists()}")

    # Test write
    test_url = "https://test.example.com"
    test_data = {"test": "data", "timestamp": "2025-10-02"}
    cache.set(test_url, test_data, ttl=3600)
    print(f"✅ Test write successful")

    # Test read
    retrieved = cache.get(test_url)
    assert retrieved == test_data, "Cache read failed"
    print(f"✅ Test read successful")

    # Get stats
    stats = cache.get_stats()
    print(f"\nCache Statistics:")
    print(json.dumps(stats, indent=2))

    print(f"\n✅ Persistent cache initialized successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())

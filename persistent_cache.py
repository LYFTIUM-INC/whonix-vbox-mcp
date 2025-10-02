"""
Persistent SQLite-based cache for browser automation.

This cache persists across MCP process restarts, solving the issue where
in-memory caches are lost when Python processes terminate.
"""

import sqlite3
import hashlib
import json
import time
import logging
from pathlib import Path
from typing import Any, Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


class PersistentCache:
    """
    SQLite-based persistent cache with TTL support.

    Features:
    - Survives process restarts (unlike in-memory cache)
    - Automatic expiration based on TTL
    - LRU eviction when max size reached
    - Thread-safe operations
    - Cache statistics tracking
    """

    def __init__(
        self,
        cache_dir: str = "/tmp/mcp_browser_cache",
        db_name: str = "response_cache.db",
        max_size: int = 1000,
        default_ttl: float = 3600  # 1 hour
    ):
        """
        Initialize persistent cache.

        Args:
            cache_dir: Directory for cache database
            db_name: Database filename
            max_size: Maximum number of cached entries
            default_ttl: Default time-to-live in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.cache_dir / db_name
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.stats = CacheStats()

        self._init_database()
        self._cleanup_expired()

        logger.info(f"Persistent cache initialized at {self.db_path}")

    def _init_database(self):
        """Create cache table if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    data TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    ttl REAL NOT NULL,
                    hits INTEGER DEFAULT 0,
                    last_accessed REAL NOT NULL
                )
            """)

            # Index for faster expiration cleanup
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expiration
                ON cache(timestamp, ttl)
            """)

            # Index for LRU eviction
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_lru
                ON cache(last_accessed)
            """)

            conn.commit()

    def _make_key(self, url: str, context: Optional[str] = None) -> str:
        """
        Generate cache key from URL and optional context.

        Args:
            url: URL or query string
            context: Optional context (e.g., search engine, task type)

        Returns:
            MD5 hash as cache key
        """
        key_input = f"{url}:{context}" if context else url
        return hashlib.md5(key_input.encode()).hexdigest()

    def get(self, url: str, context: Optional[str] = None) -> Optional[Any]:
        """
        Retrieve cached data.

        Args:
            url: URL or query string
            context: Optional context for key generation

        Returns:
            Cached data if found and not expired, None otherwise
        """
        key = self._make_key(url, context)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT data, timestamp, ttl, hits
                    FROM cache
                    WHERE key = ?
                """, (key,))

                row = cursor.fetchone()

                if row is None:
                    self.stats.misses += 1
                    return None

                data_json, timestamp, ttl, hits = row

                # Check if expired
                if time.time() - timestamp > ttl:
                    # Delete expired entry
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                    conn.commit()
                    self.stats.misses += 1
                    return None

                # Update access stats
                conn.execute("""
                    UPDATE cache
                    SET hits = ?, last_accessed = ?
                    WHERE key = ?
                """, (hits + 1, time.time(), key))
                conn.commit()

                self.stats.hits += 1

                # Deserialize data
                return json.loads(data_json)

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.stats.misses += 1
            return None

    def set(
        self,
        url: str,
        data: Any,
        ttl: Optional[float] = None,
        context: Optional[str] = None
    ):
        """
        Store data in cache.

        Args:
            url: URL or query string
            data: Data to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (uses default if not specified)
            context: Optional context for key generation
        """
        key = self._make_key(url, context)
        ttl = ttl or self.default_ttl

        try:
            # Serialize data
            data_json = json.dumps(data)

            with sqlite3.connect(self.db_path) as conn:
                # Check cache size
                cursor = conn.execute("SELECT COUNT(*) FROM cache")
                count = cursor.fetchone()[0]

                if count >= self.max_size:
                    # Evict least recently used entry
                    conn.execute("""
                        DELETE FROM cache
                        WHERE key = (
                            SELECT key FROM cache
                            ORDER BY last_accessed ASC
                            LIMIT 1
                        )
                    """)
                    self.stats.evictions += 1

                # Insert or replace entry
                now = time.time()
                conn.execute("""
                    INSERT OR REPLACE INTO cache
                    (key, url, data, timestamp, ttl, hits, last_accessed)
                    VALUES (?, ?, ?, ?, ?, 0, ?)
                """, (key, url, data_json, now, ttl, now))

                conn.commit()

        except Exception as e:
            logger.error(f"Cache set error: {e}")

    def _cleanup_expired(self):
        """Remove all expired entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                now = time.time()
                cursor = conn.execute("""
                    DELETE FROM cache
                    WHERE ? - timestamp > ttl
                """, (now,))

                deleted = cursor.rowcount
                conn.commit()

                if deleted > 0:
                    logger.info(f"Cleaned up {deleted} expired cache entries")

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

    def clear(self):
        """Clear all cache entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache")
                conn.commit()
                logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    def get_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats including size, hit rate, etc.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM cache")
                size = cursor.fetchone()[0]

                cursor = conn.execute("""
                    SELECT
                        AVG(hits) as avg_hits,
                        MAX(hits) as max_hits,
                        SUM(LENGTH(data)) as total_bytes
                    FROM cache
                """)
                avg_hits, max_hits, total_bytes = cursor.fetchone()

                return {
                    'size': size,
                    'max_size': self.max_size,
                    'hits': self.stats.hits,
                    'misses': self.stats.misses,
                    'hit_rate': f"{self.stats.hit_rate:.1f}%",
                    'evictions': self.stats.evictions,
                    'avg_entry_hits': avg_hits or 0,
                    'max_entry_hits': max_hits or 0,
                    'total_bytes': total_bytes or 0,
                    'db_path': str(self.db_path)
                }

        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return {'error': str(e)}


# Global cache instance (shared across imports)
_global_cache: Optional[PersistentCache] = None


def get_cache() -> PersistentCache:
    """
    Get or create global cache instance.

    Returns:
        Shared PersistentCache instance
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = PersistentCache()

    return _global_cache


if __name__ == "__main__":
    # Test the cache
    logging.basicConfig(level=logging.INFO)

    cache = PersistentCache(default_ttl=5)

    # Test set/get
    print("Testing cache operations...")
    cache.set("https://example.com", {"test": "data", "value": 123})

    result = cache.get("https://example.com")
    print(f"Retrieved: {result}")

    # Test with context
    cache.set("test query", {"results": [1, 2, 3]}, context="duckduckgo")
    result = cache.get("test query", context="duckduckgo")
    print(f"Retrieved with context: {result}")

    # Test stats
    print(f"\nCache stats: {json.dumps(cache.get_stats(), indent=2)}")

    # Test expiration
    print("\nWaiting for expiration (5s)...")
    time.sleep(6)

    result = cache.get("https://example.com")
    print(f"After expiration: {result}")

    print(f"\nFinal stats: {json.dumps(cache.get_stats(), indent=2)}")

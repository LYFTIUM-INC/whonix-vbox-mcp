#!/usr/bin/env python3
"""
Multi-Engine Search System
==========================

Intelligent search with automatic fallback across multiple search engines.

Features:
- Circuit Breaker Pattern: Skip failing engines temporarily
- Quality Validation: Verify results are in expected language
- Priority Ordering: Use best-performing engine first
- Result Normalization: Unified result format

Cycle 1: SearX + DuckDuckGo
Cycle 2: + Ahmia + Brave Search

Version: 1.0 (Cycle 1)
"""

import asyncio
import aiohttp
import time
import logging
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        # Fallback to old package name
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
        logger.warning("Using deprecated duckduckgo-search package. Install ddgs instead.")
    except ImportError:
        logger.warning("Neither ddgs nor duckduckgo-search available")
        DDGS = None
        DDGS_AVAILABLE = False

try:
    import langdetect
except ImportError:
    logger.warning("langdetect not available - language validation disabled")
    langdetect = None


# ========================================================================
# === CIRCUIT BREAKER PATTERN ===
# ========================================================================

@dataclass
class CircuitBreakerState:
    """Circuit breaker state for each engine"""
    failures: int = 0
    last_failure_time: float = 0
    state: str = 'closed'  # closed, open, half-open
    success_count: int = 0
    total_attempts: int = 0


class CircuitBreaker:
    """Circuit breaker to skip failing engines"""

    def __init__(self, failure_threshold: int = 3, timeout: float = 30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = CircuitBreakerState()

    def is_open(self) -> bool:
        """Check if circuit breaker is open (engine should be skipped)"""
        if self.state.state == 'closed':
            return False

        if self.state.state == 'open':
            # Check if timeout has passed
            if time.time() - self.state.last_failure_time > self.timeout:
                self.state.state = 'half-open'
                return False
            return True

        # half-open state - allow one attempt
        return False

    def record_success(self):
        """Record successful request"""
        self.state.success_count += 1
        self.state.total_attempts += 1

        if self.state.state == 'half-open':
            # Success in half-open state - close the circuit
            self.state.state = 'closed'
            self.state.failures = 0

    def record_failure(self):
        """Record failed request"""
        self.state.failures += 1
        self.state.total_attempts += 1
        self.state.last_failure_time = time.time()

        if self.state.failures >= self.failure_threshold:
            self.state.state = 'open'
            logger.warning(f"Circuit breaker OPENED after {self.state.failures} failures")

    def get_success_rate(self) -> float:
        """Calculate success rate"""
        if self.state.total_attempts == 0:
            return 0.0
        return self.state.success_count / self.state.total_attempts


# ========================================================================
# === SEARCH ENGINE IMPLEMENTATIONS ===
# ========================================================================

class BaseSearchEngine:
    """Base class for search engines"""

    def __init__(self, name: str):
        self.name = name

    async def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Perform search - must be implemented by subclasses"""
        raise NotImplementedError

    def normalize_result(self, raw_result: Dict) -> Dict:
        """Normalize result to standard format"""
        return {
            'title': raw_result.get('title', ''),
            'url': raw_result.get('url', ''),
            'snippet': raw_result.get('snippet', ''),
            'source': self.name
        }


class SearXEngine(BaseSearchEngine):
    """SearX/SearXNG search engine implementation"""

    def __init__(self):
        super().__init__('searx')

        # Public instances from searx.space
        self.instances = [
            'https://searx.be',
            'https://searx.tiekoetter.com',
            'https://searx.fmac.xyz',
            'https://search.ononoki.org',
            'https://searx.work'
        ]

        self.current_instance_index = 0
        self.tor_proxy = 'socks5://127.0.0.1:9050'

    async def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search using SearX API"""
        # Try up to 3 instances
        for attempt in range(min(3, len(self.instances))):
            instance = self.instances[self.current_instance_index]

            try:
                results = await self._search_instance(instance, query, max_results)

                if results:
                    return results

            except Exception as e:
                logger.debug(f"SearX instance {instance} failed: {e}")

            # Rotate to next instance
            self.current_instance_index = (self.current_instance_index + 1) % len(self.instances)

        raise Exception("All SearX instances failed")

    async def _search_instance(self, instance: str, query: str, max_results: int) -> List[Dict]:
        """Search a specific SearX instance"""
        params = {
            'q': query,
            'format': 'json',
            'pageno': 1
        }

        search_url = f"{instance}/search?{urlencode(params)}"

        # Use Tor proxy
        connector = aiohttp.ProxyConnector.from_url(self.tor_proxy)

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=15)
        ) as session:

            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }

            async with session.get(search_url, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")

                data = await response.json()

                results = []
                for item in data.get('results', [])[:max_results]:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'snippet': item.get('content', ''),
                        'source': 'searx',
                        'engine': item.get('engine', 'unknown')
                    })

                return results


class DuckDuckGoEngine(BaseSearchEngine):
    """DuckDuckGo search engine (fallback only)"""

    def __init__(self):
        super().__init__('duckduckgo')

        if not DDGS_AVAILABLE or not DDGS:
            raise ImportError("ddgs library not available")

    async def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search using DuckDuckGo (synchronous, wrapped in async)"""
        try:
            # Try with Tor proxy first
            ddgs = DDGS(proxy='socks5://127.0.0.1:9050')

            results_raw = list(ddgs.text(
                query,
                max_results=max_results
            ))

            results = []
            for item in results_raw:
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('href', ''),
                    'snippet': item.get('body', ''),
                    'source': 'duckduckgo'
                })

            return results

        except Exception as e:
            # Try without proxy as last resort
            logger.debug(f"DuckDuckGo with Tor failed: {e}, trying direct")

            ddgs = DDGS()
            results_raw = list(ddgs.text(query, max_results=max_results))

            results = []
            for item in results_raw:
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('href', ''),
                    'snippet': item.get('body', ''),
                    'source': 'duckduckgo-direct'
                })

            return results


# Placeholder for Cycle 2
class AhmiaEngine(BaseSearchEngine):
    """Ahmia .onion search engine (Cycle 2)"""

    def __init__(self):
        super().__init__('ahmia')

    async def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search using Ahmia API (to be implemented in Cycle 2)"""
        raise NotImplementedError("Ahmia engine will be implemented in Cycle 2")


# Placeholder for Cycle 2
class BraveEngine(BaseSearchEngine):
    """Brave Search API (Cycle 2)"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__('brave')
        self.api_key = api_key

    async def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search using Brave API (to be implemented in Cycle 2)"""
        raise NotImplementedError("Brave engine will be implemented in Cycle 2")


# ========================================================================
# === RESULT VALIDATION ===
# ========================================================================

class ResultValidator:
    """Validate search results quality"""

    @staticmethod
    def validate_results(results: List[Dict], query: str) -> bool:
        """
        Validate search results.

        Checks:
        - Results not empty
        - Results contain expected fields
        - Language detection (if available)
        """
        if not results:
            return False

        # Check structure
        for result in results[:3]:  # Check first 3
            if not all(key in result for key in ['title', 'url', 'snippet']):
                return False

        # Language detection (if available)
        if langdetect:
            try:
                # Check if results are primarily English
                sample_text = ' '.join([
                    r['title'] + ' ' + r['snippet']
                    for r in results[:3]
                ])

                if len(sample_text) > 50:
                    detected_lang = langdetect.detect(sample_text)

                    # If query is English, results should be too
                    if langdetect.detect(query) == 'en' and detected_lang != 'en':
                        logger.warning(f"Language mismatch: query=en, results={detected_lang}")
                        return False

            except Exception as e:
                # Don't fail validation on language detection errors
                logger.debug(f"Language detection failed: {e}")

        return True


# ========================================================================
# === MULTI-ENGINE SEARCH COORDINATOR ===
# ========================================================================

class MultiEngineSearch:
    """
    Intelligent search with automatic fallback across multiple engines.

    Cycle 1: SearX + DuckDuckGo
    Cycle 2: + Ahmia + Brave
    """

    def __init__(self, enable_cycle2_engines: bool = False):
        """
        Initialize multi-engine search.

        Args:
            enable_cycle2_engines: Enable Ahmia and Brave (Cycle 2 only)
        """
        self.engines = {}
        self.circuit_breakers = {}

        # Cycle 1 engines
        try:
            self.engines['searx'] = SearXEngine()
            self.circuit_breakers['searx'] = CircuitBreaker(failure_threshold=3, timeout=30)
        except Exception as e:
            logger.warning(f"SearX engine initialization failed: {e}")

        try:
            self.engines['duckduckgo'] = DuckDuckGoEngine()
            self.circuit_breakers['duckduckgo'] = CircuitBreaker(failure_threshold=2, timeout=45)
        except Exception as e:
            logger.warning(f"DuckDuckGo engine initialization failed: {e}")

        # Cycle 2 engines (placeholders)
        if enable_cycle2_engines:
            try:
                self.engines['ahmia'] = AhmiaEngine()
                self.circuit_breakers['ahmia'] = CircuitBreaker(failure_threshold=3, timeout=30)
            except Exception:
                pass

            try:
                self.engines['brave'] = BraveEngine()
                self.circuit_breakers['brave'] = CircuitBreaker(failure_threshold=5, timeout=60)
            except Exception:
                pass

        # Engine priority (SearX first, DuckDuckGo as fallback)
        self.engine_priority = ['searx', 'duckduckgo']

        if enable_cycle2_engines:
            # Cycle 2: Insert Ahmia and Brave before DuckDuckGo
            self.engine_priority = ['searx', 'ahmia', 'brave', 'duckduckgo']

        self.validator = ResultValidator()

    async def search(self, query: str, max_results: int = 10, timeout: float = 30) -> Dict[str, Any]:
        """
        Try engines in priority order until success.

        Args:
            query: Search query
            max_results: Maximum number of results
            timeout: Total timeout for all attempts

        Returns:
            Dict with success status, results, and metadata
        """
        start_time = time.time()
        attempts = []

        for engine_name in self._get_available_engines():
            # Check timeout
            if time.time() - start_time > timeout:
                break

            # Check circuit breaker
            if self.circuit_breakers[engine_name].is_open():
                logger.info(f"Skipping {engine_name} - circuit breaker is open")
                attempts.append({
                    'engine': engine_name,
                    'skipped': True,
                    'reason': 'circuit_breaker_open'
                })
                continue

            try:
                logger.info(f"Attempting search with {engine_name}")

                engine = self.engines[engine_name]
                results = await engine.search(query, max_results)

                # Validate results
                if self.validator.validate_results(results, query):
                    self.circuit_breakers[engine_name].record_success()

                    attempts.append({
                        'engine': engine_name,
                        'success': True,
                        'result_count': len(results)
                    })

                    return {
                        'success': True,
                        'engine': engine_name,
                        'query': query,
                        'results': results,
                        'total': len(results),
                        'attempts': attempts,
                        'execution_time': time.time() - start_time
                    }
                else:
                    self.circuit_breakers[engine_name].record_failure()
                    attempts.append({
                        'engine': engine_name,
                        'success': False,
                        'reason': 'validation_failed'
                    })

            except Exception as e:
                self.circuit_breakers[engine_name].record_failure()
                logger.warning(f"Search with {engine_name} failed: {e}")

                attempts.append({
                    'engine': engine_name,
                    'success': False,
                    'error': str(e)
                })

        # All engines failed
        return {
            'success': False,
            'error': 'All search engines failed',
            'query': query,
            'results': [],
            'total': 0,
            'attempts': attempts,
            'engines_tried': [a['engine'] for a in attempts],
            'execution_time': time.time() - start_time
        }

    def _get_available_engines(self) -> List[str]:
        """Get list of available engines in priority order"""
        return [
            engine_name
            for engine_name in self.engine_priority
            if engine_name in self.engines
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        stats = {}

        for engine_name, breaker in self.circuit_breakers.items():
            stats[engine_name] = {
                'state': breaker.state.state,
                'success_rate': round(breaker.get_success_rate(), 3),
                'total_attempts': breaker.state.total_attempts,
                'failures': breaker.state.failures
            }

        return stats


# ========================================================================
# === TESTING & CLI ===
# ========================================================================

async def main():
    """Test multi-engine search"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 multi_engine_search.py 'search query'")
        sys.exit(1)

    query = sys.argv[1]

    # Initialize search
    search = MultiEngineSearch()

    # Perform search
    print(f"\n🔍 Searching for: {query}\n")

    result = await search.search(query, max_results=5)

    if result['success']:
        print(f"✅ Success! Found {result['total']} results using {result['engine']}")
        print(f"⏱️  Execution time: {result['execution_time']:.2f}s\n")

        for idx, item in enumerate(result['results'], 1):
            print(f"{idx}. {item['title']}")
            print(f"   {item['url']}")
            print(f"   {item['snippet'][:100]}...")
            print()
    else:
        print(f"❌ Search failed: {result['error']}")
        print(f"⏱️  Execution time: {result['execution_time']:.2f}s\n")

        print("Attempts:")
        for attempt in result['attempts']:
            print(f"  - {attempt['engine']}: {attempt.get('error', attempt.get('reason', 'unknown'))}")

    # Show stats
    print("\n📊 Engine Statistics:")
    stats = search.get_stats()
    for engine, data in stats.items():
        print(f"  {engine}: {data['state']} (success rate: {data['success_rate']:.1%}, attempts: {data['total_attempts']})")


if __name__ == '__main__':
    asyncio.run(main())

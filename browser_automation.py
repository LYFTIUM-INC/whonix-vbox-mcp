#!/usr/bin/env python3
"""
Browser API v2 - Consolidated
All browser automation components merged into a single optimized file

This consolidated file contains:
- MCPParameterHandler: Parameter validation and serialization
- EnhancedNetworkManager: Multi-strategy network requests with fallbacks
- EnhancedJavaScriptExecutor: JavaScript execution with module resolution
- EnhancedSearchAPI: DuckDuckGo search integration
- FormHandler: Form analysis and submission
- SessionManager: Persistent cookie-based sessions
- StealthBrowser: Anti-bot detection evasion
- ContentExtractor: HTML parsing and structured data extraction
- ParallelProcessor: Async batch processing
- BrowserAPIv2: Main unified interface

Version: 2.0-consolidated
"""

import asyncio
import aiohttp
import json
import sys
import os
import time
import random
import subprocess
import tempfile
import hashlib
import re
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse, urlencode
from pathlib import Path

# Set up logging FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import persistent cache
try:
    from persistent_cache import get_cache
    PERSISTENT_CACHE_AVAILABLE = True
except ImportError:
    PERSISTENT_CACHE_AVAILABLE = False
    logger.warning("Persistent cache not available - falling back to in-memory cache")

# Import optional dependencies
try:
    from bs4 import BeautifulSoup
except ImportError:
    logger.error("BeautifulSoup4 not installed. Install with: pip3 install beautifulsoup4")
    BeautifulSoup = None

try:
    import html2text
except ImportError:
    logger.warning("html2text not installed. Install with: pip3 install html2text")
    html2text = None

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
        logger.warning("Using deprecated duckduckgo_search. Please upgrade to ddgs: pip3 install ddgs")
    except ImportError:
        logger.error("ddgs not installed. Install with: pip3 install ddgs")
        DDGS = None

# Import multi-engine search system
try:
    from multi_engine_search import MultiEngineSearch
    MULTI_ENGINE_AVAILABLE = True
except ImportError:
    logger.warning("multi_engine_search not available - using single-engine search")
    MultiEngineSearch = None
    MULTI_ENGINE_AVAILABLE = False


# ========================================================================
# === UTILITY CLASSES ===
# ========================================================================

class MCPParameterHandler:
    """Handles parameter serialization and validation for MCP tools"""

    @staticmethod
    def serialize_for_mcp(value: Any) -> str:
        """Convert any parameter type to MCP-compatible string format"""
        if value is None:
            return ""

        if isinstance(value, str):
            try:
                json.loads(value)
                return value  # Already valid JSON string
            except json.JSONDecodeError:
                return value

        elif isinstance(value, (list, dict)):
            return json.dumps(value, separators=(',', ':'))

        elif isinstance(value, (int, float, bool)):
            return str(value)

        else:
            return json.dumps(str(value))

    @staticmethod
    def deserialize_from_mcp(value: str, expected_type: type = None) -> Any:
        """Convert MCP string parameter back to expected Python type"""
        if not value:
            return None if expected_type != str else ""

        if expected_type is None:
            return MCPParameterHandler._smart_deserialize(value)

        if expected_type == str:
            return value

        elif expected_type == list:
            try:
                result = json.loads(value)
                return result if isinstance(result, list) else [result]
            except json.JSONDecodeError:
                return [item.strip() for item in value.split(',') if item.strip()]

        elif expected_type == dict:
            try:
                result = json.loads(value)
                return result if isinstance(result, dict) else {}
            except json.JSONDecodeError:
                return {}

        elif expected_type in (int, float):
            try:
                return expected_type(value)
            except ValueError:
                return 0

        elif expected_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')

        else:
            return MCPParameterHandler._smart_deserialize(value)

    @staticmethod
    def _smart_deserialize(value: str) -> Any:
        """Intelligently deserialize a string value"""
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            pass

        return value

    @staticmethod
    def validate_interactions_parameter(interactions: str) -> Dict[str, Any]:
        """Validate and parse the interactions parameter for webpage elements"""
        if not interactions:
            return {
                'valid': False,
                'error': 'Interactions parameter is required',
                'parsed': []
            }

        try:
            parsed = json.loads(interactions)

            if not isinstance(parsed, list):
                parsed = [parsed]

            validated_interactions = []
            for i, interaction in enumerate(parsed):
                if not isinstance(interaction, dict):
                    return {
                        'valid': False,
                        'error': f'Interaction {i} must be an object',
                        'parsed': []
                    }

                if 'action' not in interaction:
                    return {
                        'valid': False,
                        'error': f'Interaction {i} missing required "action" field',
                        'parsed': []
                    }

                valid_actions = ['click', 'type', 'select', 'hover', 'wait', 'scroll']
                if interaction['action'] not in valid_actions:
                    return {
                        'valid': False,
                        'error': f'Invalid action "{interaction["action"]}" in interaction {i}. Valid actions: {valid_actions}',
                        'parsed': []
                    }

                validated_interaction = {
                    'action': interaction['action'],
                    'selector': interaction.get('selector', ''),
                    'value': interaction.get('value', ''),
                    'wait': interaction.get('wait', 1000),
                    'timeout': interaction.get('timeout', 30000)
                }

                validated_interactions.append(validated_interaction)

            return {
                'valid': True,
                'error': None,
                'parsed': validated_interactions
            }

        except json.JSONDecodeError as e:
            return {
                'valid': False,
                'error': f'Invalid JSON format: {str(e)}',
                'parsed': []
            }


# ========================================================================
# === NETWORK MANAGEMENT ===
# ========================================================================

@dataclass
class RequestStrategy:
    name: str
    success_rate: float
    last_used: float
    failures: int


class EnhancedNetworkManager:
    """Multi-strategy network manager with automatic fallbacks"""

    def __init__(self):
        self.strategies = {
            'tor_primary': RequestStrategy('tor_primary', 0.5, 0, 0),
            'tor_new_circuit': RequestStrategy('tor_new_circuit', 0.7, 0, 0),
            'tor_bridge': RequestStrategy('tor_bridge', 0.6, 0, 0),
            'fallback_direct': RequestStrategy('fallback_direct', 0.9, 0, 0)
        }

        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
        ]

        self.tor_socks_proxy = "socks5://127.0.0.1:9050"
        self.sessions = {}
        self.circuit_health = {}

    async def make_resilient_request(self, url: str, method: str = 'GET', **kwargs) -> Dict[str, Any]:
        """Make a resilient request using multiple strategies and fallbacks"""
        ordered_strategies = self._get_ordered_strategies()

        last_error = None
        attempts = []

        for strategy in ordered_strategies:
            try:
                result = await self._execute_strategy(strategy, url, method, **kwargs)

                attempt_info = {
                    'strategy': strategy,
                    'success': result.get('success', False),
                    'status_code': result.get('status_code', 0),
                    'response_time': result.get('response_time', 0)
                }
                attempts.append(attempt_info)

                if result.get('success'):
                    self._update_strategy_success(strategy, True)
                    result['strategy_used'] = strategy
                    result['attempts'] = attempts
                    return result
                else:
                    self._update_strategy_success(strategy, False)
                    last_error = result.get('error', 'Unknown error')

                    await asyncio.sleep(random.uniform(1, 3))

            except Exception as e:
                self._update_strategy_success(strategy, False)
                last_error = str(e)
                attempts.append({
                    'strategy': strategy,
                    'success': False,
                    'error': str(e)
                })
                continue

        return {
            'success': False,
            'error': f'All strategies failed. Last error: {last_error}',
            'attempts': attempts,
            'strategies_tried': len(ordered_strategies)
        }

    def _get_ordered_strategies(self) -> List[str]:
        """Order strategies by success rate and recency"""
        current_time = time.time()

        scored_strategies = []
        for name, strategy in self.strategies.items():
            recency_bonus = max(0, 1 - (current_time - strategy.last_used) / 3600)
            score = strategy.success_rate + (recency_bonus * 0.1)
            scored_strategies.append((score, name))

        scored_strategies.sort(reverse=True)
        return [name for score, name in scored_strategies]

    async def _execute_strategy(self, strategy: str, url: str, method: str, **kwargs) -> Dict[str, Any]:
        """Execute a specific request strategy"""
        start_time = time.time()

        if strategy == 'tor_primary':
            result = await self._tor_request(url, method, **kwargs)
        elif strategy == 'tor_new_circuit':
            await self._new_tor_circuit()
            result = await self._tor_request(url, method, **kwargs)
        elif strategy == 'tor_bridge':
            result = await self._tor_bridge_request(url, method, **kwargs)
        elif strategy == 'fallback_direct':
            result = await self._direct_request(url, method, **kwargs)
        else:
            result = {'success': False, 'error': f'Unknown strategy: {strategy}'}

        response_time = time.time() - start_time
        result['response_time'] = response_time

        return result

    async def _tor_request(self, url: str, method: str, **kwargs) -> Dict[str, Any]:
        """Make request through Tor SOCKS proxy"""
        try:
            # Create SSL context that doesn't verify certificates (needed for Tor)
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.ProxyConnector.from_url(self.tor_socks_proxy, ssl=ssl_context)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:

                headers = kwargs.get('headers', {})
                headers.update({
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                })

                async with session.request(method, url, headers=headers, **kwargs) as response:
                    content = await response.text()

                    return {
                        'success': True,
                        'status_code': response.status,
                        'content': content,
                        'content_size': len(content),
                        'headers': dict(response.headers),
                        'user_agent': headers['User-Agent'],
                        'method': method,
                        'url': url
                    }

        except Exception as e:
            return {
                'success': False,
                'status_code': 0,
                'error': str(e),
                'method': method,
                'url': url
            }

    async def _new_tor_circuit(self):
        """Request a new Tor circuit"""
        try:
            control_process = await asyncio.create_subprocess_exec(
                'bash', '-c', 'echo "NEWNYM" | nc 127.0.0.1 9051',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            await control_process.wait()
            await asyncio.sleep(3)

        except Exception:
            await asyncio.sleep(5)

    async def _tor_bridge_request(self, url: str, method: str, **kwargs) -> Dict[str, Any]:
        """Make request through Tor with bridge configuration"""
        try:
            # Create SSL context that doesn't verify certificates (needed for Tor)
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.ProxyConnector.from_url(self.tor_socks_proxy, ssl=ssl_context)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as session:

                headers = kwargs.get('headers', {})
                headers.update({
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'no-cache'
                })

                async with session.request(method, url, headers=headers, **kwargs) as response:
                    content = await response.text()

                    return {
                        'success': True,
                        'status_code': response.status,
                        'content': content,
                        'content_size': len(content),
                        'headers': dict(response.headers),
                        'user_agent': headers['User-Agent'],
                        'method': method,
                        'url': url,
                        'via_bridge': True
                    }

        except Exception as e:
            return {
                'success': False,
                'status_code': 0,
                'error': str(e),
                'method': method,
                'url': url
            }

    async def _direct_request(self, url: str, method: str, **kwargs) -> Dict[str, Any]:
        """Make direct request (fallback when Tor fails)"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15)
            ) as session:

                headers = kwargs.get('headers', {})
                headers.update({
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9'
                })

                async with session.request(method, url, headers=headers, **kwargs) as response:
                    content = await response.text()

                    return {
                        'success': True,
                        'status_code': response.status,
                        'content': content,
                        'content_size': len(content),
                        'headers': dict(response.headers),
                        'user_agent': headers['User-Agent'],
                        'method': method,
                        'url': url,
                        'via_direct': True
                    }

        except Exception as e:
            return {
                'success': False,
                'status_code': 0,
                'error': str(e),
                'method': method,
                'url': url
            }

    def _update_strategy_success(self, strategy: str, success: bool):
        """Update strategy success rate using exponential moving average"""
        if strategy not in self.strategies:
            return

        strategy_obj = self.strategies[strategy]

        alpha = 0.3
        if success:
            new_rate = strategy_obj.success_rate * (1 - alpha) + alpha
        else:
            new_rate = strategy_obj.success_rate * (1 - alpha)
            strategy_obj.failures += 1

        strategy_obj.success_rate = max(0.1, min(0.95, new_rate))
        strategy_obj.last_used = time.time()

    def get_strategy_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get current strategy statistics"""
        stats = {}
        for name, strategy in self.strategies.items():
            stats[name] = {
                'success_rate': round(strategy.success_rate, 3),
                'failures': strategy.failures,
                'last_used': strategy.last_used,
                'last_used_ago': round(time.time() - strategy.last_used, 1) if strategy.last_used > 0 else None
            }
        return stats


# ========================================================================
# === JAVASCRIPT EXECUTION ===
# ========================================================================

class EnhancedJavaScriptExecutor:
    """Enhanced JavaScript executor with module resolution fixes"""

    def __init__(self):
        self.node_paths = [
            '/usr/bin/node',
            '/usr/local/bin/node',
            '~/.npm-global/bin/node',
            '/opt/node/bin/node'
        ]

        self.npm_global_paths = [
            '~/.npm-global/lib/node_modules',
            '/usr/lib/node_modules',
            '/usr/local/lib/node_modules',
            '/opt/node/lib/node_modules'
        ]

        self.playwright_paths = [
            '~/.npm-global/lib/node_modules/playwright',
            '/usr/lib/node_modules/playwright',
            '/usr/local/lib/node_modules/playwright',
            '/home/user/.npm-global/lib/node_modules/playwright'
        ]

        self.node_executable = self._find_node_executable()
        self.environment = self._build_environment()

    def _find_node_executable(self) -> str:
        """Find the best Node.js executable"""
        for path in self.node_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path) and os.access(expanded_path, os.X_OK):
                return expanded_path

        try:
            result = subprocess.run(['which', 'node'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        return '/usr/bin/node'

    def _build_environment(self) -> Dict[str, str]:
        """Build comprehensive Node.js environment"""
        env = os.environ.copy()

        node_paths = []
        for path in self.npm_global_paths:
            expanded = os.path.expanduser(path)
            if os.path.exists(expanded):
                node_paths.append(expanded)

        if node_paths:
            env['NODE_PATH'] = ':'.join(node_paths)

        path_additions = [
            os.path.expanduser('~/.npm-global/bin'),
            '/usr/local/bin',
            '/usr/bin'
        ]

        existing_path = env.get('PATH', '')
        new_path_entries = [p for p in path_additions if os.path.exists(p)]
        env['PATH'] = ':'.join(new_path_entries + [existing_path])

        return env

    async def execute_javascript(self, url: str, javascript_code: str, browser: str = 'chromium') -> Dict[str, Any]:
        """Execute JavaScript on a webpage with enhanced module resolution"""

        result = await self._execute_with_enhanced_env(url, javascript_code, browser)

        if result.get('success'):
            return result

        return await self._execute_with_fallback(url, javascript_code, browser)

    async def _execute_with_enhanced_env(self, url: str, javascript_code: str, browser: str) -> Dict[str, Any]:
        """Execute with enhanced environment and module resolution"""

        script_content = self._build_playwright_script(url, javascript_code, browser)

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as temp_file:
                temp_file.write(script_content)
                temp_file_path = temp_file.name

            process = await asyncio.create_subprocess_exec(
                self.node_executable,
                temp_file_path,
                env=self.environment,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)

            os.unlink(temp_file_path)

            if process.returncode == 0:
                try:
                    result = json.loads(stdout.decode())
                    result['execution_method'] = 'enhanced_env'
                    return result
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': 'Failed to parse JSON output',
                        'raw_output': stdout.decode(),
                        'stderr': stderr.decode()
                    }
            else:
                return {
                    'success': False,
                    'error': f'Node.js execution failed with code {process.returncode}',
                    'stderr': stderr.decode(),
                    'stdout': stdout.decode()
                }

        except asyncio.TimeoutError:
            return {
                'success': False,
                'error': 'JavaScript execution timed out after 60 seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Execution error: {str(e)}'
            }

    async def _execute_with_fallback(self, url: str, javascript_code: str, browser: str) -> Dict[str, Any]:
        """Fallback execution method using direct module installation"""

        await self._ensure_playwright_available()

        script_content = self._build_fallback_script(url, javascript_code, browser)

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as temp_file:
                temp_file.write(script_content)
                temp_file_path = temp_file.name

            process = await asyncio.create_subprocess_exec(
                self.node_executable,
                temp_file_path,
                env=self.environment,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=90)

            os.unlink(temp_file_path)

            if process.returncode == 0:
                try:
                    result = json.loads(stdout.decode())
                    result['execution_method'] = 'fallback'
                    return result
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': 'Failed to parse JSON output from fallback method',
                        'raw_output': stdout.decode(),
                        'stderr': stderr.decode()
                    }
            else:
                return {
                    'success': False,
                    'error': f'Fallback execution failed with code {process.returncode}',
                    'stderr': stderr.decode(),
                    'stdout': stdout.decode()
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Fallback execution error: {str(e)}'
            }

    def _build_playwright_script(self, url: str, javascript_code: str, browser: str) -> str:
        """Build a complete Playwright script with error handling"""

        browser_import = {
            'chromium': 'chromium',
            'firefox': 'firefox',
            'webkit': 'webkit'
        }.get(browser, 'chromium')

        return f"""
const {{ {browser_import} }} = require('playwright');

(async () => {{
    let browser = null;
    let page = null;

    try {{
        browser = await {browser_import}.launch({{
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--proxy-server=socks5://127.0.0.1:9050'
            ]
        }});

        page = await browser.newPage();

        await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36');

        await page.goto('{url}', {{
            waitUntil: 'networkidle',
            timeout: 30000
        }});

        const result = await page.evaluate(() => {{
            try {{
                return {javascript_code};
            }} catch (error) {{
                return {{ error: error.message, stack: error.stack }};
            }}
        }});

        const title = await page.title();
        const url_actual = page.url();

        console.log(JSON.stringify({{
            success: true,
            result: result,
            page_title: title,
            final_url: url_actual,
            browser: '{browser}',
            timestamp: new Date().toISOString()
        }}));

    }} catch (error) {{
        console.log(JSON.stringify({{
            success: false,
            error: error.message,
            stack: error.stack,
            url: '{url}',
            browser: '{browser}'
        }}));
    }} finally {{
        if (page) await page.close();
        if (browser) await browser.close();
    }}
}})();
"""

    def _build_fallback_script(self, url: str, javascript_code: str, browser: str) -> str:
        """Build a fallback script that tries to require playwright from different locations"""

        return f"""
let playwright = null;
const playwrightPaths = [
    'playwright',
    '/usr/lib/node_modules/playwright',
    '/usr/local/lib/node_modules/playwright',
    process.env.HOME + '/.npm-global/lib/node_modules/playwright'
];

for (const path of playwrightPaths) {{
    try {{
        playwright = require(path);
        break;
    }} catch (e) {{
        continue;
    }}
}}

if (!playwright) {{
    console.log(JSON.stringify({{
        success: false,
        error: 'Playwright module not found in any location',
        searched_paths: playwrightPaths
    }}));
    process.exit(1);
}}

const {{ {browser} }} = playwright;

(async () => {{
    let browser_instance = null;
    let page = null;

    try {{
        browser_instance = await {browser}.launch({{
            headless: true,
            args: ['--no-sandbox', '--proxy-server=socks5://127.0.0.1:9050']
        }});

        page = await browser_instance.newPage();
        await page.goto('{url}', {{ timeout: 30000 }});

        const result = await page.evaluate(() => {{
            return {javascript_code};
        }});

        console.log(JSON.stringify({{
            success: true,
            result: result,
            execution_method: 'fallback',
            page_title: await page.title()
        }}));

    }} catch (error) {{
        console.log(JSON.stringify({{
            success: false,
            error: error.message,
            execution_method: 'fallback'
        }}));
    }} finally {{
        if (page) await page.close();
        if (browser_instance) await browser_instance.close();
    }}
}})();
"""

    async def _ensure_playwright_available(self):
        """Ensure Playwright is available for execution"""
        for path in self.playwright_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                return True

        try:
            install_process = await asyncio.create_subprocess_exec(
                'npm', 'install', 'playwright',
                cwd=tempfile.gettempdir(),
                env=self.environment,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            await asyncio.wait_for(install_process.communicate(), timeout=120)
            return install_process.returncode == 0

        except Exception:
            return False


# ========================================================================
# === OPTIMIZATION: RATE LIMITING & CIRCUIT BREAKER ===
# ========================================================================

from collections import deque

class SearchRateLimiter:
    """Rate limiter with circuit breaker pattern"""

    def __init__(self):
        self.min_interval = 2.0  # Minimum seconds between requests
        self.last_request_time = 0
        self.recent_failures = deque(maxlen=5)
        self.circuit_state = 'closed'  # closed, open, half-open
        self.circuit_opened_at = None
        self.circuit_breaker_threshold = 3
        self.circuit_breaker_cooldown = 30.0

    def should_allow_request(self) -> tuple:
        """Check if request should be allowed, return (allowed, wait_time)"""
        now = time.time()

        # Check circuit breaker
        if self.circuit_state == 'open':
            if now - self.circuit_opened_at < self.circuit_breaker_cooldown:
                wait = self.circuit_breaker_cooldown - (now - self.circuit_opened_at)
                return False, wait
            else:
                self.circuit_state = 'half-open'

        # Check rate limit
        time_since_last = now - self.last_request_time
        if time_since_last < self.min_interval:
            wait = self.min_interval - time_since_last
            return False, wait

        return True, 0.0

    def record_request(self, success: bool, result_count: int = 0):
        """Record request outcome"""
        self.last_request_time = time.time()

        if not success or result_count == 0:
            self.recent_failures.append(time.time())
            recent_failure_count = sum(1 for t in self.recent_failures if time.time() - t < 60)

            if recent_failure_count >= self.circuit_breaker_threshold:
                self.circuit_state = 'open'
                self.circuit_opened_at = time.time()
                logger.warning(f"Circuit breaker OPENED after {recent_failure_count} failures")
        else:
            if self.circuit_state == 'half-open':
                self.circuit_state = 'closed'
                self.recent_failures.clear()


# ========================================================================
# === OPTIMIZATION: RESPONSE CACHE ===
# ========================================================================

@dataclass
class CacheEntry:
    """Cached response entry"""
    data: Any
    timestamp: float
    ttl: float
    hits: int = 0

class ResponseCache:
    """Simple TTL-based cache"""

    def __init__(self, max_size: int = 100, default_ttl: float = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = {'hits': 0, 'misses': 0}

    def _make_key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    def get(self, url: str) -> Optional[Any]:
        key = self._make_key(url)

        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry.timestamp > entry.ttl:
                del self.cache[key]
                self.stats['misses'] += 1
                return None

            entry.hits += 1
            self.stats['hits'] += 1
            return entry.data

        self.stats['misses'] += 1
        return None

    def set(self, url: str, data: Any, ttl: Optional[float] = None):
        if len(self.cache) >= self.max_size:
            # Evict oldest
            oldest = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
            del self.cache[oldest]

        key = self._make_key(url)
        self.cache[key] = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=ttl or self.default_ttl
        )


# ========================================================================
# === OPTIMIZATION: SMART TRUNCATION ===
# ========================================================================

class SmartTruncator:
    """Intelligent content truncation"""

    def __init__(self, max_tokens: int = 10000):
        self.max_tokens = max_tokens
        self.max_chars = max_tokens * 4

    def truncate(self, content: str) -> Dict:
        if len(content) <= self.max_chars:
            return {'content': content, 'truncated': False}

        # Simple smart truncation - keep beginning and structure
        truncated = content[:self.max_chars]

        # Try to end at a tag boundary
        last_close = truncated.rfind('</')
        if last_close > self.max_chars * 0.8:
            truncated = truncated[:last_close + truncated[last_close:].find('>') + 1]

        truncated += '\n<!-- TRUNCATED -->'

        return {
            'content': truncated,
            'truncated': True,
            'original_size': len(content),
            'final_size': len(truncated)
        }


# ========================================================================
# === SEARCH API ===
# ========================================================================

class EnhancedSearchAPI:
    """Enhanced search API with multi-engine fallback and rate limiting"""

    def __init__(self, use_proxy: bool = True, cache=None):
        self.use_proxy = use_proxy
        self.proxy = 'socks5://127.0.0.1:9050' if use_proxy else None
        self.rate_limiter = SearchRateLimiter()
        self.cache = cache  # Accept cache from BrowserAPIv2

        # Initialize multi-engine search if available
        if MULTI_ENGINE_AVAILABLE:
            self.multi_engine = MultiEngineSearch(enable_cycle2_engines=True)
            self.available = True
            logger.info("Multi-engine search initialized (Cycle 2: DuckDuckGo + Ahmia + Brave)")
        elif DDGS is not None:
            self.multi_engine = None
            self.available = True
            logger.warning("Using single-engine DuckDuckGo search (multi-engine not available)")
        else:
            self.multi_engine = None
            self.available = False
            logger.error("No search engines available")

    def search(self, query: str, max_results: int = 10) -> Dict:
        """Perform search with multi-engine fallback, caching, and rate limiting"""
        if not self.available:
            return {
                'success': False,
                'error': 'No search engines available',
                'query': query,
                'results': [],
                'total': 0
            }

        # Check cache first (if available)
        cache_key = f"search:{query}:{max_results}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"Cache HIT for query: {query}")
                cached['cache_hit'] = True
                return cached

        # Check rate limiter
        allowed, wait_time = self.rate_limiter.should_allow_request()
        if not allowed:
            logger.info(f"Rate limiting: waiting {wait_time:.1f}s")
            time.sleep(wait_time)

        try:
            # Use multi-engine search if available
            if self.multi_engine:
                logger.info(f"Cache MISS - Using multi-engine search for query: {query}")
                result = asyncio.run(self.multi_engine.search(query, max_results))

                # Record success/failure
                self.rate_limiter.record_request(result['success'], result.get('total', 0))

                # Cache successful results (TTL: 1 hour)
                if self.cache and result['success']:
                    self.cache.set(cache_key, result, ttl=3600)
                    logger.info(f"Cached search results for query: {query}")

                result['cache_hit'] = False
                return result
            else:
                # Fallback to single-engine DuckDuckGo
                logger.info(f"Cache MISS - Using single-engine DuckDuckGo for query: {query}")
                result = self._single_engine_search(query, max_results)

                # Cache successful results
                if self.cache and result['success']:
                    self.cache.set(cache_key, result, ttl=3600)
                    logger.info(f"Cached search results for query: {query}")

                result['cache_hit'] = False
                return result

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            self.rate_limiter.record_request(False, 0)
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'results': [],
                'total': 0,
                'cache_hit': False
            }

    def _single_engine_search(self, query: str, max_results: int = 10) -> Dict:
        """Single-engine DuckDuckGo search (fallback)"""
        try:
            ddgs = DDGS(proxy=self.proxy if self.proxy else None)

            results = list(ddgs.text(
                query,
                max_results=max_results,
                safesearch='moderate',
                backend='api'
            ))

            formatted_results = []
            for idx, result in enumerate(results):
                formatted_results.append({
                    'rank': idx + 1,
                    'title': result.get('title', ''),
                    'url': result.get('href', ''),
                    'snippet': result.get('body', ''),
                    'source': 'duckduckgo'
                })

            # Record success
            self.rate_limiter.record_request(True, len(formatted_results))

            return {
                'success': True,
                'query': query,
                'engine': 'duckduckgo',
                'results': formatted_results,
                'total': len(formatted_results),
                'max_results': max_results,
                'via_tor': self.use_proxy
            }

        except Exception as e:
            logger.error(f"Single-engine search failed: {str(e)}")
            self.rate_limiter.record_request(False, 0)
            return self.fallback_search(query, max_results)

    def fallback_search(self, query: str, max_results: int = 10) -> Dict:
        """Fallback search using alternative methods"""
        try:
            if self.use_proxy:
                logger.info("Trying search without proxy as fallback")
                ddgs = DDGS()
                results = list(ddgs.text(query, max_results=max_results))

                formatted_results = []
                for idx, result in enumerate(results):
                    formatted_results.append({
                        'rank': idx + 1,
                        'title': result.get('title', ''),
                        'url': result.get('href', ''),
                        'snippet': result.get('body', ''),
                        'source': 'duckduckgo-direct'
                    })

                return {
                    'success': True,
                    'query': query,
                    'results': formatted_results,
                    'total': len(formatted_results),
                    'max_results': max_results,
                    'via_tor': False,
                    'fallback': True
                }

        except Exception as e:
            logger.error(f"Fallback search also failed: {str(e)}")

        return {
            'success': False,
            'query': query,
            'error': 'All search methods failed',
            'results': [],
            'total': 0
        }

    def search_news(self, query: str, max_results: int = 10) -> Dict:
        """Search for news articles"""
        try:
            ddgs = DDGS(proxy=self.proxy if self.proxy else None)
            results = list(ddgs.news(query, max_results=max_results))

            formatted_results = []
            for result in results:
                formatted_results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'excerpt': result.get('excerpt', ''),
                    'date': result.get('date', ''),
                    'source': result.get('source', ''),
                    'type': 'news'
                })

            return {
                'success': True,
                'query': query,
                'results': formatted_results,
                'total': len(formatted_results),
                'type': 'news'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': []
            }

    def search_images(self, query: str, max_results: int = 10) -> Dict:
        """Search for images"""
        try:
            ddgs = DDGS(proxy=self.proxy if self.proxy else None)
            results = list(ddgs.images(query, max_results=max_results))

            formatted_results = []
            for result in results:
                formatted_results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'thumbnail': result.get('thumbnail', ''),
                    'image': result.get('image', ''),
                    'source': result.get('source', ''),
                    'type': 'image'
                })

            return {
                'success': True,
                'query': query,
                'results': formatted_results,
                'total': len(formatted_results),
                'type': 'images'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': []
            }


# ========================================================================
# === FORM HANDLER ===
# ========================================================================

class FormHandler:
    """Form analysis and submission handler"""

    def __init__(self, cookie_file: str = "/tmp/session_cookies.txt", use_proxy: bool = True):
        self.cookie_file = cookie_file
        self.use_proxy = use_proxy

        if self.use_proxy:
            self.proxies = {
                'http': 'socks5://127.0.0.1:9050',
                'https': 'socks5://127.0.0.1:9050'
            }
        else:
            self.proxies = None

        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

    def analyze_forms(self, url: str) -> List[Dict]:
        """Detect and analyze all forms on a webpage"""
        if not BeautifulSoup:
            return {'success': False, 'error': 'BeautifulSoup4 not available'}

        try:
            html = self._fetch_page_with_curl(url)

            if not html:
                return []

            soup = BeautifulSoup(html, 'html.parser')

            forms = []
            for idx, form in enumerate(soup.find_all('form')):
                form_info = self._extract_form_data(form, url, idx)
                forms.append(form_info)

            return forms

        except Exception as e:
            logger.error(f"Form analysis failed: {str(e)}")
            return []

    def _fetch_page_with_curl(self, url: str) -> str:
        """Fetch page content using curl with cookie management"""
        try:
            cmd = [
                'curl', '-s',
                '-b', self.cookie_file,
                '-c', self.cookie_file,
                '-A', self.user_agent,
                '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                '-H', 'Accept-Language: en-US,en;q=0.9',
                '--compressed'
            ]

            if self.use_proxy:
                cmd.extend(['--socks5-hostname', '127.0.0.1:9050'])

            cmd.append(url)

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"Curl failed: {result.stderr}")
                return ""

        except Exception as e:
            logger.error(f"Fetch failed: {str(e)}")
            return ""

    def _extract_form_data(self, form, base_url: str, form_index: int) -> Dict:
        """Extract detailed information from a form element"""

        form_data = {
            'form_index': form_index,
            'action': form.get('action', ''),
            'method': form.get('method', 'GET').upper(),
            'enctype': form.get('enctype', 'application/x-www-form-urlencoded'),
            'name': form.get('name', ''),
            'id': form.get('id', ''),
            'fields': [],
            'csrf_token': None,
            'submit_buttons': []
        }

        if form_data['action']:
            form_data['action'] = urljoin(base_url, form_data['action'])
        else:
            form_data['action'] = base_url

        for field in form.find_all(['input', 'select', 'textarea', 'button']):
            field_info = self._extract_field_info(field)

            if field_info:
                if field_info['name'] and ('csrf' in field_info['name'].lower() or
                                          'token' in field_info['name'].lower()):
                    form_data['csrf_token'] = field_info['value']

                if field_info['type'] == 'submit':
                    form_data['submit_buttons'].append(field_info)
                else:
                    form_data['fields'].append(field_info)

        return form_data

    def _extract_field_info(self, field) -> Optional[Dict]:
        """Extract information from a form field"""
        field_name = field.get('name', '')
        if not field_name and field.name != 'button':
            return None

        field_info = {
            'name': field_name,
            'type': field.get('type', 'text' if field.name == 'input' else field.name),
            'value': field.get('value', ''),
            'required': field.get('required') is not None,
            'placeholder': field.get('placeholder', ''),
            'maxlength': field.get('maxlength', ''),
            'pattern': field.get('pattern', ''),
            'tag': field.name
        }

        if field.name == 'select':
            options = []
            for option in field.find_all('option'):
                options.append({
                    'value': option.get('value', option.text),
                    'text': option.text.strip(),
                    'selected': option.get('selected') is not None
                })
            field_info['options'] = options

        if field.name == 'textarea':
            field_info['value'] = field.text.strip()

        return field_info

    def submit_form(self, url: str, form_data: Dict, files: Optional[Dict] = None) -> Dict:
        """Submit a form with provided data"""
        try:
            method = form_data.get('method', 'POST').upper()

            cmd = [
                'curl', '-s', '-L',
                '-b', self.cookie_file,
                '-c', self.cookie_file,
                '-A', self.user_agent,
                '-w', '\n%{http_code}',
                '--compressed'
            ]

            if self.use_proxy:
                cmd.extend(['--socks5-hostname', '127.0.0.1:9050'])

            if method == 'POST':
                if files:
                    for field_name, file_path in files.items():
                        cmd.extend(['-F', f'{field_name}=@{file_path}'])

                    for key, value in form_data.items():
                        if key not in files:
                            cmd.extend(['-F', f'{key}={value}'])
                else:
                    for key, value in form_data.items():
                        cmd.extend(['-d', f'{key}={value}'])
            else:
                query_string = urlencode(form_data)
                url = f"{url}?{query_string}"

            cmd.append(url)

            result = subprocess.run(cmd, capture_output=True, text=True)

            lines = result.stdout.strip().split('\n')
            if lines:
                status_code = lines[-1] if lines[-1].isdigit() else '200'
                content = '\n'.join(lines[:-1]) if len(lines) > 1 else result.stdout
            else:
                status_code = '000'
                content = ''

            return {
                'success': result.returncode == 0 and int(status_code) < 400,
                'status_code': int(status_code),
                'url': url,
                'method': method,
                'content_preview': content[:1000],
                'content_length': len(content)
            }

        except Exception as e:
            logger.error(f"Form submission failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }


# ========================================================================
# === SESSION MANAGER ===
# ========================================================================

class SessionManager:
    """Manages persistent browser sessions with cookie handling"""

    def __init__(self, session_dir: str = None):
        if session_dir is None:
            # Use temp directory if user home not accessible
            home_dir = os.path.expanduser("~")
            if os.access(home_dir, os.W_OK):
                session_dir = os.path.join(home_dir, ".browser_sessions")
            else:
                session_dir = os.path.join(tempfile.gettempdir(), "browser_sessions")
        self.session_dir = session_dir
        os.makedirs(session_dir, exist_ok=True)

        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

        self.metadata_file = os.path.join(session_dir, 'sessions.json')
        self.load_metadata()

    def load_metadata(self):
        """Load session metadata from disk"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except:
                self.metadata = {}
        else:
            self.metadata = {}

    def save_metadata(self):
        """Save session metadata to disk"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {str(e)}")

    def create_session(self, session_id: str, initial_url: Optional[str] = None,
                      description: str = "") -> Dict:
        """Create a new browser session"""
        cookie_file = os.path.join(self.session_dir, f"{session_id}.cookies")
        header_file = os.path.join(self.session_dir, f"{session_id}.headers")

        session_info = {
            'session_id': session_id,
            'cookie_file': cookie_file,
            'header_file': header_file,
            'created': time.time(),
            'last_accessed': time.time(),
            'description': description,
            'url_history': [],
            'request_count': 0
        }

        if initial_url:
            result = self._initialize_session(session_id, initial_url)
            session_info['initialized'] = result['success']
            if result['success']:
                session_info['url_history'].append(initial_url)
                session_info['request_count'] = 1
        else:
            session_info['initialized'] = False

        self.metadata[session_id] = session_info
        self.save_metadata()

        return {
            'success': True,
            'session': session_info
        }

    def _initialize_session(self, session_id: str, url: str) -> Dict:
        """Initialize session with first request"""
        session = self.metadata.get(session_id, {})
        cookie_file = session.get('cookie_file')

        if not cookie_file:
            return {'success': False, 'error': 'Session not found'}

        try:
            cmd = [
                'curl', '-s',
                '-c', cookie_file,
                '-D', session.get('header_file', '/dev/null'),
                '-A', self.user_agent,
                '--socks5-hostname', '127.0.0.1:9050',
                url
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            return {
                'success': result.returncode == 0,
                'content_length': len(result.stdout)
            }

        except Exception as e:
            logger.error(f"Session initialization failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    def load_session(self, session_id: str) -> Optional[Dict]:
        """Load an existing session"""
        if session_id not in self.metadata:
            return None

        session_info = self.metadata[session_id]

        if not os.path.exists(session_info['cookie_file']):
            logger.warning(f"Cookie file missing for session {session_id}")
            session_info['cookies_missing'] = True

        session_info['last_accessed'] = time.time()
        self.metadata[session_id] = session_info
        self.save_metadata()

        return session_info

    def make_request(self, session_id: str, url: str, method: str = 'GET',
                    data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
        """Make HTTP request using session cookies"""
        session = self.load_session(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}

        cookie_file = session['cookie_file']

        try:
            cmd = [
                'curl', '-s', '-L',
                '-b', cookie_file,
                '-c', cookie_file,
                '-A', self.user_agent,
                '-w', '\n%{http_code}\n%{time_total}',
                '--socks5-hostname', '127.0.0.1:9050',
                '--compressed'
            ]

            if headers:
                for key, value in headers.items():
                    cmd.extend(['-H', f'{key}: {value}'])

            if method == 'POST' and data:
                for key, value in data.items():
                    cmd.extend(['-d', f'{key}={value}'])
            elif method != 'GET':
                cmd.extend(['-X', method])

            cmd.append(url)

            result = subprocess.run(cmd, capture_output=True, text=True)

            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                time_total = lines[-1]
                status_code = lines[-2]
                content = '\n'.join(lines[:-2])
            else:
                status_code = '000'
                time_total = '0'
                content = result.stdout

            session['url_history'].append(url)
            session['request_count'] += 1
            session['last_accessed'] = time.time()
            self.metadata[session_id] = session
            self.save_metadata()

            return {
                'success': True,
                'session_id': session_id,
                'status_code': int(status_code) if status_code.isdigit() else 0,
                'response_time': float(time_total) if time_total.replace('.', '').isdigit() else 0,
                'content': content,
                'content_length': len(content),
                'url': url,
                'method': method
            }

        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }

    def delete_session(self, session_id: str) -> Dict:
        """Delete a session and its associated files"""
        if session_id not in self.metadata:
            return {'success': False, 'error': 'Session not found'}

        session = self.metadata[session_id]

        if os.path.exists(session['cookie_file']):
            os.remove(session['cookie_file'])

        if os.path.exists(session.get('header_file', '')):
            os.remove(session['header_file'])

        del self.metadata[session_id]
        self.save_metadata()

        return {
            'success': True,
            'deleted': session_id
        }

    def list_sessions(self) -> List[Dict]:
        """List all available sessions"""
        sessions = []
        for session_id, info in self.metadata.items():
            sessions.append({
                'session_id': session_id,
                'created': info['created'],
                'last_accessed': info['last_accessed'],
                'request_count': info['request_count'],
                'description': info.get('description', ''),
                'age_hours': (time.time() - info['created']) / 3600
            })

        return sorted(sessions, key=lambda x: x['last_accessed'], reverse=True)


# ========================================================================
# === STEALTH BROWSER ===
# ========================================================================

class StealthBrowser:
    """Anti-bot detection evasion techniques"""

    def __init__(self, use_proxy: bool = True):
        self.use_proxy = use_proxy

        self.user_agents = [
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]

        self.accept_languages = [
            'en-US,en;q=0.9',
            'en-GB,en;q=0.9',
            'en-US,en;q=0.9,fr;q=0.8',
            'en-US,en;q=0.9,de;q=0.8',
            'en-US,en;q=0.9,es;q=0.8'
        ]

        self.browser_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Dnt': '1'
        }

        self.timing_patterns = {
            'page_load': (2, 5),
            'read_time': (5, 30),
            'form_fill': (10, 45),
            'click_delay': (0.5, 2),
            'scroll_time': (1, 3)
        }

    def get_random_user_agent(self) -> str:
        """Get a random realistic user agent"""
        return random.choice(self.user_agents)

    def get_stealth_headers(self, url: Optional[str] = None) -> Dict[str, str]:
        """Generate a complete set of stealth headers"""
        headers = self.browser_headers.copy()

        user_agent = self.get_random_user_agent()
        headers['User-Agent'] = user_agent

        headers['Accept-Language'] = random.choice(self.accept_languages)

        return headers

    def random_delay(self, delay_type: str = 'click_delay') -> float:
        """Generate human-like random delay"""
        if delay_type in self.timing_patterns:
            min_delay, max_delay = self.timing_patterns[delay_type]
        else:
            min_delay, max_delay = 0.5, 2.0

        mean = (min_delay + max_delay) / 2
        std_dev = (max_delay - min_delay) / 4

        delay = random.gauss(mean, std_dev)
        delay = max(min_delay, min(delay, max_delay))

        time.sleep(delay)
        return delay

    def make_stealth_request(self, url: str, method: str = 'GET',
                           data: Optional[Dict] = None,
                           cookies: Optional[str] = None) -> Dict:
        """Make HTTP request with full stealth mode"""
        try:
            self.random_delay('click_delay')

            headers = self.get_stealth_headers()
            cmd = ['curl', '-s', '-L']

            for key, value in headers.items():
                cmd.extend(['-H', f'{key}: {value}'])

            cmd.extend(['--compressed', '--http2'])

            # Disable SSL verification (needed for Tor with outdated system clocks)
            cmd.extend(['--insecure'])

            if self.use_proxy:
                cmd.extend(['--socks5-hostname', '127.0.0.1:9050'])

            if cookies and os.path.exists(cookies):
                cmd.extend(['-b', cookies, '-c', cookies])

            if method == 'POST' and data:
                for key, value in data.items():
                    cmd.extend(['-d', f'{key}={value}'])
            elif method != 'GET':
                cmd.extend(['-X', method])

            cmd.extend(['-w', '\n%{http_code}\n%{time_total}\n%{size_download}'])

            cmd.append(url)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            lines = result.stdout.strip().split('\n')
            if len(lines) >= 3:
                size_download = lines[-1]
                time_total = lines[-2]
                status_code = lines[-3]
                content = '\n'.join(lines[:-3])
            else:
                status_code = '000'
                time_total = '0'
                size_download = '0'
                content = result.stdout

            return {
                'success': result.returncode == 0,
                'status_code': int(status_code) if status_code.isdigit() else 0,
                'response_time': float(time_total) if time_total.replace('.', '').isdigit() else 0,
                'content_size': int(size_download) if size_download.isdigit() else 0,
                'content': content,
                'url': url,
                'method': method,
                'user_agent': headers['User-Agent']
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Request timeout',
                'url': url
            }
        except Exception as e:
            logger.error(f"Stealth request failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }


# ========================================================================
# === CONTENT EXTRACTOR ===
# ========================================================================

class ContentExtractor:
    """Advanced HTML parsing and content extraction"""

    def __init__(self):
        self.soup = None
        self.base_url = None

        if html2text:
            self.h2t = html2text.HTML2Text()
            self.h2t.ignore_links = False
            self.h2t.ignore_images = False
            self.h2t.body_width = 0
        else:
            self.h2t = None

    def parse_html(self, html: str, base_url: Optional[str] = None) -> 'ContentExtractor':
        """Parse HTML content"""
        if not BeautifulSoup:
            raise ImportError("BeautifulSoup4 not available")

        self.soup = BeautifulSoup(html, 'html.parser')
        self.base_url = base_url
        return self

    def extract_metadata(self) -> Dict:
        """Extract page metadata"""
        if not self.soup:
            return {}

        metadata = {
            'title': '',
            'description': '',
            'keywords': '',
            'author': '',
            'canonical': '',
            'robots': '',
            'og': {},
            'twitter': {},
            'schema': []
        }

        title_tag = self.soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.text.strip()

        for meta in self.soup.find_all('meta'):
            if meta.get('name'):
                name = meta.get('name').lower()
                content = meta.get('content', '')

                if name == 'description':
                    metadata['description'] = content
                elif name == 'keywords':
                    metadata['keywords'] = content
                elif name == 'author':
                    metadata['author'] = content
                elif name == 'robots':
                    metadata['robots'] = content

            if meta.get('property'):
                prop = meta.get('property')
                if prop.startswith('og:'):
                    metadata['og'][prop] = meta.get('content', '')

            if meta.get('name'):
                name = meta.get('name')
                if name.startswith('twitter:'):
                    metadata['twitter'][name] = meta.get('content', '')

        canonical = self.soup.find('link', {'rel': 'canonical'})
        if canonical:
            metadata['canonical'] = canonical.get('href', '')

        for script in self.soup.find_all('script', type='application/ld+json'):
            try:
                schema_data = json.loads(script.string)
                metadata['schema'].append(schema_data)
            except:
                pass

        return metadata

    def extract_links(self, internal_only: bool = False,
                     external_only: bool = False,
                     include_assets: bool = False) -> List[Dict]:
        """Extract and categorize links"""
        if not self.soup:
            return []

        links = []
        domain = urlparse(self.base_url).netloc if self.base_url else None

        for a in self.soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)

            if self.base_url:
                href = urljoin(self.base_url, href)

            parsed = urlparse(href)
            if parsed.netloc == domain or not parsed.netloc:
                link_type = 'internal'
            else:
                link_type = 'external'

            if internal_only and link_type != 'internal':
                continue
            if external_only and link_type != 'external':
                continue

            links.append({
                'url': href,
                'text': text,
                'type': link_type,
                'rel': a.get('rel', []),
                'title': a.get('title', '')
            })

        return links

    def extract_tables(self, with_headers: bool = True) -> List[Dict]:
        """Extract table data"""
        if not self.soup:
            return []

        tables = []

        for table_idx, table in enumerate(self.soup.find_all('table')):
            table_data = {
                'index': table_idx,
                'headers': [],
                'rows': [],
                'caption': ''
            }

            caption = table.find('caption')
            if caption:
                table_data['caption'] = caption.text.strip()

            thead = table.find('thead')
            if thead:
                for th in thead.find_all('th'):
                    table_data['headers'].append(th.get_text(strip=True))

            tbody = table.find('tbody') or table
            for tr in tbody.find_all('tr'):
                row_data = []
                for td in tr.find_all(['td', 'th']):
                    row_data.append(td.get_text(strip=True))

                if row_data:
                    if table_data['headers'] and len(row_data) == len(table_data['headers']):
                        row_dict = dict(zip(table_data['headers'], row_data))
                        table_data['rows'].append(row_dict)
                    else:
                        table_data['rows'].append(row_data)

            tables.append(table_data)

        return tables

    def extract_text_content(self, preserve_structure: bool = False) -> str:
        """Extract clean text content"""
        if not self.soup:
            return ""

        if preserve_structure and self.h2t:
            return self.h2t.handle(str(self.soup))
        else:
            for script in self.soup(['script', 'style']):
                script.decompose()

            text = self.soup.get_text()

            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return text

    def extract_forms(self) -> List[Dict]:
        """Extract form information"""
        if not self.soup:
            return []

        forms = []

        for form_idx, form in enumerate(self.soup.find_all('form')):
            form_data = {
                'index': form_idx,
                'action': form.get('action', ''),
                'method': form.get('method', 'GET').upper(),
                'name': form.get('name', ''),
                'id': form.get('id', ''),
                'fields': []
            }

            if self.base_url and form_data['action']:
                form_data['action'] = urljoin(self.base_url, form_data['action'])

            for field in form.find_all(['input', 'select', 'textarea', 'button']):
                field_info = {
                    'tag': field.name,
                    'type': field.get('type', 'text'),
                    'name': field.get('name', ''),
                    'id': field.get('id', ''),
                    'value': field.get('value', ''),
                    'required': field.get('required') is not None,
                    'placeholder': field.get('placeholder', '')
                }

                if field.name == 'select':
                    field_info['options'] = []
                    for option in field.find_all('option'):
                        field_info['options'].append({
                            'value': option.get('value', option.text),
                            'text': option.text.strip()
                        })

                form_data['fields'].append(field_info)

            forms.append(form_data)

        return forms

    def extract_images(self) -> List[Dict]:
        """Extract image information"""
        if not self.soup:
            return []

        images = []

        for img in self.soup.find_all('img'):
            img_data = {
                'src': img.get('src', ''),
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width', ''),
                'height': img.get('height', ''),
                'loading': img.get('loading', ''),
                'srcset': img.get('srcset', '')
            }

            if self.base_url and img_data['src']:
                img_data['src'] = urljoin(self.base_url, img_data['src'])

            images.append(img_data)

        return images

    def extract_all(self) -> Dict:
        """Extract all available content"""
        return {
            'metadata': self.extract_metadata(),
            'links': self.extract_links(),
            'tables': self.extract_tables(),
            'forms': self.extract_forms(),
            'images': self.extract_images(),
            'text': self.extract_text_content()[:5000]
        }


# ========================================================================
# === PARALLEL PROCESSOR ===
# ========================================================================

class ParallelProcessor:
    """Async batch processing for browser operations"""

    def __init__(self, max_workers: int = 5, rate_limit: float = 1.0):
        self.max_workers = max_workers
        self.rate_limit = rate_limit
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

    async def process_urls_parallel(self, urls: List[str],
                                  operation: str = 'fetch',
                                  operation_args: Optional[Dict] = None) -> Dict:
        """Process multiple URLs in parallel"""
        if not urls:
            return {
                'success': True,
                'total': 0,
                'successful': 0,
                'failed': 0,
                'results': []
            }

        start_time = time.time()

        tasks = []
        for idx, url in enumerate(urls):
            task = asyncio.create_task(
                self._process_single_url(url, operation, operation_args or {}, idx)
            )
            tasks.append(task)

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=300
            )
        except asyncio.TimeoutError:
            logger.error("Batch processing timeout")
            return {
                'success': False,
                'error': 'Batch processing timeout',
                'total': len(urls),
                'results': []
            }

        successful = 0
        failed = 0
        processed_results = []

        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'url': urls[idx] if idx < len(urls) else 'unknown',
                    'success': False,
                    'error': str(result),
                    'index': idx
                })
                failed += 1
            else:
                if result.get('success', False):
                    successful += 1
                else:
                    failed += 1
                processed_results.append(result)

        total_time = time.time() - start_time

        return {
            'success': True,
            'total': len(urls),
            'successful': successful,
            'failed': failed,
            'processing_time': total_time,
            'average_time_per_url': total_time / len(urls),
            'operation': operation,
            'results': processed_results
        }

    async def _process_single_url(self, url: str, operation: str,
                                args: Dict, index: int) -> Dict:
        """Process a single URL asynchronously"""
        loop = asyncio.get_event_loop()

        try:
            if operation == 'fetch':
                result = await loop.run_in_executor(
                    self.executor,
                    self._fetch_url,
                    url, args
                )
            elif operation == 'screenshot':
                result = await loop.run_in_executor(
                    self.executor,
                    self._screenshot_url,
                    url, args
                )
            elif operation == 'analyze':
                result = await loop.run_in_executor(
                    self.executor,
                    self._analyze_url,
                    url, args
                )
            elif operation == 'search':
                result = await loop.run_in_executor(
                    self.executor,
                    self._search_query,
                    url, args
                )
            else:
                result = {
                    'success': False,
                    'error': f'Unknown operation: {operation}'
                }

            result['url'] = url
            result['index'] = index
            result['operation'] = operation

            return result

        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            return {
                'url': url,
                'index': index,
                'success': False,
                'error': str(e),
                'operation': operation
            }

    def _fetch_url(self, url: str, args: Dict) -> Dict:
        """Fetch URL content using curl"""
        try:
            start_time = time.time()

            cmd = [
                'curl', '-s', '-L',
                '-A', self.user_agent,
                '--socks5-hostname', '127.0.0.1:9050',
                '--max-time', str(args.get('timeout', 30)),
                '--compressed',
                '-w', '\n%{http_code}\n%{time_total}\n%{size_download}'
            ]

            if args.get('cookie_file'):
                cmd.extend(['-b', args['cookie_file'], '-c', args['cookie_file']])

            cmd.append(url)

            result = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=args.get('timeout', 30) + 5)

            lines = result.stdout.strip().split('\n')
            if len(lines) >= 3:
                size_download = lines[-1]
                time_total = lines[-2]
                status_code = lines[-3]
                content = '\n'.join(lines[:-3])
            else:
                status_code = '000'
                time_total = '0'
                size_download = '0'
                content = result.stdout

            processing_time = time.time() - start_time

            return {
                'success': result.returncode == 0 and int(status_code) < 400,
                'status_code': int(status_code) if status_code.isdigit() else 0,
                'response_time': float(time_total) if time_total.replace('.', '').isdigit() else 0,
                'content_size': int(size_download) if size_download.isdigit() else 0,
                'processing_time': processing_time,
                'content_preview': content[:500] if content else '',
                'has_content': len(content) > 0
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Request timeout',
                'processing_time': args.get('timeout', 30)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': 0
            }

    def _screenshot_url(self, url: str, args: Dict) -> Dict:
        """Capture URL content (simulated screenshot)"""
        # Placeholder for screenshot functionality
        return {
            'success': False,
            'error': 'Screenshot functionality not implemented in consolidated version'
        }

    def _analyze_url(self, url: str, args: Dict) -> Dict:
        """Analyze URL content"""
        try:
            fetch_result = self._fetch_url(url, args)

            if not fetch_result.get('success'):
                return fetch_result

            cmd = [
                'curl', '-s', '-L',
                '-A', self.user_agent,
                '--socks5-hostname', '127.0.0.1:9050',
                '--max-time', '30',
                url
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)

            if result.returncode != 0:
                return {
                    'success': False,
                    'error': 'Failed to fetch content for analysis'
                }

            content = result.stdout

            analysis = {
                'content_length': len(content),
                'word_count': len(content.split()),
                'line_count': len(content.splitlines()),
                'has_forms': '<form' in content.lower(),
                'has_javascript': '<script' in content.lower(),
                'has_css': '<style' in content.lower() or 'stylesheet' in content.lower(),
                'has_images': '<img' in content.lower(),
                'has_links': '<a ' in content.lower(),
                'title': '',
                'meta_description': ''
            }

            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            if title_match:
                analysis['title'] = title_match.group(1).strip()

            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', content, re.IGNORECASE)
            if desc_match:
                analysis['meta_description'] = desc_match.group(1).strip()

            return {
                'success': True,
                'analysis': analysis,
                'status_code': fetch_result.get('status_code', 0)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _search_query(self, query: str, args: Dict) -> Dict:
        """Perform search query - placeholder for integration"""
        return {
            'success': False,
            'error': 'Search functionality should use EnhancedSearchAPI directly'
        }

    def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)


# ========================================================================
# === MAIN BROWSER API ===
# ========================================================================

class BrowserAPIv2:
    """Main unified interface for enhanced browser automation"""

    def __init__(self, use_proxy: bool = True, max_workers: int = 5):
        self.use_proxy = use_proxy
        self.max_workers = max_workers

        # Initialize cache first (needed by other components)
        # OPTIMIZATION: Use persistent cache if available, fallback to in-memory
        if PERSISTENT_CACHE_AVAILABLE:
            self.cache = get_cache()
            logger.info("Using persistent SQLite cache")
        else:
            self.cache = ResponseCache(max_size=100, default_ttl=300)
            logger.warning("Using in-memory cache (not persistent)")

        # Initialize components with enhanced managers (pass cache to search API)
        self.network_manager = EnhancedNetworkManager()
        self.js_executor = EnhancedJavaScriptExecutor()
        self.search_api = EnhancedSearchAPI(use_proxy=use_proxy, cache=self.cache)
        self.form_handler = FormHandler(use_proxy=use_proxy)
        self.session_manager = SessionManager()
        self.stealth_browser = StealthBrowser(use_proxy=use_proxy)
        self.content_extractor = ContentExtractor()
        self.parallel_processor = ParallelProcessor(max_workers=max_workers)

        self.truncator = SmartTruncator(max_tokens=10000)

    def status_check(self) -> Dict:
        """Comprehensive status check with optimization metrics"""
        try:
            search_test = self.search_api.search("test", max_results=1)
            search_ok = search_test.get('success', False)

            sessions = self.session_manager.list_sessions()
            session_ok = isinstance(sessions, list)

            stealth_ok = len(self.stealth_browser.user_agents) > 0
            extractor_ok = self.content_extractor is not None
            parallel_ok = self.parallel_processor.max_workers > 0

            network_stats = self.network_manager.get_strategy_stats()

            # OPTIMIZATION: Calculate cache hit rate (works for both cache types)
            if PERSISTENT_CACHE_AVAILABLE:
                # Persistent cache uses get_stats() method
                cache_stats = self.cache.get_stats()
                cache_size = cache_stats.get('size', 0)
                cache_max_size = cache_stats.get('max_size', 0)
                cache_hits = cache_stats.get('hits', 0)
                cache_misses = cache_stats.get('misses', 0)
                cache_hit_rate = float(cache_stats.get('hit_rate', '0%').rstrip('%'))
            else:
                # In-memory cache uses attributes
                cache_size = len(self.cache.cache)
                cache_max_size = self.cache.max_size
                cache_hits = self.cache.stats['hits']
                cache_misses = self.cache.stats['misses']
                cache_total = cache_hits + cache_misses
                cache_hit_rate = (cache_hits / cache_total * 100) if cache_total > 0 else 0

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'enhanced_search': {
                        'status': 'operational' if search_ok else 'error',
                        'details': 'duckduckgo-search integration',
                        'rate_limiter': {
                            'circuit_state': self.search_api.rate_limiter.circuit_state,
                            'min_interval': f"{self.search_api.rate_limiter.min_interval}s"
                        }
                    },
                    'form_handler': {
                        'status': 'operational',
                        'details': 'POST request automation with BeautifulSoup'
                    },
                    'session_manager': {
                        'status': 'operational' if session_ok else 'error',
                        'active_sessions': len(sessions) if session_ok else 0
                    },
                    'stealth_browser': {
                        'status': 'operational' if stealth_ok else 'error',
                        'user_agents': len(self.stealth_browser.user_agents)
                    },
                    'content_extractor': {
                        'status': 'operational' if extractor_ok else 'error',
                        'details': 'BeautifulSoup4 + structured data extraction'
                    },
                    'parallel_processor': {
                        'status': 'operational' if parallel_ok else 'error',
                        'max_workers': self.parallel_processor.max_workers
                    },
                    'network_manager': {
                        'status': 'operational',
                        'strategies': network_stats
                    },
                    'javascript_executor': {
                        'status': 'operational',
                        'node_executable': self.js_executor.node_executable
                    },
                    'response_cache': {
                        'status': 'operational',
                        'type': 'persistent' if PERSISTENT_CACHE_AVAILABLE else 'memory',
                        'size': cache_size,
                        'max_size': cache_max_size,
                        'hits': cache_hits,
                        'misses': cache_misses,
                        'hit_rate': f"{cache_hit_rate:.1f}%"
                    },
                    'smart_truncator': {
                        'status': 'operational',
                        'max_tokens': self.truncator.max_tokens,
                        'max_chars': self.truncator.max_chars
                    }
                },
                'capabilities': {
                    'enhanced_search': True,
                    'rate_limiting': True,
                    'circuit_breaker': True,
                    'response_caching': True,
                    'smart_truncation': True,
                    'form_automation': True,
                    'session_persistence': True,
                    'anti_bot_evasion': True,
                    'content_analysis': True,
                    'parallel_processing': True,
                    'tor_integration': self.use_proxy,
                    'resilient_networking': True,
                    'javascript_execution': True
                },
                'version': '2.0.0-consolidated-optimized',
                'mode': 'enhanced+optimized'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def enhanced_search(self, query: str, max_results: int = 10,
                       search_type: str = 'text') -> Dict:
        """Perform enhanced search with actual results"""
        try:
            if search_type == 'news':
                result = self.search_api.search_news(query, max_results)
            elif search_type == 'images':
                result = self.search_api.search_images(query, max_results)
            else:
                result = self.search_api.search(query, max_results)

            result['api_version'] = '2.0-consolidated'
            result['enhancement'] = 'duckduckgo-search integration'

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': query
            }

    def analyze_forms(self, url: str) -> Dict:
        """Analyze forms on a webpage"""
        try:
            forms = self.form_handler.analyze_forms(url)

            return {
                'success': True,
                'url': url,
                'forms_found': len(forms),
                'forms': forms,
                'api_version': '2.0-consolidated'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    def submit_form(self, url: str, form_data: Dict,
                   files: Optional[Dict] = None) -> Dict:
        """Submit form with enhanced capabilities"""
        try:
            result = self.form_handler.submit_form(url, form_data, files)
            result['api_version'] = '2.0-consolidated'
            result['enhancement'] = 'cookie persistence + secure submission'

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    def create_session(self, session_id: str, initial_url: Optional[str] = None,
                      description: str = "") -> Dict:
        """Create persistent session"""
        try:
            result = self.session_manager.create_session(session_id, initial_url, description)
            result['api_version'] = '2.0-consolidated'
            result['enhancement'] = 'persistent cookie management'

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }

    def session_request(self, session_id: str, url: str, method: str = 'GET',
                       data: Optional[Dict] = None) -> Dict:
        """Make request using persistent session"""
        try:
            result = self.session_manager.make_request(session_id, url, method, data)
            result['api_version'] = '2.0-consolidated'

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }

    def stealth_request(self, url: str, method: str = 'GET',
                       data: Optional[Dict] = None, use_cache: bool = True,
                       max_retries: int = 3) -> Dict:
        """Make request with anti-bot evasion, caching, truncation, and retry logic"""
        try:
            # OPTIMIZATION: Check cache first (GET only)
            if method == 'GET' and use_cache:
                cached = self.cache.get(url)
                if cached:
                    # Calculate cache age (works for both cache types)
                    cache_age = 'N/A'
                    if hasattr(self.cache, 'cache') and hasattr(self.cache, '_make_key'):
                        # In-memory cache
                        key = self.cache._make_key(url)
                        if key in self.cache.cache:
                            cache_age = time.time() - self.cache.cache[key].timestamp

                    return {
                        **cached,
                        'cached': True,
                        'cache_age': cache_age,
                        'cache_type': 'persistent' if PERSISTENT_CACHE_AVAILABLE else 'memory'
                    }

            # Fetch from network with retry logic
            result = None
            last_error = None

            for attempt in range(max_retries):
                result = self.stealth_browser.make_stealth_request(url, method, data)

                # Check if request succeeded
                if result.get('success') and result.get('status_code', 0) == 200:
                    break

                # Tor circuit failure or connection issue - retry
                if result.get('status_code', 0) == 0 or result.get('status_code', 0) >= 500:
                    last_error = result.get('error', f"HTTP {result.get('status_code')}")

                    if attempt < max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s
                        wait_time = 2 ** attempt
                        logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {last_error}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue

                # Client error (4xx) - don't retry
                break

            # If all retries failed, return last error
            if not result or not result.get('success'):
                return {
                    'success': False,
                    'error': last_error or 'Request failed after retries',
                    'url': url,
                    'retries': max_retries
                }

            # OPTIMIZATION: Truncate large content
            if result.get('success') and result.get('content'):
                truncation_result = self.truncator.truncate(result['content'])
                result['content'] = truncation_result['content']
                if truncation_result['truncated']:
                    result['truncation'] = {
                        'truncated': True,
                        'original_size': truncation_result['original_size'],
                        'final_size': truncation_result['final_size']
                    }

            # OPTIMIZATION: Cache successful GET requests
            if method == 'GET' and result.get('success') and use_cache:
                # Determine TTL based on status code
                ttl = 30 if result.get('status_code', 0) >= 400 else 300
                self.cache.set(url, result, ttl=ttl)

            result['api_version'] = '2.0-consolidated-optimized'
            result['enhancement'] = 'anti-bot + caching + truncation'
            result['cached'] = False

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    async def resilient_request(self, url: str, method: str = 'GET', **kwargs) -> Dict:
        """Make resilient request with automatic fallbacks"""
        try:
            result = await self.network_manager.make_resilient_request(url, method, **kwargs)
            result['api_version'] = '2.0-consolidated'
            result['enhancement'] = 'multi-strategy resilient networking'

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    async def execute_javascript(self, url: str, javascript_code: str,
                                browser: str = 'chromium') -> Dict:
        """Execute JavaScript on a webpage"""
        try:
            result = await self.js_executor.execute_javascript(url, javascript_code, browser)
            result['api_version'] = '2.0-consolidated'

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    def extract_content(self, html: str, base_url: Optional[str] = None,
                       extract_type: str = 'all') -> Dict:
        """Extract structured content from HTML"""
        try:
            self.content_extractor.parse_html(html, base_url)

            if extract_type == 'metadata':
                extracted = self.content_extractor.extract_metadata()
            elif extract_type == 'links':
                extracted = self.content_extractor.extract_links()
            elif extract_type == 'tables':
                extracted = self.content_extractor.extract_tables()
            elif extract_type == 'forms':
                extracted = self.content_extractor.extract_forms()
            else:
                extracted = self.content_extractor.extract_all()

            return {
                'success': True,
                'extracted': extracted,
                'extract_type': extract_type,
                'api_version': '2.0-consolidated',
                'enhancement': 'BeautifulSoup4 + structured data'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'extract_type': extract_type
            }

    async def parallel_process(self, urls: List[str], operation: str = 'fetch',
                             operation_args: Optional[Dict] = None) -> Dict:
        """Process multiple URLs in parallel"""
        try:
            result = await self.parallel_processor.process_urls_parallel(
                urls, operation, operation_args
            )
            result['api_version'] = '2.0-consolidated'
            result['enhancement'] = 'asyncio parallel processing'

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'operation': operation
            }

    def cleanup(self):
        """Cleanup resources"""
        self.parallel_processor.cleanup()


# ========================================================================
# === CLI INTERFACE ===
# ========================================================================

def main():
    """Command line interface for Browser API v2 Consolidated"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: browser_api_v2_consolidated.py <command> [args...]',
            'commands': {
                'status': 'Check API status',
                'search': '<query> [max_results] - Enhanced search',
                'capture': '<url> - Capture page content via stealth request',
                'forms': '<url> - Analyze forms',
                'submit': '<url> <form_data_json> - Submit form',
                'session': '<action> <session_id> [url] - Session management',
                'stealth': '<url> - Stealth request',
                'extract': '<html_file> [base_url] - Extract content',
                'parallel': '<operation> <urls_comma_separated> - Parallel processing'
            },
            'version': '2.0-consolidated'
        }, indent=2))
        sys.exit(1)

    command = sys.argv[1].lower()
    api = BrowserAPIv2()

    try:
        if command == 'status':
            result = api.status_check()

        elif command == 'search':
            query = sys.argv[2] if len(sys.argv) > 2 else ''
            max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            result = api.enhanced_search(query, max_results)

        elif command == 'forms':
            url = sys.argv[2] if len(sys.argv) > 2 else ''
            result = api.analyze_forms(url)

        elif command == 'submit':
            url = sys.argv[2] if len(sys.argv) > 2 else ''
            form_data = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
            result = api.submit_form(url, form_data)

        elif command == 'session':
            action = sys.argv[2] if len(sys.argv) > 2 else 'create'
            session_id = sys.argv[3] if len(sys.argv) > 3 else f"session_{int(time.time())}"

            if action == 'create':
                url = sys.argv[4] if len(sys.argv) > 4 else None
                result = api.create_session(session_id, url)
            elif action == 'request':
                url = sys.argv[4] if len(sys.argv) > 4 else ''
                result = api.session_request(session_id, url)
            else:
                result = {'success': False, 'error': f'Unknown session action: {action}'}

        elif command == 'stealth':
            url = sys.argv[2] if len(sys.argv) > 2 else ''
            result = api.stealth_request(url)

        elif command == 'capture':
            url = sys.argv[2] if len(sys.argv) > 2 else ''
            # Capture is an alias for stealth request (fetch page content)
            result = api.stealth_request(url)

        elif command == 'extract':
            html_file = sys.argv[2] if len(sys.argv) > 2 else ''
            base_url = sys.argv[3] if len(sys.argv) > 3 else None

            if html_file == '-':
                html_content = sys.stdin.read()
            else:
                with open(html_file, 'r') as f:
                    html_content = f.read()

            result = api.extract_content(html_content, base_url)

        elif command == 'parallel':
            operation = sys.argv[2] if len(sys.argv) > 2 else 'fetch'
            urls = sys.argv[3].split(',') if len(sys.argv) > 3 else []

            # Run async operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(api.parallel_process(urls, operation))
            finally:
                loop.close()

        else:
            result = {
                'success': False,
                'error': f'Unknown command: {command}'
            }

        print(json.dumps(result, indent=2))

    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e),
            'command': command
        }, indent=2))

    finally:
        api.cleanup()


if __name__ == '__main__':
    main()
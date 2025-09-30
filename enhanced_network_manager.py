#!/usr/bin/env python3
"""
Enhanced Network Manager for Browser Automation
Addresses critical network connectivity issues identified in testing
"""

import asyncio
import aiohttp
import json
import time
import random
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class RequestStrategy:
    name: str
    success_rate: float
    last_used: float
    failures: int

class EnhancedNetworkManager:
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
        """
        Make a resilient request using multiple strategies and fallbacks
        """
        # Order strategies by success rate and recency
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
                    
                    # Brief delay before trying next strategy
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
        
        # Calculate strategy scores (success rate + recency bonus)
        scored_strategies = []
        for name, strategy in self.strategies.items():
            recency_bonus = max(0, 1 - (current_time - strategy.last_used) / 3600)  # Bonus for recent use
            score = strategy.success_rate + (recency_bonus * 0.1)
            scored_strategies.append((score, name))
        
        # Sort by score (descending) and return strategy names
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
        
        # Add response time
        response_time = time.time() - start_time
        result['response_time'] = response_time
        
        return result
    
    async def _tor_request(self, url: str, method: str, **kwargs) -> Dict[str, Any]:
        """Make request through Tor SOCKS proxy"""
        try:
            connector = aiohttp.ProxyConnector.from_url(self.tor_socks_proxy)
            
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
            # Send NEWNYM signal to Tor control port
            process = await asyncio.create_subprocess_exec(
                'echo', 'NEWNYM', 
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Alternative: Use telnet to control port if available
            control_process = await asyncio.create_subprocess_exec(
                'bash', '-c', 'echo "NEWNYM" | nc 127.0.0.1 9051',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await control_process.wait()
            
            # Wait for circuit to establish
            await asyncio.sleep(3)
            
        except Exception as e:
            # If control port access fails, just wait and hope for the best
            await asyncio.sleep(5)
    
    async def _tor_bridge_request(self, url: str, method: str, **kwargs) -> Dict[str, Any]:
        """Make request through Tor with bridge configuration"""
        # For now, same as regular Tor request but with longer timeout
        try:
            connector = aiohttp.ProxyConnector.from_url(self.tor_socks_proxy)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=60)  # Longer timeout for bridges
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
        
        # Update success rate (exponential moving average)
        alpha = 0.3  # Learning rate
        if success:
            new_rate = strategy_obj.success_rate * (1 - alpha) + alpha
        else:
            new_rate = strategy_obj.success_rate * (1 - alpha)
            strategy_obj.failures += 1
        
        strategy_obj.success_rate = max(0.1, min(0.95, new_rate))  # Keep in bounds
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


async def test_enhanced_network_manager():
    """Test the enhanced network manager"""
    manager = EnhancedNetworkManager()
    
    test_urls = [
        'https://httpbin.org/get',
        'https://httpbin.org/user-agent',
        'https://example.com'
    ]
    
    print("Testing Enhanced Network Manager")
    print("=" * 50)
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        result = await manager.make_resilient_request(url)
        
        print(f"Success: {result.get('success')}")
        print(f"Status Code: {result.get('status_code', 'N/A')}")
        print(f"Strategy Used: {result.get('strategy_used', 'N/A')}")
        print(f"Response Time: {result.get('response_time', 0):.2f}s")
        print(f"Content Size: {result.get('content_size', 0)} bytes")
        
        if not result.get('success'):
            print(f"Error: {result.get('error')}")
            print(f"Strategies Tried: {result.get('strategies_tried', 0)}")
    
    print("\nStrategy Statistics:")
    stats = manager.get_strategy_stats()
    for strategy, data in stats.items():
        print(f"  {strategy}: {data['success_rate']:.1%} success, {data['failures']} failures")


if __name__ == '__main__':
    asyncio.run(test_enhanced_network_manager())
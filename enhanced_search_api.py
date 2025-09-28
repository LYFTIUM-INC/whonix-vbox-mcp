#!/usr/bin/env python3
"""
Enhanced Search API - Provides actual search results instead of redirects
Uses duckduckgo-search library with Tor proxy support
"""

import json
import sys
import os
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from duckduckgo_search import DDGS
except ImportError:
    logger.error("duckduckgo-search not installed. Install with: pip3 install duckduckgo-search")
    DDGS = None

class EnhancedSearchAPI:
    def __init__(self, use_proxy: bool = True):
        """Initialize search API with optional Tor proxy"""
        self.use_proxy = use_proxy
        self.proxy = 'socks5://127.0.0.1:9050' if use_proxy else None
        
        if not DDGS:
            raise ImportError("duckduckgo-search library not available")
    
    def search(self, query: str, max_results: int = 10) -> Dict:
        """
        Perform search and return actual results
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            Dict with search results or error information
        """
        try:
            # Initialize DDGS with proxy if enabled
            ddgs = DDGS(proxy=self.proxy if self.proxy else None)
            
            # Perform text search
            results = list(ddgs.text(
                query,
                max_results=max_results,
                safesearch='moderate',
                backend='api'
            ))
            
            # Format results for consistent output
            formatted_results = []
            for idx, result in enumerate(results):
                formatted_results.append({
                    'rank': idx + 1,
                    'title': result.get('title', ''),
                    'url': result.get('href', ''),
                    'snippet': result.get('body', ''),
                    'source': 'duckduckgo'
                })
            
            return {
                'success': True,
                'query': query,
                'results': formatted_results,
                'total': len(formatted_results),
                'max_results': max_results,
                'via_tor': self.use_proxy
            }
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            # Try fallback search
            return self.fallback_search(query, max_results)
    
    def fallback_search(self, query: str, max_results: int = 10) -> Dict:
        """
        Fallback search using alternative methods
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            
        Returns:
            Dict with fallback search attempt
        """
        try:
            # Try without proxy as fallback
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


def main():
    """Command line interface for enhanced search"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: enhanced_search_api.py <query> [max_results] [search_type]'
        }))
        sys.exit(1)
    
    query = sys.argv[1]
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    search_type = sys.argv[3] if len(sys.argv) > 3 else 'text'
    
    # Initialize search API
    api = EnhancedSearchAPI(use_proxy=True)
    
    # Perform search based on type
    if search_type == 'news':
        result = api.search_news(query, max_results)
    elif search_type == 'images':
        result = api.search_images(query, max_results)
    else:
        result = api.search(query, max_results)
    
    # Output JSON result
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Custom Automation Executor
==========================

Execute custom automation tasks based on natural language descriptions.

Features:
- Natural language task parsing
- Multiple task type support
- Integration with browser API
- Structured result formatting

Cycle 1: 3 task types (extract_headings, count_links, check_content)
Cycle 2: +3 task types (get_metadata, extract_images, extract_forms)

Version: 1.0 (Cycle 1)
"""

import asyncio
import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    from bs4 import BeautifulSoup
except ImportError:
    logger.error("BeautifulSoup4 not installed. Install with: pip3 install beautifulsoup4")
    BeautifulSoup = None


# ========================================================================
# === TASK DEFINITIONS ===
# ========================================================================

@dataclass
class TaskDefinition:
    """Definition of a task type"""
    name: str
    keywords: List[str]
    description: str
    example: str
    cycle: int  # 1 or 2


# Task catalog
TASK_CATALOG = {
    # Cycle 1 tasks
    'extract_headings': TaskDefinition(
        name='extract_headings',
        keywords=['heading', 'h1', 'h2', 'h3', 'title tag', 'headers'],
        description='Extract heading tags (h1, h2, h3) from the page',
        example='Extract all headings from the page',
        cycle=1
    ),

    'count_links': TaskDefinition(
        name='count_links',
        keywords=['count links', 'count all links', 'how many links', 'number of links', 'link count', 'find links'],
        description='Count and categorize links (internal/external)',
        example='Count all links on the page',
        cycle=1
    ),

    'check_content': TaskDefinition(
        name='check_content',
        keywords=['check for', 'contains', 'find text', 'search for', 'look for'],
        description='Check if specific text or pattern exists on the page',
        example='Check if the page contains "login"',
        cycle=1
    ),

    # Cycle 2 tasks (placeholders)
    'get_metadata': TaskDefinition(
        name='get_metadata',
        keywords=['metadata', 'meta tags', 'description', 'keywords', 'og tags'],
        description='Extract page metadata (title, description, keywords)',
        example='Get page metadata',
        cycle=2
    ),

    'extract_images': TaskDefinition(
        name='extract_images',
        keywords=['images', 'img tags', 'pictures', 'photos', 'image urls'],
        description='Extract image URLs and alt text',
        example='Extract all images from the page',
        cycle=2
    ),

    'extract_forms': TaskDefinition(
        name='extract_forms',
        keywords=['form', 'input fields', 'form structure', 'form fields'],
        description='Identify and analyze forms on the page',
        example='Extract all forms from the page',
        cycle=2
    )
}


# ========================================================================
# === TASK PARSER ===
# ========================================================================

class TaskParser:
    """Parse natural language task descriptions"""

    def __init__(self, cycle: int = 1):
        """
        Initialize task parser.

        Args:
            cycle: Which cycle tasks to support (1 or 2)
        """
        self.cycle = cycle
        self.available_tasks = {
            name: task for name, task in TASK_CATALOG.items()
            if task.cycle <= cycle
        }

    def parse(self, description: str) -> Dict[str, Any]:
        """
        Parse task description to identify task type.

        Args:
            description: Natural language task description

        Returns:
            Dict with task_type, confidence, and extracted parameters
        """
        description_lower = description.lower()

        # Try to match against known task keywords
        scores = {}

        for task_name, task_def in self.available_tasks.items():
            score = 0

            for keyword in task_def.keywords:
                if keyword in description_lower:
                    # Longer keywords get higher scores
                    score += len(keyword.split())

            if score > 0:
                scores[task_name] = score

        if not scores:
            return {
                'task_type': 'unknown',
                'confidence': 0.0,
                'parameters': {},
                'available_tasks': list(self.available_tasks.keys())
            }

        # Get task with highest score
        best_task = max(scores.keys(), key=lambda k: scores[k])
        max_score = scores[best_task]

        # Calculate confidence
        total_keywords = len(self.available_tasks[best_task].keywords)
        confidence = min(1.0, max_score / total_keywords)

        # Extract parameters based on task type
        parameters = self._extract_parameters(best_task, description)

        return {
            'task_type': best_task,
            'confidence': confidence,
            'parameters': parameters,
            'description': description
        }

    def _extract_parameters(self, task_type: str, description: str) -> Dict[str, Any]:
        """Extract parameters from description based on task type"""
        parameters = {}

        if task_type == 'check_content':
            # Try to extract quoted text
            # e.g., "check for 'login button'" → search_text = "login button"
            match = re.search(r'["\']([^"\']+)["\']', description)
            if match:
                parameters['search_text'] = match.group(1)

        elif task_type == 'count_links':
            # Check if specific link type requested
            if 'internal' in description.lower():
                parameters['link_type'] = 'internal'
            elif 'external' in description.lower():
                parameters['link_type'] = 'external'

        return parameters


# ========================================================================
# === TASK HANDLERS (CYCLE 1) ===
# ========================================================================

class TaskHandlers:
    """Handlers for different task types"""

    @staticmethod
    async def extract_headings(html: str, description: str, params: Dict) -> Dict:
        """Extract heading tags from HTML (Cycle 1)"""
        if not BeautifulSoup:
            return {'error': 'BeautifulSoup4 not available'}

        soup = BeautifulSoup(html, 'html.parser')

        headings = {
            'h1': [h.get_text(strip=True) for h in soup.find_all('h1')],
            'h2': [h.get_text(strip=True) for h in soup.find_all('h2')],
            'h3': [h.get_text(strip=True) for h in soup.find_all('h3')]
        }

        return {
            'headings': headings,
            'total_count': sum(len(v) for v in headings.values()),
            'h1_count': len(headings['h1']),
            'h2_count': len(headings['h2']),
            'h3_count': len(headings['h3'])
        }

    @staticmethod
    async def count_links(html: str, description: str, params: Dict) -> Dict:
        """Count and categorize links (Cycle 1)"""
        if not BeautifulSoup:
            return {'error': 'BeautifulSoup4 not available'}

        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=True)

        internal = []
        external = []
        anchors = []
        base_domain = params.get('base_domain', '')

        for link in links:
            href = link['href']

            if href.startswith('#'):
                anchors.append(href)
            elif href.startswith('/') or (base_domain and base_domain in href):
                internal.append(href)
            elif href.startswith('http'):
                external.append(href)

        # Filter by type if requested
        link_type = params.get('link_type', 'all')

        if link_type == 'internal':
            return {
                'total_links': len(internal),
                'link_type': 'internal',
                'links': internal[:20],  # Show first 20
                'truncated': len(internal) > 20
            }
        elif link_type == 'external':
            return {
                'total_links': len(external),
                'link_type': 'external',
                'links': external[:20],
                'truncated': len(external) > 20
            }
        else:
            return {
                'total_links': len(links),
                'internal_links': len(internal),
                'external_links': len(external),
                'anchor_links': len(anchors),
                'sample_internal': internal[:5],
                'sample_external': external[:5],
                'sample_anchors': anchors[:5]
            }

    @staticmethod
    async def check_content(html: str, description: str, params: Dict) -> Dict:
        """Check if specific content exists (Cycle 1)"""
        if not BeautifulSoup:
            return {'error': 'BeautifulSoup4 not available'}

        search_text = params.get('search_text', '')

        if not search_text:
            return {
                'error': 'No search text provided',
                'hint': 'Use quotes to specify search text, e.g., check for "login button"'
            }

        soup = BeautifulSoup(html, 'html.parser')
        text_content = soup.get_text()

        search_lower = search_text.lower()
        content_lower = text_content.lower()

        found = search_lower in content_lower

        # Count occurrences
        count = content_lower.count(search_lower)

        # Find context (surrounding text)
        contexts = []
        if found:
            start_pos = 0
            while True:
                pos = content_lower.find(search_lower, start_pos)
                if pos == -1:
                    break

                # Extract context (50 chars before and after)
                context_start = max(0, pos - 50)
                context_end = min(len(text_content), pos + len(search_text) + 50)

                context = text_content[context_start:context_end].strip()
                contexts.append(context)

                start_pos = pos + 1

                if len(contexts) >= 5:  # Limit to 5 contexts
                    break

        return {
            'found': found,
            'search_text': search_text,
            'occurrences': count,
            'contexts': contexts[:3]  # Show first 3 contexts
        }

    # Cycle 2 task handlers (placeholders)
    @staticmethod
    async def get_metadata(html: str, description: str, params: Dict) -> Dict:
        """Extract page metadata (Cycle 2)"""
        raise NotImplementedError("get_metadata will be implemented in Cycle 2")

    @staticmethod
    async def extract_images(html: str, description: str, params: Dict) -> Dict:
        """Extract image URLs and alt text (Cycle 2)"""
        raise NotImplementedError("extract_images will be implemented in Cycle 2")

    @staticmethod
    async def extract_forms(html: str, description: str, params: Dict) -> Dict:
        """Identify and analyze forms (Cycle 2)"""
        raise NotImplementedError("extract_forms will be implemented in Cycle 2")


# ========================================================================
# === CUSTOM AUTOMATION EXECUTOR ===
# ========================================================================

class CustomAutomationExecutor:
    """
    Execute custom automation tasks based on natural language descriptions.

    Cycle 1: 3 task types
    Cycle 2: 6 task types
    """

    def __init__(self, browser_api=None, cycle: int = 1):
        """
        Initialize executor.

        Args:
            browser_api: Browser API instance (BrowserAPIv2)
            cycle: Which cycle tasks to support (1 or 2)
        """
        self.api = browser_api
        self.cycle = cycle
        self.parser = TaskParser(cycle=cycle)

        # Map task types to handlers
        self.task_handlers = {
            'extract_headings': TaskHandlers.extract_headings,
            'count_links': TaskHandlers.count_links,
            'check_content': TaskHandlers.check_content
        }

        # Add Cycle 2 handlers if enabled
        if cycle >= 2:
            self.task_handlers.update({
                'get_metadata': TaskHandlers.get_metadata,
                'extract_images': TaskHandlers.extract_images,
                'extract_forms': TaskHandlers.extract_forms
            })

    async def execute_task(self, description: str, url: str, params: Dict = None) -> Dict:
        """
        Parse natural language task and execute.

        Args:
            description: Natural language task description
            url: URL to operate on
            params: Optional additional parameters

        Returns:
            Dict with success status and results
        """
        if params is None:
            params = {}

        # Parse task description
        parse_result = self.parser.parse(description)

        if parse_result['task_type'] == 'unknown':
            return {
                'success': False,
                'error': f'Could not parse task type from: {description}',
                'supported_tasks': parse_result['available_tasks'],
                'hint': 'Try using keywords like "extract headings", "count links", or "check for [text]"'
            }

        task_type = parse_result['task_type']
        confidence = parse_result['confidence']

        # Merge extracted parameters with provided parameters
        task_params = {**parse_result['parameters'], **params}

        # Add base domain for link counting
        if task_type == 'count_links' and 'base_domain' not in task_params:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            task_params['base_domain'] = parsed.netloc

        # Fetch page (if browser API provided)
        if self.api:
            try:
                # stealth_request is NOT async, don't await it
                page_result = self.api.stealth_request(url)

                if not page_result.get('success'):
                    return {
                        'success': False,
                        'error': 'Failed to fetch page',
                        'details': page_result.get('error'),
                        'url': url
                    }

                html_content = page_result['content']

            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to fetch page: {str(e)}',
                    'url': url
                }
        else:
            # For testing without browser API
            html_content = params.get('html_content', '')

            if not html_content:
                return {
                    'success': False,
                    'error': 'No browser API provided and no HTML content in params',
                    'hint': 'Provide browser_api parameter or html_content in params'
                }

        # Execute task handler
        try:
            handler = self.task_handlers[task_type]
            result = await handler(html_content, description, task_params)

            return {
                'success': True,
                'task_type': task_type,
                'confidence': confidence,
                'url': url,
                'result': result
            }

        except NotImplementedError as e:
            return {
                'success': False,
                'error': str(e),
                'task_type': task_type,
                'hint': f'Task type "{task_type}" is planned for Cycle {TASK_CATALOG[task_type].cycle}'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Task execution failed: {str(e)}',
                'task_type': task_type,
                'url': url
            }

    def get_supported_tasks(self) -> List[Dict]:
        """Get list of supported tasks"""
        return [
            {
                'name': task_def.name,
                'description': task_def.description,
                'example': task_def.example,
                'cycle': task_def.cycle
            }
            for task_def in TASK_CATALOG.values()
            if task_def.cycle <= self.cycle
        ]


# ========================================================================
# === TESTING & CLI ===
# ========================================================================

async def main():
    """Test custom automation executor"""
    import sys

    # Sample HTML for testing
    sample_html = """
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Welcome to Test Page</h1>
        <h2>Section 1</h2>
        <p>This page has a login button.</p>
        <h2>Section 2</h2>
        <p>More content here.</p>
        <h3>Subsection</h3>
        <a href="/page1">Internal Link 1</a>
        <a href="/page2">Internal Link 2</a>
        <a href="https://external.com">External Link</a>
        <a href="#top">Anchor Link</a>
    </body>
    </html>
    """

    print("🧪 Testing Custom Automation Executor\n")
    print("=" * 70)

    # Initialize executor (without browser API for testing)
    executor = CustomAutomationExecutor(cycle=1)

    # Test cases
    test_cases = [
        {
            'description': 'Extract all headings from the page',
            'url': 'http://test.local',
            'params': {'html_content': sample_html}
        },
        {
            'description': 'Count all links on the page',
            'url': 'http://test.local',
            'params': {'html_content': sample_html}
        },
        {
            'description': 'Check if the page contains "login button"',
            'url': 'http://test.local',
            'params': {'html_content': sample_html}
        },
        {
            'description': 'Extract page metadata',  # Cycle 2 task
            'url': 'http://test.local',
            'params': {'html_content': sample_html}
        }
    ]

    for idx, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {idx}: {test_case['description']}")
        print("-" * 70)

        result = await executor.execute_task(**test_case)

        if result['success']:
            print(f"✅ Task executed successfully")
            print(f"   Task Type: {result['task_type']}")
            print(f"   Confidence: {result['confidence']:.1%}")
            print(f"\n   Results:")

            for key, value in result['result'].items():
                if isinstance(value, (list, dict)):
                    import json
                    print(f"     {key}: {json.dumps(value, indent=6)}")
                else:
                    print(f"     {key}: {value}")
        else:
            print(f"❌ Task failed: {result['error']}")

            if 'hint' in result:
                print(f"   💡 Hint: {result['hint']}")

    # Show supported tasks
    print("\n" + "=" * 70)
    print("📚 Supported Tasks (Cycle 1):\n")

    for task in executor.get_supported_tasks():
        print(f"  • {task['name']}")
        print(f"    {task['description']}")
        print(f"    Example: {task['example']}\n")


if __name__ == '__main__':
    asyncio.run(main())

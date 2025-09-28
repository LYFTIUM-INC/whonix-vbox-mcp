#!/usr/bin/env python3
"""
Content Extractor - Advanced HTML parsing and content extraction
Provides structured data extraction, link analysis, and intelligent content parsing
"""

import json
import sys
import re
from typing import Dict, List, Optional, Any
import logging
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


class ContentExtractor:
    def __init__(self):
        """Initialize content extractor"""
        self.soup = None
        self.base_url = None
        
        # Initialize html2text converter if available
        if html2text:
            self.h2t = html2text.HTML2Text()
            self.h2t.ignore_links = False
            self.h2t.ignore_images = False
            self.h2t.body_width = 0  # Don't wrap lines
        else:
            self.h2t = None
    
    def parse_html(self, html: str, base_url: Optional[str] = None) -> 'ContentExtractor':
        """
        Parse HTML content
        
        Args:
            html: HTML string to parse
            base_url: Base URL for resolving relative links
            
        Returns:
            Self for method chaining
        """
        if not BeautifulSoup:
            raise ImportError("BeautifulSoup4 not available")
        
        self.soup = BeautifulSoup(html, 'html.parser')
        self.base_url = base_url
        return self
    
    def extract_metadata(self) -> Dict:
        """
        Extract page metadata (title, description, keywords, etc.)
        
        Returns:
            Dictionary with metadata
        """
        if not self.soup:
            return {}
        
        metadata = {
            'title': '',
            'description': '',
            'keywords': '',
            'author': '',
            'canonical': '',
            'robots': '',
            'og': {},  # OpenGraph
            'twitter': {},  # Twitter Cards
            'schema': []  # JSON-LD
        }
        
        # Extract title
        title_tag = self.soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.text.strip()
        
        # Extract meta tags
        for meta in self.soup.find_all('meta'):
            # Standard meta tags
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
            
            # OpenGraph tags
            if meta.get('property'):
                prop = meta.get('property')
                if prop.startswith('og:'):
                    metadata['og'][prop] = meta.get('content', '')
            
            # Twitter cards
            if meta.get('name'):
                name = meta.get('name')
                if name.startswith('twitter:'):
                    metadata['twitter'][name] = meta.get('content', '')
        
        # Extract canonical URL
        canonical = self.soup.find('link', {'rel': 'canonical'})
        if canonical:
            metadata['canonical'] = canonical.get('href', '')
        
        # Extract JSON-LD structured data
        for script in self.soup.find_all('script', type='application/ld+json'):
            try:
                schema_data = json.loads(script.string)
                metadata['schema'].append(schema_data)
            except:
                pass
        
        return metadata
    
    def extract_structured_data(self) -> List[Dict]:
        """
        Extract all structured data (JSON-LD, microdata, RDFa)
        
        Returns:
            List of structured data items
        """
        if not self.soup:
            return []
        
        structured_data = []
        
        # Extract JSON-LD
        for script in self.soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                structured_data.append({
                    'type': 'json-ld',
                    'data': data
                })
            except:
                pass
        
        # Extract microdata
        for item in self.soup.find_all(attrs={'itemscope': True}):
            microdata = self._extract_microdata(item)
            if microdata:
                structured_data.append({
                    'type': 'microdata',
                    'data': microdata
                })
        
        return structured_data
    
    def _extract_microdata(self, element) -> Dict:
        """
        Extract microdata from an element
        
        Args:
            element: BeautifulSoup element with itemscope
            
        Returns:
            Dictionary with microdata
        """
        data = {}
        
        # Get item type
        if element.get('itemtype'):
            data['@type'] = element.get('itemtype')
        
        # Extract properties
        properties = {}
        for prop in element.find_all(attrs={'itemprop': True}):
            prop_name = prop.get('itemprop')
            
            # Get property value
            if prop.get('content'):
                prop_value = prop.get('content')
            elif prop.get('href'):
                prop_value = prop.get('href')
            elif prop.get('src'):
                prop_value = prop.get('src')
            else:
                prop_value = prop.text.strip()
            
            properties[prop_name] = prop_value
        
        if properties:
            data['properties'] = properties
        
        return data if data else None
    
    def extract_links(self, internal_only: bool = False, 
                     external_only: bool = False,
                     include_assets: bool = False) -> List[Dict]:
        """
        Extract and categorize links
        
        Args:
            internal_only: Only return internal links
            external_only: Only return external links
            include_assets: Include CSS, JS, image links
            
        Returns:
            List of link dictionaries
        """
        if not self.soup:
            return []
        
        links = []
        domain = urlparse(self.base_url).netloc if self.base_url else None
        
        # Extract anchor links
        for a in self.soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)
            
            # Resolve relative URLs
            if self.base_url:
                href = urljoin(self.base_url, href)
            
            # Categorize link
            parsed = urlparse(href)
            if parsed.netloc == domain or not parsed.netloc:
                link_type = 'internal'
            else:
                link_type = 'external'
            
            # Apply filters
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
        
        # Extract asset links if requested
        if include_assets:
            # CSS links
            for link in self.soup.find_all('link', {'rel': 'stylesheet'}):
                href = link.get('href')
                if href:
                    if self.base_url:
                        href = urljoin(self.base_url, href)
                    links.append({
                        'url': href,
                        'type': 'asset',
                        'asset_type': 'css'
                    })
            
            # JavaScript links
            for script in self.soup.find_all('script', src=True):
                src = script['src']
                if self.base_url:
                    src = urljoin(self.base_url, src)
                links.append({
                    'url': src,
                    'type': 'asset',
                    'asset_type': 'javascript'
                })
            
            # Image links
            for img in self.soup.find_all('img', src=True):
                src = img['src']
                if self.base_url:
                    src = urljoin(self.base_url, src)
                links.append({
                    'url': src,
                    'type': 'asset',
                    'asset_type': 'image',
                    'alt': img.get('alt', '')
                })
        
        return links
    
    def extract_tables(self, with_headers: bool = True) -> List[Dict]:
        """
        Extract table data
        
        Args:
            with_headers: Whether to use first row as headers
            
        Returns:
            List of table data
        """
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
            
            # Extract caption
            caption = table.find('caption')
            if caption:
                table_data['caption'] = caption.text.strip()
            
            # Extract headers
            thead = table.find('thead')
            if thead:
                for th in thead.find_all('th'):
                    table_data['headers'].append(th.get_text(strip=True))
            else:
                # Try to find headers in first row
                first_row = table.find('tr')
                if first_row and with_headers:
                    for th in first_row.find_all(['th', 'td']):
                        table_data['headers'].append(th.get_text(strip=True))
            
            # Extract rows
            tbody = table.find('tbody') or table
            for tr in tbody.find_all('tr'):
                # Skip header row if it was used for headers
                if tr == tbody.find('tr') and table_data['headers'] and not thead:
                    continue
                
                row_data = []
                for td in tr.find_all(['td', 'th']):
                    row_data.append(td.get_text(strip=True))
                
                if row_data:
                    # Convert to dict if headers available
                    if table_data['headers'] and len(row_data) == len(table_data['headers']):
                        row_dict = dict(zip(table_data['headers'], row_data))
                        table_data['rows'].append(row_dict)
                    else:
                        table_data['rows'].append(row_data)
            
            tables.append(table_data)
        
        return tables
    
    def extract_text_content(self, preserve_structure: bool = False) -> str:
        """
        Extract clean text content
        
        Args:
            preserve_structure: Whether to preserve document structure
            
        Returns:
            Extracted text
        """
        if not self.soup:
            return ""
        
        if preserve_structure and self.h2t:
            # Use html2text for markdown-like output
            return self.h2t.handle(str(self.soup))
        else:
            # Remove script and style elements
            for script in self.soup(['script', 'style']):
                script.decompose()
            
            # Get text
            text = self.soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
    
    def extract_forms(self) -> List[Dict]:
        """
        Extract form information
        
        Returns:
            List of form dictionaries
        """
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
            
            # Resolve relative action URL
            if self.base_url and form_data['action']:
                form_data['action'] = urljoin(self.base_url, form_data['action'])
            
            # Extract fields
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
                
                # Add select options
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
        """
        Extract image information
        
        Returns:
            List of image dictionaries
        """
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
            
            # Resolve relative URL
            if self.base_url and img_data['src']:
                img_data['src'] = urljoin(self.base_url, img_data['src'])
            
            images.append(img_data)
        
        return images
    
    def extract_all(self) -> Dict:
        """
        Extract all available content
        
        Returns:
            Dictionary with all extracted content
        """
        return {
            'metadata': self.extract_metadata(),
            'structured_data': self.extract_structured_data(),
            'links': self.extract_links(),
            'tables': self.extract_tables(),
            'forms': self.extract_forms(),
            'images': self.extract_images(),
            'text': self.extract_text_content()[:5000]  # First 5000 chars
        }


def main():
    """Command line interface for content extractor"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: content_extractor.py <html_file> [base_url]',
            'note': 'Reads HTML from file or stdin'
        }))
        sys.exit(1)
    
    # Read HTML content
    html_file = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else None
    
    if html_file == '-':
        # Read from stdin
        html_content = sys.stdin.read()
    else:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            print(json.dumps({
                'success': False,
                'error': f'Failed to read file: {str(e)}'
            }))
            sys.exit(1)
    
    # Extract content
    try:
        extractor = ContentExtractor()
        extractor.parse_html(html_content, base_url)
        
        # Extract everything
        extracted = extractor.extract_all()
        
        print(json.dumps({
            'success': True,
            'extracted': extracted,
            'statistics': {
                'links_found': len(extracted.get('links', [])),
                'tables_found': len(extracted.get('tables', [])),
                'forms_found': len(extracted.get('forms', [])),
                'images_found': len(extracted.get('images', [])),
                'text_length': len(extracted.get('text', ''))
            }
        }, indent=2))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }))


if __name__ == '__main__':
    main()
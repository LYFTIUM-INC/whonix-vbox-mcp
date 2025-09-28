#!/usr/bin/env python3
"""
Form Handler - Analyzes and submits web forms
Provides form detection, analysis, and POST submission capabilities
"""

import json
import sys
import subprocess
import os
from typing import Dict, List, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup
except ImportError:
    logger.error("BeautifulSoup4 not installed. Install with: pip3 install beautifulsoup4")
    BeautifulSoup = None

try:
    import requests
except ImportError:
    logger.error("requests not installed. Install with: pip3 install requests[socks]")
    requests = None


class FormHandler:
    def __init__(self, cookie_file: str = "/tmp/session_cookies.txt", use_proxy: bool = True):
        """
        Initialize form handler with cookie management
        
        Args:
            cookie_file: Path to cookie storage file
            use_proxy: Whether to use Tor proxy
        """
        self.cookie_file = cookie_file
        self.use_proxy = use_proxy
        
        if self.use_proxy:
            self.proxies = {
                'http': 'socks5://127.0.0.1:9050',
                'https': 'socks5://127.0.0.1:9050'
            }
        else:
            self.proxies = None
        
        # User agent for requests
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    
    def analyze_forms(self, url: str) -> List[Dict]:
        """
        Detect and analyze all forms on a webpage
        
        Args:
            url: URL of the page to analyze
            
        Returns:
            List of form dictionaries with field information
        """
        if not BeautifulSoup:
            return {'success': False, 'error': 'BeautifulSoup4 not available'}
        
        try:
            # Fetch page content using curl
            html = self._fetch_page_with_curl(url)
            
            if not html:
                return []
            
            # Parse HTML
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
        """
        Fetch page content using curl with cookie management
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or empty string on error
        """
        try:
            cmd = [
                'curl', '-s',
                '-b', self.cookie_file,  # Use cookies
                '-c', self.cookie_file,  # Save cookies
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
        """
        Extract detailed information from a form element
        
        Args:
            form: BeautifulSoup form element
            base_url: Base URL for resolving relative actions
            form_index: Index of the form on the page
            
        Returns:
            Dictionary with form metadata and fields
        """
        import urllib.parse
        
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
        
        # Resolve relative action URL
        if form_data['action']:
            form_data['action'] = urllib.parse.urljoin(base_url, form_data['action'])
        else:
            form_data['action'] = base_url
        
        # Extract all input fields
        for field in form.find_all(['input', 'select', 'textarea', 'button']):
            field_info = self._extract_field_info(field)
            
            if field_info:
                # Check for CSRF token
                if field_info['name'] and ('csrf' in field_info['name'].lower() or 
                                          'token' in field_info['name'].lower()):
                    form_data['csrf_token'] = field_info['value']
                
                # Collect submit buttons separately
                if field_info['type'] == 'submit':
                    form_data['submit_buttons'].append(field_info)
                else:
                    form_data['fields'].append(field_info)
        
        return form_data
    
    def _extract_field_info(self, field) -> Optional[Dict]:
        """
        Extract information from a form field
        
        Args:
            field: BeautifulSoup field element
            
        Returns:
            Dictionary with field information or None
        """
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
        
        # Handle select options
        if field.name == 'select':
            options = []
            for option in field.find_all('option'):
                options.append({
                    'value': option.get('value', option.text),
                    'text': option.text.strip(),
                    'selected': option.get('selected') is not None
                })
            field_info['options'] = options
        
        # Handle textarea
        if field.name == 'textarea':
            field_info['value'] = field.text.strip()
        
        return field_info
    
    def submit_form(self, url: str, form_data: Dict, files: Optional[Dict] = None) -> Dict:
        """
        Submit a form with provided data
        
        Args:
            url: Form action URL
            form_data: Dictionary of form field values
            files: Optional dictionary of files to upload
            
        Returns:
            Dictionary with submission result
        """
        try:
            method = form_data.get('method', 'POST').upper()
            
            # Build curl command
            cmd = [
                'curl', '-s', '-L',  # Follow redirects
                '-b', self.cookie_file,  # Use cookies
                '-c', self.cookie_file,  # Save cookies
                '-A', self.user_agent,
                '-w', '\n%{http_code}',  # Include status code
                '--compressed'
            ]
            
            if self.use_proxy:
                cmd.extend(['--socks5-hostname', '127.0.0.1:9050'])
            
            # Add form data
            if method == 'POST':
                if files:
                    # Handle file upload
                    for field_name, file_path in files.items():
                        cmd.extend(['-F', f'{field_name}=@{file_path}'])
                    
                    # Add other form fields
                    for key, value in form_data.items():
                        if key not in files:
                            cmd.extend(['-F', f'{key}={value}'])
                else:
                    # Regular form data
                    for key, value in form_data.items():
                        cmd.extend(['-d', f'{key}={value}'])
            else:
                # GET request with query parameters
                import urllib.parse
                query_string = urllib.parse.urlencode(form_data)
                url = f"{url}?{query_string}"
            
            cmd.append(url)
            
            # Execute request
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Parse response
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
    
    def fill_form_intelligently(self, form_info: Dict, user_data: Dict) -> Dict:
        """
        Intelligently fill form fields based on field names and types
        
        Args:
            form_info: Form analysis result
            user_data: User-provided data
            
        Returns:
            Dictionary with filled form data
        """
        filled_data = {}
        
        for field in form_info.get('fields', []):
            field_name = field['name']
            field_type = field['type']
            
            # Check if user provided value
            if field_name in user_data:
                filled_data[field_name] = user_data[field_name]
            else:
                # Try to intelligently guess based on field name
                lower_name = field_name.lower()
                
                if 'email' in lower_name:
                    filled_data[field_name] = user_data.get('email', 'test@example.com')
                elif 'username' in lower_name or 'user' in lower_name:
                    filled_data[field_name] = user_data.get('username', 'testuser')
                elif 'password' in lower_name or 'pass' in lower_name:
                    filled_data[field_name] = user_data.get('password', 'testpass123')
                elif 'name' in lower_name:
                    filled_data[field_name] = user_data.get('name', 'Test User')
                elif 'phone' in lower_name or 'tel' in lower_name:
                    filled_data[field_name] = user_data.get('phone', '555-0123')
                elif field['required']:
                    # Fill required fields with generic data
                    filled_data[field_name] = 'test_value'
                
                # Handle checkboxes
                if field_type == 'checkbox' and field_name not in filled_data:
                    filled_data[field_name] = 'on' if field.get('required') else ''
        
        # Include CSRF token if present
        if form_info.get('csrf_token'):
            for field in form_info.get('fields', []):
                if 'csrf' in field['name'].lower() or 'token' in field['name'].lower():
                    filled_data[field['name']] = form_info['csrf_token']
                    break
        
        return filled_data


def main():
    """Command line interface for form handler"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: form_handler.py <command> <url> [data]',
            'commands': ['analyze', 'submit']
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    url = sys.argv[2] if len(sys.argv) > 2 else ''
    
    handler = FormHandler()
    
    if command == 'analyze':
        forms = handler.analyze_forms(url)
        print(json.dumps({
            'success': True,
            'url': url,
            'forms_found': len(forms),
            'forms': forms
        }, indent=2))
    
    elif command == 'submit':
        form_data = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        result = handler.submit_form(url, form_data)
        print(json.dumps(result, indent=2))
    
    else:
        print(json.dumps({
            'success': False,
            'error': f'Unknown command: {command}'
        }))


if __name__ == '__main__':
    main()
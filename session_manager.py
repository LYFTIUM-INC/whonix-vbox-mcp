#!/usr/bin/env python3
"""
Session Manager - Manages persistent browser sessions with cookie handling
Provides session creation, loading, saving, and cookie management
"""

import os
import json
import time
import subprocess
import hashlib
from typing import Dict, Optional, List, Any
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, session_dir: str = "/home/user/.browser_sessions"):
        """
        Initialize session manager with storage directory
        
        Args:
            session_dir: Directory to store session files
        """
        self.session_dir = session_dir
        os.makedirs(session_dir, exist_ok=True)
        
        # User agent for consistency
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        
        # Session metadata file
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
        """
        Create a new browser session
        
        Args:
            session_id: Unique session identifier
            initial_url: Optional URL to initialize session
            description: Optional session description
            
        Returns:
            Dictionary with session information
        """
        # Generate session file paths
        cookie_file = os.path.join(self.session_dir, f"{session_id}.cookies")
        header_file = os.path.join(self.session_dir, f"{session_id}.headers")
        
        # Create session metadata
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
        
        # Initialize session with first request if URL provided
        if initial_url:
            result = self._initialize_session(session_id, initial_url)
            session_info['initialized'] = result['success']
            if result['success']:
                session_info['url_history'].append(initial_url)
                session_info['request_count'] = 1
        else:
            session_info['initialized'] = False
        
        # Save to metadata
        self.metadata[session_id] = session_info
        self.save_metadata()
        
        return {
            'success': True,
            'session': session_info
        }
    
    def _initialize_session(self, session_id: str, url: str) -> Dict:
        """
        Initialize session with first request
        
        Args:
            session_id: Session identifier
            url: URL to request
            
        Returns:
            Result dictionary
        """
        session = self.metadata.get(session_id, {})
        cookie_file = session.get('cookie_file')
        
        if not cookie_file:
            return {'success': False, 'error': 'Session not found'}
        
        try:
            cmd = [
                'curl', '-s',
                '-c', cookie_file,  # Save cookies
                '-D', session.get('header_file', '/dev/null'),  # Save headers
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
        """
        Load an existing session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session information or None if not found
        """
        if session_id not in self.metadata:
            return None
        
        session_info = self.metadata[session_id]
        
        # Check if cookie file exists
        if not os.path.exists(session_info['cookie_file']):
            logger.warning(f"Cookie file missing for session {session_id}")
            session_info['cookies_missing'] = True
        
        # Update last accessed time
        session_info['last_accessed'] = time.time()
        self.metadata[session_id] = session_info
        self.save_metadata()
        
        return session_info
    
    def make_request(self, session_id: str, url: str, method: str = 'GET',
                    data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request using session cookies
        
        Args:
            session_id: Session identifier
            url: URL to request
            method: HTTP method (GET, POST, etc.)
            data: Optional form data for POST requests
            headers: Optional additional headers
            
        Returns:
            Response dictionary
        """
        session = self.load_session(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        cookie_file = session['cookie_file']
        
        try:
            # Build curl command
            cmd = [
                'curl', '-s', '-L',  # Silent, follow redirects
                '-b', cookie_file,  # Use cookies
                '-c', cookie_file,  # Update cookies
                '-A', self.user_agent,
                '-w', '\n%{http_code}\n%{time_total}',  # Include status and time
                '--socks5-hostname', '127.0.0.1:9050',
                '--compressed'
            ]
            
            # Add custom headers
            if headers:
                for key, value in headers.items():
                    cmd.extend(['-H', f'{key}: {value}'])
            
            # Handle different methods
            if method == 'POST' and data:
                for key, value in data.items():
                    cmd.extend(['-d', f'{key}={value}'])
            elif method != 'GET':
                cmd.extend(['-X', method])
            
            cmd.append(url)
            
            # Execute request
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Parse response
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                time_total = lines[-1]
                status_code = lines[-2]
                content = '\n'.join(lines[:-2])
            else:
                status_code = '000'
                time_total = '0'
                content = result.stdout
            
            # Update session metadata
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
        """
        Delete a session and its associated files
        
        Args:
            session_id: Session identifier
            
        Returns:
            Result dictionary
        """
        if session_id not in self.metadata:
            return {'success': False, 'error': 'Session not found'}
        
        session = self.metadata[session_id]
        
        # Delete cookie file
        if os.path.exists(session['cookie_file']):
            os.remove(session['cookie_file'])
        
        # Delete header file
        if os.path.exists(session.get('header_file', '')):
            os.remove(session['header_file'])
        
        # Remove from metadata
        del self.metadata[session_id]
        self.save_metadata()
        
        return {
            'success': True,
            'deleted': session_id
        }
    
    def list_sessions(self) -> List[Dict]:
        """
        List all available sessions
        
        Returns:
            List of session information dictionaries
        """
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
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> Dict:
        """
        Clean up sessions older than specified age
        
        Args:
            max_age_hours: Maximum session age in hours
            
        Returns:
            Cleanup result dictionary
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        deleted = []
        for session_id, info in list(self.metadata.items()):
            age = current_time - info['created']
            if age > max_age_seconds:
                self.delete_session(session_id)
                deleted.append(session_id)
        
        return {
            'success': True,
            'deleted_count': len(deleted),
            'deleted_sessions': deleted
        }
    
    def export_cookies(self, session_id: str, format: str = 'netscape') -> Optional[str]:
        """
        Export session cookies in specified format
        
        Args:
            session_id: Session identifier
            format: Export format (netscape, json)
            
        Returns:
            Exported cookie string or None
        """
        session = self.load_session(session_id)
        if not session or not os.path.exists(session['cookie_file']):
            return None
        
        try:
            with open(session['cookie_file'], 'r') as f:
                cookie_data = f.read()
            
            if format == 'json':
                # Parse Netscape format to JSON
                cookies = []
                for line in cookie_data.split('\n'):
                    if line and not line.startswith('#'):
                        parts = line.split('\t')
                        if len(parts) >= 7:
                            cookies.append({
                                'domain': parts[0],
                                'flag': parts[1],
                                'path': parts[2],
                                'secure': parts[3],
                                'expiration': parts[4],
                                'name': parts[5],
                                'value': parts[6] if len(parts) > 6 else ''
                            })
                return json.dumps(cookies, indent=2)
            else:
                return cookie_data
                
        except Exception as e:
            logger.error(f"Cookie export failed: {str(e)}")
            return None


def main():
    """Command line interface for session manager"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: session_manager.py <command> [args]',
            'commands': ['create', 'load', 'request', 'list', 'delete', 'cleanup']
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    manager = SessionManager()
    
    if command == 'create':
        session_id = sys.argv[2] if len(sys.argv) > 2 else f"session_{int(time.time())}"
        url = sys.argv[3] if len(sys.argv) > 3 else None
        result = manager.create_session(session_id, url)
        print(json.dumps(result, indent=2))
    
    elif command == 'load':
        session_id = sys.argv[2] if len(sys.argv) > 2 else ''
        session = manager.load_session(session_id)
        if session:
            print(json.dumps({'success': True, 'session': session}, indent=2))
        else:
            print(json.dumps({'success': False, 'error': 'Session not found'}))
    
    elif command == 'request':
        session_id = sys.argv[2] if len(sys.argv) > 2 else ''
        url = sys.argv[3] if len(sys.argv) > 3 else ''
        result = manager.make_request(session_id, url)
        print(json.dumps(result, indent=2))
    
    elif command == 'list':
        sessions = manager.list_sessions()
        print(json.dumps({
            'success': True,
            'count': len(sessions),
            'sessions': sessions
        }, indent=2))
    
    elif command == 'delete':
        session_id = sys.argv[2] if len(sys.argv) > 2 else ''
        result = manager.delete_session(session_id)
        print(json.dumps(result, indent=2))
    
    elif command == 'cleanup':
        max_age = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        result = manager.cleanup_old_sessions(max_age)
        print(json.dumps(result, indent=2))
    
    else:
        print(json.dumps({
            'success': False,
            'error': f'Unknown command: {command}'
        }))


if __name__ == '__main__':
    main()
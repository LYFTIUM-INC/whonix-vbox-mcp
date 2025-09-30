#!/usr/bin/env python3
"""
Enhanced JavaScript Executor
Fixes Node.js module access issues for browser automation
"""

import os
import json
import tempfile
import subprocess
import asyncio
from typing import Dict, Any, Optional

class EnhancedJavaScriptExecutor:
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
        
        # Fallback to which command
        try:
            result = subprocess.run(['which', 'node'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return '/usr/bin/node'  # Last resort
    
    def _build_environment(self) -> Dict[str, str]:
        """Build comprehensive Node.js environment"""
        env = os.environ.copy()
        
        # Build NODE_PATH
        node_paths = []
        for path in self.npm_global_paths:
            expanded = os.path.expanduser(path)
            if os.path.exists(expanded):
                node_paths.append(expanded)
        
        if node_paths:
            env['NODE_PATH'] = ':'.join(node_paths)
        
        # Update PATH
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
        
        # First, try the enhanced execution method
        result = await self._execute_with_enhanced_env(url, javascript_code, browser)
        
        if result.get('success'):
            return result
        
        # If that fails, try the fallback method
        return await self._execute_with_fallback(url, javascript_code, browser)
    
    async def _execute_with_enhanced_env(self, url: str, javascript_code: str, browser: str) -> Dict[str, Any]:
        """Execute with enhanced environment and module resolution"""
        
        script_content = self._build_playwright_script(url, javascript_code, browser)
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as temp_file:
                temp_file.write(script_content)
                temp_file_path = temp_file.name
            
            # Execute with enhanced environment
            process = await asyncio.create_subprocess_exec(
                self.node_executable,
                temp_file_path,
                env=self.environment,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            
            # Clean up temp file
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
        
        # Try to install playwright locally if not available
        await self._ensure_playwright_available()
        
        script_content = self._build_fallback_script(url, javascript_code, browser)
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as temp_file:
                temp_file.write(script_content)
                temp_file_path = temp_file.name
            
            # Execute with fallback method
            process = await asyncio.create_subprocess_exec(
                self.node_executable,
                temp_file_path,
                env=self.environment,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=90)
            
            # Clean up temp file
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
        // Launch browser with Tor proxy
        browser = await {browser_import}.launch({{
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--proxy-server=socks5://127.0.0.1:9050'
            ]
        }});
        
        // Create new page
        page = await browser.newPage();
        
        // Set user agent
        await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36');
        
        // Navigate to URL
        await page.goto('{url}', {{ 
            waitUntil: 'networkidle',
            timeout: 30000 
        }});
        
        // Execute user JavaScript
        const result = await page.evaluate(() => {{
            try {{
                return {javascript_code};
            }} catch (error) {{
                return {{ error: error.message, stack: error.stack }};
            }}
        }});
        
        // Get page info
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
        // Cleanup
        if (page) await page.close();
        if (browser) await browser.close();
    }}
}})();
"""
    
    def _build_fallback_script(self, url: str, javascript_code: str, browser: str) -> str:
        """Build a fallback script that tries to require playwright from different locations"""
        
        return f"""
// Try different playwright module locations
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
        # Check if playwright is already available
        for path in self.playwright_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                return True
        
        # Try to install playwright locally
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
    
    def get_diagnostic_info(self) -> Dict[str, Any]:
        """Get diagnostic information about the JavaScript execution environment"""
        diagnostics = {
            'node_executable': self.node_executable,
            'node_executable_exists': os.path.exists(self.node_executable),
            'node_version': None,
            'npm_paths': [],
            'playwright_paths': [],
            'environment_path': self.environment.get('PATH', ''),
            'environment_node_path': self.environment.get('NODE_PATH', '')
        }
        
        # Get Node.js version
        try:
            result = subprocess.run([self.node_executable, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                diagnostics['node_version'] = result.stdout.strip()
        except:
            pass
        
        # Check npm paths
        for path in self.npm_global_paths:
            expanded = os.path.expanduser(path)
            if os.path.exists(expanded):
                diagnostics['npm_paths'].append(expanded)
        
        # Check playwright paths
        for path in self.playwright_paths:
            expanded = os.path.expanduser(path)
            if os.path.exists(expanded):
                diagnostics['playwright_paths'].append(expanded)
        
        return diagnostics


async def test_enhanced_javascript_executor():
    """Test the enhanced JavaScript executor"""
    executor = EnhancedJavaScriptExecutor()
    
    print("Enhanced JavaScript Executor Diagnostics")
    print("=" * 50)
    
    diagnostics = executor.get_diagnostic_info()
    for key, value in diagnostics.items():
        print(f"{key}: {value}")
    
    print("\nTesting JavaScript Execution")
    print("=" * 50)
    
    # Test simple execution
    result = await executor.execute_javascript(
        'https://example.com',
        'document.title'
    )
    
    print(f"Test Result:")
    print(f"Success: {result.get('success')}")
    print(f"Method: {result.get('execution_method', 'N/A')}")
    if result.get('success'):
        print(f"Page Title: {result.get('result')}")
    else:
        print(f"Error: {result.get('error')}")


if __name__ == '__main__':
    asyncio.run(test_enhanced_javascript_executor())
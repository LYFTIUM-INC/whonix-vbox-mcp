#!/usr/bin/env python3
"""
Advanced Form Automation MCP for VBox-Whonix
=============================================
Provides intelligent form filling, element detection, and visual automation
"""

import asyncio
import json
import os
import subprocess
import time
import base64
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

try:
    from fastmcp import FastMCP
    mcp = FastMCP("Advanced Form Automation MCP")
except ImportError:
    print("FastMCP not available")
    mcp = None

# Configuration
DEFAULT_VM = "Whonix-Workstation-Xfce"
DEFAULT_CREDENTIALS = {"username": "user", "password": os.getenv("WHONIX_VM_PASSWORD", "")}

class AdvancedFormAutomationService:
    """Service for intelligent form automation and visual interactions"""
    
    def __init__(self):
        self.form_templates = {}
        self.element_patterns = {}
        
    async def analyze_form_structure(self, vm_name: str, url: str) -> Dict[str, Any]:
        """Analyze webpage form structure and identify fillable fields"""
        
        analysis_script = f"""
const {{ firefox }} = require('playwright');

async function analyzeForm() {{
    const browser = await firefox.launch({{ headless: true }});
    const page = await browser.newPage();
    
    try {{
        await page.goto('{url}', {{ waitUntil: 'networkidle' }});
        
        // Find all forms and their elements
        const formAnalysis = await page.evaluate(() => {{
            const forms = Array.from(document.querySelectorAll('form'));
            
            return forms.map((form, formIndex) => {{
                const inputs = Array.from(form.querySelectorAll('input, textarea, select'));
                
                const formData = {{
                    formIndex: formIndex,
                    action: form.action || window.location.href,
                    method: form.method || 'GET',
                    fields: []
                }};
                
                inputs.forEach((input, fieldIndex) => {{
                    const field = {{
                        fieldIndex: fieldIndex,
                        tagName: input.tagName.toLowerCase(),
                        type: input.type || 'text',
                        name: input.name || '',
                        id: input.id || '',
                        placeholder: input.placeholder || '',
                        required: input.required || false,
                        value: input.value || '',
                        className: input.className || '',
                        selector: ''
                    }};
                    
                    // Generate unique selector
                    if (input.id) {{
                        field.selector = `#${{input.id}}`;
                    }} else if (input.name) {{
                        field.selector = `[name="${{input.name}}"]`;
                    }} else {{
                        field.selector = `form:nth-child(${{formIndex + 1}}) ${{input.tagName.toLowerCase()}}:nth-child(${{fieldIndex + 1}})`;
                    }}
                    
                    // Determine field purpose based on attributes
                    const fieldText = (input.placeholder + ' ' + input.name + ' ' + input.id + ' ' + input.className).toLowerCase();
                    
                    if (fieldText.includes('email') || fieldText.includes('@')) {{
                        field.purpose = 'email';
                    }} else if (fieldText.includes('password') || input.type === 'password') {{
                        field.purpose = 'password';
                    }} else if (fieldText.includes('name') && !fieldText.includes('username')) {{
                        field.purpose = 'name';
                    }} else if (fieldText.includes('phone') || fieldText.includes('tel')) {{
                        field.purpose = 'phone';
                    }} else if (fieldText.includes('address')) {{
                        field.purpose = 'address';
                    }} else if (fieldText.includes('city')) {{
                        field.purpose = 'city';
                    }} else if (fieldText.includes('zip') || fieldText.includes('postal')) {{
                        field.purpose = 'zip';
                    }} else if (fieldText.includes('country')) {{
                        field.purpose = 'country';
                    }} else if (fieldText.includes('username') || fieldText.includes('login')) {{
                        field.purpose = 'username';
                    }} else if (input.type === 'submit') {{
                        field.purpose = 'submit';
                    }} else {{
                        field.purpose = 'text';
                    }}
                    
                    formData.fields.push(field);
                }});
                
                return formData;
            }});
        }});
        
        // Get page metadata
        const title = await page.title();
        const currentUrl = page.url();
        
        console.log(JSON.stringify({{
            success: true,
            title: title,
            url: currentUrl,
            forms: formAnalysis,
            timestamp: new Date().toISOString()
        }}));
        
    }} catch (error) {{
        console.log(JSON.stringify({{
            success: false,
            error: error.message,
            timestamp: new Date().toISOString()
        }}));
    }} finally {{
        await browser.close();
    }}
}}

analyzeForm();
"""
        
        script_path = f"/tmp/form_analysis_{int(time.time())}.js"
        await self._write_file_to_vm(vm_name, script_path, analysis_script)
        
        try:
            result = await self._execute_vm_command(
                vm_name,
                f"cd /tmp && timeout 60 node {script_path}",
                timeout=70
            )
            
            output = result.get("stdout", "")
            try:
                return json.loads(output.strip())
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Failed to parse form analysis",
                    "raw_output": output
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await self._execute_vm_command(vm_name, f"rm -f {script_path}")

    async def fill_form_intelligently(self, vm_name: str, url: str, 
                                    form_data: Dict[str, Any],
                                    submit: bool = False) -> Dict[str, Any]:
        """Intelligently fill form based on field detection"""
        
        # First analyze the form
        form_analysis = await self.analyze_form_structure(vm_name, url)
        if not form_analysis.get("success"):
            return form_analysis
        
        forms = form_analysis.get("forms", [])
        if not forms:
            return {"success": False, "error": "No forms found on page"}
        
        # Use first form or find best match
        target_form = forms[0]
        form_index = target_form.get("formIndex", 0)
        
        # Generate filling script
        fill_actions = []
        filled_fields = []
        
        for field in target_form.get("fields", []):
            field_purpose = field.get("purpose", "")
            selector = field.get("selector", "")
            field_type = field.get("type", "")
            
            if not selector or field_type == "submit":
                continue
                
            # Map form data to field purposes
            fill_value = None
            if field_purpose == "email" and "email" in form_data:
                fill_value = form_data["email"]
            elif field_purpose == "password" and "password" in form_data:
                fill_value = form_data["password"]
            elif field_purpose == "username" and "username" in form_data:
                fill_value = form_data["username"]
            elif field_purpose == "name" and "name" in form_data:
                fill_value = form_data["name"]
            elif field_purpose == "phone" and "phone" in form_data:
                fill_value = form_data["phone"]
            elif field_purpose == "address" and "address" in form_data:
                fill_value = form_data["address"]
            elif field_purpose == "city" and "city" in form_data:
                fill_value = form_data["city"]
            elif field_purpose == "zip" and "zip" in form_data:
                fill_value = form_data["zip"]
            elif field_purpose == "country" and "country" in form_data:
                fill_value = form_data["country"]
            elif field.get("name") in form_data:
                fill_value = form_data[field.get("name")]
            elif field.get("id") in form_data:
                fill_value = form_data[field.get("id")]
            
            if fill_value:
                if field_type == "select":
                    fill_actions.append(f"await page.selectOption('{selector}', '{fill_value}');")
                elif field_type in ["checkbox", "radio"]:
                    if str(fill_value).lower() in ["true", "1", "yes", "on"]:
                        fill_actions.append(f"await page.check('{selector}');")
                else:
                    fill_actions.append(f"await page.fill('{selector}', '{fill_value}');")
                
                filled_fields.append({
                    "selector": selector,
                    "purpose": field_purpose,
                    "value": fill_value,
                    "type": field_type
                })
        
        # Add submit action if requested
        submit_action = ""
        if submit:
            submit_action = """
        // Find and click submit button
        const submitBtn = await page.$('input[type="submit"], button[type="submit"], button:has-text("Submit"), button:has-text("Login"), button:has-text("Sign")');
        if (submitBtn) {
            await submitBtn.click();
            await page.waitForTimeout(3000);
        }
"""
        
        fill_script = f"""
const {{ firefox }} = require('playwright');

async function fillForm() {{
    const browser = await firefox.launch({{ headless: true }});
    const page = await browser.newPage();
    
    try {{
        await page.goto('{url}', {{ waitUntil: 'networkidle' }});
        await page.waitForTimeout(2000);
        
        // Fill form fields
        {chr(10).join(fill_actions)}
        
        {submit_action}
        
        // Get final page state
        const title = await page.title();
        const currentUrl = page.url();
        
        console.log(JSON.stringify({{
            success: true,
            final_url: currentUrl,
            title: title,
            fields_filled: {len(filled_fields)},
            submitted: {str(submit).lower()},
            timestamp: new Date().toISOString()
        }}));
        
    }} catch (error) {{
        console.log(JSON.stringify({{
            success: false,
            error: error.message,
            timestamp: new Date().toISOString()
        }}));
    }} finally {{
        await browser.close();
    }}
}}

fillForm();
"""
        
        script_path = f"/tmp/form_fill_{int(time.time())}.js"
        await self._write_file_to_vm(vm_name, script_path, fill_script)
        
        try:
            result = await self._execute_vm_command(
                vm_name,
                f"cd /tmp && timeout 60 node {script_path}",
                timeout=70
            )
            
            output = result.get("stdout", "")
            try:
                fill_result = json.loads(output.strip())
                fill_result["filled_fields"] = filled_fields
                return fill_result
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Failed to parse form fill result",
                    "raw_output": output,
                    "filled_fields": filled_fields
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await self._execute_vm_command(vm_name, f"rm -f {script_path}")

    async def detect_visual_elements(self, vm_name: str, url: str,
                                   element_types: List[str] = None) -> Dict[str, Any]:
        """Detect and locate visual elements on webpage"""
        
        if not element_types:
            element_types = ["buttons", "links", "forms", "images", "inputs"]
        
        detection_script = f"""
const {{ firefox }} = require('playwright');

async function detectElements() {{
    const browser = await firefox.launch({{ headless: true }});
    const page = await browser.newPage();
    
    try {{
        await page.goto('{url}', {{ waitUntil: 'networkidle' }});
        
        const elementData = await page.evaluate(() => {{
            const elements = {{}};
            
            // Detect buttons
            if ({str('buttons' in element_types).lower()}) {{
                elements.buttons = Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"]')).map((btn, i) => ({{
                    index: i,
                    text: btn.textContent || btn.value || '',
                    type: btn.type || 'button',
                    id: btn.id || '',
                    className: btn.className || '',
                    selector: btn.id ? `#${{btn.id}}` : `button:nth-child(${{i + 1}})`,
                    visible: btn.offsetParent !== null,
                    bounds: btn.getBoundingClientRect()
                }}));
            }}
            
            // Detect links  
            if ({str('links' in element_types).lower()}) {{
                elements.links = Array.from(document.querySelectorAll('a[href]')).map((link, i) => ({{
                    index: i,
                    text: link.textContent || '',
                    href: link.href || '',
                    id: link.id || '',
                    className: link.className || '',
                    selector: link.id ? `#${{link.id}}` : `a:nth-child(${{i + 1}})`,
                    visible: link.offsetParent !== null,
                    bounds: link.getBoundingClientRect()
                }}));
            }}
            
            // Detect form inputs
            if ({str('inputs' in element_types).lower()}) {{
                elements.inputs = Array.from(document.querySelectorAll('input, textarea, select')).map((input, i) => ({{
                    index: i,
                    type: input.type || 'text',
                    name: input.name || '',
                    id: input.id || '',
                    placeholder: input.placeholder || '',
                    className: input.className || '',
                    selector: input.id ? `#${{input.id}}` : `input:nth-child(${{i + 1}})`,
                    visible: input.offsetParent !== null,
                    bounds: input.getBoundingClientRect(),
                    required: input.required || false
                }}));
            }}
            
            // Detect images
            if ({str('images' in element_types).lower()}) {{
                elements.images = Array.from(document.querySelectorAll('img')).map((img, i) => ({{
                    index: i,
                    src: img.src || '',
                    alt: img.alt || '',
                    id: img.id || '',
                    className: img.className || '',
                    selector: img.id ? `#${{img.id}}` : `img:nth-child(${{i + 1}})`,
                    visible: img.offsetParent !== null,
                    bounds: img.getBoundingClientRect(),
                    loaded: img.complete
                }}));
            }}
            
            // Detect forms
            if ({str('forms' in element_types).lower()}) {{
                elements.forms = Array.from(document.querySelectorAll('form')).map((form, i) => ({{
                    index: i,
                    action: form.action || '',
                    method: form.method || 'GET',
                    id: form.id || '',
                    className: form.className || '',
                    selector: form.id ? `#${{form.id}}` : `form:nth-child(${{i + 1}})`,
                    visible: form.offsetParent !== null,
                    bounds: form.getBoundingClientRect(),
                    fieldCount: form.querySelectorAll('input, textarea, select').length
                }}));
            }}
            
            return elements;
        }});
        
        const title = await page.title();
        const currentUrl = page.url();
        
        console.log(JSON.stringify({{
            success: true,
            title: title,
            url: currentUrl,
            elements: elementData,
            element_types: {element_types},
            timestamp: new Date().toISOString()
        }}));
        
    }} catch (error) {{
        console.log(JSON.stringify({{
            success: false,
            error: error.message,
            timestamp: new Date().toISOString()
        }}));
    }} finally {{
        await browser.close();
    }}
}}

detectElements();
"""
        
        script_path = f"/tmp/element_detection_{int(time.time())}.js"
        await self._write_file_to_vm(vm_name, script_path, detection_script)
        
        try:
            result = await self._execute_vm_command(
                vm_name,
                f"cd /tmp && timeout 60 node {script_path}",
                timeout=70
            )
            
            output = result.get("stdout", "")
            try:
                return json.loads(output.strip())
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Failed to parse element detection result",
                    "raw_output": output
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await self._execute_vm_command(vm_name, f"rm -f {script_path}")

    async def perform_visual_automation(self, vm_name: str, url: str,
                                      automation_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform complex visual automation workflows"""
        
        # Generate automation script from steps
        step_code = ""
        completed_steps = []
        
        for i, step in enumerate(automation_steps):
            action = step.get("action", "").lower()
            target = step.get("target", "")
            value = step.get("value", "")
            wait_time = step.get("wait", 1000)
            condition = step.get("condition", "")
            
            if action == "click_text":
                step_code += f"""
        // Step {i + 1}: Click element containing text '{target}'
        try {{
            await page.click(`text="{target}"`);
            await page.waitForTimeout({wait_time});
            console.log("Step {i + 1}: Clicked text '{target}' successfully");
        }} catch (e) {{
            console.log("Step {i + 1}: Failed to click text '{target}' - " + e.message);
        }}
"""
            elif action == "click_visible":
                step_code += f"""
        // Step {i + 1}: Click first visible element matching '{target}'
        try {{
            await page.click('{target}');
            await page.waitForTimeout({wait_time});
            console.log("Step {i + 1}: Clicked element '{target}' successfully");
        }} catch (e) {{
            console.log("Step {i + 1}: Failed to click element '{target}' - " + e.message);
        }}
"""
            elif action == "wait_for_element":
                step_code += f"""
        // Step {i + 1}: Wait for element '{target}' to appear
        try {{
            await page.waitForSelector('{target}', {{ timeout: {wait_time} }});
            console.log("Step {i + 1}: Element '{target}' appeared");
        }} catch (e) {{
            console.log("Step {i + 1}: Element '{target}' did not appear - " + e.message);
        }}
"""
            elif action == "scroll_to":
                step_code += f"""
        // Step {i + 1}: Scroll to element '{target}'
        try {{
            await page.locator('{target}').scrollIntoViewIfNeeded();
            await page.waitForTimeout({wait_time});
            console.log("Step {i + 1}: Scrolled to element '{target}' successfully");
        }} catch (e) {{
            console.log("Step {i + 1}: Failed to scroll to element '{target}' - " + e.message);
        }}
"""
            elif action == "extract_text":
                step_code += f"""
        // Step {i + 1}: Extract text from element '{target}'
        try {{
            const text = await page.textContent('{target}');
            console.log("Step {i + 1}: Extracted text: " + text);
        }} catch (e) {{
            console.log("Step {i + 1}: Failed to extract text from '{target}' - " + e.message);
        }}
"""
            elif action == "check_condition":
                step_code += f"""
        // Step {i + 1}: Check condition '{condition}'
        try {{
            const conditionMet = await page.evaluate(() => {{{condition}}});
            console.log("Step {i + 1}: Condition result: " + conditionMet);
        }} catch (e) {{
            console.log("Step {i + 1}: Failed to evaluate condition - " + e.message);
        }}
"""
            
            completed_steps.append({
                "step": i + 1,
                "action": action,
                "target": target,
                "value": value
            })
        
        automation_script = f"""
const {{ firefox }} = require('playwright');

async function performAutomation() {{
    const browser = await firefox.launch({{ headless: true }});
    const page = await browser.newPage();
    
    try {{
        await page.goto('{url}', {{ waitUntil: 'networkidle' }});
        console.log("Page loaded successfully");
        
        {step_code}
        
        const title = await page.title();
        const currentUrl = page.url();
        
        console.log(JSON.stringify({{
            success: true,
            final_url: currentUrl,
            title: title,
            steps_completed: {len(completed_steps)},
            timestamp: new Date().toISOString()
        }}));
        
    }} catch (error) {{
        console.log(JSON.stringify({{
            success: false,
            error: error.message,
            timestamp: new Date().toISOString()
        }}));
    }} finally {{
        await browser.close();
    }}
}}

performAutomation();
"""
        
        script_path = f"/tmp/visual_automation_{int(time.time())}.js"
        await self._write_file_to_vm(vm_name, script_path, automation_script)
        
        try:
            result = await self._execute_vm_command(
                vm_name,
                f"cd /tmp && timeout 120 node {script_path}",
                timeout=130
            )
            
            output = result.get("stdout", "")
            try:
                # Parse JSON result (last line should be JSON)
                lines = output.strip().split('\n')
                json_line = None
                for line in reversed(lines):
                    try:
                        json_result = json.loads(line)
                        json_line = json_result
                        break
                    except json.JSONDecodeError:
                        continue
                
                if json_line:
                    json_line["automation_steps"] = completed_steps
                    json_line["execution_log"] = lines[:-1] if len(lines) > 1 else []
                    return json_line
                else:
                    return {
                        "success": False,
                        "error": "No valid JSON result found",
                        "raw_output": output,
                        "automation_steps": completed_steps
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to parse automation result: {str(e)}",
                    "raw_output": output
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await self._execute_vm_command(vm_name, f"rm -f {script_path}")

    # Helper methods
    async def _execute_vm_command(self, vm_name: str, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute command in VM"""
        try:
            cmd = [
                "VBoxManage", "guestcontrol", vm_name, "run",
                "--exe", "/bin/bash",
                "--username", DEFAULT_CREDENTIALS["username"],
                "--password", DEFAULT_CREDENTIALS["password"],
                "--wait-stdout", "--wait-stderr",
                "--", "-c", command
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=timeout)
            
            return {
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "returncode": result.returncode
            }
            
        except Exception as e:
            return {"error": str(e), "returncode": -1}

    async def _write_file_to_vm(self, vm_name: str, vm_path: str, content: str):
        """Write content to file in VM"""
        escaped_content = content.replace("'", "'\"'\"'")
        await self._execute_vm_command(vm_name, f"echo '{escaped_content}' > {vm_path}")

# Initialize service
form_service = AdvancedFormAutomationService()

# MCP Tool Definitions
if mcp:
    @mcp.tool()
    async def analyze_webpage_form_structure(
        url: str,
        vm_name: str = DEFAULT_VM
    ) -> str:
        """Analyze webpage forms and identify fillable fields with their purposes"""
        result = await form_service.analyze_form_structure(vm_name, url)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def fill_webpage_form_intelligently(
        url: str,
        form_data: str,  # JSON string of form data
        vm_name: str = DEFAULT_VM,
        submit: bool = False
    ) -> str:
        """Intelligently fill webpage forms based on field detection"""
        try:
            data = json.loads(form_data)
            result = await form_service.fill_form_intelligently(vm_name, url, data, submit)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError:
            return json.dumps({"success": False, "error": "Invalid form data JSON"})

    @mcp.tool()
    async def detect_webpage_visual_elements(
        url: str,
        vm_name: str = DEFAULT_VM,
        element_types: str = "buttons,links,forms,images,inputs"  # Comma-separated list
    ) -> str:
        """Detect and locate visual elements on webpage"""
        types_list = [t.strip() for t in element_types.split(",")]
        result = await form_service.detect_visual_elements(vm_name, url, types_list)
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def perform_visual_webpage_automation(
        url: str,
        automation_steps: str,  # JSON string of automation steps
        vm_name: str = DEFAULT_VM
    ) -> str:
        """Perform complex visual automation workflows on webpage"""
        try:
            steps = json.loads(automation_steps)
            result = await form_service.perform_visual_automation(vm_name, url, steps)
            return json.dumps(result, indent=2)
        except json.JSONDecodeError:
            return json.dumps({"success": False, "error": "Invalid automation steps JSON"})

# Export for use as MCP server
if __name__ == "__main__":
    if mcp:
        mcp.run()
    else:
        print("Advanced Form Automation MCP server ready")
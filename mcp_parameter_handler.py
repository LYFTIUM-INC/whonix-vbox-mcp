#!/usr/bin/env python3
"""
MCP Parameter Handler
Fixes parameter type validation issues for browser automation tools
"""

import json
import re
from typing import Any, Union, List, Dict, Optional

class MCPParameterHandler:
    """Handles parameter serialization and validation for MCP tools"""
    
    @staticmethod
    def serialize_for_mcp(value: Any) -> str:
        """
        Convert any parameter type to MCP-compatible string format
        """
        if value is None:
            return ""
        
        if isinstance(value, str):
            # If it's already a string, check if it's valid JSON
            try:
                json.loads(value)
                return value  # Already valid JSON string
            except json.JSONDecodeError:
                return value  # Return as-is if not JSON
        
        elif isinstance(value, (list, dict)):
            return json.dumps(value, separators=(',', ':'))
        
        elif isinstance(value, (int, float, bool)):
            return str(value)
        
        else:
            # For other types, convert to string representation
            return json.dumps(str(value))
    
    @staticmethod
    def deserialize_from_mcp(value: str, expected_type: type = None) -> Any:
        """
        Convert MCP string parameter back to expected Python type
        """
        if not value:
            return None if expected_type != str else ""
        
        # If no expected type, try to infer from content
        if expected_type is None:
            return MCPParameterHandler._smart_deserialize(value)
        
        # Handle specific expected types
        if expected_type == str:
            return value
        
        elif expected_type == list:
            try:
                result = json.loads(value)
                return result if isinstance(result, list) else [result]
            except json.JSONDecodeError:
                # Try to parse as comma-separated values
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
        """
        Intelligently deserialize a string value
        """
        # Try JSON first
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
        
        # Try boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    @staticmethod
    def validate_interactions_parameter(interactions: str) -> Dict[str, Any]:
        """
        Specifically validate and parse the interactions parameter for webpage elements
        """
        if not interactions:
            return {
                'valid': False,
                'error': 'Interactions parameter is required',
                'parsed': []
            }
        
        try:
            # Parse as JSON
            parsed = json.loads(interactions)
            
            # Ensure it's a list
            if not isinstance(parsed, list):
                parsed = [parsed]
            
            # Validate each interaction
            validated_interactions = []
            for i, interaction in enumerate(parsed):
                if not isinstance(interaction, dict):
                    return {
                        'valid': False,
                        'error': f'Interaction {i} must be an object',
                        'parsed': []
                    }
                
                # Check required fields
                if 'action' not in interaction:
                    return {
                        'valid': False,
                        'error': f'Interaction {i} missing required "action" field',
                        'parsed': []
                    }
                
                # Validate action types
                valid_actions = ['click', 'type', 'select', 'hover', 'wait', 'scroll']
                if interaction['action'] not in valid_actions:
                    return {
                        'valid': False,
                        'error': f'Invalid action "{interaction["action"]}" in interaction {i}. Valid actions: {valid_actions}',
                        'parsed': []
                    }
                
                # Add default values
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
    
    @staticmethod
    def build_interaction_example() -> str:
        """
        Build an example interactions parameter for documentation
        """
        example_interactions = [
            {
                "action": "click",
                "selector": "button#submit",
                "wait": 1000
            },
            {
                "action": "type",
                "selector": "input[name='username']",
                "value": "testuser",
                "wait": 500
            },
            {
                "action": "select",
                "selector": "select[name='country']",
                "value": "US",
                "wait": 500
            }
        ]
        
        return json.dumps(example_interactions, indent=2)
    
    @staticmethod
    def validate_form_data_parameter(form_data: str) -> Dict[str, Any]:
        """
        Validate and parse form data parameter
        """
        if not form_data:
            return {
                'valid': True,
                'error': None,
                'parsed': {}
            }
        
        try:
            parsed = json.loads(form_data)
            
            if not isinstance(parsed, dict):
                return {
                    'valid': False,
                    'error': 'Form data must be a JSON object',
                    'parsed': {}
                }
            
            # Validate form data values
            validated_data = {}
            for key, value in parsed.items():
                if isinstance(value, (str, int, float, bool)):
                    validated_data[key] = str(value)
                elif isinstance(value, list):
                    validated_data[key] = [str(v) for v in value]
                else:
                    validated_data[key] = str(value)
            
            return {
                'valid': True,
                'error': None,
                'parsed': validated_data
            }
            
        except json.JSONDecodeError as e:
            return {
                'valid': False,
                'error': f'Invalid JSON format in form data: {str(e)}',
                'parsed': {}
            }
    
    @staticmethod
    def validate_custom_parameters(custom_parameters: str) -> Dict[str, Any]:
        """
        Validate custom parameters for automation tasks
        """
        if not custom_parameters:
            return {
                'valid': True,
                'error': None,
                'parsed': {}
            }
        
        try:
            parsed = json.loads(custom_parameters)
            
            if not isinstance(parsed, dict):
                return {
                    'valid': False,
                    'error': 'Custom parameters must be a JSON object',
                    'parsed': {}
                }
            
            return {
                'valid': True,
                'error': None,
                'parsed': parsed
            }
            
        except json.JSONDecodeError as e:
            return {
                'valid': False,
                'error': f'Invalid JSON format in custom parameters: {str(e)}',
                'parsed': {}
            }


class MCPResponseBuilder:
    """Helper class to build consistent MCP responses"""
    
    @staticmethod
    def success_response(data: Dict[str, Any], message: str = None) -> str:
        """Build a success response"""
        response = {
            'success': True,
            'timestamp': MCPResponseBuilder._get_timestamp(),
            **data
        }
        
        if message:
            response['message'] = message
        
        return json.dumps(response, indent=2)
    
    @staticmethod
    def error_response(error: str, details: Dict[str, Any] = None) -> str:
        """Build an error response"""
        response = {
            'success': False,
            'error': error,
            'timestamp': MCPResponseBuilder._get_timestamp()
        }
        
        if details:
            response['details'] = details
        
        return json.dumps(response, indent=2)
    
    @staticmethod
    def validation_error_response(field: str, error: str, received_value: Any = None) -> str:
        """Build a validation error response"""
        response = {
            'success': False,
            'error': f'Parameter validation failed for "{field}": {error}',
            'validation_error': True,
            'field': field,
            'timestamp': MCPResponseBuilder._get_timestamp()
        }
        
        if received_value is not None:
            response['received_value'] = str(received_value)
        
        return json.dumps(response, indent=2)
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()


def test_parameter_handler():
    """Test the MCP parameter handler"""
    handler = MCPParameterHandler()
    
    print("Testing MCP Parameter Handler")
    print("=" * 40)
    
    # Test interactions parameter
    interactions_test = '''[
        {"action": "click", "selector": "button"},
        {"action": "type", "selector": "input", "value": "test"}
    ]'''
    
    result = handler.validate_interactions_parameter(interactions_test)
    print(f"Interactions validation: {result['valid']}")
    print(f"Parsed interactions: {len(result['parsed'])} items")
    
    # Test form data parameter
    form_data_test = '{"username": "test", "password": "secret"}'
    
    result = handler.validate_form_data_parameter(form_data_test)
    print(f"Form data validation: {result['valid']}")
    print(f"Parsed form data: {result['parsed']}")
    
    # Test serialization
    test_list = [1, 2, 3]
    serialized = handler.serialize_for_mcp(test_list)
    deserialized = handler.deserialize_from_mcp(serialized, list)
    print(f"Serialization test: {test_list} -> {serialized} -> {deserialized}")


if __name__ == '__main__':
    test_parameter_handler()
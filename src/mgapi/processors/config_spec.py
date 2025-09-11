"""Configuration specification processor."""

import json
from typing import Tuple

from .base import BaseSpecProcessor


class ConfigSpecProcessor(BaseSpecProcessor):
    """Processor for configuration specification CSV files.
    
    Expected CSV columns:
    - component: Component name
    - key: Configuration key
    - value: Configuration value
    - environment: Target environment (dev, staging, prod)
    - action: Action to perform (set, get, delete) - optional, defaults to 'set'
    """
    
    spec_type = "config_spec"
    required_columns = ['component', 'key', 'value', 'environment']
    
    def validate_row(self, row: dict) -> Tuple[bool, str]:
        """Validate configuration specification row.
        
        Args:
            row: Row data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        for col in self.required_columns:
            if not row.get(col):
                return False, f"Missing required field: {col}"
        
        # Validate environment
        valid_envs = ['dev', 'staging', 'prod', 'test']
        env = row.get('environment', '').lower()
        if env not in valid_envs:
            return False, f"Invalid environment: {env}. Must be one of: {valid_envs}"
        
        # Validate action if provided
        action = row.get('action', 'set').lower()
        valid_actions = ['set', 'get', 'delete']
        if action not in valid_actions:
            return False, f"Invalid action: {action}. Must be one of: {valid_actions}"
        
        # Validate component name (no spaces, alphanumeric + underscore)
        component = row.get('component', '')
        if not component.replace('_', '').replace('-', '').isalnum():
            return False, f"Invalid component name: {component}. Use only letters, numbers, underscore, hyphen"
        
        # Validate key name
        key = row.get('key', '')
        if not key.replace('_', '').replace('.', '').isalnum():
            return False, f"Invalid key name: {key}. Use only letters, numbers, underscore, dot"
        
        return True, "Valid"
    
    def row_to_command(self, row: dict) -> str:
        """Convert config spec row to API command.
        
        Args:
            row: Row data dictionary
            
        Returns:
            JSON command string for API
        """
        action = row.get('action', 'set').lower()
        
        command_data = {
            "tool": "config_manager",
            "action": action,
            "params": {
                "component": row['component'],
                "environment": row['environment'],
                "key": row['key']
            }
        }
        
        if action in ['set']:
            # Include value for set operations
            value = row['value']
            
            # Try to parse as JSON for complex values
            try:
                parsed_value = json.loads(value)
                command_data["params"]["value"] = parsed_value
            except (json.JSONDecodeError, TypeError):
                # Use as string if not valid JSON
                command_data["params"]["value"] = str(value)
        
        # Add optional fields
        if row.get('description'):
            command_data["params"]["description"] = row['description']
        
        if row.get('type'):
            command_data["params"]["type"] = row['type']
        
        return json.dumps(command_data)
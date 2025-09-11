"""User specification processor."""

import json
import re
from typing import Tuple

from .base import BaseSpecProcessor


class UserSpecProcessor(BaseSpecProcessor):
    """Processor for user specification CSV files.
    
    Expected CSV columns:
    - username: User's login name
    - email: User's email address
    - role: User role (admin, user, etc.)
    - action: Action to perform (create, update, delete)
    - department: User's department (optional)
    """
    
    spec_type = "user_spec"
    required_columns = ['username', 'email', 'role', 'action']
    
    def validate_row(self, row: dict) -> Tuple[bool, str]:
        """Validate user specification row.
        
        Args:
            row: Row data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        for col in self.required_columns:
            if not row.get(col):
                return False, f"Missing required field: {col}"
        
        # Validate email format
        email = row.get('email', '')
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return False, f"Invalid email format: {email}"
        
        # Validate action
        valid_actions = ['create', 'update', 'delete']
        action = row.get('action', '').lower()
        if action not in valid_actions:
            return False, f"Invalid action: {action}. Must be one of: {valid_actions}"
        
        # Validate role
        valid_roles = ['admin', 'user', 'manager', 'viewer']
        role = row.get('role', '').lower()
        if role not in valid_roles:
            return False, f"Invalid role: {role}. Must be one of: {valid_roles}"
        
        # Username validation
        username = row.get('username', '')
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, f"Invalid username format: {username}. Use only letters, numbers, underscore, hyphen"
        
        return True, "Valid"
    
    def row_to_command(self, row: dict) -> str:
        """Convert user spec row to API command.
        
        Args:
            row: Row data dictionary
            
        Returns:
            JSON command string for API
        """
        action = row['action'].lower()
        
        command_data = {
            "tool": "user_manager",
            "action": action,
            "params": {
                "username": row['username']
            }
        }
        
        if action == 'create':
            command_data["params"].update({
                "email": row['email'],
                "role": row['role'],
                "department": row.get('department', ''),
                "full_name": row.get('full_name', ''),
            })
        
        elif action == 'update':
            # Only include non-empty update fields
            updates = {}
            for field in ['email', 'role', 'department', 'full_name']:
                if row.get(field):
                    updates[field] = row[field]
            
            if updates:
                command_data["params"]["updates"] = updates
        
        elif action == 'delete':
            # Delete only needs username
            pass
        
        return json.dumps(command_data)
"""Spec processors for different CSV types."""

from typing import List

from .user_spec import UserSpecProcessor
from .config_spec import ConfigSpecProcessor

# Registry of available spec processors
SPEC_PROCESSORS = {
    'user_spec': UserSpecProcessor,
    'config_spec': ConfigSpecProcessor,
}


def get_processor(spec_type: str):
    """Get processor class for given spec type.
    
    Args:
        spec_type: Type of spec processor
        
    Returns:
        Processor class
        
    Raises:
        ValueError: If spec type is not supported
    """
    if spec_type not in SPEC_PROCESSORS:
        available = list(SPEC_PROCESSORS.keys())
        raise ValueError(f"Unknown spec type: {spec_type}. Available: {available}")
    
    return SPEC_PROCESSORS[spec_type]


def list_spec_types() -> List[str]:
    """Get list of available spec types.
    
    Returns:
        List of spec type names
    """
    return list(SPEC_PROCESSORS.keys())
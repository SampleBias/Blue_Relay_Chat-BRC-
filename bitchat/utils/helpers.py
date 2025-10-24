"""
Helper utility functions for Blue Relay Chat RPi 4 client.

This module provides various helper functions used throughout the application.
"""

import os
import uuid
import time
import secrets
import string
import hashlib
import base64
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
import re

from ..exceptions import ValidationError


def generate_id(length: int = 16) -> str:
    """
    Generate a random ID string.
    
    Args:
        length: Length of the ID to generate
        
    Returns:
        Random ID string
    """
    return secrets.token_hex(length // 2)


def generate_message_id() -> str:
    """
    Generate a unique message ID.
    
    Returns:
        Unique message ID
    """
    timestamp = int(time.time() * 1000)
    random_str = secrets.token_hex(8)
    return f"msg_{timestamp}_{random_str}"


def generate_channel_id(name: str) -> str:
    """
    Generate a channel ID from a channel name.
    
    Args:
        name: Channel name
        
    Returns:
        Channel ID
    """
    # Normalize name
    normalized = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
    
    # Create hash
    hash_value = hashlib.sha256(name.encode()).hexdigest()[:8]
    
    return f"channel_{normalized}_{hash_value}"


def format_timestamp(timestamp: Union[datetime, int, float], format_str: str = "%H:%M:%S") -> str:
    """
    Format a timestamp for display.
    
    Args:
        timestamp: Timestamp to format (datetime object or Unix timestamp)
        format_str: Format string for datetime
        
    Returns:
        Formatted timestamp string
    """
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp)
    else:
        dt = timestamp
    
    return dt.strftime(format_str)


def format_bytes(bytes_count: int) -> str:
    """
    Format a byte count for display.
    
    Args:
        bytes_count: Number of bytes
        
    Returns:
        Formatted byte count string
    """
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    elif bytes_count < 1024 * 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_count / (1024 * 1024 * 1024):.1f} GB"


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize a string for safe display or storage.
    
    Args:
        text: String to sanitize
        max_length: Maximum length of the result
        
    Returns:
        Sanitized string
    """
    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def is_valid_nostr_public_key(pubkey: str) -> bool:
    """
    Check if a string is a valid Nostr public key.
    
    Args:
        pubkey: Public key string to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Nostr public keys are 64 hex characters (32 bytes)
    return bool(re.match(r'^[a-fA-F0-9]{64}$', pubkey))


def is_valid_nostr_id(event_id: str) -> bool:
    """
    Check if a string is a valid Nostr event ID.
    
    Args:
        event_id: Event ID string to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Nostr event IDs are 64 hex characters (32 bytes)
    return bool(re.match(r'^[a-fA-F0-9]{64}$', event_id))


def encode_base64(data: bytes) -> str:
    """
    Encode bytes to base64 string.
    
    Args:
        data: Bytes to encode
        
    Returns:
        Base64 encoded string
    """
    return base64.b64encode(data).decode('ascii')


def decode_base64(encoded: str) -> bytes:
    """
    Decode base64 string to bytes.
    
    Args:
        encoded: Base64 encoded string
        
    Returns:
        Decoded bytes
    """
    return base64.b64decode(encoded.encode('ascii'))


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely load a JSON string.
    
    Args:
        json_str: JSON string to load
        default: Default value if loading fails
        
    Returns:
        Loaded JSON object or default value
    """
    try:
        import json
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: dict, default: str = "{}") -> str:
    """
    Safely dump an object to JSON string.
    
    Args:
        obj: Object to dump
        default: Default value if dumping fails
        
    Returns:
        JSON string or default value
    """
    try:
        import json
        return json.dumps(obj)
    except (TypeError, ValueError):
        return default


def get_system_info() -> Dict[str, Any]:
    """
    Get system information.
    
    Returns:
        Dictionary containing system information
    """
    info = {
        "platform": os.name,
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "time": datetime.now(timezone.utc).isoformat(),
    }
    
    # Get CPU info if available
    try:
        import platform
        info["cpu"] = platform.processor()
        info["machine"] = platform.machine()
    except:
        pass
    
    # Get memory info if available
    try:
        import psutil
        memory = psutil.virtual_memory()
        info["memory"] = {
            "total": format_bytes(memory.total),
            "available": format_bytes(memory.available),
            "percent": memory.percent,
        }
    except:
        pass
    
    return info


def validate_channel_name(name: str) -> bool:
    """
    Validate a channel name.
    
    Args:
        name: Channel name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name or not name.strip():
        return False
    
    # Check length
    if len(name) > 64:
        return False
    
    # Check for valid characters (alphanumeric, spaces, hyphens, underscores)
    return bool(re.match(r'^[a-zA-Z0-9 _\-]+$', name))


def validate_username(username: str) -> bool:
    """
    Validate a username.
    
    Args:
        username: Username to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not username or not username.strip():
        return False
    
    # Check length
    if len(username) < 3 or len(username) > 32:
        return False
    
    # Check for valid characters (alphanumeric, underscores, hyphens)
    return bool(re.match(r'^[a-zA-Z0-9_\-]+$', username))


def parse_duration(duration_str: str) -> int:
    """
    Parse a duration string into seconds.
    
    Args:
        duration_str: Duration string (e.g., "1h", "30m", "60s")
        
    Returns:
        Duration in seconds
    """
    if not duration_str:
        return 0
    
    # Parse pattern
    match = re.match(r'^(\d+)([smhd])$', duration_str.lower())
    if not match:
        return 0
    
    value, unit = match.groups()
    value = int(value)
    
    # Convert to seconds
    if unit == 's':
        return value
    elif unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600
    elif unit == 'd':
        return value * 86400
    
    return 0


def format_duration(seconds: int) -> str:
    """
    Format a duration in seconds into a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours}h"
    else:
        days = seconds // 86400
        return f"{days}d"


def generate_password(length: int = 12, include_symbols: bool = True) -> str:
    """
    Generate a random password.
    
    Args:
        length: Length of the password
        include_symbols: Whether to include symbols
        
    Returns:
        Generated password
    """
    chars = string.ascii_letters + string.digits
    if include_symbols:
        chars += "!@#$%^&*()"
    
    return ''.join(secrets.choice(chars) for _ in range(length))


def calculate_message_hash(content: str, sender: str, timestamp: int) -> str:
    """
    Calculate a hash for a message.
    
    Args:
        content: Message content
        sender: Sender ID
        timestamp: Message timestamp
        
    Returns:
        Message hash
    """
    data = f"{content}:{sender}:{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten a nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for nested items
        sep: Separator for keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    
    return dict(items)


def retry_async(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retrying async functions.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff: Multiplier for delay after each attempt
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            
            # All attempts failed, raise the last exception
            raise last_exception
        
        return wrapper
    return decorator


def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """
    Split a list into chunks of size n.
    
    Args:
        lst: List to split
        n: Chunk size
        
    Returns:
        List of chunks
    """
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """
    Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))
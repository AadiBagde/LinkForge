"""
Input validation utilities for LinkForge.
Ensures all user input is safe, properly formatted, and within constraints.
"""

import re
from typing import Optional
from urllib.parse import urlparse
from fastapi import HTTPException


# Constants
MIN_CUSTOM_CODE_LENGTH = 3
MAX_CUSTOM_CODE_LENGTH = 20
MAX_URL_LENGTH = 2048
MIN_URL_LENGTH = 10

# Regex patterns
CUSTOM_CODE_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{" + str(MIN_CUSTOM_CODE_LENGTH) + "," + str(MAX_CUSTOM_CODE_LENGTH) + "}$")
SAFE_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


class ValidationError(HTTPException):
    """Custom validation error exception"""
    
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)


def validate_custom_code(code: str) -> str:
    """
    Validate custom short code format.
    
    Args:
        code: Custom code from user
        
    Returns:
        Validated code
        
    Raises:
        ValidationError: If code is invalid
    """
    if not code:
        raise ValidationError("Custom code cannot be empty")
    
    if len(code) < MIN_CUSTOM_CODE_LENGTH:
        raise ValidationError(
            f"Custom code must be at least {MIN_CUSTOM_CODE_LENGTH} characters long"
        )
    
    if len(code) > MAX_CUSTOM_CODE_LENGTH:
        raise ValidationError(
            f"Custom code must not exceed {MAX_CUSTOM_CODE_LENGTH} characters"
        )
    
    if not CUSTOM_CODE_PATTERN.match(code):
        raise ValidationError(
            "Custom code must contain only alphanumeric characters, hyphens, and underscores"
        )
    
    # Prevent reserved codes
    reserved_codes = {
        "api", "admin", "auth", "docs", "redoc", "health",
        "metrics", "debug", "analytics", "shorten", "qr"
    }
    if code.lower() in reserved_codes:
        raise ValidationError(f"'{code}' is a reserved code and cannot be used")
    
    return code


def validate_url(url: str) -> str:
    """
    Validate URL format and safety.
    
    Args:
        url: Original URL from user
        
    Returns:
        Validated URL
        
    Raises:
        ValidationError: If URL is invalid
    """
    if not url:
        raise ValidationError("URL cannot be empty")
    
    if len(url) < MIN_URL_LENGTH:
        raise ValidationError(f"URL is too short (minimum {MIN_URL_LENGTH} characters)")
    
    if len(url) > MAX_URL_LENGTH:
        raise ValidationError(f"URL is too long (maximum {MAX_URL_LENGTH} characters)")
    
    # Check if it starts with http:// or https://
    if not SAFE_URL_PATTERN.match(url):
        raise ValidationError("URL must start with http:// or https://")
    
    try:
        parsed = urlparse(url)
        
        # Validate scheme
        if parsed.scheme not in ("http", "https"):
            raise ValidationError("Only HTTP and HTTPS schemes are supported")
        
        # Validate netloc (domain)
        if not parsed.netloc:
            raise ValidationError("URL must have a valid domain")
        
        # Check for localhost/internal IPs (security measure)
        internal_hosts = {
            "localhost", "127.0.0.1", "192.168.", "10.", "172.",
            "0.0.0.0", "::1", "[::1]"
        }
        
        hostname = parsed.hostname or ""
        if hostname.lower() in internal_hosts or hostname.startswith(("192.168.", "10.", "172.")):
            raise ValidationError("Cannot shorten internal/private network URLs")
        
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"Invalid URL format: {str(e)}")
    
    return url


def sanitize_string(text: str, max_length: int = 500) -> str:
    """
    Sanitize string to prevent XSS attacks.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not text:
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", "'", '"', "&"]
    for char in dangerous_chars:
        text = text.replace(char, "")
    
    return text.strip()


def validate_email(email: str) -> str:
    """
    Validate email format.
    
    Args:
        email: Email address
        
    Returns:
        Validated email
        
    Raises:
        ValidationError: If email is invalid
    """
    if not email or len(email) > 255:
        raise ValidationError("Invalid email address")
    
    # Simple email regex
    email_pattern = re.compile(
        r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    )
    
    if not email_pattern.match(email):
        raise ValidationError("Invalid email format")
    
    return email.lower()


def validate_password(password: str) -> str:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Validated password
        
    Raises:
        ValidationError: If password is weak
    """
    if not password or len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    if len(password) > 128:
        raise ValidationError("Password is too long")
    
    # Check for at least one uppercase, lowercase, number, and special char
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if not (has_upper and has_lower and has_digit):
        raise ValidationError(
            "Password must contain at least one uppercase letter, "
            "one lowercase letter, and one number"
        )
    
    return password

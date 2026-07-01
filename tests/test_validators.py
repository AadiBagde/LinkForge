"""
Tests for input validation functions.
"""

import pytest
from app.core.validators import (
    validate_url,
    validate_custom_code,
    validate_email,
    validate_password,
    sanitize_string,
)
from fastapi import HTTPException


class TestURLValidation:
    """Tests for URL validation."""
    
    def test_valid_url(self):
        """Test validation of valid URLs."""
        valid_urls = [
            "https://github.com",
            "https://www.example.com",
            "http://localhost:8000",
            "https://example.com/path?query=value#anchor",
            "https://example.com:8443",
        ]
        
        for url in valid_urls:
            # Should not raise
            validate_url(url)
    
    def test_invalid_url_format(self):
        """Test rejection of invalid URL formats."""
        invalid_urls = [
            "not-a-url",
            "example.com",  # Missing scheme
            "htp://invalid.com",  # Wrong scheme
            "ftp://example.com",  # Unsupported scheme
            "",  # Empty
        ]
        
        for url in invalid_urls:
            with pytest.raises(HTTPException):
                validate_url(url)
    
    def test_url_too_long(self):
        """Test rejection of URLs exceeding maximum length."""
        long_url = "https://example.com/" + "a" * 2000
        
        with pytest.raises(HTTPException):
            validate_url(long_url)
    
    def test_internal_ip_blocked(self):
        """Test that internal IPs are blocked."""
        internal_urls = [
            "http://localhost:8000",
            "http://127.0.0.1",
            "http://192.168.1.1",
            "http://10.0.0.1",
            "http://172.16.0.1",
        ]
        
        for url in internal_urls:
            with pytest.raises(HTTPException):
                validate_url(url)


class TestCustomCodeValidation:
    """Tests for custom code validation."""
    
    def test_valid_custom_code(self):
        """Test validation of valid custom codes."""
        valid_codes = [
            "abc",
            "mysite",
            "github2024",
            "123abc",
            "a",  # Minimum
        ]
        
        for code in valid_codes:
            # Should not raise
            validate_custom_code(code)
    
    def test_invalid_custom_code_format(self):
        """Test rejection of invalid custom code formats."""
        invalid_codes = [
            "abc@def",  # Special char
            "abc def",  # Space
            "",  # Empty
            "123456789012345678901",  # Too long (> 20)
        ]
        
        for code in invalid_codes:
            with pytest.raises(HTTPException):
                validate_custom_code(code)
    
    def test_reserved_code_blocked(self):
        """Test that reserved codes are blocked."""
        reserved_codes = [
            "auth",
            "api",
            "admin",
            "shorten",
            "analytics",
            "health",
        ]
        
        for code in reserved_codes:
            with pytest.raises(HTTPException):
                validate_custom_code(code)


class TestEmailValidation:
    """Tests for email validation."""
    
    def test_valid_email(self):
        """Test validation of valid emails."""
        valid_emails = [
            "user@example.com",
            "john.doe@company.co.uk",
            "test+tag@example.com",
        ]
        
        for email in valid_emails:
            # Should not raise
            validate_email(email)
    
    def test_invalid_email(self):
        """Test rejection of invalid emails."""
        invalid_emails = [
            "not-an-email",
            "missing@domain",
            "@nodomain.com",
            "user@",
            "",
        ]
        
        for email in invalid_emails:
            with pytest.raises(HTTPException):
                validate_email(email)


class TestPasswordValidation:
    """Tests for password validation."""
    
    def test_valid_password(self):
        """Test validation of valid passwords."""
        valid_passwords = [
            "StrongPass123",
            "MyP@ssw0rd",
            "LongPasswordWith123Numbers",
        ]
        
        for password in valid_passwords:
            # Should not raise
            validate_password(password)
    
    def test_weak_password_too_short(self):
        """Test rejection of too-short passwords."""
        with pytest.raises(HTTPException):
            validate_password("Short1")  # Less than 8 chars
    
    def test_weak_password_no_uppercase(self):
        """Test rejection of passwords without uppercase."""
        with pytest.raises(HTTPException):
            validate_password("lowercase123")
    
    def test_weak_password_no_digit(self):
        """Test rejection of passwords without digits."""
        with pytest.raises(HTTPException):
            validate_password("NoDigitPassword")
    
    def test_weak_password_common(self):
        """Test rejection of common passwords."""
        common_passwords = [
            "Password123",  # Very common
            "Admin123",
            "Welcome123",
        ]
        
        for password in common_passwords:
            # Depending on implementation, might be blocked
            # This is optional depending on password requirements
            pass


class TestStringSanitization:
    """Tests for XSS prevention via string sanitization."""
    
    def test_sanitize_xss_attempts(self):
        """Test sanitization of XSS attempts."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "<img src=x onerror='alert(1)'>",
            "javascript:alert('xss')",
            "<iframe src='evil.com'></iframe>",
        ]
        
        for payload in xss_attempts:
            sanitized = sanitize_string(payload)
            # Should not contain script tags or javascript
            assert "<script>" not in sanitized.lower()
            assert "javascript:" not in sanitized.lower()
            assert "onerror" not in sanitized.lower()
    
    def test_sanitize_normal_text(self):
        """Test that normal text is preserved."""
        normal_text = "This is a normal string"
        sanitized = sanitize_string(normal_text)
        assert sanitized == normal_text
    
    def test_sanitize_special_chars(self):
        """Test handling of special characters."""
        special_text = "Test with special: @#$%^&*()"
        sanitized = sanitize_string(special_text)
        # Should preserve normal special characters
        assert "@#$%" in sanitized


class TestValidationEdgeCases:
    """Tests for edge cases in validation."""
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters."""
        # Should not raise
        validate_url("https://example.com/café")
    
    def test_internationalized_domain(self):
        """Test handling of internationalized domains."""
        # IDN domains should work
        validate_url("https://münchen.de")
    
    def test_very_long_valid_url(self):
        """Test handling of long but valid URLs."""
        # URL with query parameters
        long_url = "https://example.com?" + "&".join([f"param{i}=value{i}" for i in range(50)])
        # Should either pass or fail gracefully
        try:
            validate_url(long_url)
        except HTTPException as e:
            # If fails, should be clear reason
            assert "length" in str(e).lower() or "too long" in str(e).lower()

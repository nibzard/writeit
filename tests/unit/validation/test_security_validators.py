"""Tests for security validators."""

import tempfile
from pathlib import Path

import pytest

from writeit.shared.validation import ValidationContext
from writeit.shared.validation.security_validators import (
    CommandInjectionValidator,
    ContentSanitizer,
    FileSizeValidator,
    ResourceLimitValidator,
    SQLInjectionValidator,
    XSSValidator,
)


class TestCommandInjectionValidator:
    """Test CommandInjectionValidator."""
    
    def test_safe_command(self):
        validator = CommandInjectionValidator()
        result = validator.validate("echo hello world", ValidationContext())
        assert result.is_valid
    
    def test_dangerous_shell_metacharacters(self):
        validator = CommandInjectionValidator()
        dangerous_commands = [
            "echo hello; rm -rf /",
            "echo hello && rm file",
            "echo hello | cat",
            "echo hello & background",
            "echo $(whoami)",
            "echo `whoami`",
        ]
        
        for cmd in dangerous_commands:
            result = validator.validate(cmd, ValidationContext())
            assert not result.is_valid
            assert any("command injection" in error.lower() for error in result.errors)
    
    def test_dangerous_commands(self):
        validator = CommandInjectionValidator()
        dangerous_commands = [
            "rm -rf /",
            "del important_file",
            "curl malicious.com",
            "wget bad-script.sh",
            "nc -l 1234",
            "ssh attacker.com",
        ]
        
        for cmd in dangerous_commands:
            result = validator.validate(cmd, ValidationContext())
            assert not result.is_valid
            assert any("dangerous command" in error.lower() for error in result.errors)
    
    def test_script_execution_patterns(self):
        validator = CommandInjectionValidator()
        script_patterns = [
            '<script>alert("xss")</script>',
            'javascript:alert(1)',
            'vbscript:msgbox("test")',
            'onclick="alert(1)"',
        ]
        
        for pattern in script_patterns:
            result = validator.validate(pattern, ValidationContext())
            assert not result.is_valid
            assert any("script execution" in error.lower() for error in result.errors)
    
    def test_whitelisted_commands(self):
        validator = CommandInjectionValidator(
            allow_whitelisted_commands=True,
            whitelisted_commands={"curl"}
        )
        
        # Whitelisted command should pass
        result = validator.validate("curl safe-api.com", ValidationContext())
        assert result.is_valid
        
        # Non-whitelisted dangerous command should fail
        result = validator.validate("rm file", ValidationContext())
        assert not result.is_valid
    
    def test_non_string_input(self):
        validator = CommandInjectionValidator()
        result = validator.validate(123, ValidationContext())
        assert not result.is_valid
        assert any("must be a string" in error for error in result.errors)


class TestSQLInjectionValidator:
    """Test SQLInjectionValidator."""
    
    def test_safe_input(self):
        validator = SQLInjectionValidator()
        result = validator.validate("John Doe", ValidationContext())
        assert result.is_valid
    
    def test_sql_keywords(self):
        validator = SQLInjectionValidator()
        sql_injections = [
            "SELECT * FROM users",
            "admin'; DROP TABLE users; --",
            "1 OR 1=1",
            "'; INSERT INTO users VALUES ('hacker', 'pass'); --",
            "UNION SELECT password FROM users",
        ]
        
        for injection in sql_injections:
            result = validator.validate(injection, ValidationContext())
            assert not result.is_valid
            assert any("sql injection" in error.lower() for error in result.errors)
    
    def test_sql_comments(self):
        validator = SQLInjectionValidator()
        comment_injections = [
            "admin' --",
            "test /* comment */ injection",
            "value'; -- comment",
        ]
        
        for injection in comment_injections:
            result = validator.validate(injection, ValidationContext())
            assert not result.is_valid
            assert any("sql injection" in error.lower() for error in result.errors)
    
    def test_classic_injection_patterns(self):
        validator = SQLInjectionValidator()
        classic_patterns = [
            "' or '1'='1",
            "' or 'a'='a",
            "admin' or '1'='1' --",
        ]
        
        for pattern in classic_patterns:
            result = validator.validate(pattern, ValidationContext())
            assert not result.is_valid
            assert any("sql injection" in error.lower() for error in result.errors)
    
    def test_non_string_input(self):
        validator = SQLInjectionValidator()
        result = validator.validate(123, ValidationContext())
        assert not result.is_valid
        assert any("must be a string" in error for error in result.errors)


class TestXSSValidator:
    """Test XSSValidator."""
    
    def test_safe_content(self):
        validator = XSSValidator()
        result = validator.validate("This is safe content", ValidationContext())
        assert result.is_valid
    
    def test_script_tags(self):
        validator = XSSValidator()
        xss_attacks = [
            '<script>alert("xss")</script>',
            '<SCRIPT>alert("XSS")</SCRIPT>',
            '<script src="malicious.js"></script>',
        ]
        
        for attack in xss_attacks:
            result = validator.validate(attack, ValidationContext())
            assert not result.is_valid
            assert any("xss" in error.lower() for error in result.errors)
    
    def test_dangerous_tags(self):
        validator = XSSValidator()
        dangerous_tags = [
            '<iframe src="malicious.com"></iframe>',
            '<object data="malicious.swf"></object>',
            '<embed src="malicious.swf">',
            '<link rel="stylesheet" href="malicious.css">',
            '<meta http-equiv="refresh" content="0;url=malicious.com">',
        ]
        
        for tag in dangerous_tags:
            result = validator.validate(tag, ValidationContext())
            assert not result.is_valid
            assert any("xss" in error.lower() for error in result.errors)
    
    def test_javascript_protocols(self):
        validator = XSSValidator()
        protocols = [
            'javascript:alert(1)',
            'vbscript:msgbox("test")',
        ]
        
        for protocol in protocols:
            result = validator.validate(protocol, ValidationContext())
            assert not result.is_valid
            assert any("xss" in error.lower() for error in result.errors)
    
    def test_event_handlers(self):
        validator = XSSValidator()
        events = [
            'onclick="alert(1)"',
            'onmouseover="javascript:alert(1)"',
            'onerror="alert(1)"',
        ]
        
        for event in events:
            result = validator.validate(event, ValidationContext())
            assert not result.is_valid
            assert any("xss" in error.lower() for error in result.errors)
    
    def test_encoded_attacks(self):
        validator = XSSValidator()
        encoded_attacks = [
            '%3Cscript%3Ealert(1)%3C/script%3E',
            '&lt;script&gt;alert(1)&lt;/script&gt;',
            '&#x3C;script&#x3E;alert(1)&#x3C;/script&#x3E;',
        ]
        
        for attack in encoded_attacks:
            result = validator.validate(attack, ValidationContext())
            assert not result.is_valid
            assert any("encoded xss" in error.lower() for error in result.errors)
    
    def test_sanitize_mode(self):
        validator = XSSValidator(sanitize=True)
        result = validator.validate('<script>alert("xss")</script>', ValidationContext())
        
        # In sanitize mode, XSS should generate warnings instead of errors
        assert any("would be sanitized" in warning for warning in result.warnings)
    
    def test_non_string_input(self):
        validator = XSSValidator()
        result = validator.validate(123, ValidationContext())
        assert not result.is_valid
        assert any("must be a string" in error for error in result.errors)


class TestContentSanitizer:
    """Test ContentSanitizer."""
    
    def test_safe_content(self):
        sanitizer = ContentSanitizer()
        result = sanitizer.validate("This is safe content", ValidationContext())
        assert result.is_valid
        assert not result.warnings
    
    def test_html_content_sanitization(self):
        sanitizer = ContentSanitizer()
        html_content = '<div>Test <script>alert("xss")</script> content</div>'
        result = sanitizer.validate(html_content, ValidationContext())
        
        assert result.is_valid
        assert any("html content was escaped" in warning.lower() for warning in result.warnings)
        assert 'sanitized_content' in result.metadata
    
    def test_javascript_protocol_detection(self):
        sanitizer = ContentSanitizer()
        result = sanitizer.validate('Click <a href="javascript:alert(1)">here</a>', ValidationContext())
        
        assert result.is_valid
        assert any("javascript protocol detected" in warning.lower() for warning in result.warnings)
    
    def test_non_string_input(self):
        sanitizer = ContentSanitizer()
        result = sanitizer.validate(123, ValidationContext())
        assert not result.is_valid
        assert any("must be a string" in error for error in result.errors)
    
    def test_strip_dangerous_disabled(self):
        sanitizer = ContentSanitizer(strip_dangerous=False)
        html_content = '<div>Test content</div>'
        result = sanitizer.validate(html_content, ValidationContext())
        
        assert result.is_valid
        assert any("html tags detected" in warning.lower() for warning in result.warnings)
        # Should not escape when strip_dangerous=False
        assert 'sanitized_content' not in result.metadata


class TestFileSizeValidator:
    """Test FileSizeValidator."""
    
    def test_file_within_size_limit(self):
        validator = FileSizeValidator(max_size_bytes=1024)  # 1KB limit
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"x" * 500)  # 500 bytes
            temp_file.flush()
            
            result = validator.validate(temp_file.name, ValidationContext())
            assert result.is_valid
    
    def test_file_exceeds_size_limit(self):
        validator = FileSizeValidator(max_size_bytes=100)  # 100 bytes limit
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"x" * 200)  # 200 bytes
            temp_file.flush()
            
            result = validator.validate(temp_file.name, ValidationContext())
            assert not result.is_valid
            assert any("exceeds limit" in error for error in result.errors)
    
    def test_nonexistent_file(self):
        validator = FileSizeValidator(max_size_bytes=1024)
        result = validator.validate("nonexistent_file.txt", ValidationContext())
        
        assert not result.is_valid
        assert any("does not exist" in error for error in result.errors)
    
    def test_non_string_input(self):
        validator = FileSizeValidator(max_size_bytes=1024)
        result = validator.validate(123, ValidationContext())
        assert not result.is_valid
        assert any("must be a string" in error for error in result.errors)


class TestResourceLimitValidator:
    """Test ResourceLimitValidator."""
    
    def test_no_limits(self):
        validator = ResourceLimitValidator()
        result = validator.validate("any_value", ValidationContext())
        
        assert result.is_valid
        assert "No resource limits" in validator.description
    
    def test_memory_limit(self):
        validator = ResourceLimitValidator(max_memory_mb=256)
        result = validator.validate("any_value", ValidationContext())
        
        assert result.is_valid
        assert any("Memory usage will be limited" in warning for warning in result.warnings)
        assert result.metadata['max_memory_mb'] == 256
    
    def test_execution_time_limit(self):
        validator = ResourceLimitValidator(max_execution_time_seconds=30)
        result = validator.validate("any_value", ValidationContext())
        
        assert result.is_valid
        assert any("Execution time will be limited" in warning for warning in result.warnings)
        assert result.metadata['max_execution_time_seconds'] == 30
    
    def test_iteration_limit(self):
        validator = ResourceLimitValidator(max_iterations=1000)
        result = validator.validate("any_value", ValidationContext())
        
        assert result.is_valid
        assert any("Iterations will be limited" in warning for warning in result.warnings)
        assert result.metadata['max_iterations'] == 1000
    
    def test_all_limits(self):
        validator = ResourceLimitValidator(
            max_memory_mb=512,
            max_execution_time_seconds=60,
            max_iterations=5000
        )
        result = validator.validate("any_value", ValidationContext())
        
        assert result.is_valid
        assert len(result.warnings) == 3
        assert "memory: 512MB" in validator.description
        assert "time: 60s" in validator.description
        assert "iterations: 5000" in validator.description
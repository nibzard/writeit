"""Security-focused validators for preventing common attacks."""

import html
import re
import subprocess
from pathlib import Path
from typing import Any, List, Optional, Set

from .interfaces import ValidationContext, ValidationResult, ValidationRule


class CommandInjectionValidator(ValidationRule[str]):
    """Validates against command injection attacks."""
    
    # Common command injection patterns
    DANGEROUS_PATTERNS = [
        r'[;&|`$()]',  # Shell metacharacters
        r'\\x[0-9a-fA-F]{2}',  # Hex encoding
        r'%[0-9a-fA-F]{2}',  # URL encoding
        r'\$\{[^}]*\}',  # Variable substitution
        r'`[^`]*`',  # Command substitution
        r'\$\([^)]*\)',  # Command substitution
    ]
    
    DANGEROUS_COMMANDS = {
        'rm', 'del', 'rmdir', 'rd', 'format', 'fdisk', 'mkfs',
        'dd', 'curl', 'wget', 'nc', 'netcat', 'telnet', 'ssh',
        'eval', 'exec', 'system', 'shell_exec', 'passthru',
        'proc_open', 'popen', 'shell', 'cmd', 'powershell'
    }
    
    def __init__(self, allow_whitelisted_commands: bool = False,
                 whitelisted_commands: Optional[Set[str]] = None):
        self._allow_whitelisted = allow_whitelisted_commands
        self._whitelisted = whitelisted_commands or set()
    
    def validate(self, value: str, context: ValidationContext) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult.failure(["Value must be a string"])
        
        errors = []
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, value):
                errors.append(f"Potential command injection detected: matches pattern {pattern}")
        
        # Check for dangerous commands
        words = value.split()
        if words:
            first_word = words[0].lower()
            if first_word in self.DANGEROUS_COMMANDS:
                if not (self._allow_whitelisted and first_word in self._whitelisted):
                    errors.append(f"Dangerous command detected: {first_word}")
        
        # Check for script execution patterns
        script_patterns = [
            r'<script[^>]*>',  # Script tags
            r'javascript:',    # JavaScript protocol
            r'vbscript:',     # VBScript protocol
            r'on\w+\s*=',     # Event handlers
        ]
        
        for pattern in script_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                errors.append(f"Script execution pattern detected: {pattern}")
        
        if errors:
            return ValidationResult.failure(errors)
        
        return ValidationResult.success()
    
    @property
    def description(self) -> str:
        return "Must not contain command injection patterns"


class SQLInjectionValidator(ValidationRule[str]):
    """Validates against SQL injection attacks."""
    
    SQL_KEYWORDS = {
        'select', 'insert', 'update', 'delete', 'drop', 'create', 'alter',
        'truncate', 'exec', 'execute', 'union', 'declare', 'cast', 'convert'
    }
    
    DANGEROUS_PATTERNS = [
        r"'[^']*'",  # String literals
        r'--',       # SQL comments
        r'/\*.*?\*/',  # Block comments
        r';',        # Statement terminator
        r'\bor\b.*?=.*?=',  # OR injection pattern
        r'\band\b.*?=.*?=', # AND injection pattern
        r"'\s*or\s*'",  # Classic injection
        r"'\s*;\s*",    # Statement injection
    ]
    
    def validate(self, value: str, context: ValidationContext) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult.failure(["Value must be a string"])
        
        errors = []
        lower_value = value.lower()
        
        # Check for dangerous patterns first (more specific detection)
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                errors.append(f"Potential SQL injection: pattern detected {pattern}")
        
        # Check for SQL keywords in suspicious contexts only if other patterns found
        if errors or any(dangerous in lower_value for dangerous in ['--', ';', "'", '"']):
            for keyword in self.SQL_KEYWORDS:
                pattern = rf'\b{keyword}\b'
                if re.search(pattern, lower_value):
                    errors.append(f"Potential SQL injection: SQL keyword '{keyword}' detected")
                    break  # Only report one keyword to avoid spam
        
        if errors:
            return ValidationResult.failure(errors)
        
        return ValidationResult.success()
    
    @property
    def description(self) -> str:
        return "Must not contain SQL injection patterns"


class XSSValidator(ValidationRule[str]):
    """Validates against Cross-Site Scripting (XSS) attacks."""
    
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'<iframe[^>]*>',             # Iframe tags
        r'<object[^>]*>',             # Object tags
        r'<embed[^>]*>',              # Embed tags
        r'<link[^>]*>',               # Link tags
        r'<meta[^>]*>',               # Meta tags
        r'javascript:',               # JavaScript protocol
        r'vbscript:',                # VBScript protocol
        r'on\w+\s*=',                # Event handlers
        r'expression\s*\(',          # CSS expression
        r'@import',                  # CSS import
        r'url\s*\(',                 # CSS URL
    ]
    
    def __init__(self, sanitize: bool = False):
        self._sanitize = sanitize
    
    def validate(self, value: str, context: ValidationContext) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult.failure(["Value must be a string"])
        
        errors = []
        warnings = []
        
        # Check for XSS patterns
        for pattern in self.XSS_PATTERNS:
            matches = re.findall(pattern, value, re.IGNORECASE | re.DOTALL)
            if matches:
                if self._sanitize:
                    warnings.append(f"XSS pattern detected and would be sanitized: {pattern}")
                else:
                    errors.append(f"Potential XSS attack detected: {pattern}")
        
        # Check for encoded attacks
        encoded_patterns = [
            r'%3[cC]script',  # <script encoded
            r'&lt;script',    # <script HTML encoded
            r'&#x3C;script',  # <script hex encoded
        ]
        
        for pattern in encoded_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                errors.append(f"Encoded XSS pattern detected: {pattern}")
        
        if errors:
            return ValidationResult.failure(errors, warnings)
        
        return ValidationResult.success(warnings)
    
    @property
    def description(self) -> str:
        suffix = " (will sanitize)" if self._sanitize else ""
        return f"Must not contain XSS patterns{suffix}"


class ContentSanitizer(ValidationRule[str]):
    """Sanitizes and validates content for safe display."""
    
    def __init__(self, allowed_tags: Optional[Set[str]] = None,
                 strip_dangerous: bool = True):
        self._allowed_tags = allowed_tags or {'p', 'br', 'strong', 'em', 'ul', 'ol', 'li'}
        self._strip_dangerous = strip_dangerous
    
    def validate(self, value: str, context: ValidationContext) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult.failure(["Value must be a string"])
        
        warnings = []
        sanitized_value = value
        
        # HTML escape the content
        if self._strip_dangerous:
            sanitized_value = html.escape(sanitized_value)
            if sanitized_value != value:
                warnings.append("HTML content was escaped for safety")
        
        # Check for potentially dangerous content
        if re.search(r'<[^>]*>', value):
            warnings.append("HTML tags detected in content")
        
        if re.search(r'javascript:', value, re.IGNORECASE):
            warnings.append("JavaScript protocol detected in content")
        
        metadata = {'sanitized_content': sanitized_value} if sanitized_value != value else {}
        
        return ValidationResult.success(warnings, metadata)
    
    @property
    def description(self) -> str:
        return "Content will be sanitized for safe display"


class FileSizeValidator(ValidationRule[str]):
    """Validates file size limits."""
    
    def __init__(self, max_size_bytes: int):
        self._max_size = max_size_bytes
    
    def validate(self, value: str, context: ValidationContext) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult.failure(["Value must be a string (file path)"])
        
        try:
            file_path = Path(value)
            if not file_path.exists():
                return ValidationResult.failure([f"File does not exist: {value}"])
            
            file_size = file_path.stat().st_size
            if file_size > self._max_size:
                mb_size = file_size / (1024 * 1024)
                max_mb = self._max_size / (1024 * 1024)
                return ValidationResult.failure([
                    f"File size {mb_size:.1f}MB exceeds limit of {max_mb:.1f}MB"
                ])
            
            return ValidationResult.success()
            
        except OSError as e:
            return ValidationResult.failure([f"Error reading file: {e}"])
    
    @property
    def description(self) -> str:
        mb_limit = self._max_size / (1024 * 1024)
        return f"File size must not exceed {mb_limit:.1f}MB"


class ResourceLimitValidator(ValidationRule[Any]):
    """Validates resource consumption limits."""
    
    def __init__(self, max_memory_mb: Optional[int] = None,
                 max_execution_time_seconds: Optional[int] = None,
                 max_iterations: Optional[int] = None):
        self._max_memory = max_memory_mb
        self._max_execution_time = max_execution_time_seconds
        self._max_iterations = max_iterations
    
    def validate(self, value: Any, context: ValidationContext) -> ValidationResult:
        warnings = []
        
        # This is more of a policy validator - the actual enforcement
        # would happen in the execution engine
        
        if self._max_memory is not None:
            warnings.append(f"Memory usage will be limited to {self._max_memory}MB")
        
        if self._max_execution_time is not None:
            warnings.append(f"Execution time will be limited to {self._max_execution_time} seconds")
        
        if self._max_iterations is not None:
            warnings.append(f"Iterations will be limited to {self._max_iterations}")
        
        metadata = {
            'max_memory_mb': self._max_memory,
            'max_execution_time_seconds': self._max_execution_time,
            'max_iterations': self._max_iterations
        }
        
        return ValidationResult.success(warnings, metadata)
    
    @property
    def description(self) -> str:
        limits = []
        if self._max_memory:
            limits.append(f"memory: {self._max_memory}MB")
        if self._max_execution_time:
            limits.append(f"time: {self._max_execution_time}s")
        if self._max_iterations:
            limits.append(f"iterations: {self._max_iterations}")
        
        return f"Resource limits: {', '.join(limits)}" if limits else "No resource limits"
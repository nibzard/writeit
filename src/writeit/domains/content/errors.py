"""Content domain errors."""

from ...shared.errors import DomainError


class ContentError(DomainError):
    """Base exception for content domain errors."""
    pass


class TemplateNotFoundError(ContentError):
    """Raised when a template is not found."""
    
    def __init__(self, template_name: str):
        self.template_name = template_name
        super().__init__(f"Template '{template_name}' not found")


class TemplateValidationError(ContentError):
    """Raised when template validation fails."""
    
    def __init__(self, template_name: str, validation_errors: list = None):
        self.template_name = template_name
        self.validation_errors = validation_errors or []
        message = f"Template '{template_name}' validation failed"
        if self.validation_errors:
            message += f": {', '.join(self.validation_errors)}"
        super().__init__(message)


class TemplateAlreadyExistsError(ContentError):
    """Raised when trying to create a template that already exists."""
    
    def __init__(self, template_name: str):
        self.template_name = template_name
        super().__init__(f"Template '{template_name}' already exists")


class ContentGenerationError(ContentError):
    """Raised when content generation fails."""
    
    def __init__(self, template_name: str, reason: str = None):
        self.template_name = template_name
        self.reason = reason
        message = f"Content generation failed for template '{template_name}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class StylePrimerNotFoundError(ContentError):
    """Raised when a style primer is not found."""
    
    def __init__(self, style_name: str):
        self.style_name = style_name
        super().__init__(f"Style primer '{style_name}' not found")


class StylePrimerValidationError(ContentError):
    """Raised when style primer validation fails."""
    
    def __init__(self, style_name: str, validation_errors: list = None):
        self.style_name = style_name
        self.validation_errors = validation_errors or []
        message = f"Style primer '{style_name}' validation failed"
        if self.validation_errors:
            message += f": {', '.join(self.validation_errors)}"
        super().__init__(message)


class ContentValidationError(ContentError):
    """Raised when content validation fails."""
    
    def __init__(self, content_id: str, validation_errors: list = None):
        self.content_id = content_id
        self.validation_errors = validation_errors or []
        message = f"Content '{content_id}' validation failed"
        if self.validation_errors:
            message += f": {', '.join(self.validation_errors)}"
        super().__init__(message)


class ContentFormatError(ContentError):
    """Raised when content format is invalid."""
    
    def __init__(self, content_id: str, expected_format: str, actual_format: str = None):
        self.content_id = content_id
        self.expected_format = expected_format
        self.actual_format = actual_format
        message = f"Content '{content_id}' format error"
        if actual_format:
            message += f": expected '{expected_format}', got '{actual_format}'"
        else:
            message += f": invalid format, expected '{expected_format}'"
        super().__init__(message)


__all__ = [
    "ContentError",
    "TemplateNotFoundError",
    "TemplateValidationError",
    "TemplateAlreadyExistsError", 
    "ContentGenerationError",
    "StylePrimerNotFoundError",
    "StylePrimerValidationError",
    "ContentValidationError",
    "ContentFormatError",
]
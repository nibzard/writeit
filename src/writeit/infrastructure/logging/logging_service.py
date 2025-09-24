"""Logging infrastructure for WriteIt."""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime
import json
import sys


class WriteItLogFormatter(logging.Formatter):
    """Custom log formatter for WriteIt with structured logging support."""
    
    def __init__(self, include_workspace: bool = True):
        self.include_workspace = include_workspace
        super().__init__()
    
    def format(self, record):
        """Format log record with WriteIt-specific information."""
        
        # Create base format
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        level = record.levelname
        name = record.name
        message = record.getMessage()
        
        # Basic format: timestamp level name message
        basic_format = f"{timestamp} {level} {name} {message}"
        
        # Add workspace info if available
        if self.include_workspace and hasattr(record, 'workspace_name'):
            basic_format = f"[{record.workspace_name}] {basic_format}"
        
        # Add structured data if available
        if hasattr(record, 'structured_data'):
            structured_json = json.dumps(record.structured_data)
            basic_format = f"{basic_format} | {structured_json}"
        
        # Add exception info if present
        if record.exc_info:
            basic_format += "\n" + self.formatException(record.exc_info)
        
        return basic_format


class LoggingService:
    """Centralized logging service for WriteIt."""
    
    def __init__(self):
        self._configured = False
        self._workspace_name: Optional[str] = None
    
    def setup_logging(
        self,
        log_level: str = "INFO",
        log_file: Optional[Path] = None,
        enable_console: bool = True,
        workspace_name: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
    ) -> logging.Logger:
        """Setup centralized logging for WriteIt.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
            enable_console: Whether to log to console
            workspace_name: Workspace name for log identification
            max_bytes: Maximum bytes per log file before rotation
            backup_count: Number of backup log files to keep
            
        Returns:
            Configured logger instance
        """
        
        # Store workspace name for formatter
        self._workspace_name = workspace_name
        
        # Create main logger
        logger = logging.getLogger("writeit")
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create custom formatter
        formatter = WriteItLogFormatter(include_workspace=workspace_name is not None)
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, log_level.upper()))
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler with rotation
        if log_file:
            # Ensure log directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, log_level.upper()))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
        
        # Mark as configured
        self._configured = True
        
        # Add workspace info to logger
        if workspace_name:
            logger = self._add_workspace_adapter(logger, workspace_name)
        
        return logger
    
    def _add_workspace_adapter(self, logger: logging.Logger, workspace_name: str) -> logging.Logger:
        """Add workspace information to log records."""
        
        class WorkspaceAdapter(logging.LoggerAdapter):
            """Logger adapter that adds workspace information."""
            
            def __init__(self, logger, workspace_name):
                super().__init__(logger, {})
                self.workspace_name = workspace_name
            
            def process(self, msg, kwargs):
                """Add workspace name to log record."""
                kwargs.setdefault('extra', {})['workspace_name'] = self.workspace_name
                return msg, kwargs
        
        return WorkspaceAdapter(logger, workspace_name)
    
    def get_logger(self, name: str = "writeit") -> logging.Logger:
        """Get a logger instance.
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
    
    def configure_default_logging(self, workspace_path: Optional[Path] = None) -> logging.Logger:
        """Configure default logging with sensible defaults.
        
        This method provides backward compatibility with the legacy logging system.
        
        Args:
            workspace_path: Optional workspace path for log file location
            
        Returns:
            Configured logger instance
        """
        
        # Determine log file location
        log_file = None
        if workspace_path:
            log_file = workspace_path / "logs" / "writeit.log"
        
        # Setup logging with defaults
        return self.setup_logging(
            log_level="INFO",
            log_file=log_file,
            enable_console=True,
            workspace_name=self._workspace_name,
            max_bytes=10 * 1024 * 1024,  # 10MB
            backup_count=5,
        )
    
    def add_structured_data(self, logger: logging.Logger, **data):
        """Add structured data to the next log call.
        
        Args:
            logger: Logger instance
            **data: Structured data to include in log records
        """
        
        # Create a custom logger that includes structured data
        class StructuredDataLogger(logging.Logger):
            """Logger that includes structured data."""
            
            def __init__(self, name, level=logging.NOTSET):
                super().__init__(name, level)
                self.structured_data = data
            
            def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None):
                """Create log record with structured data."""
                if extra is None:
                    extra = {}
                extra['structured_data'] = data
                return super().makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra)
        
        # Replace the logger temporarily
        original_logger_class = logging.getLoggerClass()
        logging.setLoggerClass(StructureduredDataLogger)
        
        try:
            # Get new logger instance
            new_logger = logging.getLogger(logger.name)
            new_logger.setLevel(logger.level)
            new_logger.handlers = logger.handlers
            new_logger.propagate = logger.propagate
            
            return new_logger
        finally:
            # Restore original logger class
            logging.setLoggerClass(original_logger_class)


# Global logging service instance
_logging_service = LoggingService()


def get_logging_service() -> LoggingService:
    """Get the global logging service instance."""
    return _logging_service


def configure_default_logging(workspace_path: Optional[Path] = None) -> logging.Logger:
    """Configure default logging with sensible defaults.
    
    This function provides backward compatibility with the legacy logging system.
    
    Args:
        workspace_path: Optional workspace path for log file location
        
    Returns:
        Configured logger instance
    """
    return _logging_service.configure_default_logging(workspace_path)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    enable_console: bool = True,
    workspace_name: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """Setup centralized logging for WriteIt.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        enable_console: Whether to log to console
        workspace_name: Workspace name for log identification
        max_bytes: Maximum bytes per log file before rotation
        backup_count: Number of backup log files to keep
        
    Returns:
        Configured logger instance
    """
    return _logging_service.setup_logging(
        log_level=log_level,
        log_file=log_file,
        enable_console=enable_console,
        workspace_name=workspace_name,
        max_bytes=max_bytes,
        backup_count=backup_count,
    )


__all__ = [
    "LoggingService",
    "WriteItLogFormatter",
    "get_logging_service",
    "configure_default_logging",
    "setup_logging",
]
"""Centralized logging configuration and utilities.

Provides:
- get_logger(): Get a configured logger for any module
- Structured logging helpers
- Request context injection
"""
import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__ from calling module)
        level: Optional logging level override
    
    Returns:
        Configured logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("User logged in", extra={"user_id": str(user.id)})
    """
    logger = logging.getLogger(name)
    
    if level is not None:
        logger.setLevel(level)
    
    return logger


# Convenience loggers for common use cases
def get_service_logger(service_name: str) -> logging.Logger:
    """Get logger for service layer.
    
    Args:
        service_name: Name of the service module
    
    Returns:
        Logger with 'services' namespace
    """
    return get_logger(f"services.{service_name}")


def get_api_logger(view_name: str) -> logging.Logger:
    """Get logger for API views.
    
    Args:
        view_name: Name of the view/endpoint
    
    Returns:
        Logger with 'api' namespace
    """
    return get_logger(f"api.{view_name}")


def get_task_logger(task_name: str) -> logging.Logger:
    """Get logger for Celery tasks.
    
    Args:
        task_name: Name of the task
    
    Returns:
        Logger with 'tasks' namespace
    """
    return get_logger(f"tasks.{task_name}")


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Adapter that adds structured context to log messages.
    
    Usage:
        logger = get_logger(__name__)
        adapter = StructuredLoggerAdapter(logger, {"request_id": "abc123"})
        adapter.info("Processing request", extra={"user_id": "xyz"})
    """
    
    def process(self, msg, kwargs):
        """Add context data to log record."""
        # Merge adapter's extra with call's extra
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs

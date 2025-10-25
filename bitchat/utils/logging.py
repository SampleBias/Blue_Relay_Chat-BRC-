"""
Logging utilities for bitchat RPi 4 client.

This module provides centralized logging configuration and utilities
for consistent logging throughout the application.
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional, Union

from ..constants import DEFAULT_DATA_DIR


def setup_logging(
    level: Union[str, int] = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # Default to 10MB
    backup_count: int = 5,
    console_output: bool = True,
) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, uses default location.
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
        console_output: Whether to output logs to console
        
    Returns:
        Configured logger instance
    """
    # Convert string level to logging constant
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Create root logger
    logger = logging.getLogger("bitchat")
    logger.setLevel(level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if log file specified
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Use rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"bitchat.{name}")


def set_log_level(level: Union[str, int]) -> None:
    """
    Change the logging level for all bitchat loggers.
    
    Args:
        level: New logging level
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Update root logger level
    logger = logging.getLogger("bitchat")
    logger.setLevel(level)
    
    # Update all handlers
    for handler in logger.handlers:
        handler.setLevel(level)


def add_log_file(
    log_file: str,
    level: Union[str, int] = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # Default to 10MB
    backup_count: int = 5,
) -> None:
    """
    Add a file handler to the root logger.
    
    Args:
        log_file: Path to log file
        level: Logging level for this handler
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
    """
    # Convert string level to logging constant
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Create and add file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    logger = logging.getLogger("bitchat")
    logger.addHandler(file_handler)


def log_exception(logger: logging.Logger, message: str, exc_info: bool = True) -> None:
    """
    Log an exception with optional traceback.
    
    Args:
        logger: Logger instance to use
        message: Error message to log
        exc_info: Whether to include exception information
    """
    logger.error(message, exc_info=exc_info)


def log_function_call(logger: logging.Logger) -> callable:
    """
    Decorator to log function calls.
    
    Args:
        logger: Logger instance to use
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} returned {result}")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
                raise
        return wrapper
    return decorator


def log_async_function_call(logger: logging.Logger) -> callable:
    """
    Decorator to log async function calls.
    
    Args:
        logger: Logger instance to use
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            logger.debug(f"Calling async {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"async {func.__name__} returned {result}")
                return result
            except Exception as e:
                logger.error(f"async {func.__name__} raised {type(e).__name__}: {e}")
                raise
        return wrapper
    return decorator


class ContextFilter(logging.Filter):
    """Custom log filter to add context information."""
    
    def __init__(self, context: Optional[dict] = None):
        """
        Initialize the context filter.
        
        Args:
            context: Dictionary of context information to add to log records
        """
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context information to log records."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True
    
    def update_context(self, **kwargs) -> None:
        """Update the context information."""
        self.context.update(kwargs)


class PerformanceLogger:
    """Logger for performance monitoring and metrics."""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize the performance logger.
        
        Args:
            logger: Logger instance to use
        """
        self.logger = logger
        self.timers = {}
    
    def start_timer(self, name: str) -> None:
        """Start a named timer."""
        import time
        self.timers[name] = time.time()
    
    def end_timer(self, name: str) -> float:
        """
        End a named timer and log the duration.
        
        Args:
            name: Timer name
            
        Returns:
            Duration in seconds
        """
        import time
        if name not in self.timers:
            self.logger.warning(f"Timer '{name}' was not started")
            return 0.0
        
        duration = time.time() - self.timers[name]
        del self.timers[name]
        self.logger.info(f"Performance: {name} took {duration:.3f} seconds")
        return duration
    
    def log_memory_usage(self) -> None:
        """Log current memory usage."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            self.logger.info(f"Memory usage: {memory_mb:.1f} MB")
        except ImportError:
            self.logger.warning("psutil not available for memory monitoring")
        except Exception as e:
            self.logger.error(f"Error getting memory usage: {e}")
    
    def log_cpu_usage(self) -> None:
        """Log current CPU usage."""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            self.logger.info(f"CPU usage: {cpu_percent:.1f}%")
        except ImportError:
            self.logger.warning("psutil not available for CPU monitoring")
        except Exception as e:
            self.logger.error(f"Error getting CPU usage: {e}")


# Create a default performance logger instance
def get_performance_logger(name: str) -> PerformanceLogger:
    """
    Get a performance logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        PerformanceLogger instance
    """
    logger = get_logger(name)
    return PerformanceLogger(logger)
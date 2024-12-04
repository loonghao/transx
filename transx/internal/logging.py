"""Logging configuration for TransX.
"""
# ruff: noqa: I001
# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# Import built-in modules
import logging
import os
import sys
import traceback


try:
    # Import built-in modules
    from logging import NullHandler
except ImportError:
    # Python 2.6 compatibility
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

def _get_caller_name():
    """Get the name of the calling module.

    Returns:
        str: Name of the calling module or 'transx' if not found
    """
    try:
        frame = sys._getframe(2)  # Skip this function and get_logger/setup_logging
        name = frame.f_globals.get("__name__")
        if name:
            return name
    except (AttributeError, ValueError):
        # Handle cases where sys._getframe is not available
        try:
            # Alternative method using traceback
            stack = traceback.extract_stack()
            if len(stack) >= 3:
                # Get the filename of the caller (excluding .py)
                caller = os.path.splitext(os.path.basename(stack[-3][0]))[0]
                return "transx." + caller
        except Exception:
            pass
    return "transx"

def setup_logging(name=None, level=logging.INFO):
    """Set up logging configuration.

    Args:
        name (str, optional): Logger name. If None, uses __name__ of caller
        level (int, optional): Logging level. Defaults to INFO

    Returns:
        logging.Logger: Configured logger instance
    """
    if name is None:
        name = _get_caller_name()

    logger = logging.getLogger(name)

    # Only configure if no handlers are set (avoid duplicate configuration)
    root_logger = logging.getLogger()
    if not logger.handlers and not root_logger.handlers:
        # Set up default configuration
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Add stream handler
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        root_logger.setLevel(level)

    # Ensure logger has at least a NullHandler to prevent "No handlers found" warning
    if not logger.handlers:
        logger.addHandler(NullHandler())

    # Set level for this specific logger
    logger.setLevel(level)

    return logger

def get_logger(name=None):
    """Get a logger instance.

    This is the preferred way to get a logger in the TransX codebase.

    Args:
        name (str, optional): Logger name. If None, uses __name__ of caller

    Returns:
        logging.Logger: Logger instance
    """
    if name is None:
        name = _get_caller_name()

    logger = logging.getLogger(name)

    # Ensure logger has at least a NullHandler
    if not logger.handlers:
        logger.addHandler(NullHandler())

    return logger

"""
Utility module for Flip or FlOOP.

Provides shared constants, path resolution helpers, logging configuration,
and the centralized color/size definitions used across all screens.
"""

import os
import logging

# ---------------------------------------------------------------------------
# Path Constants
# ---------------------------------------------------------------------------

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
"""Absolute path to the project root directory (one level above ``src/``)."""

ASSETS_DIR: str = os.path.join(BASE_DIR, "assets")
"""Absolute path to the ``assets/`` folder containing images and audio."""

# ---------------------------------------------------------------------------
# Window / UI Constants
# ---------------------------------------------------------------------------

WINDOW_WIDTH: int = 750
"""Fixed width of the application window in pixels."""

WINDOW_HEIGHT: int = 865
"""Fixed height of the application window in pixels."""

WINDOW_SIZE: tuple[int, int] = (WINDOW_WIDTH, WINDOW_HEIGHT)
"""``(width, height)`` tuple for the application window."""

# Color palette — rustic parchment / jungle theme
COLOR_PARCHMENT: str = "#FBF4E6"
"""Light parchment background color."""

COLOR_BROWN_DARK: str = "#5C3A21"
"""Dark brown used for borders and headings."""

COLOR_BROWN_BUTTON: str = "#80461B"
"""Medium brown used for primary action buttons."""

COLOR_BROWN_BUTTON_ACTIVE: str = "#6B3A16"
"""Active/hover state for primary action buttons."""

COLOR_TAN_BUTTON: str = "#C19A6B"
"""Tan color used for secondary action buttons."""

COLOR_TAN_BUTTON_ACTIVE: str = "#A68456"
"""Active/hover state for secondary action buttons."""

COLOR_TEXT_DARK: str = "#333333"
"""Dark gray used for body text."""

COLOR_TEXT_MUTED: str = "#777777"
"""Muted gray used for subtitles and hints."""

COLOR_TEXT_CREDITS: str = "#444444"
"""Gray used for credits text."""

COLOR_TEXT_ITALIC: str = "#555555"
"""Gray used for italic/footer text."""

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logger(name: str = "flip_or_floop") -> logging.Logger:
    """
    Create and return a configured logger instance.

    The logger writes to ``stderr`` with a consistent format including
    the timestamp, logger name, severity level, and message.  Calling
    this function multiple times with the same *name* returns the same
    logger instance (standard :mod:`logging` behaviour).

    Args:
        name: The logger name.  Defaults to ``"flip_or_floop"``.

    Returns:
        A :class:`logging.Logger` configured with a ``StreamHandler``.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when called more than once.
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# Module-level logger for internal use.
_logger = setup_logger("utils")

# ---------------------------------------------------------------------------
# Asset Helpers
# ---------------------------------------------------------------------------

def get_asset_path(filename: str) -> str:
    """
    Resolve the absolute path for an asset file inside the ``assets/`` folder.

    Args:
        filename: The basename of the asset (e.g. ``"background.png"``).

    Returns:
        The absolute path to the asset.

    Raises:
        FileNotFoundError: If the resolved path does not exist on disk.
        ValueError: If *filename* is empty or ``None``.
    """
    if not filename:
        raise ValueError("Asset filename must not be empty or None.")

    path = os.path.join(ASSETS_DIR, filename)

    if not os.path.exists(path):
        _logger.error("Asset not found: %s", path)
        raise FileNotFoundError(
            f"Asset '{filename}' not found at expected path: {path}"
        )

    return path

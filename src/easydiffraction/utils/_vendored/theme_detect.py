# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Jupyter theme detection with custom detection order.

This module wraps the vendored jupyter_dark_detect package and provides
a custom detection order optimized for EasyDiffraction's use case.

Detection Strategy (in priority order):

1. JupyterLab settings files (~/.jupyter/lab/user-settings/)
2. VS Code settings (when VSCODE_PID env var is present)
3. JavaScript DOM inspection (for browser-based environments)
4. System preferences (macOS, Windows) - fallback only

Note:
    The detection order differs from upstream jupyter_dark_detect.
    We prioritize JavaScript DOM inspection over system preferences
    because the Jupyter theme may differ from the system theme.

Example:
    >>> from easydiffraction.utils._vendored.theme_detect import is_dark
    >>> if is_dark():
    ...     print('Dark mode detected')
"""

from __future__ import annotations

from typing import Optional

# Import detection functions from vendored jupyter_dark_detect
from easydiffraction.utils._vendored.jupyter_dark_detect.detector import (
    _check_javascript_detection,
)
from easydiffraction.utils._vendored.jupyter_dark_detect.detector import _check_jupyterlab_settings
from easydiffraction.utils._vendored.jupyter_dark_detect.detector import _check_system_preferences
from easydiffraction.utils._vendored.jupyter_dark_detect.detector import _check_vscode_settings


def is_dark() -> bool:
    """Check if the Jupyter environment is running in dark mode.

    This function uses a custom detection order that prioritizes
    Jupyter-specific detection over system preferences.

    Detection order:

    1. JupyterLab settings files (most reliable for JupyterLab)
    2. VS Code settings (when running in VS Code)
    3. JavaScript DOM inspection (for browser-based Jupyter)
    4. System preferences (fallback - may differ from Jupyter theme)

    Returns:
        True if dark mode is detected, False otherwise.
    """
    # Try Jupyter-specific methods first
    result = _check_jupyterlab_settings()
    if result is not None:
        return result

    result = _check_vscode_settings()
    if result is not None:
        return result

    # JavaScript DOM inspection for browser environments
    # (Classic Notebook, Colab, Binder, etc.)
    # This comes BEFORE system preferences because Jupyter theme
    # may differ from system theme
    result = _check_javascript_detection()
    if result is not None:
        return result

    # System preferences as last resort
    # Returns True (dark), False (light), or None (unknown)
    # Default to light mode (False) if nothing detected
    system_result = _check_system_preferences()
    return system_result if system_result is not None else False


def get_detection_result() -> dict[str, Optional[bool]]:
    """Get results from all detection methods for debugging.

    Returns:
        Dictionary with detection method names as keys and their
        results (True/False/None) as values.
    """
    return {
        'jupyterlab_settings': _check_jupyterlab_settings(),
        'vscode_settings': _check_vscode_settings(),
        'javascript_dom': _check_javascript_detection(),
        'system_preferences': _check_system_preferences(),
    }

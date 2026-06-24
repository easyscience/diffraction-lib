# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Jupyter theme detection with custom detection order.

This module wraps the vendored jupyter_dark_detect package and provides
a custom detection order optimized for EasyDiffraction's use case.

Detection Strategy (in priority order):

1. JupyterLab settings files (~/.jupyter/lab/user-settings/)
2. VS Code settings (when VSCODE_PID env var is present)
3. System preferences (macOS, Windows) - fallback only

Note: the upstream JavaScript DOM probe is deliberately **not** in this
order. It depends on the classic Notebook ``IPython.notebook.kernel``
API, which JupyterLab removed, so it can never return a value there; it
only publishes an (invisible) ``Javascript`` display and sleeps. Calling
it once per figure/table render left a stack of blank output rows in the
notebook (worst case, several per ``project.save()``). The probe is kept
available through :func:`get_detection_result` for debugging but is not
used for live theme detection. Detection still differs from upstream by
prioritizing the Jupyter-specific settings files over system
preferences, because the Jupyter theme may differ from the system theme.

Example: >>> from easydiffraction.utils._vendored.theme_detect import
is_dark >>> if is_dark(): ...     print('Dark mode detected')
"""

from __future__ import annotations

# Import detection functions from vendored jupyter_dark_detect
from easydiffraction.utils._vendored.jupyter_dark_detect.detector import (
    _check_javascript_detection,
)
from easydiffraction.utils._vendored.jupyter_dark_detect.detector import _check_jupyterlab_settings
from easydiffraction.utils._vendored.jupyter_dark_detect.detector import _check_system_preferences
from easydiffraction.utils._vendored.jupyter_dark_detect.detector import _check_vscode_settings


def is_dark() -> bool:
    """
    Check if the Jupyter environment is running in dark mode.

    This function uses a custom detection order that prioritizes
    Jupyter-specific detection over system preferences.

    Detection order:

    1. JupyterLab settings files (most reliable for JupyterLab) 2. VS
    Code settings (when running in VS Code) 3. System preferences
    (fallback - may differ from Jupyter theme)

    The JavaScript DOM probe is intentionally omitted: it cannot return
    a value under JupyterLab and only emits blank ``Javascript`` display
    output as a side effect (see the module docstring).

    Returns
    -------
    bool
        True if dark mode is detected, False otherwise.
    """
    # Try Jupyter-specific methods first
    result = _check_jupyterlab_settings()
    if result is not None:
        return result

    result = _check_vscode_settings()
    if result is not None:
        return result

    # System preferences as last resort
    # Returns True (dark), False (light), or None (unknown)
    # Default to light mode (False) if nothing detected
    system_result = _check_system_preferences()
    return system_result if system_result is not None else False


def get_detection_result() -> dict[str, bool | None]:
    """
    Get results from all detection methods for debugging.

    Returns
    -------
    dict[str, bool | None]
        Dictionary with detection method names as keys and their results
        (True/False/None) as values.
    """
    return {
        'jupyterlab_settings': _check_jupyterlab_settings(),
        'vscode_settings': _check_vscode_settings(),
        'javascript_dom': _check_javascript_detection(),
        'system_preferences': _check_system_preferences(),
    }

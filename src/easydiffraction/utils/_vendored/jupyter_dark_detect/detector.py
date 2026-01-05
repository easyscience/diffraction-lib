"""Dark mode detection for Jupyter environments."""

import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


def is_dark() -> bool:
    """Check if Jupyter Notebook/Lab is running in dark mode.

    This function attempts multiple detection strategies:
    1. JupyterLab theme settings files
    2. VS Code settings (when running in VS Code)
    3. JavaScript DOM inspection
    4. System preferences (macOS)

    Returns:
        bool: True if dark mode is detected, False otherwise
    """
    # Try JupyterLab settings first
    result = _check_jupyterlab_settings()
    if result is not None:
        return result

    # Check VS Code settings
    result = _check_vscode_settings()
    if result is not None:
        return result

    # Try JavaScript detection
    result = _check_javascript_detection()
    if result is not None:
        return result

    # Check system preferences
    result = _check_system_preferences()
    if result is not None:
        return result

    # Default to light mode
    return False


def _check_jupyterlab_settings() -> Optional[bool]:
    """Check JupyterLab theme settings files."""
    jupyter_config_paths = [
        Path.home()
        / '.jupyter'
        / 'lab'
        / 'user-settings'
        / '@jupyterlab'
        / 'apputils-extension'
        / 'themes.jupyterlab-settings',
        Path.home()
        / '.jupyter'
        / 'lab'
        / 'user-settings'
        / '@jupyterlab'
        / 'apputils-extension'
        / 'themes.jupyterlab-settings.json',
    ]

    for config_path in jupyter_config_paths:
        if config_path.exists():
            try:
                with Path(config_path).open('r') as f:
                    content = f.read()
                    # Remove comments from the JSON (JupyterLab allows comments)
                    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
                    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

                    settings = json.loads(content)
                    theme = settings.get('theme', '').lower()

                    if 'dark' in theme:
                        return True
                    elif 'light' in theme:
                        return False
            except Exception:
                continue

    return None


def _check_vscode_settings() -> Optional[bool]:
    """Check VS Code settings when running in VS Code."""
    if 'VSCODE_PID' not in os.environ:
        return None

    # Check VS Code NLS config first
    vscode_nls = os.environ.get('VSCODE_NLS_CONFIG', '')
    if 'dark' in vscode_nls.lower():
        return True

    # Check VS Code settings files
    vscode_settings_paths = [
        Path.cwd() / '.vscode' / 'settings.json',
        Path.home() / '.config' / 'Code' / 'User' / 'settings.json',
        Path.home() / 'Library' / 'Application Support' / 'Code' / 'User' / 'settings.json',
        # macOS
        Path.home() / 'AppData' / 'Roaming' / 'Code' / 'User' / 'settings.json',  # Windows
    ]

    for settings_path in vscode_settings_paths:
        if settings_path.exists():
            try:
                with Path(settings_path).open('r') as f:
                    settings = json.load(f)
                    theme = settings.get('workbench.colorTheme', '').lower()
                    if 'dark' in theme:
                        return True
                    elif 'light' in theme:
                        return False
            except Exception:
                continue

    return None


def _check_javascript_detection() -> Optional[bool]:
    """Use JavaScript to detect dark mode in the browser."""
    try:
        from IPython import get_ipython
        from IPython.display import Javascript
        from IPython.display import display

        ipython = get_ipython()
        if ipython is None:
            return None

        # First try the advanced detection with computed styles
        try:
            display(
                Javascript("""
                (function() {
                    var isDark = false;

                    // Check JupyterLab theme
                    if (document.body.classList.contains('jp-mod-dark') || 
                        document.body.classList.contains('theme-dark') ||
                        document.body.classList.contains('vscode-dark')) {
                        isDark = true;
                    }

                    // Check theme attribute
                    var themeAttr = document.body.getAttribute('data-jp-theme-name');
                    if (themeAttr && themeAttr.includes('dark')) {
                        isDark = true;
                    }

                    // Check computed background color
                    var notebookEl = document.querySelector('.jp-Notebook') || 
                                   document.querySelector('.notebook_app') ||
                                   document.body;
                    if (notebookEl) {
                        var bgColor = window.getComputedStyle(notebookEl).backgroundColor;
                        var rgb = bgColor.match(/\\d+/g);
                        if (rgb && rgb.length >= 3) {
                            var brightness = (parseInt(rgb[0]) + parseInt(rgb[1]) + parseInt(rgb[2])) / 3;
                            if (brightness < 128) {
                                isDark = true;
                            }
                        }
                    }

                    // Store result
                    if (typeof IPython !== 'undefined' && IPython.notebook && IPython.notebook.kernel) {
                        IPython.notebook.kernel.execute('_jupyter_dark_detect_result = ' + isDark);
                    }
                })();
            """)
            )

            # Give JavaScript time to execute
            time.sleep(0.2)

            # Check for result
            if hasattr(sys.modules['__main__'], '_jupyter_dark_detect_result'):
                result = bool(sys.modules['__main__']._jupyter_dark_detect_result)
                delattr(sys.modules['__main__'], '_jupyter_dark_detect_result')
                return result

        except Exception:
            pass

        # Fallback to simpler detection
        result = ipython.run_cell_magic(
            'javascript',
            '',
            """
            if (typeof IPython !== 'undefined' && IPython.notebook) {
                IPython.notebook.kernel.execute("_jupyter_dark_detect_result = " + 
                    (document.body.classList.contains('theme-dark') || 
                     document.body.classList.contains('jp-mod-dark') ||
                     (document.body.getAttribute('data-jp-theme-name') && 
                      document.body.getAttribute('data-jp-theme-name').includes('dark'))));
            }
        """,
        )

        # Check for result
        if hasattr(sys.modules['__main__'], '_jupyter_dark_detect_result'):
            result = bool(sys.modules['__main__']._jupyter_dark_detect_result)
            delattr(sys.modules['__main__'], '_jupyter_dark_detect_result')
            return result

    except Exception:
        pass

    return None


def _check_system_preferences() -> Optional[bool]:
    """Check system dark mode preferences."""
    try:
        system = platform.system()

        if system == 'Darwin':  # macOS
            result = subprocess.run(
                ['defaults', 'read', '-g', 'AppleInterfaceStyle'], capture_output=True, text=True
            )
            return result.returncode == 0 and 'dark' in result.stdout.lower()

        elif system == 'Windows':
            try:
                import winreg

                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize',
                )
                value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
                winreg.CloseKey(key)
                return value == 0  # 0 means dark mode
            except Exception:
                pass

    except Exception:
        pass

    return None

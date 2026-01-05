"""jupyter-dark-detect: Detect dark mode in Jupyter environments.

This package provides a simple API to detect whether Jupyter Notebook/Lab
is running in dark mode across different environments.
"""

from .detector import is_dark

__version__ = '0.1.0'
__all__ = ['is_dark']

# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors
# SPDX-License-Identifier: BSD-3-Clause
"""Vendored third-party modules.

This package contains third-party code that has been vendored into the
project to avoid external dependencies not available on conda-forge.

Packages:
    jupyter_dark_detect/
        Vendored copy of jupyter_dark_detect (MIT License).
        Check jupyter_dark_detect.__version__ for vendored version.

        To update, replace these files from upstream:
        - https://github.com/OpenMined/jupyter-dark-detect/blob/main/jupyter_dark_detect/__init__.py
        - https://github.com/OpenMined/jupyter-dark-detect/blob/main/jupyter_dark_detect/detector.py

        Then run 'pixi run fix' to format and check for issues.

Modules:
    theme_detect:
        Custom wrapper around jupyter_dark_detect with optimized
        detection order for EasyDiffraction's use case.
"""

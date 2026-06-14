# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Test configuration for the tutorial-output checks.

Pytest runs with ``--import-mode=importlib``, which does not add the
test directory to ``sys.path``. Insert it here so the test module can
import the sibling ``analysis_edifa_reader`` helper.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

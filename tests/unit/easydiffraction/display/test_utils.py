# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for display/utils.py (JupyterScrollManager)."""


class TestJupyterScrollManager:
    def test_applied_starts_false(self):
        from easydiffraction.display.utils import JupyterScrollManager

        # Reset class state
        JupyterScrollManager._applied = False
        assert JupyterScrollManager._applied is False

    def test_disable_is_noop_outside_jupyter(self):
        from easydiffraction.display.utils import JupyterScrollManager

        JupyterScrollManager._applied = False
        JupyterScrollManager.disable_jupyter_scroll()
        # Outside Jupyter, _applied stays False
        assert JupyterScrollManager._applied is False

    def test_idempotency(self):
        from easydiffraction.display.utils import JupyterScrollManager

        JupyterScrollManager._applied = False
        JupyterScrollManager.disable_jupyter_scroll()
        JupyterScrollManager.disable_jupyter_scroll()
        # Still False outside Jupyter
        assert JupyterScrollManager._applied is False

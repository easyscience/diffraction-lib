# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.singleton import ConstraintsHandler


def test_constraints_handler_is_singleton():
    h1 = ConstraintsHandler.get()
    h2 = ConstraintsHandler.get()
    assert h1 is h2

# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_uid_map_handler_rejects_non_descriptor():
    from easydiffraction.core.singleton import UidMapHandler

    h = UidMapHandler.get()
    with pytest.raises(TypeError):
        h.add_to_uid_map(object())

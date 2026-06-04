# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations


def test_writer_error_is_easy_diffraction_error():
    from easydiffraction.core.errors import EasyDiffractionError
    from easydiffraction.core.errors import EasyDiffractionWriterError

    error = EasyDiffractionWriterError('failed')

    assert isinstance(error, EasyDiffractionError)
    assert str(error) == 'failed'

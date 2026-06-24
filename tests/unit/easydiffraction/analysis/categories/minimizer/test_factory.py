# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the minimizer category factory."""

from __future__ import annotations

import pytest


def test_factory_default_creates_lmfit_leastsq_minimizer():
    import easydiffraction.analysis.categories.minimizer  # noqa: F401
    from easydiffraction.analysis.categories.minimizer.factory import MinimizerCategoryFactory
    from easydiffraction.analysis.categories.minimizer.lmfit_leastsq import LmfitLeastsqMinimizer

    minimizer = MinimizerCategoryFactory.create_default_for()

    assert MinimizerCategoryFactory.default_tag() == 'lmfit (leastsq)'
    assert isinstance(minimizer, LmfitLeastsqMinimizer)


def test_factory_rejects_unsupported_minimizer_type():
    import easydiffraction.analysis.categories.minimizer  # noqa: F401
    from easydiffraction.analysis.categories.minimizer.factory import MinimizerCategoryFactory

    with pytest.raises(ValueError, match='Unsupported type'):
        MinimizerCategoryFactory.create('missing')

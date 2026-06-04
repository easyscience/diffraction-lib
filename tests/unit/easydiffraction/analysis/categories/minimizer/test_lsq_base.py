# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for least-squares minimizer category behavior."""

from __future__ import annotations

import gemmi


def test_lsq_minimizer_defaults_to_settings_only():
    from easydiffraction.analysis.categories.minimizer.lmfit_leastsq import (
        LmfitLeastsqMinimizer,
    )

    minimizer = LmfitLeastsqMinimizer()

    assert minimizer.max_iterations.value == 1000
    assert minimizer._setting_descriptor_names == ('max_iterations',)
    assert minimizer._result_descriptor_names == ()


def test_lsq_minimizer_reads_cif_settings():
    from easydiffraction.analysis.categories.minimizer.lmfit_leastsq import (
        LmfitLeastsqMinimizer,
    )

    document = gemmi.cif.read_string(
        """data_minimizer
_minimizer.max_iterations 42
"""
    )
    minimizer = LmfitLeastsqMinimizer()
    minimizer.from_cif(document.sole_block())

    assert minimizer.max_iterations.value == 42

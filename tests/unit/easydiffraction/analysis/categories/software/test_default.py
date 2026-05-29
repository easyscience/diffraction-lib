# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations


def test_software_category_exposes_roles_and_timestamp():
    from easydiffraction.analysis.categories.software.base import SoftwareRole
    from easydiffraction.analysis.categories.software.default import Software

    software = Software()
    software.framework.name = 'EasyDiffraction'
    software.calculator.name = 'cryspy'
    software.minimizer.name = 'lmfit'
    software.timestamp = '2026-05-29T12:00:00+00:00'

    assert isinstance(software.framework, SoftwareRole)
    assert isinstance(software.calculator, SoftwareRole)
    assert isinstance(software.minimizer, SoftwareRole)
    assert len(software.parameters) == 10
    assert '_software.framework_name EasyDiffraction' in software.as_cif
    assert '_software.calculator_name cryspy' in software.as_cif
    assert '_software.minimizer_name lmfit' in software.as_cif
    assert '_software.timestamp 2026-05-29T12:00:00+00:00' in software.as_cif

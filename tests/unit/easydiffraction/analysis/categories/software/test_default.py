# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations


def test_software_category_exposes_roles_and_timestamp():
    from easydiffraction.analysis.categories.software.base import SoftwareRole
    from easydiffraction.analysis.categories.software.default import Software
    from easydiffraction.analysis.enums import SoftwareRoleEnum

    software = Software()
    software[SoftwareRoleEnum.FRAMEWORK.value].name = 'EasyDiffraction'
    software[SoftwareRoleEnum.CALCULATOR.value].name = 'cryspy'
    software[SoftwareRoleEnum.MINIMIZER.value].name = 'lmfit'

    assert isinstance(software[SoftwareRoleEnum.FRAMEWORK.value], SoftwareRole)
    assert isinstance(software[SoftwareRoleEnum.CALCULATOR.value], SoftwareRole)
    assert isinstance(software[SoftwareRoleEnum.MINIMIZER.value], SoftwareRole)
    assert software.names == ['framework', 'calculator', 'minimizer']
    assert len(software.parameters) == 12
    assert software.has_provenance()
    cif_text = software.as_cif
    assert '_software.id' in cif_text
    assert 'framework EasyDiffraction' in cif_text
    assert 'calculator cryspy' in cif_text
    assert 'minimizer lmfit' in cif_text

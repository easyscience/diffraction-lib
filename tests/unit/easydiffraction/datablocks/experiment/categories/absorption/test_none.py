# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.datablocks.experiment.categories.absorption.none as MUT

    assert MUT.__name__.endswith('absorption.none')


def test_none_type_info():
    from easydiffraction.datablocks.experiment.categories.absorption.none import NoAbsorption

    assert NoAbsorption.type_info.tag == 'none'
    assert NoAbsorption.type_info.description != ''


def test_none_has_no_mu_r_parameter():
    from easydiffraction.datablocks.experiment.categories.absorption.none import NoAbsorption

    absorption = NoAbsorption()
    assert not hasattr(absorption, 'mu_r')


def test_none_identity_and_default_type():
    from easydiffraction.datablocks.experiment.categories.absorption.none import NoAbsorption

    absorption = NoAbsorption()
    assert absorption._identity.category_code == 'absorption'
    assert absorption.type == 'none'


def test_none_compatibility_and_calculator_support():
    from easydiffraction.datablocks.experiment.categories.absorption.none import NoAbsorption
    from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

    assert SampleFormEnum.POWDER in NoAbsorption.compatibility.sample_form
    assert ScatteringTypeEnum.BRAGG in NoAbsorption.compatibility.scattering_type
    assert NoAbsorption.calculator_support.supports(CalculatorEnum.CRYSPY)
    assert NoAbsorption.calculator_support.supports(CalculatorEnum.CRYSFML)
    assert not NoAbsorption.calculator_support.supports(CalculatorEnum.PDFFIT)

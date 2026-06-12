# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.datablocks.experiment.categories.absorption.cylinder_hewat as MUT

    assert MUT.__name__.endswith('absorption.cylinder_hewat')


def test_cylinder_hewat_type_info():
    from easydiffraction.datablocks.experiment.categories.absorption.cylinder_hewat import (
        CylinderHewatAbsorption,
    )

    assert CylinderHewatAbsorption.type_info.tag == 'cylinder-hewat'
    assert CylinderHewatAbsorption.type_info.description != ''


def test_cylinder_hewat_mu_r_default_and_setter():
    from easydiffraction.datablocks.experiment.categories.absorption.cylinder_hewat import (
        CylinderHewatAbsorption,
    )

    absorption = CylinderHewatAbsorption()
    assert absorption.mu_r.value == 0.0

    absorption.mu_r = 0.7
    assert absorption.mu_r.value == 0.7


def test_cylinder_hewat_mu_r_must_be_non_negative(monkeypatch):
    from easydiffraction.datablocks.experiment.categories.absorption.cylinder_hewat import (
        CylinderHewatAbsorption,
    )
    from easydiffraction.utils.logging import Logger

    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

    absorption = CylinderHewatAbsorption()
    absorption.mu_r = 0.7
    absorption.mu_r = -0.1  # ge=0 -> rejected, keeps previous value
    assert absorption.mu_r.value == 0.7


def test_cylinder_hewat_mu_r_cif_handler_names():
    from easydiffraction.datablocks.experiment.categories.absorption.cylinder_hewat import (
        CylinderHewatAbsorption,
    )

    absorption = CylinderHewatAbsorption()
    assert '_absorption.mu_r' in absorption._mu_r._cif_handler.names
    assert absorption._mu_r._cif_handler.iucr_name == '_easydiffraction_absorption.mu_r'


def test_cylinder_hewat_is_constant_wavelength_only():
    from easydiffraction.datablocks.experiment.categories.absorption.cylinder_hewat import (
        CylinderHewatAbsorption,
    )
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

    compatibility = CylinderHewatAbsorption.compatibility
    assert SampleFormEnum.POWDER in compatibility.sample_form
    assert ScatteringTypeEnum.BRAGG in compatibility.scattering_type
    assert BeamModeEnum.CONSTANT_WAVELENGTH in compatibility.beam_mode
    assert BeamModeEnum.TIME_OF_FLIGHT not in compatibility.beam_mode

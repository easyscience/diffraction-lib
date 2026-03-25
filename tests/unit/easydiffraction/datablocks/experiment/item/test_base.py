# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.datablocks.experiment.item.base as MUT

    expected_module_name = 'easydiffraction.datablocks.experiment.item.base'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_pd_experiment_peak_profile_type_switch(capsys):
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
    from easydiffraction.datablocks.experiment.item.base import PdExperimentBase
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

    class ConcretePd(PdExperimentBase):
        def _load_ascii_data_to_experiment(self, data_path: str) -> None:
            pass

    et = ExperimentType()
    et._set_sample_form(SampleFormEnum.POWDER.value)
    et._set_beam_mode(BeamModeEnum.CONSTANT_WAVELENGTH.value)
    et._set_radiation_probe(RadiationProbeEnum.NEUTRON.value)
    et._set_scattering_type(ScatteringTypeEnum.BRAGG.value)

    ex = ConcretePd(name='ex1', type=et)
    # valid switch using tag string
    ex.peak_profile_type = 'pseudo-voigt'
    assert ex.peak_profile_type == 'pseudo-voigt'
    # invalid string should warn and keep previous
    ex.peak_profile_type = 'non-existent'
    captured = capsys.readouterr().out
    assert 'Unsupported' in captured or 'Unknown' in captured

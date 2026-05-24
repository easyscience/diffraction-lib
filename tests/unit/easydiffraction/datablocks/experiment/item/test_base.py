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
        def _load_ascii_data_to_experiment(self, data_path: str) -> int:
            return 0

    et = ExperimentType()
    et._set_sample_form(SampleFormEnum.POWDER.value)
    et._set_beam_mode(BeamModeEnum.CONSTANT_WAVELENGTH.value)
    et._set_radiation_probe(RadiationProbeEnum.NEUTRON.value)
    et._set_scattering_type(ScatteringTypeEnum.BRAGG.value)

    ex = ConcretePd(name='ex1', type=et)
    # valid switch using tag string
    ex.peak.type = 'pseudo-voigt'
    assert ex.peak.type == 'pseudo-voigt'
    # invalid string should warn and keep previous
    ex.peak.type = 'non-existent'
    captured = capsys.readouterr().out
    assert 'Unsupported' in captured or 'Unknown' in captured


def test_pd_experiment_set_peak_profile_type_silent(capsys):
    """_set_peak_profile_type switches the peak type without console output."""
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
    from easydiffraction.datablocks.experiment.item.base import PdExperimentBase
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

    class ConcretePd(PdExperimentBase):
        def _load_ascii_data_to_experiment(self, data_path: str) -> int:
            return 0

    et = ExperimentType()
    et._set_sample_form(SampleFormEnum.POWDER.value)
    et._set_beam_mode(BeamModeEnum.CONSTANT_WAVELENGTH.value)
    et._set_radiation_probe(RadiationProbeEnum.NEUTRON.value)
    et._set_scattering_type(ScatteringTypeEnum.BRAGG.value)

    ex = ConcretePd(name='ex1', type=et)
    ex._set_peak_profile_type('pseudo-voigt + empirical asymmetry')

    # Profile type was switched
    assert ex.peak.type == 'pseudo-voigt + empirical asymmetry'
    assert ex.peak.__class__.__name__ == 'CwlPseudoVoigtEmpiricalAsymmetry'

    # No console output was emitted
    captured = capsys.readouterr().out
    assert captured == ''


def test_pd_experiment_set_peak_profile_type_invalid_keeps_default(capsys):
    """_set_peak_profile_type logs a warning for unsupported tags."""
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
    from easydiffraction.datablocks.experiment.item.base import PdExperimentBase
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

    class ConcretePd(PdExperimentBase):
        def _load_ascii_data_to_experiment(self, data_path: str) -> int:
            return 0

    et = ExperimentType()
    et._set_sample_form(SampleFormEnum.POWDER.value)
    et._set_beam_mode(BeamModeEnum.CONSTANT_WAVELENGTH.value)
    et._set_radiation_probe(RadiationProbeEnum.NEUTRON.value)
    et._set_scattering_type(ScatteringTypeEnum.BRAGG.value)

    ex = ConcretePd(name='ex1', type=et)
    original_type = ex.peak.type
    ex._set_peak_profile_type('nonexistent-profile')

    # Profile type unchanged
    assert ex.peak.type == original_type


def test_pd_experiment_restore_switchable_types_switches_peak():
    """_restore_switchable_types reads _peak.type from a CIF block."""
    import gemmi

    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
    from easydiffraction.datablocks.experiment.item.base import PdExperimentBase
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

    class ConcretePd(PdExperimentBase):
        def _load_ascii_data_to_experiment(self, data_path: str) -> int:
            return 0

    et = ExperimentType()
    et._set_sample_form(SampleFormEnum.POWDER.value)
    et._set_beam_mode(BeamModeEnum.CONSTANT_WAVELENGTH.value)
    et._set_radiation_probe(RadiationProbeEnum.NEUTRON.value)
    et._set_scattering_type(ScatteringTypeEnum.BRAGG.value)

    ex = ConcretePd(name='ex1', type=et)

    cif = 'data_ex1\n_peak.type "pseudo-voigt + empirical asymmetry"\n'
    doc = gemmi.cif.read_string(cif)
    block = doc.sole_block()

    ex._restore_switchable_types(block)

    assert ex.peak.type == 'pseudo-voigt + empirical asymmetry'
    assert ex.peak.__class__.__name__ == 'CwlPseudoVoigtEmpiricalAsymmetry'


def test_base_experiment_restore_switchable_types_is_noop():
    """ExperimentBase._restore_switchable_types is a safe no-op."""
    import gemmi

    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
    from easydiffraction.datablocks.experiment.item.base import ExperimentBase
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

    class ConcreteBase(ExperimentBase):
        def _load_ascii_data_to_experiment(self, data_path: str) -> None:
            pass

    et = ExperimentType()
    et._set_sample_form(SampleFormEnum.POWDER.value)
    et._set_beam_mode(BeamModeEnum.CONSTANT_WAVELENGTH.value)
    et._set_radiation_probe(RadiationProbeEnum.NEUTRON.value)
    et._set_scattering_type(ScatteringTypeEnum.BRAGG.value)

    ex = ConcreteBase(name='ex1', type=et)

    cif = 'data_ex1\n_peak.type "pseudo-voigt + empirical asymmetry"\n'
    doc = gemmi.cif.read_string(cif)
    block = doc.sole_block()

    # Must not raise
    ex._restore_switchable_types(block)

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

    ex = ConcretePd(name='ex1', experiment_type=et)
    # valid switch using tag string
    import pytest

    ex.peak.type = 'pseudo-voigt'
    assert ex.peak.type == 'cwl-pseudo-voigt'
    # invalid string should raise and keep previous
    with pytest.raises(ValueError, match='Unsupported peak profile'):
        ex.peak.type = 'non-existent'
    assert ex.peak.type == 'cwl-pseudo-voigt'


def test_pd_experiment_peak_profile_switch_warning_lists_added_settings(monkeypatch):
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
    from easydiffraction.datablocks.experiment.item import base as item_base
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

    warnings: list[str] = []
    monkeypatch.setattr(item_base.log, 'warning', warnings.append)
    ex = ConcretePd(name='ex1', experiment_type=et)

    ex.peak.type = 'pseudo-voigt + empirical asymmetry'

    assert warnings == [
        (
            'Switching peak profile type adds these settings with defaults:\n'
            '• asym_empir_1=0.0\n'
            '• asym_empir_2=0.0\n'
            '• asym_empir_3=0.0\n'
            '• asym_empir_4=0.0'
        )
    ]


def test_pd_experiment_peak_profile_switch_warning_lists_reset_settings(monkeypatch):
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
    from easydiffraction.datablocks.experiment.item import base as item_base
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

    warnings: list[str] = []
    monkeypatch.setattr(item_base.log, 'warning', warnings.append)
    ex = ConcretePd(name='ex1', experiment_type=et)
    ex.peak.broad_gauss_u = 0.05

    ex.peak.type = 'pseudo-voigt + empirical asymmetry'

    assert warnings[1] == (
        'Switching peak profile type resets these settings to defaults:\n'
        '• broad_gauss_u: 0.05 -> 0.01'
    )


def test_pd_experiment_peak_profile_switch_warning_lists_removed_settings(monkeypatch):
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
    from easydiffraction.datablocks.experiment.item import base as item_base
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

    warnings: list[str] = []
    monkeypatch.setattr(item_base.log, 'warning', warnings.append)
    ex = ConcretePd(name='ex1', experiment_type=et)
    ex.peak.type = 'pseudo-voigt + empirical asymmetry'
    warnings.clear()

    ex.peak.type = 'pseudo-voigt'

    assert warnings == [
        (
            'Switching peak profile type removes these settings:\n'
            '• asym_empir_1\n'
            '• asym_empir_2\n'
            '• asym_empir_3\n'
            '• asym_empir_4'
        )
    ]


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

    ex = ConcretePd(name='ex1', experiment_type=et)
    ex._set_peak_profile_type('pseudo-voigt + empirical asymmetry')

    # Profile type was switched
    assert ex.peak.type == 'cwl-pseudo-voigt-empirical-asymmetry'
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

    ex = ConcretePd(name='ex1', experiment_type=et)
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

    ex = ConcretePd(name='ex1', experiment_type=et)

    cif = 'data_ex1\n_peak.type "pseudo-voigt + empirical asymmetry"\n'
    doc = gemmi.cif.read_string(cif)
    block = doc.sole_block()

    ex._restore_switchable_types(block)

    assert ex.peak.type == 'cwl-pseudo-voigt-empirical-asymmetry'
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

    ex = ConcreteBase(name='ex1', experiment_type=et)

    cif = 'data_ex1\n_peak.type "pseudo-voigt + empirical asymmetry"\n'
    doc = gemmi.cif.read_string(cif)
    block = doc.sole_block()

    # Must not raise
    ex._restore_switchable_types(block)

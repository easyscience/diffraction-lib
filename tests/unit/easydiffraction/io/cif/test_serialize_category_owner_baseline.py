# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from easydiffraction.datablocks.experiment.item.factory import ExperimentFactory
from easydiffraction.datablocks.structure.item.base import Structure
from easydiffraction.project.project import Project


def test_real_structure_as_cif_starts_with_data_header() -> None:
    structure = Structure(name='nickelate')

    assert structure.as_cif.startswith('data_nickelate')


def test_real_experiment_as_cif_starts_with_data_header() -> None:
    experiment = ExperimentFactory.from_scratch(
        name='powder_scan',
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='bragg',
    )

    assert experiment.as_cif.startswith('data_powder_scan')


def test_real_analysis_as_cif_is_singleton_section_without_data_header() -> None:
    project = Project(name='proj')

    analysis_cif = project.analysis.as_cif

    assert analysis_cif.startswith('_fitting.mode_type single')
    assert not analysis_cif.startswith('data_')
    assert '_fitting.minimizer_type' in analysis_cif
    assert '_joint_fit.experiment_id' not in analysis_cif
    assert '_sequential_fit.data_dir' not in analysis_cif
    assert '_sequential_fit_extract.id' not in analysis_cif


def test_real_analysis_as_cif_includes_aliases_and_constraints_when_present() -> None:
    project = Project(name='proj')
    project.structures.create(name='phase_1')
    parameter = project.structures['phase_1'].cell.length_a

    analysis = project.analysis
    analysis.aliases.create(label='a_param', param=parameter)
    analysis.constraints.create(expression='a_param = a_param')

    analysis_cif = analysis.as_cif

    assert '_alias.label' in analysis_cif
    assert '_alias.param_unique_name' in analysis_cif
    assert '_constraint.expression' in analysis_cif
    assert 'a_param = a_param' in analysis_cif


def test_real_analysis_as_cif_includes_joint_fit_only_in_joint_mode() -> None:
    project = Project(name='proj')
    analysis = project.analysis
    analysis._set_fitting_mode_type('joint')
    analysis.joint_fit.create(experiment_id='ex1', weight=0.5)

    analysis_cif = analysis.as_cif

    assert not analysis_cif.startswith('data_')
    assert '_fitting.mode_type joint' in analysis_cif
    assert '_joint_fit.experiment_id' in analysis_cif
    assert '_joint_fit.weight' in analysis_cif
    assert '_sequential_fit.data_dir' not in analysis_cif
    assert '_sequential_fit_extract.id' not in analysis_cif


def test_real_analysis_as_cif_includes_sequential_sections_only_in_sequential_mode() -> None:
    project = Project(name='proj')
    analysis = project.analysis
    analysis._set_fitting_mode_type('sequential')
    analysis.sequential_fit.data_dir.value = 'scans'
    analysis.sequential_fit.file_pattern.value = '*.xye'
    analysis.sequential_fit_extract.create(
        id='temperature',
        target='diffrn.ambient_temperature',
        pattern=r'temp_(\d+)',
        required=True,
    )

    analysis_cif = analysis.as_cif

    assert not analysis_cif.startswith('data_')
    assert '_fitting.mode_type sequential' in analysis_cif
    assert '_sequential_fit.data_dir scans' in analysis_cif
    assert '_sequential_fit.file_pattern *.xye' in analysis_cif
    assert '_sequential_fit_extract.id' in analysis_cif
    assert '_sequential_fit_extract.target' in analysis_cif
    assert 'diffrn.ambient_temperature' in analysis_cif
    assert '_joint_fit.experiment_id' not in analysis_cif

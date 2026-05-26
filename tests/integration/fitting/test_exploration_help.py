# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""Integration tests for help(), show_as_cif(), and switchable-category show methods."""


def test_project_str(lbco_fitted_project):
    project = lbco_fitted_project
    text = str(project)
    assert 'Project' in text
    assert '1 structures' in text
    assert '1 experiments' in text


def test_project_help(lbco_fitted_project):
    project = lbco_fitted_project
    project.help()


def test_project_full_name(lbco_fitted_project):
    project = lbco_fitted_project
    assert project.full_name == project.name


def test_structure_help(lbco_fitted_project):
    project = lbco_fitted_project
    model = project.structures['lbco']
    model.help()


def test_structure_show_as_cif(lbco_fitted_project):
    project = lbco_fitted_project
    model = project.structures['lbco']
    model.show_as_cif()


def test_structure_as_cif(lbco_fitted_project):
    project = lbco_fitted_project
    model = project.structures['lbco']
    cif_text = model.as_cif
    assert isinstance(cif_text, str)
    assert '_space_group' in cif_text


def test_structure_switchable_category_types(lbco_fitted_project):
    project = lbco_fitted_project
    model = project.structures['lbco']
    # Cell
    assert model.cell is not None
    # Space group
    assert model.space_group is not None
    # Atom sites
    assert model.atom_sites is not None


def test_experiment_help(lbco_fitted_project):
    project = lbco_fitted_project
    expt = project.experiments['hrpt']
    expt.help()


def test_experiment_show_as_cif(lbco_fitted_project):
    project = lbco_fitted_project
    expt = project.experiments['hrpt']
    expt.show_as_cif()


def test_experiment_show_as_cif_omits_empty_category_gaps(lbco_fitted_project, monkeypatch):
    import re

    import easydiffraction.datablocks.experiment.item.base as experiment_base

    captured = {}

    def fake_render_cif(cif_text):
        captured['cif_text'] = cif_text

    monkeypatch.setattr(experiment_base, 'render_cif', fake_render_cif)

    project = lbco_fitted_project
    expt = project.experiments['hrpt']
    expt.show_as_cif()

    cif_text = captured['cif_text']
    assert re.search(r'_pd_phase_block\.scale\n[^\n]+\n\n_background\.type', cif_text) is not None
    assert re.search(r'_background\.type [^\n]+\n\nloop_', cif_text) is not None
    assert '\n\n\n' not in cif_text


def test_experiment_as_cif(lbco_fitted_project):
    project = lbco_fitted_project
    expt = project.experiments['hrpt']
    cif_text = expt.as_cif
    assert isinstance(cif_text, str)
    assert len(cif_text) > 0


def test_experiment_switchable_category_types(lbco_fitted_project):
    project = lbco_fitted_project
    expt = project.experiments['hrpt']
    # Instrument
    assert expt.instrument is not None
    # Background
    expt.background.show_supported()
    assert isinstance(expt.background.type, str)
    # Peak profile
    expt.peak.show_supported()
    assert isinstance(expt.peak.type, str)
    # Linked phases
    assert expt.linked_phases is not None
    # Calculator
    expt.calculator.show_supported()
    assert isinstance(expt.calculator.type, str)
    # Diffrn
    assert expt.diffrn is not None


def test_experiment_data_info(lbco_fitted_project):
    project = lbco_fitted_project
    expt = project.experiments['hrpt']
    # Data access
    assert expt.data is not None
    assert expt.data.x is not None
    assert len(expt.data.x) > 0
    assert expt.data.intensity_meas is not None


def test_structure_cell_properties(lbco_fitted_project):
    project = lbco_fitted_project
    model = project.structures['lbco']
    # Access cell parameters
    assert model.cell.length_a.value > 0
    params = model.cell.parameters
    assert len(params) > 0


def test_structure_atom_sites_iteration(lbco_fitted_project):
    project = lbco_fitted_project
    model = project.structures['lbco']
    count = 0
    for site in model.atom_sites:
        assert site.label.value is not None
        assert site.type_symbol.value is not None
        count += 1
    assert count == 4


def test_structures_collection_names(lbco_fitted_project):
    project = lbco_fitted_project
    names = project.structures.names
    assert 'lbco' in names
    # Parameters
    params = project.structures.parameters
    assert len(params) > 0
    fittable = project.structures.fittable_parameters
    assert len(fittable) > 0
    free = project.structures.free_parameters
    assert len(free) > 0


def test_experiments_collection_names(lbco_fitted_project):
    project = lbco_fitted_project
    names = project.experiments.names
    assert 'hrpt' in names
    params = project.experiments.parameters
    assert len(params) > 0
    fittable = project.experiments.fittable_parameters
    assert len(fittable) > 0
    free = project.experiments.free_parameters
    assert len(free) > 0

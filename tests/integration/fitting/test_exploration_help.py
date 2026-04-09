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
    model.show_supported_cell_types()
    model.show_current_cell_type()
    assert isinstance(model.cell_type, str)
    # Space group
    model.show_supported_space_group_types()
    model.show_current_space_group_type()
    assert isinstance(model.space_group_type, str)
    # Atom sites
    model.show_supported_atom_sites_types()
    model.show_current_atom_sites_type()
    assert isinstance(model.atom_sites_type, str)


def test_experiment_help(lbco_fitted_project):
    project = lbco_fitted_project
    expt = project.experiments['hrpt']
    expt.help()


def test_experiment_show_as_cif(lbco_fitted_project):
    project = lbco_fitted_project
    expt = project.experiments['hrpt']
    expt.show_as_cif()


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
    expt.show_supported_instrument_types()
    expt.show_current_instrument_type()
    assert isinstance(expt.instrument_type, str)
    # Background
    expt.show_supported_background_types()
    expt.show_current_background_type()
    assert isinstance(expt.background_type, str)
    # Peak profile
    expt.show_supported_peak_profile_types()
    expt.show_current_peak_profile_type()
    assert isinstance(expt.peak_profile_type, str)
    # Linked phases
    expt.show_supported_linked_phases_types()
    expt.show_current_linked_phases_type()
    assert isinstance(expt.linked_phases_type, str)
    # Calculator
    expt.show_supported_calculator_types()
    expt.show_current_calculator_type()
    assert isinstance(expt.calculator_type, str)
    # Diffrn
    expt.show_supported_diffrn_types()
    expt.show_current_diffrn_type()
    assert isinstance(expt.diffrn_type, str)


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

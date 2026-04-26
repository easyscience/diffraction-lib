# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""Integration tests for Analysis display methods and CIF serialization."""


def test_display_all_params(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.display.all_params()


def test_display_fittable_params(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.display.fittable_params()


def test_display_free_params(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.display.free_params()


def test_display_how_to_access_parameters(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.display.how_to_access_parameters()


def test_display_parameter_cif_uids(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.display.parameter_cif_uids()


def test_display_constraints_empty(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.display.constraints()


def test_display_fit_results(lbco_fitted_project):
    project = lbco_fitted_project
    assert project.analysis.fit_results is not None
    project.analysis.display.fit_results()


def test_display_as_cif(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.display.as_cif()


def test_analysis_as_cif(lbco_fitted_project):
    project = lbco_fitted_project
    cif_text = project.analysis.as_cif()
    assert isinstance(cif_text, str)
    assert len(cif_text) > 0


def test_analysis_help(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.help()


def test_show_minimizer_types_again(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.fit.show_minimizer_types()


def test_show_minimizer_types(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.fit.show_minimizer_types()


def test_fit_results_attributes(lbco_fitted_project):
    project = lbco_fitted_project
    results = project.analysis.fit_results
    assert results is not None
    assert results.reduced_chi_square is not None
    assert results.reduced_chi_square > 0
    assert isinstance(results.success, bool)

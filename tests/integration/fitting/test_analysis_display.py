# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""Integration tests for project display reports and analysis CIF helpers."""


def test_display_all_params(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.parameters.all()


def test_display_fittable_params(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.parameters.fittable()


def test_display_free_params(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.parameters.free()


def test_display_how_to_access_parameters(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.parameters.access()


def test_display_parameter_uids(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.parameters.uid()


def test_display_parameter_edi_tags(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.parameters.edi()


def test_display_parameter_cif_tags(lbco_fitted_project):
    project = lbco_fitted_project
    project.display.parameters.cif()


def test_display_constraints_empty(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.constraints.show()


def test_display_fit_results(lbco_fitted_project):
    project = lbco_fitted_project
    assert project.analysis.fit_results is not None
    project.display.fit.results()


def test_display_as_text(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.show_as_text()


def test_analysis_as_cif(lbco_fitted_project):
    project = lbco_fitted_project
    cif_text = project.analysis.as_cif
    assert isinstance(cif_text, str)
    assert len(cif_text) > 0


def test_analysis_help(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.help()


def test_minimizer_show_supported_again(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.minimizer.show_supported()


def test_minimizer_show_supported(lbco_fitted_project):
    project = lbco_fitted_project
    project.analysis.minimizer.show_supported()


def test_fit_results_attributes(lbco_fitted_project):
    project = lbco_fitted_project
    results = project.analysis.fit_results
    assert results is not None
    assert results.reduced_chi_square is not None
    assert results.reduced_chi_square > 0
    assert isinstance(results.success, bool)

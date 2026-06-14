# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for Project.load()."""

from __future__ import annotations

import pytest

from easydiffraction.project.project import Project


class TestLoadMinimal:
    """Load a project that has no structures or experiments."""

    def test_raises_on_missing_directory(self, tmp_path):
        missing = tmp_path / 'nonexistent'
        with pytest.raises(FileNotFoundError, match='not found'):
            Project.load(str(missing))

    def test_round_trips_empty_project(self, tmp_path):
        original = Project(name='empty', title='Empty', description='nothing')
        original.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))

        assert loaded.name == 'empty'
        assert loaded.metadata.title == 'Empty'
        assert loaded.metadata.description == 'nothing'
        assert loaded.metadata.path is not None
        assert len(loaded.structures) == 0
        assert len(loaded.experiments) == 0


class TestLoadStructures:
    """Load structures from a saved project."""

    def test_round_trips_structure(self, tmp_path):
        original = Project(name='s1')
        original.structures.create(name='cosio')
        s = original.structures['cosio']
        s.space_group.name_h_m = 'P m -3 m'
        s.cell.length_a = 3.88
        s.atom_sites.create(
            id='Co',
            type_symbol='Co',
            fract_x=0.0,
            fract_y=0.0,
            fract_z=0.0,
            adp_iso=0.5,
        )
        original.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))

        assert len(loaded.structures) == 1
        ls = loaded.structures['cosio']
        assert ls.space_group.name_h_m.value == 'P m -3 m'
        assert abs(ls.cell.length_a.value - 3.88) < 1e-6
        assert len(ls.atom_sites) == 1
        assert ls.atom_sites['Co'].type_symbol.value == 'Co'
        assert abs(ls.atom_sites['Co'].adp_iso.value - 0.5) < 1e-6


class TestLoadAnalysis:
    """Load analysis settings from a saved project."""

    def test_round_trips_minimizer(self, tmp_path):
        original = Project(name='a1')
        original.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))

        assert loaded.analysis.minimizer.type == 'lmfit (leastsq)'

    def test_round_trips_fit_mode(self, tmp_path):
        original = Project(name='a2')
        original.analysis.fitting_mode.type = 'joint'
        original.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))

        assert loaded.analysis.fitting_mode.type == 'joint'

    def test_round_trips_display_engine_configuration(self, tmp_path):
        original = Project(name='d1')
        original.rendering_plot.type = 'asciichartpy'
        original.rendering_table.type = 'rich'
        original.rendering_structure.type = 'ascii'
        original.structure_style.atom_view = 'vdw'
        original.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))

        assert loaded.rendering_plot.type == 'asciichartpy'
        assert loaded.rendering_table.type == 'rich'
        assert loaded.rendering_structure.type == 'ascii'
        assert loaded.structure_style.atom_view.value == 'vdw'

    def test_round_trips_constraints(self, tmp_path):
        original = Project(name='c1')
        original.structures.create(name='s')
        s = original.structures['s']
        s.cell.length_a = 5.0
        s.cell.length_b = 5.0

        original.analysis.aliases.create(
            id='a_param',
            param=s.cell.length_a,
        )
        original.analysis.aliases.create(
            id='b_param',
            param=s.cell.length_b,
        )
        original.analysis.constraints.create(expression='b_param = a_param')
        original.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))

        assert len(loaded.analysis.aliases) == 2
        assert loaded.analysis.aliases['a_param'].id.value == 'a_param'
        assert loaded.analysis.aliases['b_param'].id.value == 'b_param'
        # Verify alias param references are resolved
        assert loaded.analysis.aliases['a_param'].param is not None
        assert loaded.analysis.aliases['b_param'].param is not None

        assert len(loaded.analysis.constraints) == 1
        assert loaded.analysis.constraints['b_param'].id.value == 'b_param'
        assert loaded.analysis.constraints['b_param'].expression.value == 'b_param = a_param'
        assert loaded.analysis.constraints[0].expression.value == 'b_param = a_param'
        assert loaded.analysis.constraints.enabled is True

    def test_round_trips_deterministic_fit_state_and_keeps_live_parameter_values(self, tmp_path):
        original = Project(name='fit_state')
        original.structures.create(name='lbco')
        structure = original.structures['lbco']
        structure.space_group.name_h_m = 'P m -3 m'
        structure.cell.length_a = 3.88
        parameter = structure.cell.length_a
        parameter.free = True
        parameter.uncertainty = 0.07
        parameter.fit_min = 3.8
        parameter.fit_max = 3.9
        parameter._set_bounds_uncertainty_multiplier(4.0)
        parameter._fit_start_value = 3.87
        parameter._fit_start_uncertainty = 0.02

        original.analysis.fit_parameters.create(
            parameter_unique_name=parameter.unique_name,
            fit_min=parameter.fit_min,
            fit_max=parameter.fit_max,
            bounds_uncertainty_multiplier=4.0,
            start_value=3.87,
            start_uncertainty=0.02,
        )
        original.analysis.fit_result._set_result_kind('deterministic')
        original.analysis.fit_result._set_success(value=True)
        original.analysis.fit_result._set_message('Fit converged')
        original.analysis.fit_result._set_iterations(37)
        original.analysis.fit_result._set_fitting_time(1.82)
        original.analysis.fit_result._set_reduced_chi_square(1.031)
        original.analysis._set_has_persisted_fit_state(value=True)
        original.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))
        loaded_parameter = loaded.structures['lbco'].cell.length_a

        assert loaded.analysis.fit_result.result_kind.value == 'deterministic'
        assert loaded.analysis.fit_parameters[parameter.unique_name].fit_min.value == 3.8
        assert loaded_parameter.value == 3.88
        assert loaded_parameter.fit_min == 3.8
        assert loaded_parameter.fit_max == 3.9
        assert loaded_parameter.bounds_uncertainty_multiplier == 4.0
        assert loaded_parameter._fit_start_value == 3.87
        assert loaded_parameter._fit_start_uncertainty == 0.02
        assert loaded_parameter.uncertainty == 0.07

    def test_round_trips_persisted_deterministic_correlation_summary_for_reloaded_display(
        self,
        tmp_path,
    ):
        from easydiffraction.display.plotting import Plotter

        original = Project(name='fit_correlation_state')
        original.structures.create(name='lbco')
        structure = original.structures['lbco']
        structure.space_group.name_h_m = 'P m -3 m'
        structure.cell.length_a = 3.88
        structure.cell.length_b = 3.89

        parameter_a = structure.cell.length_a
        parameter_b = structure.cell.length_b
        for parameter, start_value in (
            (parameter_a, 3.87),
            (parameter_b, 3.88),
        ):
            parameter.free = True
            parameter.uncertainty = 0.05
            parameter.fit_min = 3.8
            parameter.fit_max = 3.9
            parameter._set_bounds_uncertainty_multiplier(4.0)
            parameter._fit_start_value = start_value
            parameter._fit_start_uncertainty = 0.02
            original.analysis.fit_parameters.create(
                parameter_unique_name=parameter.unique_name,
                fit_min=parameter.fit_min,
                fit_max=parameter.fit_max,
                bounds_uncertainty_multiplier=4.0,
                start_value=start_value,
                start_uncertainty=0.02,
            )

        original.analysis.fit_result._set_result_kind('deterministic')
        original.analysis.fit_result._set_success(value=True)
        original.analysis.fit_result._set_message('Fit converged')
        original.analysis.fit_result._set_iterations(21)
        original.analysis.fit_result._set_fitting_time(0.74)
        original.analysis.fit_result._set_reduced_chi_square(1.031)
        original.analysis.fit_result._set_objective_name('chi-square')
        original.analysis.fit_result._set_objective_value(1.031)
        original.analysis.fit_result._set_n_data_points(120)
        original.analysis.fit_result._set_n_parameters(2)
        original.analysis.fit_result._set_n_free_parameters(2)
        original.analysis.fit_result._set_degrees_of_freedom(118)
        original.analysis.fit_result._set_covariance_available(value=False)
        original.analysis.fit_result._set_correlation_available(value=True)
        original.analysis.fit_parameter_correlations.create(
            source_kind='deterministic',
            parameter_unique_name_i=parameter_b.unique_name,
            parameter_unique_name_j=parameter_a.unique_name,
            correlation=0.42,
        )
        original.analysis._set_has_persisted_fit_state(value=True)
        original.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))
        plotter = Plotter()
        plotter._set_project(loaded)

        corr_df = plotter._get_param_correlation_dataframe()

        assert corr_df is not None
        assert list(corr_df.index) == [parameter_a.unique_name, parameter_b.unique_name]
        assert list(corr_df.columns) == [parameter_a.unique_name, parameter_b.unique_name]
        assert corr_df.loc[parameter_a.unique_name, parameter_a.unique_name] == pytest.approx(1.0)
        assert corr_df.loc[parameter_b.unique_name, parameter_b.unique_name] == pytest.approx(1.0)
        assert corr_df.loc[parameter_a.unique_name, parameter_b.unique_name] == pytest.approx(0.42)
        assert corr_df.loc[parameter_b.unique_name, parameter_a.unique_name] == pytest.approx(0.42)

    def test_round_trips_dream_minimizer_settings(self, tmp_path):
        original = Project(name='bayes_state')
        original.analysis.minimizer.type = 'bumps (dream)'
        original.analysis.fit_result._set_result_kind('bayesian')
        minimizer = original.analysis.minimizer
        minimizer.sampling_steps = 300
        minimizer.burn_in_steps = 60
        minimizer.thinning_interval = 2
        minimizer.population_size = 8
        minimizer.parallel_workers = 0
        minimizer.initialization_method = 'latin_hypercube'
        original.analysis._set_has_persisted_fit_state(value=True)
        original.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))
        minimizer = loaded.analysis.minimizer

        assert minimizer is not None
        assert minimizer.sampling_steps.value == 300
        assert minimizer.burn_in_steps.value == 60
        assert minimizer.thinning_interval.value == 2
        assert minimizer.population_size.value == 8
        assert minimizer.parallel_workers.value == 0
        assert minimizer.initialization_method.value == 'latin_hypercube'
        assert minimizer._native_kwargs()['init'] == 'lhs'

    def test_round_trips_partial_dream_minimizer_settings(self, tmp_path):
        original = Project(name='partial_bayes_state')
        original.analysis.minimizer.type = 'bumps (dream)'
        original.analysis.fit_result._set_result_kind('bayesian')
        minimizer = original.analysis.minimizer
        minimizer.sampling_steps = 300
        minimizer.burn_in_steps = 60
        original.analysis._set_has_persisted_fit_state(value=True)
        original.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))
        minimizer = loaded.analysis.minimizer

        assert minimizer is not None
        assert minimizer.sampling_steps.value == 300
        assert minimizer.burn_in_steps.value == 60
        assert minimizer.thinning_interval.value == 1
        assert minimizer.population_size.value == 4


class TestLoadAnalysisCifFallback:
    """Load falls back from analysis/analysis.cif to analysis.cif at root."""

    def test_loads_analysis_from_subdir(self, tmp_path):
        """Current save layout: analysis/analysis.cif."""
        original = Project(name='fb1')
        original.save_as(str(tmp_path / 'proj'))

        # Verify analysis.cif is in analysis/ subdirectory (current save layout)
        assert (tmp_path / 'proj' / 'analysis' / 'analysis.edi').is_file()

        loaded = Project.load(str(tmp_path / 'proj'))
        assert loaded.analysis.minimizer.type == 'lmfit (leastsq)'

    def test_loads_analysis_from_root_fallback(self, tmp_path):
        """Old layout fallback: analysis.cif at project root."""
        original = Project(name='fb2')
        original.save_as(str(tmp_path / 'proj'))

        # Move analysis.cif from analysis/ subdirectory to project root
        proj_dir = tmp_path / 'proj'
        analysis_dir = proj_dir / 'analysis'
        (analysis_dir / 'analysis.edi').rename(proj_dir / 'analysis.edi')
        analysis_dir.rmdir()

        loaded = Project.load(str(proj_dir))
        assert loaded.analysis.minimizer.type == 'lmfit (leastsq)'

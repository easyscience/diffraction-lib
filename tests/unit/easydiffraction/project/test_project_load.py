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
        assert loaded.info.title == 'Empty'
        assert loaded.info.description == 'nothing'
        assert loaded.info.path is not None
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
            label='Co',
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

        assert loaded.analysis.fitting.minimizer_type.value == 'lmfit (leastsq)'

    def test_round_trips_fit_mode(self, tmp_path):
        original = Project(name='a2')
        original.analysis.fitting_mode_type = 'joint'
        original.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))

        assert loaded.analysis.fitting_mode_type == 'joint'

    def test_round_trips_rendering_configuration(self, tmp_path):
        original = Project(name='d1')
        original.rendering.chart_engine = 'asciichartpy'
        original.rendering.table_engine = 'rich'
        original.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))

        assert loaded.rendering.chart_engine.value == 'asciichartpy'
        assert loaded.rendering.table_engine.value == 'rich'

    def test_round_trips_constraints(self, tmp_path):
        original = Project(name='c1')
        original.structures.create(name='s')
        s = original.structures['s']
        s.cell.length_a = 5.0
        s.cell.length_b = 5.0

        original.analysis.aliases.create(
            label='a_param',
            param=s.cell.length_a,
        )
        original.analysis.aliases.create(
            label='b_param',
            param=s.cell.length_b,
        )
        original.analysis.constraints.create(expression='b_param = a_param')
        original.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))

        assert len(loaded.analysis.aliases) == 2
        assert loaded.analysis.aliases['a_param'].label.value == 'a_param'
        assert loaded.analysis.aliases['b_param'].label.value == 'b_param'
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
        parameter._set_fit_bounds_uncertainty_multiplier(4.0)
        parameter._fit_start_value = 3.87
        parameter._fit_start_uncertainty = 0.02

        original.analysis.fit_parameters.create(
            param_unique_name=parameter.unique_name,
            fit_min=parameter.fit_min,
            fit_max=parameter.fit_max,
            fit_bounds_uncertainty_multiplier=4.0,
            start_value=3.87,
            start_uncertainty=0.02,
        )
        original.analysis.fit_result._set_result_kind('deterministic')
        original.analysis.fit_result._set_success(value=True)
        original.analysis.fit_result._set_message('Fit converged')
        original.analysis.fit_result._set_iterations(37)
        original.analysis.fit_result._set_fitting_time(1.82)
        original.analysis.fit_result._set_reduced_chi_square(1.031)
        original.analysis.deterministic_result._set_optimizer_name('lmfit')
        original.analysis.deterministic_result._set_method_name('leastsq')
        original.analysis._set_has_persisted_fit_state(value=True)
        original.save_as(str(tmp_path / 'proj'))

        loaded = Project.load(str(tmp_path / 'proj'))
        loaded_parameter = loaded.structures['lbco'].cell.length_a

        assert loaded.analysis.fit_result.result_kind.value == 'deterministic'
        assert loaded.analysis.fit_parameters[parameter.unique_name].fit_min.value == 3.8
        assert loaded_parameter.value == 3.88
        assert loaded_parameter.fit_min == 3.8
        assert loaded_parameter.fit_max == 3.9
        assert loaded_parameter.fit_bounds_uncertainty_multiplier == 4.0
        assert loaded_parameter._fit_start_value == 3.87
        assert loaded_parameter._fit_start_uncertainty == 0.02
        assert loaded_parameter.uncertainty == 0.07


class TestLoadAnalysisCifFallback:
    """Load falls back from analysis/analysis.cif to analysis.cif at root."""

    def test_loads_analysis_from_subdir(self, tmp_path):
        """Current save layout: analysis/analysis.cif."""
        original = Project(name='fb1')
        original.save_as(str(tmp_path / 'proj'))

        # Verify analysis.cif is in analysis/ subdirectory (current save layout)
        assert (tmp_path / 'proj' / 'analysis' / 'analysis.cif').is_file()

        loaded = Project.load(str(tmp_path / 'proj'))
        assert loaded.analysis.fitting.minimizer_type.value == 'lmfit (leastsq)'

    def test_loads_analysis_from_root_fallback(self, tmp_path):
        """Old layout fallback: analysis.cif at project root."""
        original = Project(name='fb2')
        original.save_as(str(tmp_path / 'proj'))

        # Move analysis.cif from analysis/ subdirectory to project root
        proj_dir = tmp_path / 'proj'
        analysis_dir = proj_dir / 'analysis'
        (analysis_dir / 'analysis.cif').rename(proj_dir / 'analysis.cif')
        analysis_dir.rmdir()

        loaded = Project.load(str(proj_dir))
        assert loaded.analysis.fitting.minimizer_type.value == 'lmfit (leastsq)'

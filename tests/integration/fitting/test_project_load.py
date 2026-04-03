# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Integration tests for Project save → load round-trip."""

from __future__ import annotations

import tempfile

from numpy.testing import assert_almost_equal

from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import StructureFactory
from easydiffraction import download_data

TEMP_DIR = tempfile.gettempdir()


# ------------------------------------------------------------------
#  Helpers
# ------------------------------------------------------------------


def _create_lbco_project() -> Project:
    """
    Build a complete LBCO project ready for fitting.

    Returns a project with one structure, one experiment (with data),
    instrument settings, peak profile, background, linked phases, free
    parameters, aliases, and constraints.
    """
    # Structure
    model = StructureFactory.from_scratch(name='lbco')
    model.space_group.name_h_m = 'P m -3 m'
    model.cell.length_a = 3.8909
    model.atom_sites.create(
        label='La',
        type_symbol='La',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        b_iso=0.5,
    )
    model.atom_sites.create(
        label='Ba',
        type_symbol='Ba',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        b_iso=0.5,
    )
    model.atom_sites.create(
        label='Co',
        type_symbol='Co',
        fract_x=0.5,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='b',
        b_iso=0.5,
    )
    model.atom_sites.create(
        label='O',
        type_symbol='O',
        fract_x=0,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='c',
        b_iso=0.5,
    )

    # Experiment
    data_path = download_data(id=3, destination=TEMP_DIR)
    expt = ExperimentFactory.from_data_path(
        name='hrpt',
        data_path=data_path,
    )
    expt.instrument.setup_wavelength = 1.494
    expt.instrument.calib_twotheta_offset = 0.6225
    expt.peak.broad_gauss_u = 0.0834
    expt.peak.broad_gauss_v = -0.1168
    expt.peak.broad_gauss_w = 0.123
    expt.peak.broad_lorentz_x = 0
    expt.peak.broad_lorentz_y = 0.0797
    expt.background.create(id='1', x=10, y=170)
    expt.background.create(id='2', x=165, y=170)
    expt.linked_phases.create(id='lbco', scale=9.0)

    # Project assembly
    project = Project(name='lbco_project')
    project.structures.add(model)
    project.experiments.add(expt)

    # Free parameters
    model.cell.length_a.free = True
    expt.linked_phases['lbco'].scale.free = True
    expt.instrument.calib_twotheta_offset.free = True
    expt.background['1'].y.free = True
    expt.background['2'].y.free = True

    # Aliases and constraints
    project.analysis.aliases.create(
        label='biso_La',
        param=model.atom_sites['La'].b_iso,
    )
    project.analysis.aliases.create(
        label='biso_Ba',
        param=model.atom_sites['Ba'].b_iso,
    )
    project.analysis.constraints.create(expression='biso_Ba = biso_La')

    return project


def _collect_param_snapshot(project: Project) -> dict[str, float]:
    """Return ``{unique_name: value}`` for all project parameters."""
    return {p.unique_name: p.value for p in project.parameters}


def _collect_free_flags(project: Project) -> dict[str, bool]:
    """Return ``{unique_name: free}`` for fittable parameters."""
    from easydiffraction.core.variable import Parameter  # noqa: PLC0415

    return {p.unique_name: p.free for p in project.parameters if isinstance(p, Parameter)}


# ------------------------------------------------------------------
#  Test 1: save → load → compare all parameters
# ------------------------------------------------------------------


def test_save_load_round_trip_preserves_parameters(tmp_path) -> None:
    """
    Every parameter value must survive a save → load cycle.

    Also verifies project info, free flags, aliases, and constraints.
    """
    original = _create_lbco_project()
    original_params = _collect_param_snapshot(original)
    original_free = _collect_free_flags(original)

    # Save
    proj_dir = str(tmp_path / 'lbco_project')
    original.save_as(proj_dir)

    # Load
    loaded = Project.load(proj_dir)

    # Compare project info
    assert loaded.name == original.name
    assert loaded.info.title == original.info.title

    # Compare structures
    assert loaded.structures.names == original.structures.names
    orig_s = original.structures['lbco']
    load_s = loaded.structures['lbco']
    assert load_s.space_group.name_h_m.value == orig_s.space_group.name_h_m.value
    assert_almost_equal(load_s.cell.length_a.value, orig_s.cell.length_a.value, decimal=6)
    assert len(load_s.atom_sites) == len(orig_s.atom_sites)

    # Compare experiments
    assert loaded.experiments.names == original.experiments.names

    # Compare all parameter values
    loaded_params = _collect_param_snapshot(loaded)
    for name, orig_val in original_params.items():
        assert name in loaded_params, f'Parameter {name} missing after load'
        if isinstance(orig_val, float):
            assert_almost_equal(
                loaded_params[name],
                orig_val,
                decimal=6,
                err_msg=f'Mismatch for {name}',
            )
        else:
            assert loaded_params[name] == orig_val, f'Mismatch for {name}'

    # Compare free flags
    loaded_free = _collect_free_flags(loaded)
    for name, orig_flag in original_free.items():
        if name in loaded_free:
            assert loaded_free[name] == orig_flag, (
                f'Free flag mismatch for {name}: expected {orig_flag}, got {loaded_free[name]}'
            )

    # Compare aliases
    assert len(loaded.analysis.aliases) == len(original.analysis.aliases)
    for orig_alias in original.analysis.aliases:
        label = orig_alias.label.value
        loaded_alias = loaded.analysis.aliases[label]
        assert loaded_alias.param_unique_name.value == orig_alias.param_unique_name.value
        assert loaded_alias.param is not None, f"Alias '{label}' param reference not resolved"

    # Compare constraints
    assert len(loaded.analysis.constraints) == len(original.analysis.constraints)
    for i, orig_c in enumerate(original.analysis.constraints):
        assert loaded.analysis.constraints[i].expression.value == orig_c.expression.value
    assert loaded.analysis.constraints.enabled is True

    # Compare analysis settings
    assert loaded.analysis.current_minimizer == original.analysis.current_minimizer
    assert loaded.analysis.fit_mode.mode.value == original.analysis.fit_mode.mode.value


# ------------------------------------------------------------------
#  Test 2: create → fit → save → load → fit → compare χ²
# ------------------------------------------------------------------


def test_save_load_round_trip_preserves_fit_quality(tmp_path) -> None:
    """
    A loaded project must produce the same χ² as the original.

    Fits the original project, saves it, loads it back, fits again,
    and compares reduced χ² values.
    """
    # Create and fit the original project
    original = _create_lbco_project()
    original.analysis.fit(verbosity='silent')
    original_chi2 = original.analysis.fit_results.reduced_chi_square

    # Save the fitted project
    proj_dir = str(tmp_path / 'lbco_fitted')
    original.save_as(proj_dir)

    # Load
    loaded = Project.load(proj_dir)

    # Fit the loaded project
    loaded.analysis.fit(verbosity='silent')
    loaded_chi2 = loaded.analysis.fit_results.reduced_chi_square

    # The χ² values should be very close (same starting point,
    # same data, same model)
    assert_almost_equal(loaded_chi2, original_chi2, decimal=1)

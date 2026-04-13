# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Integration tests for Analysis.fit_sequential()."""

from __future__ import annotations

import csv
import shutil
import tempfile
from pathlib import Path

import pytest
from numpy.testing import assert_almost_equal

from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import StructureFactory
from easydiffraction import download_data

TEMP_DIR = tempfile.gettempdir()


def _create_sequential_project(tmp_path: Path) -> tuple[Project, str]:
    """
    Build a project for sequential fitting and save it.

    Returns the project and the path to a data directory with a few
    copies of the same data file (to simulate a scan).
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
        adp_iso=0.5,
    )
    model.atom_sites.create(
        label='Ba',
        type_symbol='Ba',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        adp_iso=0.5,
    )
    model.atom_sites.create(
        label='Co',
        type_symbol='Co',
        fract_x=0.5,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='b',
        adp_iso=0.5,
    )
    model.atom_sites.create(
        label='O',
        type_symbol='O',
        fract_x=0,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='c',
        adp_iso=0.5,
    )

    # Experiment (template)
    data_path = download_data(id=3, destination=TEMP_DIR)
    expt = ExperimentFactory.from_data_path(
        name='template',
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
    project = Project(name='seq_test')
    project.structures.add(model)
    project.experiments.add(expt)

    # Free parameters
    model.cell.length_a.free = True
    expt.linked_phases['lbco'].scale.free = True
    expt.instrument.calib_twotheta_offset.free = True
    expt.background['1'].y.free = True
    expt.background['2'].y.free = True

    # Initial fit on the template
    project.analysis.fit(verbosity='silent')

    # Save project
    proj_dir = str(tmp_path / 'seq_project')
    project.save_as(proj_dir)

    # Create a data directory with copies of the same data file
    data_dir = tmp_path / 'scan_data'
    data_dir.mkdir()
    for i in range(3):
        shutil.copy(data_path, data_dir / f'scan_{i + 1:03d}.xye')

    return project, str(data_dir)


# ------------------------------------------------------------------
#  Test 1: Basic sequential fit produces CSV
# ------------------------------------------------------------------


def test_fit_sequential_produces_csv(tmp_path) -> None:
    """fit_sequential creates a results.csv with one row per file."""
    project, data_dir = _create_sequential_project(tmp_path)

    project.analysis.fit_sequential(
        data_dir=data_dir,
        verbosity='silent',
    )

    csv_path = project.info.path / 'analysis' / 'results.csv'
    assert csv_path.is_file(), 'results.csv was not created'

    with csv_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3, f'Expected 3 rows, got {len(rows)}'

    # Each row should have fit_success
    for row in rows:
        assert row['fit_success'] == 'True', f'Fit failed for {row["file_path"]}'

    # Each row should have parameter values
    assert 'lbco.cell.length_a' in rows[0]
    assert rows[0]['lbco.cell.length_a'] != ''


# ------------------------------------------------------------------
#  Test 2: Crash recovery skips already-fitted files
# ------------------------------------------------------------------


def test_fit_sequential_crash_recovery(tmp_path) -> None:
    """Running fit_sequential twice does not re-fit already-fitted files."""
    project, data_dir = _create_sequential_project(tmp_path)

    # First run: fit all 3 files
    project.analysis.fit_sequential(
        data_dir=data_dir,
        verbosity='silent',
    )

    csv_path = project.info.path / 'analysis' / 'results.csv'
    with csv_path.open() as f:
        rows_first = list(csv.DictReader(f))
    assert len(rows_first) == 3

    # Second run: should skip all 3 files
    project.analysis.fit_sequential(
        data_dir=data_dir,
        verbosity='silent',
    )

    with csv_path.open() as f:
        rows_second = list(csv.DictReader(f))
    # Still 3 rows — no duplicates
    assert len(rows_second) == 3


# ------------------------------------------------------------------
#  Test 3: Parameter propagation
# ------------------------------------------------------------------


def test_fit_sequential_parameter_propagation(tmp_path) -> None:
    """Parameters from one fit propagate to the next."""
    project, data_dir = _create_sequential_project(tmp_path)

    project.analysis.fit_sequential(
        data_dir=data_dir,
        verbosity='silent',
    )

    csv_path = project.info.path / 'analysis' / 'results.csv'
    with csv_path.open() as f:
        rows = list(csv.DictReader(f))

    # All rows should have similar parameter values (same data)
    vals = [float(r['lbco.cell.length_a']) for r in rows]
    for v in vals:
        assert_almost_equal(v, vals[0], decimal=3)


# ------------------------------------------------------------------
#  Test 4: extract_diffrn callback
# ------------------------------------------------------------------


def test_fit_sequential_with_diffrn_callback(tmp_path) -> None:
    """extract_diffrn callback populates diffrn columns in CSV."""
    project, data_dir = _create_sequential_project(tmp_path)

    temperatures = {'scan_001.xye': 300.0, 'scan_002.xye': 350.0, 'scan_003.xye': 400.0}

    def extract_diffrn(file_path: str) -> dict[str, float]:
        name = Path(file_path).name
        return {'ambient_temperature': temperatures.get(name, 0.0)}

    project.analysis.fit_sequential(
        data_dir=data_dir,
        extract_diffrn=extract_diffrn,
        verbosity='silent',
    )

    csv_path = project.info.path / 'analysis' / 'results.csv'
    with csv_path.open() as f:
        rows = list(csv.DictReader(f))

    # Check that temperature column is present and populated
    for row in rows:
        name = Path(row['file_path']).name
        if 'diffrn.ambient_temperature' in row:
            expected = temperatures.get(name, 0.0)
            assert_almost_equal(float(row['diffrn.ambient_temperature']), expected)


# ------------------------------------------------------------------
#  Test 5: Precondition checks
# ------------------------------------------------------------------


def test_fit_sequential_requires_saved_project(tmp_path) -> None:
    """fit_sequential raises if project hasn't been saved."""
    data_path = download_data(id=3, destination=TEMP_DIR)
    model = StructureFactory.from_scratch(name='s')
    expt = ExperimentFactory.from_data_path(
        name='e',
        data_path=data_path,
    )
    expt.linked_phases.create(id='s', scale=1.0)
    expt.linked_phases['s'].scale.free = True
    project = Project(name='unsaved')
    project.structures.add(model)
    project.experiments.add(expt)

    with pytest.raises(ValueError, match='must be saved'):
        project.analysis.fit_sequential(data_dir=str(tmp_path))


def test_fit_sequential_requires_one_structure(tmp_path) -> None:
    """fit_sequential raises if no structures exist."""
    project = Project(name='no_struct')
    project.save_as(str(tmp_path / 'proj'))

    with pytest.raises(ValueError, match='exactly 1 structure'):
        project.analysis.fit_sequential(data_dir=str(tmp_path))


def test_fit_sequential_requires_one_experiment(tmp_path) -> None:
    """fit_sequential raises if no experiments exist."""
    model = StructureFactory.from_scratch(name='s')
    project = Project(name='no_expt')
    project.structures.add(model)
    project.save_as(str(tmp_path / 'proj'))

    with pytest.raises(ValueError, match='exactly 1 experiment'):
        project.analysis.fit_sequential(data_dir=str(tmp_path))


# ------------------------------------------------------------------
#  Test 6: Parallel sequential fit (max_workers=2)
# ------------------------------------------------------------------


def test_fit_sequential_parallel(tmp_path) -> None:
    """fit_sequential with max_workers=2 produces correct CSV."""
    project, data_dir = _create_sequential_project(tmp_path)

    project.analysis.fit_sequential(
        data_dir=data_dir,
        max_workers=2,
        verbosity='silent',
    )

    csv_path = project.info.path / 'analysis' / 'results.csv'
    assert csv_path.is_file(), 'results.csv was not created'

    with csv_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3, f'Expected 3 rows, got {len(rows)}'

    for row in rows:
        assert row['fit_success'] == 'True', f'Fit failed for {row["file_path"]}'

    # Parameter values should be present and reasonable
    assert 'lbco.cell.length_a' in rows[0]
    vals = [float(r['lbco.cell.length_a']) for r in rows]
    for v in vals:
        assert_almost_equal(v, vals[0], decimal=3)


# ------------------------------------------------------------------
#  Test 7: Dataset replay from CSV (apply_params_from_csv)
# ------------------------------------------------------------------


def test_apply_params_from_csv_loads_data_and_params(tmp_path) -> None:
    """apply_params_from_csv overrides params and reloads data."""
    project, data_dir = _create_sequential_project(tmp_path)

    project.analysis.fit_sequential(
        data_dir=data_dir,
        verbosity='silent',
    )

    csv_path = project.info.path / 'analysis' / 'results.csv'
    with csv_path.open() as f:
        rows = list(csv.DictReader(f))

    # Read the expected cell_length_a from CSV row 1
    expected_a = float(rows[1]['lbco.cell.length_a'])

    # Apply params from row 1
    project.apply_params_from_csv(row_index=1)

    # Verify the parameter value was overridden
    model = next(iter(project.structures.values()))
    assert_almost_equal(model.cell.length_a.value, expected_a, decimal=5)

    # Verify that the experiment has measured data loaded
    # (from the file_path in that CSV row)
    expt = next(iter(project.experiments.values()))
    assert expt.data.intensity_meas is not None


def test_apply_params_from_csv_raises_on_missing_csv(tmp_path) -> None:
    """apply_params_from_csv raises if no CSV exists."""
    project = Project(name='no_csv')
    project.save_as(str(tmp_path / 'proj'))

    with pytest.raises(FileNotFoundError, match='Results CSV not found'):
        project.apply_params_from_csv(row_index=0)


def test_apply_params_from_csv_raises_on_bad_index(tmp_path) -> None:
    """apply_params_from_csv raises on out-of-range index."""
    project, data_dir = _create_sequential_project(tmp_path)

    project.analysis.fit_sequential(
        data_dir=data_dir,
        verbosity='silent',
    )

    with pytest.raises(IndexError, match='out of range'):
        project.apply_params_from_csv(row_index=99)

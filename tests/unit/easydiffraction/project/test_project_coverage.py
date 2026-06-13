# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Supplementary coverage tests for the Project facade module.

These exercise module-level CSV/CIF helpers, read-only property
aliases, the switchable-category filter hook, file-I/O error paths,
and the negative/out-of-range branches of ``apply_params_from_csv``.
"""

from __future__ import annotations

import csv
import pathlib
import tempfile
from collections import UserList
from types import SimpleNamespace

import pytest

import easydiffraction.core.variable as variable_module
import easydiffraction.project.project as project_module
from easydiffraction.project.project import Project
from easydiffraction.project.project import _apply_csv_row_to_diffrn
from easydiffraction.project.project import _apply_csv_row_to_params
from easydiffraction.project.project import _load_easydiff_directory
from easydiffraction.project.project import _load_project_analysis
from easydiffraction.project.project import _load_project_metadata
from easydiffraction.project.project import _resolve_data_path_from_results_csv
from easydiffraction.project.project import _resolved_analysis_path
from easydiffraction.utils.logging import Logger


class _FakeColumns(UserList):
    """A minimal stand-in for a pandas column index (iterable of names)."""


def _series(values: dict[str, object]):
    import pandas as pd

    return pd.Series(values)


# ----------------------------------------------------------------------
# _apply_csv_row_to_params
# ----------------------------------------------------------------------


def test_apply_csv_row_overrides_value_and_uncertainty():
    param = SimpleNamespace(value=0.0, uncertainty=0.0)
    columns = _FakeColumns(['cell.length_a', 'cell.length_a.uncertainty'])
    row = _series({'cell.length_a': 3.91, 'cell.length_a.uncertainty': 0.04})

    _apply_csv_row_to_params(
        row,
        columns,
        {'cell.length_a': param},
        meta_columns=set(),
    )

    assert param.value == 3.91
    assert param.uncertainty == 0.04


def test_apply_csv_row_skips_meta_and_diffrn_and_nan_columns():
    param = SimpleNamespace(value=1.0, uncertainty=2.0)
    columns = _FakeColumns([
        'file_path',
        'diffrn.twotheta_offset',
        'cell.length_a',
        'cell.length_a.uncertainty',
    ])
    # The value column is NaN and the uncertainty references an unknown
    # parameter, so neither field on the live parameter should change.
    row = _series({
        'file_path': 'scan.dat',
        'diffrn.twotheta_offset': 0.1,
        'cell.length_a': float('nan'),
        'cell.length_a.uncertainty': float('nan'),
    })

    _apply_csv_row_to_params(
        row,
        columns,
        {'cell.length_a': param},
        meta_columns={'file_path'},
    )

    assert param.value == 1.0
    assert param.uncertainty == 2.0


# ----------------------------------------------------------------------
# _apply_csv_row_to_diffrn
# ----------------------------------------------------------------------


def test_apply_csv_row_to_diffrn_sets_numeric_descriptor(monkeypatch):
    class _FakeNumericDescriptor:
        def __init__(self):
            self.value = 0.0

    monkeypatch.setattr(variable_module, 'NumericDescriptor', _FakeNumericDescriptor)

    descriptor = _FakeNumericDescriptor()
    experiment = SimpleNamespace(diffrn=SimpleNamespace(twotheta_offset=descriptor))
    columns = _FakeColumns(['cell.length_a', 'diffrn.twotheta_offset', 'diffrn.missing'])
    row = _series({
        'cell.length_a': 3.0,
        'diffrn.twotheta_offset': 0.25,
        'diffrn.missing': float('nan'),
    })

    _apply_csv_row_to_diffrn(row, columns, experiment)

    assert descriptor.value == 0.25


def test_apply_csv_row_to_diffrn_ignores_non_descriptor_field(monkeypatch):
    class _FakeNumericDescriptor:
        def __init__(self):
            self.value = 0.0

    monkeypatch.setattr(variable_module, 'NumericDescriptor', _FakeNumericDescriptor)

    # diffrn.label is a plain string, not a NumericDescriptor, so the
    # helper must leave it untouched without raising.
    experiment = SimpleNamespace(diffrn=SimpleNamespace(label='cw'))
    columns = _FakeColumns(['diffrn.label'])
    row = _series({'diffrn.label': 1.0})

    _apply_csv_row_to_diffrn(row, columns, experiment)

    assert experiment.diffrn.label == 'cw'


# ----------------------------------------------------------------------
# _resolve_data_path_from_results_csv
# ----------------------------------------------------------------------


def test_resolve_data_path_returns_none_for_empty_or_non_string():
    project_path = pathlib.Path('/projects/demo')

    assert _resolve_data_path_from_results_csv(project_path, '') is None
    assert _resolve_data_path_from_results_csv(project_path, float('nan')) is None


def test_resolve_data_path_preserves_absolute_path():
    project_path = pathlib.Path('/projects/demo')
    absolute = pathlib.Path('/data/scan_001.dat')

    resolved = _resolve_data_path_from_results_csv(project_path, str(absolute))

    assert resolved == absolute


def test_resolve_data_path_joins_relative_to_project():
    project_path = pathlib.Path('/projects/demo')

    resolved = _resolve_data_path_from_results_csv(project_path, 'experiments/scan.dat')

    assert resolved == project_path / 'experiments' / 'scan.dat'


# ----------------------------------------------------------------------
# _load_easydiff_directory / _load_project_metadata / _resolved_analysis_path
# ----------------------------------------------------------------------


def test_load_easydiff_directory_skips_missing_directory(tmp_path):
    calls: list[str] = []

    _load_easydiff_directory(
        tmp_path / 'absent',
        calls.append,
        replacement='structures/<structure>.easydiff',
    )

    assert calls == []


def test_load_easydiff_directory_loads_sorted_easydiff_files(tmp_path):
    easydiff_dir = tmp_path / 'structures'
    easydiff_dir.mkdir()
    (easydiff_dir / 'b.easydiff').write_text('b')
    (easydiff_dir / 'a.easydiff').write_text('a')
    (easydiff_dir / 'note.txt').write_text('ignored')

    calls: list[str] = []
    _load_easydiff_directory(
        easydiff_dir,
        calls.append,
        replacement='structures/<structure>.easydiff',
    )

    assert calls == [str(easydiff_dir / 'a.easydiff'), str(easydiff_dir / 'b.easydiff')]


def test_load_easydiff_directory_rejects_legacy_cif(tmp_path):
    easydiff_dir = tmp_path / 'structures'
    easydiff_dir.mkdir()
    (easydiff_dir / 'lbco.cif').write_text('legacy')

    with pytest.raises(ValueError, match=r'structures/<structure>\.easydiff'):
        _load_easydiff_directory(
            easydiff_dir,
            lambda _path: None,
            replacement='structures/<structure>.easydiff',
        )


def test_load_project_metadata_no_easydiff_raises(tmp_path):
    project = Project(name='unchanged_info')

    with pytest.raises(FileNotFoundError, match=r'project\.easydiff'):
        _load_project_metadata(project, tmp_path)


def test_resolved_analysis_path_returns_none_when_absent(tmp_path):
    assert _resolved_analysis_path(tmp_path) is None


def test_resolved_analysis_path_uses_root_fallback(tmp_path):
    root_easydiff = tmp_path / 'analysis.easydiff'
    root_easydiff.write_text('analysis')

    assert _resolved_analysis_path(tmp_path) == root_easydiff


def test_load_project_analysis_no_cif_is_noop(tmp_path):
    project = Project(name='no_analysis_cif')
    original_analysis = project.analysis

    # No analysis CIF on disk: the restore helper must return without
    # touching the project's analysis object.
    _load_project_analysis(project, tmp_path)

    assert project.analysis is original_analysis


# ----------------------------------------------------------------------
# Switchable-category filter hook and current-project tracking
# ----------------------------------------------------------------------


def test_supported_filters_for_returns_empty_mapping():
    assert Project._supported_filters_for(object()) == {}


def test_current_project_path_none_when_unsaved(monkeypatch):
    monkeypatch.setattr(Project, '_current_project', None, raising=True)

    assert Project.current_project_path() is None


def test_current_project_path_reports_saved_path(tmp_path):
    project = Project(name='tracked')
    expected = tmp_path / 'tracked-project'
    project.metadata.path = expected

    assert Project.current_project_path() == expected


# ----------------------------------------------------------------------
# Dunder and read-only property aliases
# ----------------------------------------------------------------------


def test_str_reports_counts():
    project = Project(name='shown')
    project.structures.create(name='one')

    text = str(project)

    assert "Project 'shown'" in text
    assert '1 structures' in text
    assert '0 experiments' in text


def test_full_name_aliases_name():
    project = Project(name='aliased')

    assert project.full_name == 'aliased'
    assert project.full_name == project.name


def test_parameters_aggregates_structures_and_experiments():
    project = Project(name='params')
    structure_param = object()
    experiment_param = object()
    project._structures = SimpleNamespace(parameters=[structure_param])
    project._experiments = SimpleNamespace(parameters=[experiment_param])

    assert project.parameters == [structure_param, experiment_param]


def test_as_cif_delegates_to_serializer(monkeypatch):
    project = Project(name='serialized')
    monkeypatch.setattr(project_module, 'project_to_cif', lambda p: f'cif-for-{p.name}')

    assert project.as_cif == 'cif-for-serialized'


# ----------------------------------------------------------------------
# Typechecked collection setters
# ----------------------------------------------------------------------


def test_structures_setter_accepts_collection():
    from easydiffraction.datablocks.structure.collection import Structures

    project = Project(name='set_structures')
    replacement = Structures()
    project.structures = replacement

    assert project.structures is replacement


def test_structures_setter_rejects_wrong_type():
    import typeguard

    project = Project(name='bad_structures')
    with pytest.raises(typeguard.TypeCheckError):
        project.structures = object()


def test_experiments_setter_accepts_collection():
    from easydiffraction.datablocks.experiment.collection import Experiments

    project = Project(name='set_experiments')
    replacement = Experiments()
    project.experiments = replacement

    assert project.experiments is replacement


def test_experiments_setter_rejects_wrong_type():
    import typeguard

    project = Project(name='bad_experiments')
    with pytest.raises(typeguard.TypeCheckError):
        project.experiments = object()


# ----------------------------------------------------------------------
# _build_parameter_map and _resolve_alias_references
# ----------------------------------------------------------------------


def test_build_parameter_map_skips_params_without_unique_name():
    project = Project(name='param_map')
    named = SimpleNamespace(unique_name='cell.length_a')
    anonymous = SimpleNamespace(unique_name=None)
    project._structures = SimpleNamespace(parameters=[named])
    project._experiments = SimpleNamespace(parameters=[anonymous])

    param_map = project._build_parameter_map()

    assert param_map == {'cell.length_a': named}


def test_resolve_alias_references_warns_on_unknown_parameter(monkeypatch):
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

    project = Project(name='alias_resolve')
    project.structures.create(name='lbco')
    structure = project.structures['lbco']
    structure.cell.length_a = 4.0

    project.analysis.aliases.create(
        id='a_param',
        param=structure.cell.length_a,
    )
    alias = project.analysis.aliases['a_param']
    alias.parameter_unique_name.value = 'does.not.exist'

    warnings: list[str] = []
    monkeypatch.setattr(project_module.log, 'warning', warnings.append)

    project._resolve_alias_references()

    assert any('does.not.exist' in message for message in warnings)


# ----------------------------------------------------------------------
# save() / save_as() error and branch paths
# ----------------------------------------------------------------------


def test_save_without_path_logs_error_and_returns(monkeypatch):
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

    project = Project(name='no_path')
    errors: list[str] = []
    monkeypatch.setattr(project_module.log, 'error', errors.append)

    project.save()

    assert project.metadata.path is None
    assert any('save_as()' in message for message in errors)


def test_save_writes_experiment_easydiff_files(tmp_path, monkeypatch):
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.project.project_metadata import ProjectMetadata

    monkeypatch.setattr(ProjectMetadata, 'as_cif', property(lambda self: 'info'))
    monkeypatch.setattr(Analysis, 'as_cif', property(lambda self: 'analysis'))

    project = Project(name='with_experiments')
    project.report.html = False

    experiment = SimpleNamespace(name='scan1', as_cif='data_scan1')

    class _Experiments(SimpleNamespace):
        @staticmethod
        def values():
            return [experiment]

    project._experiments = _Experiments(parameters=[])
    project.save_as(str(tmp_path / 'proj'))

    # Experiments are persisted as EasyDiff files carrying the schema
    # marker; the original section header is preserved.
    written = (tmp_path / 'proj' / 'experiments' / 'scan1.easydiff').read_text()
    assert written.startswith('data_scan1')
    assert '_easydiff.schema_name EasyDiffraction' in written


def test_save_as_temporary_writes_under_system_tempdir(monkeypatch):
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.project.project_metadata import ProjectMetadata

    monkeypatch.setattr(ProjectMetadata, 'as_cif', property(lambda self: 'info'))
    monkeypatch.setattr(Analysis, 'as_cif', property(lambda self: 'analysis'))

    project = Project(name='temp_save')
    project.report.html = False
    unique_dir = f'edx_temp_{id(project)}'

    try:
        project.save_as(unique_dir, temporary=True)
        expected = pathlib.Path(tempfile.gettempdir()) / unique_dir
        assert (expected / 'project.easydiff').is_file()
        assert project.metadata.path == expected
    finally:
        import shutil

        target = pathlib.Path(tempfile.gettempdir()) / unique_dir
        if target.is_dir():
            shutil.rmtree(target)


def test_save_as_overwrite_clears_children_when_target_is_cwd(tmp_path, monkeypatch):
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.project.project_metadata import ProjectMetadata

    monkeypatch.setattr(ProjectMetadata, 'as_cif', property(lambda self: 'info'))
    monkeypatch.setattr(Analysis, 'as_cif', property(lambda self: 'analysis'))

    target = tmp_path / 'cwd_project'
    target.mkdir()
    stale_file = target / 'stale.txt'
    stale_file.write_text('stale')
    stale_dir = target / 'old_subdir'
    stale_dir.mkdir()
    (stale_dir / 'inner.txt').write_text('inner')

    monkeypatch.chdir(target)

    project = Project(name='cwd_save')
    project.report.html = False
    project.save_as(str(target))

    # The directory itself is preserved (it is the CWD) but its prior
    # children are removed before the fresh project is written.
    assert not stale_file.exists()
    assert not stale_dir.exists()
    assert (target / 'project.easydiff').is_file()


# ----------------------------------------------------------------------
# apply_params_from_csv error and indexing paths
# ----------------------------------------------------------------------


def test_apply_params_from_csv_requires_saved_path():
    project = Project(name='unsaved_csv')

    with pytest.raises(FileNotFoundError, match='Save the project first'):
        project.apply_params_from_csv(0)


def test_apply_params_from_csv_missing_results_csv(tmp_path):
    project = Project(name='missing_csv')
    project.metadata.path = tmp_path / 'proj'
    (project.metadata.path / 'analysis').mkdir(parents=True)

    with pytest.raises(FileNotFoundError, match='Results CSV not found'):
        project.apply_params_from_csv(0)


def _write_results_csv(analysis_dir: pathlib.Path, rows: list[dict[str, object]]) -> None:
    analysis_dir.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with (analysis_dir / 'results.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _stub_project_collections(project: Project):
    """Replace structures/experiments with light fakes for CSV tests."""

    class _Experiment:
        def __init__(self):
            self.diffrn = SimpleNamespace()
            self._need_categories_update = False
            self.loaded: list[str] = []

        def _load_ascii_data_to_experiment(self, file_path):
            self.loaded.append(file_path)

    experiment = _Experiment()
    structure = SimpleNamespace(_need_categories_update=False)

    class _Structures(UserList):
        parameters: list = []

    class _Experiments:
        parameters: list = []

        @staticmethod
        def values():
            return [experiment]

    structures = _Structures([structure])
    project._structures = structures
    project._experiments = _Experiments()
    return SimpleNamespace(experiment=experiment, structure=structure)


def test_apply_params_from_csv_out_of_range_raises(tmp_path):
    project = Project(name='range_csv')
    project.metadata.path = tmp_path / 'proj'
    _write_results_csv(project.metadata.path / 'analysis', [{'file_path': ''}])
    _stub_project_collections(project)

    with pytest.raises(IndexError, match='out of range'):
        project.apply_params_from_csv(5)


def test_apply_params_from_csv_negative_index_out_of_range_raises(tmp_path):
    project = Project(name='neg_range_csv')
    project.metadata.path = tmp_path / 'proj'
    _write_results_csv(project.metadata.path / 'analysis', [{'file_path': ''}])
    _stub_project_collections(project)

    with pytest.raises(IndexError, match='out of range'):
        project.apply_params_from_csv(-5)


def test_apply_params_from_csv_negative_index_skips_absent_data_file(tmp_path, monkeypatch):
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

    project = Project(name='neg_csv')
    project.metadata.path = tmp_path / 'proj'
    _write_results_csv(
        project.metadata.path / 'analysis',
        [
            {'file_path': 'first.dat'},
            {'file_path': 'experiments/missing.dat'},
        ],
    )
    fakes = _stub_project_collections(project)

    # Negative index addresses the last row; its file_path does not
    # resolve to a real file, so no data is reloaded but flags update.
    project.apply_params_from_csv(-1)

    assert fakes.experiment.loaded == []
    assert fakes.experiment._need_categories_update is True
    assert fakes.structure._need_categories_update is True

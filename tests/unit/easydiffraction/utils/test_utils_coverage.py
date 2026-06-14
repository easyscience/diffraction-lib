# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""Supplementary unit tests for easydiffraction.utils.utils — coverage gaps."""

import urllib.request

import numpy as np
import pytest

# --- _validate_url -----------------------------------------------------------


def test_validate_url_accepts_http():
    import easydiffraction.utils.utils as MUT

    # Should not raise for http
    MUT._validate_url('http://example.com/file.cif')


def test_validate_url_accepts_https():
    import easydiffraction.utils.utils as MUT

    # Should not raise for https
    MUT._validate_url('https://example.com/file.cif')


# --- _local_filename ----------------------------------------------------------


def test_local_filename_with_extension():
    import easydiffraction.utils.utils as MUT

    result = MUT._local_filename('meas-lbco-hrpt', 'measured/lbco-hrpt.xye')
    assert result == 'meas-lbco-hrpt.xye'


def test_local_filename_cif_extension():
    import easydiffraction.utils.utils as MUT

    result = MUT._local_filename('struct-lbco', 'structures/lbco.cif')
    assert result == 'struct-lbco.cif'


def test_local_filename_no_extension():
    import easydiffraction.utils.utils as MUT

    result = MUT._local_filename('proj-x', 'projects/x')
    assert result == 'proj-x'


def test_record_path_raises_for_missing_path_key():
    import easydiffraction.utils.utils as MUT

    with pytest.raises(KeyError, match="Index record must contain 'path' key"):
        MUT._record_path({'url': 'https://example.com/data.xye'})


# --- _normalize_known_hash ----------------------------------------------------


def test_normalize_known_hash_none():
    import easydiffraction.utils.utils as MUT

    assert MUT._normalize_known_hash(None) is None


def test_normalize_known_hash_empty_string():
    import easydiffraction.utils.utils as MUT

    assert MUT._normalize_known_hash('') is None


def test_normalize_known_hash_placeholder():
    import easydiffraction.utils.utils as MUT

    assert MUT._normalize_known_hash('sha256:...') is None


def test_normalize_known_hash_placeholder_uppercase():
    import easydiffraction.utils.utils as MUT

    assert MUT._normalize_known_hash('SHA256:...') is None


def test_normalize_known_hash_valid():
    import easydiffraction.utils.utils as MUT

    h = 'sha256:abc123'
    assert MUT._normalize_known_hash(h) == h


def test_normalize_known_hash_strips_whitespace():
    import easydiffraction.utils.utils as MUT

    h = '  sha256:abc123  '
    assert MUT._normalize_known_hash(h) == 'sha256:abc123'


# --- stripped_package_version -------------------------------------------------


def test_stripped_package_version_returns_public():
    import easydiffraction.utils.utils as MUT

    # numpy is always installed in the test env
    result = MUT.stripped_package_version('numpy')
    assert result is not None
    assert '+' not in result  # no local segment


def test_stripped_package_version_missing_package():
    import easydiffraction.utils.utils as MUT

    result = MUT.stripped_package_version('__definitely_not_installed__')
    assert result is None


def test_stripped_package_version_strips_local(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: '1.2.3+local456')
    result = MUT.stripped_package_version('mypkg')
    assert result == '1.2.3'


def test_stripped_package_version_invalid_version(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: 'not-a-version!!!')
    result = MUT.stripped_package_version('mypkg')
    assert result == 'not-a-version!!!'


# --- _is_dev_version ---------------------------------------------------------


def test_is_dev_version_none_version(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: None)
    assert MUT._is_dev_version('easydiffraction') is True


# --- _safe_urlopen ------------------------------------------------------------


def test_safe_urlopen_rejects_non_https_string():
    import easydiffraction.utils.utils as MUT

    with pytest.raises(ValueError, match='Only https URLs are permitted'):
        MUT._safe_urlopen('http://example.com/file')


def test_safe_urlopen_rejects_non_https_request():
    import easydiffraction.utils.utils as MUT

    req = urllib.request.Request('http://example.com/file')
    with pytest.raises(ValueError, match='Only https URLs are permitted'):
        MUT._safe_urlopen(req)


def test_safe_urlopen_rejects_invalid_type():
    import easydiffraction.utils.utils as MUT

    with pytest.raises(TypeError, match='Expected str or Request, got int'):
        MUT._safe_urlopen(42)


# --- _resolve_tutorial_url ----------------------------------------------------


def test_resolve_tutorial_url_replaces_version(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, '_get_version_for_url', lambda: '1.0.0')
    template = 'https://example.com/{version}/tutorials/ed-1.ipynb'
    result = MUT._resolve_tutorial_url(template)
    assert result == 'https://example.com/1.0.0/tutorials/ed-1.ipynb'


def test_resolve_tutorial_url_dev(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, '_get_version_for_url', lambda: 'dev')
    template = 'https://example.com/{version}/tutorials/ed-2.ipynb'
    result = MUT._resolve_tutorial_url(template)
    assert result == 'https://example.com/dev/tutorials/ed-2.ipynb'


# --- render_cif ---------------------------------------------------------------


def test_render_cif_outputs_cif_text(capsys):
    import easydiffraction.utils.utils as MUT

    cif_text = '_cell_length_a 5.0\n_cell_length_b 6.0'
    MUT.render_cif(cif_text)
    out = capsys.readouterr().out
    assert '_cell_length_a 5.0' in out
    assert '_cell_length_b 6.0' in out


# --- sin_theta_over_lambda_to_d_spacing ---------------------------------------


def test_sin_theta_over_lambda_to_d_scalar():
    import easydiffraction.utils.utils as MUT

    # d = 1 / (2 * sin_theta_over_lambda)
    result = MUT.sin_theta_over_lambda_to_d_spacing(0.25)
    assert np.isclose(result, 2.0)


def test_sin_theta_over_lambda_to_d_array():
    import easydiffraction.utils.utils as MUT

    vals = np.array([0.1, 0.25, 0.5])
    expected = 1.0 / (2 * vals)
    result = MUT.sin_theta_over_lambda_to_d_spacing(vals)
    assert np.allclose(result, expected)


def test_sin_theta_over_lambda_to_d_zero_returns_nan():
    import easydiffraction.utils.utils as MUT

    result = MUT.sin_theta_over_lambda_to_d_spacing(np.array([0.0]))
    assert np.isnan(result[0])


def test_sin_theta_over_lambda_to_d_negative_returns_nan():
    import easydiffraction.utils.utils as MUT

    result = MUT.sin_theta_over_lambda_to_d_spacing(np.array([-0.1]))
    assert np.isnan(result[0])


# --- str_to_ufloat additional branches ----------------------------------------


def test_str_to_ufloat_none_returns_default():
    import easydiffraction.utils.utils as MUT

    u = MUT.str_to_ufloat(None, default=5.0)
    assert np.isclose(u.nominal_value, 5.0)
    assert np.isnan(u.std_dev)


def test_str_to_ufloat_none_no_default_raises():
    import easydiffraction.utils.utils as MUT

    # When s=None and default=None, ufloat(None, nan) raises TypeError
    with pytest.raises(TypeError):
        MUT.str_to_ufloat(None)


def test_str_to_ufloat_empty_brackets_mark_missing_uncertainty():
    import warnings

    import easydiffraction.utils.utils as MUT

    with warnings.catch_warnings():
        warnings.simplefilter('error')
        u = MUT.str_to_ufloat('3.566()')

    assert np.isclose(u.nominal_value, 3.566)
    assert np.isnan(u.std_dev)


def test_str_to_ufloat_invalid_string_returns_default():
    import easydiffraction.utils.utils as MUT

    u = MUT.str_to_ufloat('not_a_number', default=99.0)
    assert np.isclose(u.nominal_value, 99.0)
    assert np.isnan(u.std_dev)


# --- tof_to_d additional branches ---------------------------------------------


def test_tof_to_d_type_error_non_array():
    import easydiffraction.utils.utils as MUT

    with pytest.raises(TypeError, match="'tof' must be a NumPy array"):
        MUT.tof_to_d([10.0, 20.0], offset=0.0, linear=1.0, quad=0.0)


def test_tof_to_d_type_error_non_numeric_offset():
    import easydiffraction.utils.utils as MUT

    with pytest.raises(TypeError, match="'offset' must be a real number"):
        MUT.tof_to_d(np.array([10.0]), offset='bad', linear=1.0, quad=0.0)


def test_tof_to_d_type_error_non_numeric_linear():
    import easydiffraction.utils.utils as MUT

    with pytest.raises(TypeError, match="'linear' must be a real number"):
        MUT.tof_to_d(np.array([10.0]), offset=0.0, linear=None, quad=0.0)


def test_tof_to_d_both_linear_and_quad_zero():
    import easydiffraction.utils.utils as MUT

    tof = np.array([1.0, 2.0])
    result = MUT.tof_to_d(tof, offset=0.0, linear=0.0, quad=0.0)
    assert np.all(np.isnan(result))


def test_tof_to_d_negative_discriminant():
    import easydiffraction.utils.utils as MUT

    # Choose coefficients that produce a negative discriminant:
    # disc = linear^2 - 4*quad*(offset - tof) < 0
    # linear=0, quad=1, offset=10, tof=5 → disc = 0 - 4*1*(10-5) = -20 < 0
    tof = np.array([5.0])
    result = MUT.tof_to_d(tof, offset=10.0, linear=0.0, quad=1.0)
    assert np.all(np.isnan(result))


def test_tof_to_d_linear_negative_tof_minus_offset_gives_nan():
    import easydiffraction.utils.utils as MUT

    # linear case: d = (tof - offset) / linear → negative when tof < offset
    tof = np.array([1.0])
    result = MUT.tof_to_d(tof, offset=10.0, linear=1.0, quad=0.0)
    assert np.all(np.isnan(result))


# --- download_data ------------------------------------------------------------


def test_download_data_unknown_id(monkeypatch):
    import easydiffraction.utils.utils as MUT

    fake_index = {'struct-lbco': {'path': 'struct-lbco.cif', 'hash': None}}
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)
    with pytest.raises(KeyError, match="Unknown dataset 'struct-missing'"):
        MUT.download_data('struct-missing')


def test_download_data_already_exists_no_overwrite(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'meas-lbco-hrpt': {
            'path': 'meas-lbco-hrpt.xye',
            'hash': None,
            'description': 'Test data',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Create existing file (named after the dataset id, not the slug).
    (tmp_path / 'meas-lbco-hrpt.xye').write_text('existing data')

    result = MUT.download_data('meas-lbco-hrpt', destination=str(tmp_path), overwrite=False)
    assert result == str(tmp_path / 'meas-lbco-hrpt.xye')
    out = capsys.readouterr().out
    assert 'already present' in out
    assert (tmp_path / 'meas-lbco-hrpt.xye').read_text() == 'existing data'


def test_download_data_success(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'meas-lbco-hrpt': {
            'path': 'meas-lbco-hrpt.xye',
            'hash': None,
            'description': 'Test data',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Mock pooch.retrieve to create the file
    def fake_retrieve(url, known_hash, fname, path):
        import pathlib

        pathlib.Path(path, fname).write_text('x y e', encoding='utf-8')
        return str(pathlib.Path(path, fname))

    monkeypatch.setattr(MUT.pooch, 'retrieve', fake_retrieve)

    result = MUT.download_data('meas-lbco-hrpt', destination=str(tmp_path))
    assert result == str(tmp_path / 'meas-lbco-hrpt.xye')
    assert (tmp_path / 'meas-lbco-hrpt.xye').exists()
    out = capsys.readouterr().out
    assert 'downloaded' in out


def test_download_data_overwrite_existing(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'meas-lbco-hrpt': {
            'path': 'meas-lbco-hrpt.xye',
            'hash': None,
            'description': 'Test data',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Create existing file (named after the dataset id).
    (tmp_path / 'meas-lbco-hrpt.xye').write_text('old data')

    def fake_retrieve(url, known_hash, fname, path):
        import pathlib

        pathlib.Path(path, fname).write_text('new data', encoding='utf-8')
        return str(pathlib.Path(path, fname))

    monkeypatch.setattr(MUT.pooch, 'retrieve', fake_retrieve)

    result = MUT.download_data('meas-lbco-hrpt', destination=str(tmp_path), overwrite=True)
    assert result == str(tmp_path / 'meas-lbco-hrpt.xye')
    assert (tmp_path / 'meas-lbco-hrpt.xye').read_text() == 'new data'


def test_download_data_no_description(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'struct-lbco': {
            'path': 'struct-lbco.cif',
            'hash': 'sha256:...',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Create existing file so we hit the no-overwrite short-circuit
    (tmp_path / 'struct-lbco.cif').write_text('existing')

    result = MUT.download_data('struct-lbco', destination=str(tmp_path))
    assert result == str(tmp_path / 'struct-lbco.cif')
    out = capsys.readouterr().out
    assert "Data 'struct-lbco'" in out


def test_download_data_uses_tutorial_artifact_root_fallback(monkeypatch, tmp_path):
    import easydiffraction.utils.environment as env
    import easydiffraction.utils.utils as MUT

    repo_root = tmp_path / 'repo'
    tutorials_dir = repo_root / 'docs' / 'docs' / 'tutorials'
    tutorials_dir.mkdir(parents=True)

    fake_index = {
        'meas-lbco-hrpt': {
            'path': 'meas-lbco-hrpt.xye',
            'hash': None,
            'description': 'Test data',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)
    monkeypatch.setattr(env, '_repo_root', lambda: repo_root)
    monkeypatch.delenv('EASYDIFFRACTION_ARTIFACT_ROOT', raising=False)
    monkeypatch.delenv('PIXI_PROJECT_ROOT', raising=False)
    monkeypatch.chdir(tutorials_dir)

    def fake_retrieve(url, known_hash, fname, path):
        import pathlib

        pathlib.Path(path, fname).write_text('x y e', encoding='utf-8')
        return str(pathlib.Path(path, fname))

    monkeypatch.setattr(MUT.pooch, 'retrieve', fake_retrieve)

    result = MUT.download_data('meas-lbco-hrpt', destination='data')

    expected_path = repo_root / 'tmp' / 'tutorials' / 'data' / 'meas-lbco-hrpt.xye'
    assert result == str(expected_path)
    assert expected_path.exists()


# --- download_tutorial with overwrite=True ------------------------------------


def test_download_tutorial_overwrite(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'quick-start': {
            'url': 'https://example.com/{version}/tutorials/quick-start.ipynb',
            'title': 'Quick Start',
        },
    }
    monkeypatch.setattr(MUT, '_fetch_tutorials_index', lambda: fake_index)
    monkeypatch.setattr(MUT, '_get_version_for_url', lambda: '0.8.0')

    # Create existing file
    (tmp_path / 'quick-start.ipynb').write_text('old content')

    class DummyResp:
        def read(self):
            return b'{"cells": ["new"]}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(MUT, '_safe_urlopen', lambda url: DummyResp())

    result = MUT.download_tutorial('quick-start', destination=str(tmp_path), overwrite=True)
    assert result == str(tmp_path / 'quick-start.ipynb')
    assert 'new' in (tmp_path / 'quick-start.ipynb').read_text()


# --- display_path -------------------------------------------------------------


def test_display_path_relative_to_cwd(monkeypatch, tmp_path):
    import pathlib

    import easydiffraction.utils.utils as MUT

    monkeypatch.chdir(tmp_path)
    target = tmp_path / 'sub' / 'data.cif'
    result = MUT.display_path(target)
    # Path inside cwd is shown relative, not absolute.
    assert result == str(pathlib.Path('sub') / 'data.cif')


def test_display_path_uses_walk_up_for_sibling(monkeypatch, tmp_path):
    import easydiffraction.utils.utils as MUT

    cwd = tmp_path / 'project'
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    sibling = tmp_path / 'sibling' / 'data.cif'
    result = MUT.display_path(sibling)
    # Sibling outside cwd subtree walks up with '..' instead of absolute.
    assert result.startswith('..')
    assert result.endswith('data.cif')


def test_display_path_falls_back_to_absolute(monkeypatch, tmp_path):
    import pathlib

    import easydiffraction.utils.utils as MUT

    target = tmp_path / 'elsewhere' / 'data.cif'
    resolved_target = target.resolve()
    original_relative_to = pathlib.Path.relative_to

    def fake_relative_to(self, *args, **kwargs):
        # Simulate a path with no relative form (e.g. a different Windows
        # drive) only for the path under test; delegate every other call so
        # pytest's own use of Path.relative_to (result reporting) still works.
        if self == resolved_target:
            msg = 'on a different drive'
            raise ValueError(msg)
        return original_relative_to(self, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, 'relative_to', fake_relative_to)
    result = MUT.display_path(target)
    # With no relative form the absolute resolved path is returned.
    assert result == str(resolved_target)


# --- print_metrics_table ------------------------------------------------------


def test_print_metrics_table_empty_rows_renders_nothing(monkeypatch):
    import easydiffraction.utils.utils as MUT

    called = []
    monkeypatch.setattr(MUT, 'render_table', lambda **kwargs: called.append(kwargs))
    MUT.print_metrics_table([])
    # Empty rows short-circuit before any rendering.
    assert called == []


def test_print_metrics_table_renders_two_columns(monkeypatch):
    import easydiffraction.utils.utils as MUT

    captured = {}
    monkeypatch.setattr(MUT, 'render_table', lambda **kwargs: captured.update(kwargs))
    MUT.print_metrics_table([['Chi2', '1.23'], ['Points', '500']])
    assert captured['columns_headers'] == ['Metric', 'Value']
    assert captured['columns_alignment'] == ['left', 'right']
    assert captured['columns_data'] == [['Chi2', '1.23'], ['Points', '500']]


# --- print_table_footnote -----------------------------------------------------


def test_print_table_footnote_empty_entries_does_nothing(monkeypatch):
    import easydiffraction.utils.utils as MUT

    called = []
    monkeypatch.setattr(MUT.console, 'small', lambda *lines: called.extend(lines))
    MUT.print_table_footnote([])
    assert called == []


def test_print_table_footnote_aligns_bullets(monkeypatch):
    import easydiffraction.utils.utils as MUT

    captured = []
    monkeypatch.setattr(MUT.console, 'small', lambda *lines: captured.extend(lines))
    MUT.print_table_footnote([('Rwp', 'weighted profile'), ('GoF', 'goodness of fit')])
    assert len(captured) == 2
    assert '• Rwp' in captured[0]
    assert '= weighted profile' in captured[0]
    assert '= goodness of fit' in captured[1]
    # Width is padded to the longest header (3) + 4 -> '=' aligns across rows.
    assert captured[0].index('=') == captured[1].index('=')


# --- format_bulleted_warning empty items --------------------------------------


def test_format_bulleted_warning_no_items_returns_header():
    import easydiffraction.utils.utils as MUT

    result = MUT.format_bulleted_warning('Just a header', [])
    assert result == 'Just a header'


# --- _fetch_data_index --------------------------------------------------------


def test_fetch_data_index_reads_cached_json(monkeypatch, tmp_path):
    import json

    import easydiffraction.utils.utils as MUT

    index_file = tmp_path / 'data-index.json'
    index_file.write_text(json.dumps({'1': {'path': 'a.xye'}}), encoding='utf-8')

    monkeypatch.setattr(MUT.pooch, 'os_cache', lambda name: tmp_path)
    monkeypatch.setattr(
        MUT.pooch,
        'retrieve',
        lambda url, known_hash, fname, path, progressbar: str(index_file),
    )

    result = MUT._fetch_data_index()
    assert result == {'1': {'path': 'a.xye'}}


# --- _existing_project_dir ----------------------------------------------------


def test_existing_project_dir_none_when_no_project(tmp_path):
    import easydiffraction.utils.utils as MUT

    assert MUT._existing_project_dir(tmp_path) is None


def test_existing_project_dir_returns_parent(tmp_path):
    import easydiffraction.utils.utils as MUT

    project_dir = tmp_path / 'myproject'
    project_dir.mkdir()
    (project_dir / 'project.edi').write_text('data_block')
    result = MUT._existing_project_dir(tmp_path)
    assert result == project_dir.resolve()


# --- list_data ----------------------------------------------------------------


def test_list_data_empty_index(monkeypatch, capsys):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, '_fetch_data_index', dict)
    MUT.list_data()
    out = capsys.readouterr().out
    assert 'No datasets available' in out


def test_list_data_renders_rows(monkeypatch):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'struct-lbco': {'path': 'struct-lbco.cif', 'description': 'Structure'},
        'meas-lbco-hrpt': {'path': 'meas-lbco-hrpt.xye', 'description': 'Pattern'},
        'expt-lbco-hrpt': {'path': 'expt-lbco-hrpt.cif'},
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    captured = {}
    monkeypatch.setattr(MUT, 'render_table', lambda **kwargs: captured.update(kwargs))
    MUT.list_data()

    # Columns are the dataset name, the file format (bare extension), and
    # the description; the renderer adds its own row number, and the
    # removed 'kind'/'#' columns are no longer present.
    assert captured['columns_headers'] == ['name', 'format', 'description']

    rows = captured['columns_data']
    # Names sort alphabetically: expt-…, meas-…, struct-….
    assert [row[0] for row in rows] == [
        'expt-lbco-hrpt',
        'meas-lbco-hrpt',
        'struct-lbco',
    ]
    # Format column is the record-path extension without the leading dot.
    assert rows[2][1] == 'cif'
    # Missing description defaults to an empty string.
    assert rows[0][2] == ''


# --- download_data project-archive branches -----------------------------------


def test_download_data_project_archive_already_extracted(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'proj-lbco-hrpt': {
            'path': 'proj-lbco-hrpt.zip',
            'hash': None,
            'description': 'Project archive',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Pre-create an extracted project directory matching the fname stem.
    # With no record hash the extraction dir is the bare id stem (no tag).
    extraction_dir = tmp_path / 'proj-lbco-hrpt'
    project_dir = extraction_dir / 'inner'
    project_dir.mkdir(parents=True)
    (project_dir / 'project.edi').write_text('data_block')

    result = MUT.download_data('proj-lbco-hrpt', destination=str(tmp_path))
    assert result == str(project_dir.resolve())
    out = capsys.readouterr().out
    assert 'already extracted' in out


def test_download_data_project_archive_zip_present_extracts(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'proj-lbco-hrpt': {
            'path': 'proj-lbco-hrpt.zip',
            'hash': None,
            'description': 'Project archive',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # The zip file exists but no extraction dir yet.
    zip_path = tmp_path / 'proj-lbco-hrpt.zip'
    zip_path.write_text('zip bytes')

    extracted = tmp_path / 'proj-lbco-hrpt' / 'project'
    extracted.mkdir(parents=True)

    def fake_extract(file_path, destination):
        assert str(file_path) == str(zip_path)
        return extracted

    monkeypatch.setattr(MUT, 'extract_project_from_zip', fake_extract)

    result = MUT.download_data('proj-lbco-hrpt', destination=str(tmp_path))
    assert result == str(extracted)
    # The zip is removed after extraction.
    assert not zip_path.exists()
    out = capsys.readouterr().out
    assert 'extracted to' in out


def test_download_data_project_archive_downloads_and_extracts(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'proj-lbco-hrpt': {
            'path': 'proj-lbco-hrpt.zip',
            'hash': None,
            'description': 'Project archive',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    zip_path = tmp_path / 'proj-lbco-hrpt.zip'

    def fake_retrieve(url, known_hash, fname, path):
        import pathlib

        target = pathlib.Path(path, fname)
        target.write_text('zip bytes', encoding='utf-8')
        return str(target)

    monkeypatch.setattr(MUT.pooch, 'retrieve', fake_retrieve)

    extracted = tmp_path / 'proj-lbco-hrpt' / 'project'
    extracted.mkdir(parents=True)

    def fake_extract(file_path, destination):
        return extracted

    monkeypatch.setattr(MUT, 'extract_project_from_zip', fake_extract)

    result = MUT.download_data('proj-lbco-hrpt', destination=str(tmp_path))
    assert result == str(extracted)
    # Downloaded zip is cleaned up after extraction.
    assert not zip_path.exists()
    out = capsys.readouterr().out
    assert 'downloaded and extracted' in out


def test_download_data_overwrite_logs_debug_and_redownloads(monkeypatch, tmp_path):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'meas-lbco-hrpt': {
            'path': 'meas-lbco-hrpt.xye',
            'hash': None,
            'description': 'Test data',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    existing = tmp_path / 'meas-lbco-hrpt.xye'
    existing.write_text('old')

    debug_messages = []
    monkeypatch.setattr(MUT.log, 'debug', lambda msg, *a, **k: debug_messages.append(msg))

    def fake_retrieve(url, known_hash, fname, path):
        import pathlib

        pathlib.Path(path, fname).write_text('fresh', encoding='utf-8')
        return str(pathlib.Path(path, fname))

    monkeypatch.setattr(MUT.pooch, 'retrieve', fake_retrieve)

    result = MUT.download_data('meas-lbco-hrpt', destination=str(tmp_path), overwrite=True)
    assert result == str(existing)
    assert existing.read_text() == 'fresh'
    # The overwrite path emits a debug log before unlinking.
    assert any('will be overwritten' in m for m in debug_messages)


def test_download_data_project_archive_overwrite_removes_extraction(monkeypatch, tmp_path):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'proj-lbco-hrpt': {
            'path': 'proj-lbco-hrpt.zip',
            'hash': None,
            'description': 'Project archive',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Pre-existing extraction dir that should be wiped on overwrite.
    extraction_dir = tmp_path / 'proj-lbco-hrpt'
    stale = extraction_dir / 'stale'
    stale.mkdir(parents=True)
    (stale / 'old.cif').write_text('old')

    def fake_retrieve(url, known_hash, fname, path):
        import pathlib

        pathlib.Path(path, fname).write_text('zip bytes', encoding='utf-8')
        return str(pathlib.Path(path, fname))

    monkeypatch.setattr(MUT.pooch, 'retrieve', fake_retrieve)

    extracted = tmp_path / 'proj-lbco-hrpt' / 'project'

    def fake_extract(file_path, destination):
        extracted.mkdir(parents=True, exist_ok=True)
        return extracted

    monkeypatch.setattr(MUT, 'extract_project_from_zip', fake_extract)

    result = MUT.download_data('proj-lbco-hrpt', destination=str(tmp_path), overwrite=True)
    assert result == str(extracted)
    # The stale extracted content was removed before re-extraction.
    assert not (extraction_dir / 'stale').exists()


# --- list_tutorials markup branch ---------------------------------------------


def test_list_tutorials_terminal_markup_branch(monkeypatch):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'quick-start': {
            'url': 'https://example.com/{version}/tutorials/quick-start.ipynb',
            'title': 'Quick Start',
            'description': 'A quick start tutorial',
        },
        'no-description': {
            'url': 'https://example.com/{version}/tutorials/no-description.ipynb',
            'title': 'No Description',
        },
    }
    monkeypatch.setattr(MUT, '_fetch_tutorials_index', lambda: fake_index)
    monkeypatch.setattr(MUT, '_get_version_for_url', lambda: '0.8.0')
    # Force terminal (non-Jupyter) so the Rich-markup branch runs.
    monkeypatch.setattr(MUT, 'in_jupyter', lambda: False)

    captured = {}
    monkeypatch.setattr(MUT, 'render_table', lambda **kwargs: captured.update(kwargs))
    MUT.list_tutorials()

    # One column; each cell stacks name / title / (dimmed) description.
    assert captured['columns_headers'] == ['tutorial']
    cells = [row[0] for row in captured['columns_data']]
    quick = next(c for c in cells if c.startswith('quick-start'))
    nodesc = next(c for c in cells if c.startswith('no-description'))
    # First line is the name in default color (no markup).
    assert quick.splitlines()[0] == 'quick-start'
    assert 'Quick Start' in quick
    assert '[dim]' in quick  # description rendered dim
    # Row without a description has only name + styled title (no [dim]).
    assert nodesc.splitlines()[0] == 'no-description'
    assert 'No Description' in nodesc
    assert '[dim]' not in nodesc


def test_list_tutorials_jupyter_plain_title_branch(monkeypatch):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'quick-start': {
            'url': 'https://example.com/{version}/tutorials/quick-start.ipynb',
            'title': 'Quick Start',
            'description': 'A quick start tutorial',
        },
    }
    monkeypatch.setattr(MUT, '_fetch_tutorials_index', lambda: fake_index)
    monkeypatch.setattr(MUT, '_get_version_for_url', lambda: '0.8.0')
    # Force Jupyter so the plain-title branch runs.
    monkeypatch.setattr(MUT, 'in_jupyter', lambda: True)

    captured = {}
    monkeypatch.setattr(MUT, 'render_table', lambda **kwargs: captured.update(kwargs))
    MUT.list_tutorials()

    # Jupyter cell uses plain lines: name, title, description (no markup).
    cell = captured['columns_data'][0][0]
    lines = cell.split('\n')
    assert lines[0] == 'quick-start'
    assert lines[1] == 'Quick Start'
    assert lines[2] == 'A quick start tutorial'
    assert '[dim]' not in cell


# --- download_tutorial title-less message branch ------------------------------


def test_download_tutorial_no_title_message(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'quick-start': {'url': 'https://example.com/{version}/tutorials/quick-start.ipynb'},
    }
    monkeypatch.setattr(MUT, '_fetch_tutorials_index', lambda: fake_index)
    monkeypatch.setattr(MUT, '_get_version_for_url', lambda: '0.8.0')

    class DummyResp:
        def read(self):
            return b'{"cells": []}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(MUT, '_safe_urlopen', lambda url: DummyResp())

    result = MUT.download_tutorial('quick-start', destination=str(tmp_path))
    assert result == str(tmp_path / 'quick-start.ipynb')
    out = capsys.readouterr().out
    # Without a title the message is just "Tutorial 'quick-start'" (no ': <title>').
    assert "Tutorial 'quick-start'" in out


# --- download_all_tutorials error handling ------------------------------------


def test_download_all_tutorials_logs_failure_and_continues(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'good-tutorial': {
            'url': 'https://example.com/{version}/tutorials/good-tutorial.ipynb',
            'title': 'Good',
        },
        'zzz-bad-tutorial': {
            'url': 'https://example.com/{version}/tutorials/zzz-bad-tutorial.ipynb',
            'title': 'Bad',
        },
    }
    monkeypatch.setattr(MUT, '_fetch_tutorials_index', lambda: fake_index)
    monkeypatch.setattr(MUT, '_get_version_for_url', lambda: '0.8.0')

    def flaky_download(name, destination, overwrite):
        if name == 'zzz-bad-tutorial':
            msg = 'boom'
            raise OSError(msg)
        return str(tmp_path / f'{name}.ipynb')

    monkeypatch.setattr(MUT, 'download_tutorial', flaky_download)

    warnings = []
    monkeypatch.setattr(MUT.log, 'warning', lambda msg, *a, **k: warnings.append(msg))

    result = MUT.download_all_tutorials(destination=str(tmp_path))
    # The failing tutorial is skipped; the good one is returned.
    assert result == [str(tmp_path / 'good-tutorial.ipynb')]
    assert any("Failed to download tutorial 'zzz-bad-tutorial'" in m for m in warnings)


# --- build_table_renderable ---------------------------------------------------


def test_build_table_renderable_returns_renderable():
    import easydiffraction.utils.utils as MUT

    renderable = MUT.build_table_renderable(
        columns_data=[['a', 'b'], ['c', 'd']],
        columns_alignment=['left', 'right'],
        columns_headers=['One', 'Two'],
    )
    # A backend-native renderable object is returned (not None).
    assert renderable is not None


# --- _help_first_sentence -----------------------------------------------------


def test_help_first_sentence_empty_docstring_returns_empty():
    import easydiffraction.utils.utils as MUT

    assert MUT._help_first_sentence(None) == ''
    assert MUT._help_first_sentence('') == ''


def test_help_first_sentence_collapses_first_paragraph():
    import easydiffraction.utils.utils as MUT

    doc = '  First line\n  second line\n\n  Second paragraph.'
    result = MUT._help_first_sentence(doc)
    assert result == 'First line second line'


# --- _help_property_rows / _help_method_rows ----------------------------------


def test_help_property_rows_marks_writable_and_skips_private():
    import easydiffraction.utils.utils as MUT

    class Example:
        @property
        def read_only(self):
            """A read-only prop."""
            return 1

        @property
        def editable(self):
            """An editable prop."""
            return 2

        @editable.setter
        def editable(self, value):
            self._editable = value

        @property
        def _hidden(self):
            """Hidden."""
            return 3

    rows = MUT._help_property_rows(Example)
    by_name = {row[0]: row for row in rows}
    assert '_hidden' not in by_name
    # Writable column is a check mark only when a setter exists.
    assert by_name['editable'][1] == '✓'
    assert by_name['read_only'][1] == ''
    assert by_name['read_only'][2] == 'A read-only prop.'


def test_help_method_rows_handles_static_and_classmethods():
    import easydiffraction.utils.utils as MUT

    class Example:
        def instance_method(self):
            """Instance docs."""

        @staticmethod
        def static_method():
            """Static docs."""

        @classmethod
        def class_method(cls):
            """Class docs."""

        not_callable = 42

        def _private(self):
            """Hidden."""

    rows = MUT._help_method_rows(Example)
    names = {row[0] for row in rows}
    assert 'instance_method()' in names
    assert 'static_method()' in names
    assert 'class_method()' in names
    # Private methods and non-callable attributes are excluded.
    assert '_private()' not in names
    assert 'not_callable()' not in names
    docs = {row[0]: row[1] for row in rows}
    assert docs['static_method()'] == 'Static docs.'


# --- render_object_help empty branches ----------------------------------------


def test_render_object_help_no_public_api_renders_nothing(monkeypatch, capsys):
    import easydiffraction.utils.utils as MUT

    class Empty:
        def _hidden(self):
            """Hidden."""

    calls = []
    monkeypatch.setattr(MUT, 'render_table', lambda **kwargs: calls.append(kwargs))
    MUT.render_object_help(Empty())
    out = capsys.readouterr().out
    # No public properties or methods -> no tables, no headings.
    assert calls == []
    assert 'Properties' not in out
    assert 'Methods' not in out


def test_render_object_help_methods_only(monkeypatch):
    import easydiffraction.utils.utils as MUT

    class MethodsOnly:
        def run(self):
            """Run it."""

    headings = []

    def record(text):
        headings.append(text)

    monkeypatch.setattr(MUT.console, 'paragraph', record)
    monkeypatch.setattr(MUT, 'render_table', lambda **kwargs: None)
    MUT.render_object_help(MethodsOnly())
    # Only the Methods section renders when there are no public properties.
    assert headings == ['Methods']


def test_render_object_help_properties_only(monkeypatch):
    import easydiffraction.utils.utils as MUT

    class PropsOnly:
        @property
        def value(self):
            """A value."""
            return 1

    headings = []

    def record(text):
        headings.append(text)

    monkeypatch.setattr(MUT.console, 'paragraph', record)
    monkeypatch.setattr(MUT, 'render_table', lambda **kwargs: None)
    MUT.render_object_help(PropsOnly())
    # Only the Properties section renders when there are no public methods.
    assert headings == ['Properties']


# --- name validation, resolution, and ref pinning ----------------------------


@pytest.mark.parametrize(
    'name',
    ['struct-lbco', 'meas-lbco-hrpt', 'proj-lbco-hrpt', 'expt-lbco-hrpt'],
)
def test_validate_dataset_id_accepts_valid_names(name):
    import easydiffraction.utils.utils as MUT

    MUT._validate_dataset_id(name)  # must not raise


@pytest.mark.parametrize(
    'name',
    [
        'struct-LBCO',  # uppercase
        'expt-lbco-hrpt.edi',  # extension in name
        'nope-lbco',  # unknown category prefix
        'lbco',  # missing category prefix
        'meas/lbco',  # path form with slash
        'meas--lbco',  # doubled dash
        'meas-',  # empty name after prefix
    ],
)
def test_validate_dataset_id_rejects_invalid_names(name):
    import easydiffraction.utils.utils as MUT

    with pytest.raises(ValueError, match='Invalid'):
        MUT._validate_dataset_id(name)


def test_validate_tutorial_id_rejects_slash():
    import easydiffraction.utils.utils as MUT

    MUT._validate_tutorial_id('refine-lbco-hrpt-from-cif')  # must not raise
    with pytest.raises(ValueError, match='Invalid tutorial name'):
        MUT._validate_tutorial_id('meas/lbco')


def test_is_project_id_only_projects_namespace():
    import easydiffraction.utils.utils as MUT

    assert MUT._is_project_id('proj-lbco-hrpt') is True
    assert MUT._is_project_id('meas-lbco-hrpt') is False


def test_resolve_positional_one_based_against_listing_order():
    import easydiffraction.utils.utils as MUT

    keys = ['struct-lbco', 'meas-lbco-hrpt', 'proj-lbco-hrpt']
    assert MUT._resolve_positional(1, keys, kind='dataset') == 'struct-lbco'
    assert MUT._resolve_positional(3, keys, kind='dataset') == 'proj-lbco-hrpt'
    with pytest.raises(IndexError):
        MUT._resolve_positional(0, keys, kind='dataset')
    with pytest.raises(IndexError):
        MUT._resolve_positional(4, keys, kind='dataset')


def test_data_index_ref_rejects_malformed(monkeypatch):
    import easydiffraction.utils.utils as MUT

    class _Res:
        def __init__(self, text):
            self._text = text

        def joinpath(self, _name):
            return self

        def read_text(self, encoding='utf-8'):
            return self._text

    MUT._data_index_ref.cache_clear()
    monkeypatch.setattr(MUT.importlib.resources, 'files', lambda _pkg: _Res('not-a-sha'))
    with pytest.raises(ValueError, match='Invalid data index ref'):
        MUT._data_index_ref()
    MUT._data_index_ref.cache_clear()


def test_data_index_ref_accepts_full_sha(monkeypatch):
    import easydiffraction.utils.utils as MUT

    sha = 'a' * 40

    class _Res:
        def joinpath(self, _name):
            return self

        def read_text(self, encoding='utf-8'):
            return sha + '\n'

    MUT._data_index_ref.cache_clear()
    monkeypatch.setattr(MUT.importlib.resources, 'files', lambda _pkg: _Res())
    assert MUT._data_index_ref() == sha
    MUT._data_index_ref.cache_clear()


def test_download_data_project_archive_stale_zip_revalidated(monkeypatch, tmp_path):
    """A stale local project ZIP is re-downloaded, never extracted as-is."""
    import pathlib

    import easydiffraction.utils.utils as MUT

    fake_index = {
        'proj-lbco-hrpt': {
            'path': 'proj-lbco-hrpt.zip',
            'hash': 'sha256:' + 'a' * 64,  # will not match the stale local zip
            'description': 'Project archive',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # A stale project ZIP from an older pinned commit is already present.
    zip_path = tmp_path / 'proj-lbco-hrpt.zip'
    zip_path.write_text('stale zip bytes')

    calls = {'retrieve': 0}

    def fake_retrieve(url, known_hash, fname, path):
        calls['retrieve'] += 1
        target = pathlib.Path(path, fname)
        target.write_text('fresh zip bytes', encoding='utf-8')
        return str(target)

    monkeypatch.setattr(MUT.pooch, 'retrieve', fake_retrieve)

    extracted = tmp_path / 'fresh' / 'project'
    extracted.mkdir(parents=True)
    seen = {}

    def fake_extract(file_path, destination):
        seen['bytes'] = pathlib.Path(file_path).read_text(encoding='utf-8')
        return extracted

    monkeypatch.setattr(MUT, 'extract_project_from_zip', fake_extract)

    result = MUT.download_data('proj-lbco-hrpt', destination=str(tmp_path))
    assert result == str(extracted)
    # The stale ZIP was re-downloaded before extraction, not served as-is.
    assert calls['retrieve'] == 1
    assert seen['bytes'] == 'fresh zip bytes'


def test_ordered_keys_honors_explicit_order_field():
    """Records with an `order` field sort by it; others stay alphabetical."""
    import easydiffraction.utils.utils as MUT

    tutorials = {
        'zzz-intro': {'order': 1, 'title': 'Intro'},
        'aaa-advanced': {'order': 2, 'title': 'Advanced'},
    }
    # Learning order wins over lexicographic slug order.
    assert MUT._ordered_keys(tutorials) == ['zzz-intro', 'aaa-advanced']

    datasets = {
        'struct-lbco': {'path': 'struct-lbco.cif'},
        'meas-lbco-hrpt': {'path': 'meas-lbco-hrpt.xye'},
    }
    # No order field -> alphabetical by slug.
    assert MUT._ordered_keys(datasets) == ['meas-lbco-hrpt', 'struct-lbco']


def test_resolve_tutorial_positional_follows_learning_order(monkeypatch):
    """Row number 1 resolves to the first learning-order tutorial."""
    import easydiffraction.utils.utils as MUT

    index = {
        'second': {'order': 2, 'title': 'Second'},
        'first': {'order': 1, 'title': 'First'},
    }
    monkeypatch.setattr(MUT, '_fetch_tutorials_index', lambda: index)
    assert MUT._resolve_tutorial_id(1, index) == 'first'
    assert MUT._resolve_tutorial_id(2, index) == 'second'

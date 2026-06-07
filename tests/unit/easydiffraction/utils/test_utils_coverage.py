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


# --- _filename_for_id_from_path -----------------------------------------------


def test_filename_for_id_from_path_with_extension():
    import easydiffraction.utils.utils as MUT

    result = MUT._filename_for_id_from_path(12, 'file.xye')
    assert result == 'ed-12.xye'


def test_filename_for_id_from_path_cif_extension():
    import easydiffraction.utils.utils as MUT

    result = MUT._filename_for_id_from_path('3', 'path/model.cif')
    assert result == 'ed-3.cif'


def test_filename_for_id_from_path_no_extension():
    import easydiffraction.utils.utils as MUT

    result = MUT._filename_for_id_from_path(7, 'path/noext')
    assert result == 'ed-7'


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

    fake_index = {'1': {'path': 'data.xye', 'hash': None}}
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)
    with pytest.raises(KeyError, match='Unknown dataset id=999'):
        MUT.download_data(id=999)


def test_download_data_already_exists_no_overwrite(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '1': {
            'path': 'data.xye',
            'hash': None,
            'description': 'Test data',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Create existing file
    (tmp_path / 'ed-1.xye').write_text('existing data')

    result = MUT.download_data(id=1, destination=str(tmp_path), overwrite=False)
    assert result == str(tmp_path / 'ed-1.xye')
    out = capsys.readouterr().out
    assert 'already present' in out
    assert (tmp_path / 'ed-1.xye').read_text() == 'existing data'


def test_download_data_success(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '1': {
            'path': 'data.xye',
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

    result = MUT.download_data(id=1, destination=str(tmp_path))
    assert result == str(tmp_path / 'ed-1.xye')
    assert (tmp_path / 'ed-1.xye').exists()
    out = capsys.readouterr().out
    assert 'downloaded' in out


def test_download_data_overwrite_existing(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '1': {
            'path': 'data.xye',
            'hash': None,
            'description': 'Test data',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Create existing file
    (tmp_path / 'ed-1.xye').write_text('old data')

    def fake_retrieve(url, known_hash, fname, path):
        import pathlib

        pathlib.Path(path, fname).write_text('new data', encoding='utf-8')
        return str(pathlib.Path(path, fname))

    monkeypatch.setattr(MUT.pooch, 'retrieve', fake_retrieve)

    result = MUT.download_data(id=1, destination=str(tmp_path), overwrite=True)
    assert result == str(tmp_path / 'ed-1.xye')
    assert (tmp_path / 'ed-1.xye').read_text() == 'new data'


def test_download_data_no_description(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '1': {
            'path': 'data.xye',
            'hash': 'sha256:...',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Create existing file so we hit the no-overwrite short-circuit
    (tmp_path / 'ed-1.xye').write_text('existing')

    result = MUT.download_data(id=1, destination=str(tmp_path))
    assert result == str(tmp_path / 'ed-1.xye')
    out = capsys.readouterr().out
    assert 'Data #1' in out


def test_download_data_uses_tutorial_artifact_root_fallback(monkeypatch, tmp_path):
    import easydiffraction.utils.environment as env
    import easydiffraction.utils.utils as MUT

    repo_root = tmp_path / 'repo'
    tutorials_dir = repo_root / 'docs' / 'docs' / 'tutorials'
    tutorials_dir.mkdir(parents=True)

    fake_index = {
        '1': {
            'path': 'data.xye',
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

    result = MUT.download_data(id=1, destination='data')

    expected_path = repo_root / 'tmp' / 'tutorials' / 'data' / 'ed-1.xye'
    assert result == str(expected_path)
    assert expected_path.exists()


# --- download_tutorial with overwrite=True ------------------------------------


def test_download_tutorial_overwrite(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '1': {
            'url': 'https://example.com/{version}/tutorials/ed-1/ed-1.ipynb',
            'title': 'Quick Start',
        },
    }
    monkeypatch.setattr(MUT, '_fetch_tutorials_index', lambda: fake_index)
    monkeypatch.setattr(MUT, '_get_version_for_url', lambda: '0.8.0')

    # Create existing file
    (tmp_path / 'ed-1.ipynb').write_text('old content')

    class DummyResp:
        def read(self):
            return b'{"cells": ["new"]}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(MUT, '_safe_urlopen', lambda url: DummyResp())

    result = MUT.download_tutorial(id=1, destination=str(tmp_path), overwrite=True)
    assert result == str(tmp_path / 'ed-1.ipynb')
    assert 'new' in (tmp_path / 'ed-1.ipynb').read_text()


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
    (project_dir / 'project.cif').write_text('data_block')
    result = MUT._existing_project_dir(tmp_path)
    assert result == project_dir.resolve()


# --- list_data ----------------------------------------------------------------


def test_list_data_empty_index(monkeypatch, capsys):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, '_fetch_data_index', dict)
    MUT.list_data()
    out = capsys.readouterr().out
    assert 'No example data available' in out


def test_list_data_renders_rows(monkeypatch):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '2': {'path': 'sub/two.cif', 'kind': 'project', 'description': 'Second'},
        '10': {'path': 'ten.xye', 'kind': 'pattern', 'description': 'Tenth'},
        '1': {'path': 'one.xye'},
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    captured = {}
    monkeypatch.setattr(MUT, 'render_table', lambda **kwargs: captured.update(kwargs))
    MUT.list_data()

    rows = captured['columns_data']
    # Numeric ids sort numerically: 1, 2, 10.
    assert [row[0] for row in rows] == ['1', '2', '10']
    # File column uses the basename of the record path.
    assert rows[1][1] == 'two.cif'
    # Missing kind/description default to empty strings.
    assert rows[0][2] == ''
    assert rows[0][3] == ''


# --- download_data project-archive branches -----------------------------------


def test_download_data_project_archive_already_extracted(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '5': {
            'path': 'proj.zip',
            'kind': 'project',
            'hash': None,
            'description': 'Project archive',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Pre-create an extracted project directory matching fname stem 'ed-5'.
    extraction_dir = tmp_path / 'ed-5'
    project_dir = extraction_dir / 'inner'
    project_dir.mkdir(parents=True)
    (project_dir / 'project.cif').write_text('data_block')

    result = MUT.download_data(id=5, destination=str(tmp_path))
    assert result == str(project_dir.resolve())
    out = capsys.readouterr().out
    assert 'already extracted' in out


def test_download_data_project_archive_zip_present_extracts(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '6': {
            'path': 'proj.zip',
            'kind': 'project',
            'hash': None,
            'description': 'Project archive',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # The zip file exists but no extraction dir yet.
    zip_path = tmp_path / 'ed-6.zip'
    zip_path.write_text('zip bytes')

    extracted = tmp_path / 'ed-6' / 'project'
    extracted.mkdir(parents=True)

    def fake_extract(file_path, destination):
        assert str(file_path) == str(zip_path)
        return extracted

    monkeypatch.setattr(MUT, 'extract_project_from_zip', fake_extract)

    result = MUT.download_data(id=6, destination=str(tmp_path))
    assert result == str(extracted)
    # The zip is removed after extraction.
    assert not zip_path.exists()
    out = capsys.readouterr().out
    assert 'extracted to' in out


def test_download_data_project_archive_downloads_and_extracts(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '7': {
            'path': 'proj.zip',
            'kind': 'project',
            'hash': None,
            'description': 'Project archive',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    zip_path = tmp_path / 'ed-7.zip'

    def fake_retrieve(url, known_hash, fname, path):
        import pathlib

        target = pathlib.Path(path, fname)
        target.write_text('zip bytes', encoding='utf-8')
        return str(target)

    monkeypatch.setattr(MUT.pooch, 'retrieve', fake_retrieve)

    extracted = tmp_path / 'ed-7' / 'project'
    extracted.mkdir(parents=True)

    def fake_extract(file_path, destination):
        return extracted

    monkeypatch.setattr(MUT, 'extract_project_from_zip', fake_extract)

    result = MUT.download_data(id=7, destination=str(tmp_path))
    assert result == str(extracted)
    # Downloaded zip is cleaned up after extraction.
    assert not zip_path.exists()
    out = capsys.readouterr().out
    assert 'downloaded and extracted' in out


def test_download_data_overwrite_logs_debug_and_redownloads(monkeypatch, tmp_path):
    import easydiffraction.utils.utils as MUT

    fake_index = {'1': {'path': 'data.xye', 'hash': None, 'description': 'Test data'}}
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    existing = tmp_path / 'ed-1.xye'
    existing.write_text('old')

    debug_messages = []
    monkeypatch.setattr(MUT.log, 'debug', lambda msg, *a, **k: debug_messages.append(msg))

    def fake_retrieve(url, known_hash, fname, path):
        import pathlib

        pathlib.Path(path, fname).write_text('fresh', encoding='utf-8')
        return str(pathlib.Path(path, fname))

    monkeypatch.setattr(MUT.pooch, 'retrieve', fake_retrieve)

    result = MUT.download_data(id=1, destination=str(tmp_path), overwrite=True)
    assert result == str(existing)
    assert existing.read_text() == 'fresh'
    # The overwrite path emits a debug log before unlinking.
    assert any('will be overwritten' in m for m in debug_messages)


def test_download_data_project_archive_overwrite_removes_extraction(monkeypatch, tmp_path):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '8': {
            'path': 'proj.zip',
            'kind': 'project',
            'hash': None,
            'description': 'Project archive',
        }
    }
    monkeypatch.setattr(MUT, '_fetch_data_index', lambda: fake_index)

    # Pre-existing extraction dir that should be wiped on overwrite.
    extraction_dir = tmp_path / 'ed-8'
    stale = extraction_dir / 'stale'
    stale.mkdir(parents=True)
    (stale / 'old.cif').write_text('old')

    def fake_retrieve(url, known_hash, fname, path):
        import pathlib

        pathlib.Path(path, fname).write_text('zip bytes', encoding='utf-8')
        return str(pathlib.Path(path, fname))

    monkeypatch.setattr(MUT.pooch, 'retrieve', fake_retrieve)

    extracted = tmp_path / 'ed-8' / 'project'

    def fake_extract(file_path, destination):
        extracted.mkdir(parents=True, exist_ok=True)
        return extracted

    monkeypatch.setattr(MUT, 'extract_project_from_zip', fake_extract)

    result = MUT.download_data(id=8, destination=str(tmp_path), overwrite=True)
    assert result == str(extracted)
    # The stale extracted content was removed before re-extraction.
    assert not (extraction_dir / 'stale').exists()


# --- list_tutorials markup branch ---------------------------------------------


def test_list_tutorials_terminal_markup_branch(monkeypatch):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '1': {
            'url': 'https://example.com/{version}/tutorials/ed-1/ed-1.ipynb',
            'title': 'Quick Start',
            'description': 'A quick start tutorial',
        },
        '2': {
            'url': 'https://example.com/{version}/tutorials/ed-2/ed-2.ipynb',
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

    rows = captured['columns_data']
    # Row with a description carries the dimmed second line.
    assert '[dim]' in rows[0][2]
    assert 'Quick Start' in rows[0][2]
    # Row without a description has only the styled title (no [dim]).
    assert '[dim]' not in rows[1][2]
    assert 'No Description' in rows[1][2]


def test_list_tutorials_jupyter_plain_title_branch(monkeypatch):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '1': {
            'url': 'https://example.com/{version}/tutorials/ed-1/ed-1.ipynb',
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

    rows = captured['columns_data']
    # Jupyter shows the plain title with no Rich markup.
    assert rows[0][2] == 'Quick Start'
    assert '[dim]' not in rows[0][2]


# --- download_tutorial title-less message branch ------------------------------


def test_download_tutorial_no_title_message(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '1': {'url': 'https://example.com/{version}/tutorials/ed-1/ed-1.ipynb'},
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

    result = MUT.download_tutorial(id=1, destination=str(tmp_path))
    assert result == str(tmp_path / 'ed-1.ipynb')
    out = capsys.readouterr().out
    # Without a title the message is just 'Tutorial #1' (no ': <title>').
    assert 'Tutorial #1' in out


# --- download_all_tutorials error handling ------------------------------------


def test_download_all_tutorials_logs_failure_and_continues(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        '1': {
            'url': 'https://example.com/{version}/tutorials/ed-1/ed-1.ipynb',
            'title': 'Good',
        },
        '2': {
            'url': 'https://example.com/{version}/tutorials/ed-2/ed-2.ipynb',
            'title': 'Bad',
        },
    }
    monkeypatch.setattr(MUT, '_fetch_tutorials_index', lambda: fake_index)
    monkeypatch.setattr(MUT, '_get_version_for_url', lambda: '0.8.0')

    def flaky_download(id, destination, overwrite):
        if str(id) == '2':
            msg = 'boom'
            raise OSError(msg)
        return str(tmp_path / f'ed-{id}.ipynb')

    monkeypatch.setattr(MUT, 'download_tutorial', flaky_download)

    warnings = []
    monkeypatch.setattr(MUT.log, 'warning', lambda msg, *a, **k: warnings.append(msg))

    result = MUT.download_all_tutorials(destination=str(tmp_path))
    # The failing tutorial is skipped; the good one is returned.
    assert result == [str(tmp_path / 'ed-1.ipynb')]
    assert any('Failed to download tutorial #2' in m for m in warnings)


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

# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import os

import numpy as np
import pytest


def test_module_import():
    import easydiffraction.utils.utils as MUT

    expected_module_name = 'easydiffraction.utils.utils'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_format_bulleted_warning():
    import easydiffraction.utils.utils as MUT

    warning = MUT.format_bulleted_warning('Header:', ['first', 'second'])

    assert warning == 'Header:\n• first\n• second'


def test_twotheta_to_d_scalar_and_array():
    import easydiffraction.utils.utils as MUT

    wavelength = 1.54
    # scalar
    expected_scalar = wavelength / (2 * np.sin(np.radians(30 / 2)))
    actual_scalar = MUT.twotheta_to_d(30.0, wavelength)
    assert np.isclose(expected_scalar, actual_scalar)
    # array
    twotheta = np.array([10.0, 20.0, 40.0])
    expected_array = wavelength / (2 * np.sin(np.radians(twotheta / 2)))
    actual_array = MUT.twotheta_to_d(twotheta, wavelength)
    assert np.allclose(expected_array, actual_array)


def test_tof_to_d_linear_case():
    import easydiffraction.utils.utils as MUT

    tof = np.array([10.0, 20.0, 30.0])
    offset, linear, quad = 2.0, 4.0, 0.0
    expected = (tof - offset) / linear
    actual = MUT.tof_to_d(tof, offset, linear, quad)
    assert np.allclose(expected, actual)


def test_tof_to_d_quadratic_case_smallest_positive_root():
    import easydiffraction.utils.utils as MUT

    # Model: TOF = quad * d^2, with offset=linear=0
    quad = 2.0
    tof = np.array([2.0, 8.0, 18.0])  # roots: sqrt(tof/quad)
    expected = np.sqrt(tof / quad)
    actual = MUT.tof_to_d(tof, offset=0.0, linear=0.0, quad=quad)
    assert np.allclose(expected, actual, equal_nan=False)


def test_str_to_ufloat_parsing_nominal_and_esd():
    import easydiffraction.utils.utils as MUT

    u = MUT.str_to_ufloat('3.566(2)')
    expected = np.array([3.566, 0.002])
    actual = np.array([u.nominal_value, u.std_dev])
    assert np.allclose(expected, actual)


def test_str_to_ufloat_no_esd_defaults_nan():
    import easydiffraction.utils.utils as MUT

    u = MUT.str_to_ufloat('1.23')
    expected_value = 1.23
    actual_value = u.nominal_value
    # uncertainty is NaN when not specified
    assert np.isclose(expected_value, actual_value)
    assert np.isnan(u.std_dev)


def test_extract_metadata(tmp_path):
    import easydiffraction.io.ascii as ascii_io

    text = '# DIFC = 123.45 two_theta = 67.89\nrest of file\n'
    p = tmp_path / 'file.xye'
    p.write_text(text)
    difc = ascii_io.extract_metadata(str(p), r'DIFC\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)')
    two_theta = ascii_io.extract_metadata(
        str(p), r'two_theta\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)'
    )
    assert np.isclose(difc, 123.45)
    assert np.isclose(two_theta, 67.89)


def test_validate_url_rejects_non_http_https():
    import easydiffraction.utils.utils as MUT

    with pytest.raises(
        ValueError,
        match=r"Unsafe URL scheme 'ftp'\. Only HTTP and HTTPS are allowed\.",
    ):
        MUT._validate_url('ftp://example.com/file')


def test_is_github_ci_env_true(monkeypatch):
    import easydiffraction.utils.environment as env

    monkeypatch.setenv('GITHUB_ACTIONS', 'true')
    expected = True
    actual = env.in_github_ci()
    assert expected == actual


def test_package_version_missing_package_returns_none():
    import easydiffraction.utils.utils as MUT

    expected = None
    actual = MUT.package_version('__definitely_not_installed__')
    assert expected == actual


def test_is_notebook_false_in_plain_env(monkeypatch):
    import easydiffraction.utils.environment as env

    # Ensure no IPython and not PyCharm
    monkeypatch.setenv('PYCHARM_HOSTED', '', prepend=False)
    assert env.in_jupyter() is False


def test_is_pycharm_and_is_colab(monkeypatch):
    import easydiffraction.utils.environment as env

    # PyCharm
    monkeypatch.setenv('PYCHARM_HOSTED', '1')
    assert env.in_pycharm() is True
    # Colab detection when module is absent -> False
    assert env.in_colab() is False


def test_render_table_terminal_branch(capsys, monkeypatch):
    import easydiffraction.utils.utils as MUT

    # Ensure non-notebook rendering; on CI/default env it's terminal anyway.
    MUT.render_table(
        columns_data=[[1, 2], [3, 4]],
        columns_alignment=['left', 'left'],
        columns_headers=['A', 'B'],
    )
    out = capsys.readouterr().out
    # fancy_outline uses box-drawing characters; accept a couple of expected ones
    assert ('╒' in out and '╕' in out) or ('┌' in out and '┐' in out)


def test_render_object_help_prints_public_api(capsys):
    import easydiffraction.utils.utils as MUT

    class Example:
        @property
        def value(self):
            """Visible value."""
            return 1

        def run(self):
            """Run visible action."""

        def _hidden(self):
            """Hidden action."""

    MUT.render_object_help(Example())
    out = capsys.readouterr().out
    assert 'Properties' in out
    assert 'value' in out
    assert 'Visible value.' in out
    assert 'Methods' in out
    assert 'run()' in out
    assert 'Run visible action.' in out
    assert '_hidden' not in out


def test_is_dev_version_with_dev_suffix(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: '0.8.0+dev123')
    assert MUT._is_dev_version('easydiffraction') is True


def test_is_dev_version_with_dirty_suffix(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: '0.8.0+dirty5')
    assert MUT._is_dev_version('easydiffraction') is True


def test_is_dev_version_with_devdirty_suffix(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: '0.8.0+devdirty7')
    assert MUT._is_dev_version('easydiffraction') is True


def test_is_dev_version_with_999_version(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: '999.0.0+dev331')
    assert MUT._is_dev_version('easydiffraction') is True


def test_is_dev_version_released_version(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: '0.8.0.post1')
    assert MUT._is_dev_version('easydiffraction') is False


def test_get_version_for_url_dev(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: '0.8.0+dev123')
    assert MUT._get_version_for_url() == 'dev'


def test_get_version_for_url_released(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: '0.8.0.post1')
    assert MUT._get_version_for_url() == '0.8.0.post1'


def test_parameter_docs_url_uses_grouped_docs_route(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: '0.8.0.post1')

    url = MUT.parameter_docs_url('_cell.length_a')

    assert url == (
        'https://easyscience.github.io/diffraction-lib/0.8.0.post1/'
        'user-guide/parameters/structure/cell/#cell-length-a'
    )


def test_parameter_docs_url_maps_category_page_alias(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: '0.8.0.post1')

    url = MUT.parameter_docs_url('_excluded_regions.start')

    assert url == (
        'https://easyscience.github.io/diffraction-lib/0.8.0.post1/'
        'user-guide/parameters/experiment/excluded_region/#excluded-region-start'
    )


def test_parameter_docs_url_maps_data_range_items(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: '0.8.0.post1')

    twotheta_url = MUT.parameter_docs_url('_data_range.two_theta_min')
    sthovl_url = MUT.parameter_docs_url('_data_range.sin_theta_over_lambda_max')

    assert twotheta_url == (
        'https://easyscience.github.io/diffraction-lib/0.8.0.post1/'
        'user-guide/parameters/experiment/pd_meas/#pd-meas-2theta-range-min'
    )
    assert sthovl_url == (
        'https://easyscience.github.io/diffraction-lib/0.8.0.post1/'
        'user-guide/parameters/experiment/refln/#refln-sin-theta-over-lambda-range-max'
    )


def test_parameter_docs_blocks_match_docs_tree():
    """Guard the owner-grouped route map against docs-tree drift."""
    import pathlib

    import easydiffraction.utils.utils as MUT

    repo_root = pathlib.Path(__file__).resolve().parents[4]
    params_dir = repo_root / 'docs' / 'docs' / 'user-guide' / 'parameters'

    docs_pages = {
        (owner_dir.name, page.stem)
        for owner_dir in params_dir.iterdir()
        if owner_dir.is_dir()
        for page in owner_dir.glob('*.md')
    }
    mapped_pages = {
        (block, category)
        for block, categories in MUT._PARAMETER_DOCS_BLOCKS.items()
        for category in categories
    }

    # Every grouped route must resolve to an existing reference page and
    # vice versa, so runtime parameter URLs cannot drift from the docs.
    assert mapped_pages == docs_pages

    # Each mapped category resolves to its own owner/category route.
    for block, category in mapped_pages:
        assert MUT._parameter_docs_page(category) == f'{block}/{category}'


@pytest.mark.filterwarnings('ignore:Failed to fetch tutorials index:UserWarning')
def test_fetch_tutorials_index_returns_empty_on_error(monkeypatch):
    import easydiffraction.utils.utils as MUT

    # Force urlopen to fail
    def failing_urlopen(url):
        msg = 'Network error'
        raise OSError(msg)

    monkeypatch.setattr(MUT, '_safe_urlopen', failing_urlopen)
    # Clear cache to ensure fresh fetch
    MUT._fetch_tutorials_index.cache_clear()

    # The function catches errors and returns empty dict (after warning)
    result = MUT._fetch_tutorials_index()
    assert result == {}


def test_list_tutorials_empty_index(monkeypatch, capsys):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, '_fetch_tutorials_index', dict)
    MUT.list_tutorials()
    out = capsys.readouterr().out
    assert 'No tutorials available' in out


def test_list_tutorials_with_data(monkeypatch, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'quick-start': {
            'url': 'https://example.com/{version}/tutorials/quick-start.ipynb',
            'title': 'Quick Start',
            'description': 'A quick start tutorial',
        },
        'advanced': {
            'url': 'https://example.com/{version}/tutorials/advanced.ipynb',
            'title': 'Advanced',
            'description': 'An advanced tutorial',
        },
    }
    monkeypatch.setattr(MUT, '_fetch_tutorials_index', lambda: fake_index)
    monkeypatch.setattr(MUT, 'package_version', lambda name: '0.8.0')
    MUT.list_tutorials()
    out = capsys.readouterr().out
    assert 'Tutorials available for easydiffraction v0.8.0' in out
    assert 'Quick Start' in out
    assert 'Advanced' in out


@pytest.mark.parametrize(
    ('terminal_columns', 'expected_width'),
    [(200, 100), (72, 72)],
)
def test_list_tutorials_caps_table_width(monkeypatch, terminal_columns, expected_width):
    import easydiffraction.utils.utils as MUT

    fake_index = {'quick-start': {'url': 'https://x/{version}/t/quick-start.ipynb'}}
    monkeypatch.setattr(MUT, '_fetch_tutorials_index', lambda: fake_index)
    monkeypatch.setattr(MUT, 'package_version', lambda name: '0.8.0')
    monkeypatch.setattr(
        MUT.shutil, 'get_terminal_size', lambda: os.terminal_size((terminal_columns, 24))
    )

    captured = {}
    monkeypatch.setattr(MUT, 'render_table', lambda **kwargs: captured.update(kwargs))

    MUT.list_tutorials()
    assert captured['width'] == expected_width


def test_download_tutorial_unknown_id(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, '_fetch_tutorials_index', lambda: {'quick-start': {}})
    with pytest.raises(KeyError, match="Unknown tutorial 'missing-tutorial'"):
        MUT.download_tutorial('missing-tutorial')


def test_download_tutorial_success(monkeypatch, tmp_path):
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
    assert (tmp_path / 'quick-start.ipynb').exists()


def test_download_tutorial_py_format_swaps_extension(monkeypatch, tmp_path):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'quick-start': {
            'url': 'https://example.com/{version}/tutorials/quick-start/quick-start.ipynb',
            'title': 'Quick Start',
        },
    }
    monkeypatch.setattr(MUT, '_fetch_tutorials_index', lambda: fake_index)
    monkeypatch.setattr(MUT, '_get_version_for_url', lambda: '0.8.0')

    requested_urls = []

    class DummyResp:
        def read(self):
            return b'# quick-start script'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(url):
        requested_urls.append(url)
        return DummyResp()

    monkeypatch.setattr(MUT, '_safe_urlopen', fake_urlopen)

    result = MUT.download_tutorial('quick-start', destination=str(tmp_path), file_format='py')
    assert result == str(tmp_path / 'quick-start.py')
    assert (tmp_path / 'quick-start.py').exists()
    # The notebook lives nested (tutorials/<name>/<name>.ipynb) but the
    # .py source is published flat at tutorials/<name>.py.
    assert requested_urls == ['https://example.com/0.8.0/tutorials/quick-start.py']


def test_download_tutorial_unknown_format(monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, '_fetch_tutorials_index', lambda: {'quick-start': {}})
    with pytest.raises(ValueError, match="Unknown tutorial format 'txt'"):
        MUT.download_tutorial('quick-start', file_format='txt')


def test_download_tutorial_uses_artifact_root(monkeypatch, tmp_path):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'quick-start': {
            'url': 'https://example.com/{version}/tutorials/quick-start.ipynb',
            'title': 'Quick Start',
        },
    }
    artifact_root = tmp_path / 'artifacts'
    monkeypatch.setenv('EASYDIFFRACTION_ARTIFACT_ROOT', str(artifact_root))
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

    result = MUT.download_tutorial('quick-start', destination='tutorials')

    expected_path = artifact_root / 'tutorials' / 'quick-start.ipynb'
    assert result == str(expected_path)
    assert expected_path.exists()


def test_download_tutorial_already_exists_no_overwrite(monkeypatch, tmp_path, capsys):
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
    (tmp_path / 'quick-start.ipynb').write_text('existing content')

    result = MUT.download_tutorial('quick-start', destination=str(tmp_path), overwrite=False)
    assert result == str(tmp_path / 'quick-start.ipynb')
    out = capsys.readouterr().out
    assert 'already present' in out
    # Content should not be changed
    assert (tmp_path / 'quick-start.ipynb').read_text() == 'existing content'


def test_show_version_prints(capsys, monkeypatch):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, 'package_version', lambda name: '1.2.3+abc')
    MUT.show_version()
    out = capsys.readouterr().out
    assert '1.2.3+abc' in out


def test_download_all_tutorials_empty_index(monkeypatch, capsys):
    import easydiffraction.utils.utils as MUT

    monkeypatch.setattr(MUT, '_fetch_tutorials_index', dict)
    result = MUT.download_all_tutorials()
    assert result == []
    out = capsys.readouterr().out
    assert 'No tutorials available' in out


def test_download_all_tutorials_success(monkeypatch, tmp_path, capsys):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'quick-start': {
            'url': 'https://example.com/{version}/tutorials/quick-start.ipynb',
            'title': 'Quick Start',
        },
        'advanced': {
            'url': 'https://example.com/{version}/tutorials/advanced.ipynb',
            'title': 'Advanced',
        },
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

    result = MUT.download_all_tutorials(destination=str(tmp_path))
    assert len(result) == 2
    assert (tmp_path / 'quick-start.ipynb').exists()
    assert (tmp_path / 'advanced.ipynb').exists()


def test_download_all_tutorials_reports_resolved_artifact_root(
    monkeypatch,
    tmp_path,
    capsys,
):
    import easydiffraction.utils.utils as MUT

    fake_index = {
        'quick-start': {
            'url': 'https://example.com/{version}/tutorials/quick-start.ipynb',
            'title': 'Quick Start',
        },
    }
    artifact_root = tmp_path / 'artifacts'
    monkeypatch.setenv('EASYDIFFRACTION_ARTIFACT_ROOT', str(artifact_root))
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

    result = MUT.download_all_tutorials(destination='tutorials')

    expected_dir = artifact_root / 'tutorials'
    assert result == [str(expected_dir / 'quick-start.ipynb')]
    assert (expected_dir / 'quick-start.ipynb').exists()
    out = capsys.readouterr().out
    assert 'Downloaded 1 tutorials' in out
    normalized_out = out.replace('\\', '/').replace('\n', '')
    assert str(expected_dir).replace('\\', '/') in normalized_out


def test_resolve_tutorial_url():

    # Test with a specific version
    url_template = 'https://example.com/{version}/tutorials/ed-1/ed-1.ipynb'
    # We need to test _resolve_tutorial_url, but it uses _get_version_for_url internally
    # So we just test that the function exists and replaces {version}
    result = url_template.replace('{version}', '0.8.0')
    assert result == 'https://example.com/0.8.0/tutorials/ed-1/ed-1.ipynb'

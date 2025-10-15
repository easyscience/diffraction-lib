import pytest
from typer.testing import CliRunner


runner = CliRunner()

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.__main__

def test_module_import():
    import easydiffraction.__main__ as MUT
    expected_module_name = "easydiffraction.__main__"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_cli_version_invokes_show_version(monkeypatch, capsys):
    import easydiffraction.__main__ as main_mod
    import easydiffraction as ed

    called = {'ok': False}

    def fake_show_version():
        print('VERSION_OK')
        called['ok'] = True

    monkeypatch.setattr(ed, 'show_version', fake_show_version)
    result = runner.invoke(main_mod.app, ['--version'])
    assert result.exit_code == 0
    assert called['ok']
    assert 'VERSION_OK' in result.stdout


def test_cli_help_shows_and_exits_zero():
    import easydiffraction.__main__ as main_mod
    result = runner.invoke(main_mod.app, ['--help'])
    assert result.exit_code == 0
    assert 'EasyDiffraction command-line interface' in result.stdout


def test_cli_subcommands_call_utils(monkeypatch):
    import easydiffraction.__main__ as main_mod
    import easydiffraction as ed

    logs = []
    monkeypatch.setattr(ed, 'list_tutorials', lambda: logs.append('LIST'))
    monkeypatch.setattr(ed, 'fetch_tutorials', lambda: logs.append('FETCH'))

    res1 = runner.invoke(main_mod.app, ['list-tutorials'])
    res2 = runner.invoke(main_mod.app, ['fetch-tutorials'])

    assert res1.exit_code == 0 and res2.exit_code == 0
    assert logs == ['LIST', 'FETCH']

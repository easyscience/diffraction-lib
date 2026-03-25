# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_module_import():
    import easydiffraction.project.project as MUT

    expected_module_name = 'easydiffraction.project.project'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_project_help(capsys):
    from easydiffraction.project.project import Project

    p = Project()
    p.help()
    out = capsys.readouterr().out
    assert "Help for 'Project'" in out
    assert 'experiments' in out
    assert 'analysis' in out
    assert 'summary' in out


# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_show_params_empty_branches(capsys):
    from easydiffraction.analysis.analysis import Analysis

    class Empty:
        @property
        def parameters(self):
            return []

        @property
        def fittable_parameters(self):
            return []

        @property
        def free_parameters(self):
            return []

        def __iter__(self):
            return iter(())

    class P:
        structures = Empty()
        experiments = Empty()
        _varname = 'proj'

    a = Analysis(project=P())

    # display.all_params -> warning path
    a.display.all_params()
    # display.fittable_params -> warning path
    a.display.fittable_params()
    # display.free_params -> warning path
    a.display.free_params()

    out = capsys.readouterr().out
    assert (
        'No parameters found' in out
        or 'No fittable parameters' in out
        or 'No free parameters' in out
    )

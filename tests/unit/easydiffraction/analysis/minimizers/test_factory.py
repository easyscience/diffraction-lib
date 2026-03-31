# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_minimizer_factory_list_and_show(capsys):
    from easydiffraction.analysis.minimizers.factory import MinimizerFactory

    lst = MinimizerFactory.supported_tags()
    assert isinstance(lst, list) and len(lst) >= 1
    MinimizerFactory.show_supported()
    out = capsys.readouterr().out
    assert 'Supported types' in out


def test_minimizer_factory_unknown_raises():
    from easydiffraction.analysis.minimizers.factory import MinimizerFactory

    try:
        MinimizerFactory.create('___unknown___')
    except ValueError as e:
        assert 'Unsupported type' in str(e)
    else:
        assert False, 'Expected ValueError'


def test_minimizer_factory_create_known_and_register():
    from easydiffraction.analysis.minimizers.base import MinimizerBase
    from easydiffraction.analysis.minimizers.factory import MinimizerFactory
    from easydiffraction.core.metadata import TypeInfo

    # Create a known minimizer instance (lmfit exists)
    m = MinimizerFactory.create('lmfit')
    assert isinstance(m, MinimizerBase)

    # Register a custom minimizer and create it
    @MinimizerFactory.register
    class Custom(MinimizerBase):
        type_info = TypeInfo(tag='custom-test', description='x')

        def _prepare_solver_args(self, parameters):
            return {}

        def _run_solver(self, objective_function, **kwargs):
            return None

        def _sync_result_to_parameters(self, raw_result, parameters):
            pass

        def _check_success(self, raw_result):
            return True

    created = MinimizerFactory.create('custom-test')
    assert isinstance(created, Custom)

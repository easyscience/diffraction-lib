# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def _make_param(db, cat, entry, name, val):
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    param = Parameter(
        name=name,
        value_spec=AttributeSpec(default=0.0),
        cif_handler=CifHandler(names=[f'_{cat}.{name}']),
    )
    param.value = val
    param._identity.datablock_entry_name = lambda: db
    param._identity.category_code = cat
    if entry:
        param._identity.category_entry_name = lambda: entry
    else:
        param._identity.category_entry_name = lambda: ''
    return param


def test_how_to_access_parameters_prints_paths_and_uids(capsys, monkeypatch):
    import easydiffraction.analysis.analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    p1 = _make_param('db1', 'catA', '', 'alpha', 1.0)
    p2 = _make_param('db2', 'catB', 'row1', 'beta', 2.0)

    class Coll:
        def __init__(self, params):
            self.parameters = params

    class Project:
        _varname = 'proj'

        def __init__(self):
            self.structures = Coll([p1])
            self.experiments = Coll([p2])

    # Capture the table payload by monkeypatching render_table to avoid
    # terminal wrapping/ellipsis affecting string matching.
    captured = {}

    def fake_render_table(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(analysis_mod, 'render_table', fake_render_table)
    a = Analysis(Project())
    a.display.how_to_access_parameters()

    out = capsys.readouterr().out
    assert 'How to access parameters' in out

    # Validate headers and row contents independent of terminal renderer
    headers = captured.get('columns_headers') or []
    data = captured.get('columns_data') or []

    assert 'How to Access in Python Code' in headers

    # Flatten rows to strings for simple membership checks
    flat_rows = [' '.join(map(str, row)) for row in data]

    # Python access paths
    assert any("proj.structures['db1'].catA.alpha" in r for r in flat_rows)
    assert any("proj.experiments['db2'].catB['row1'].beta" in r for r in flat_rows)

    # Now check CIF unique identifiers via the new API
    captured2 = {}

    def fake_render_table2(**kwargs):
        captured2.update(kwargs)

    monkeypatch.setattr(analysis_mod, 'render_table', fake_render_table2)
    a.display.parameter_cif_uids()
    headers2 = captured2.get('columns_headers') or []
    data2 = captured2.get('columns_data') or []
    assert 'Unique Identifier for CIF Constraints' in headers2
    flat_rows2 = [' '.join(map(str, row)) for row in data2]
    # Unique names are datablock.category[.entry].parameter
    assert any('db1 catA  alpha' in r.replace('.', ' ') for r in flat_rows2)
    assert any('db2 catB row1 beta' in r.replace('.', ' ') for r in flat_rows2)


def test_how_to_access_parameters_skips_large_loop_categories(capsys, monkeypatch):
    import easydiffraction.analysis.analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    visible = _make_param('db1', 'catA', '', 'alpha', 1.0)
    data_param = _make_param('db2', 'pd_data', '1', 'intensity_meas', 2.0)
    refln_param = _make_param('db2', 'refln', '1', 'f_calc', 3.0)

    class Coll:
        def __init__(self, params):
            self.parameters = params

    class Project:
        _varname = 'proj'

        def __init__(self):
            self.structures = Coll([visible])
            self.experiments = Coll([data_param, refln_param])

    captured = {}

    def fake_render_table(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(analysis_mod, 'render_table', fake_render_table)
    Analysis(Project()).display.how_to_access_parameters()

    out = capsys.readouterr().out
    assert 'How to access parameters' in out

    flat_rows = [' '.join(map(str, row)) for row in captured.get('columns_data') or []]
    assert any("proj.structures['db1'].catA.alpha" in row for row in flat_rows)
    assert not any('pd_data' in row for row in flat_rows)
    assert not any('refln' in row for row in flat_rows)


def test_parameter_cif_uids_skips_large_loop_categories(monkeypatch):
    import easydiffraction.analysis.analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    visible = _make_param('db1', 'catA', '', 'alpha', 1.0)
    data_param = _make_param('db2', 'pd_data', '1', 'intensity_meas', 2.0)
    refln_param = _make_param('db2', 'refln', '1', 'f_calc', 3.0)

    class Coll:
        def __init__(self, params):
            self.parameters = params

    class Project:
        _varname = 'proj'

        def __init__(self):
            self.structures = Coll([visible])
            self.experiments = Coll([data_param, refln_param])

    captured = {}

    def fake_render_table(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(analysis_mod, 'render_table', fake_render_table)
    Analysis(Project()).display.parameter_cif_uids()

    flat_rows = [' '.join(map(str, row)) for row in captured.get('columns_data') or []]
    assert any('db1 catA  alpha' in row.replace('.', ' ') for row in flat_rows)
    assert not any('pd_data' in row for row in flat_rows)
    assert not any('refln' in row for row in flat_rows)


def test_all_params_skips_large_loop_categories(monkeypatch):
    import easydiffraction.analysis.analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    structure_param = _make_param('s1', 'cell', '', 'length_a', 4.0)
    visible_experiment_param = _make_param('e1', 'instrument', '', 'wavelength', 1.5)
    data_param = _make_param('e1', 'pd_data', '1', 'intensity_meas', 10.0)
    refln_param = _make_param('e1', 'refln', '1', 'f_calc', 12.0)

    class Coll:
        def __init__(self, params):
            self.parameters = params

        def __iter__(self):
            return iter(())

    class Project:
        def __init__(self):
            self.structures = Coll([structure_param])
            self.experiments = Coll([visible_experiment_param, data_param, refln_param])

    rendered = []

    class FakeTableRenderer:
        def render(self, df):
            rendered.append(df)

    monkeypatch.setattr(analysis_mod.TableRenderer, 'get', staticmethod(lambda: FakeTableRenderer()))
    Analysis(Project()).display.all_params()

    assert len(rendered) == 2
    experiment_categories = rendered[1][('category', 'left')].tolist()
    experiment_parameters = rendered[1][('parameter', 'left')].tolist()
    assert experiment_categories == ['instrument']
    assert experiment_parameters == ['wavelength']

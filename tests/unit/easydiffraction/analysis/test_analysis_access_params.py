# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def _make_param(
    db,
    cat,
    entry,
    name,
    val,
    *,
    units='none',
    display_units=None,
    user_constrained=False,
    symmetry_constrained=False,
):
    from easydiffraction.core.display_handler import DisplayHandler
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    display_handler = (
        DisplayHandler(display_units=display_units) if display_units is not None else None
    )
    param = Parameter(
        name=name,
        units=units,
        value_spec=AttributeSpec(default=0.0),
        cif_handler=CifHandler(names=[f'_{cat}.{name}']),
        display_handler=display_handler,
    )
    param.value = val
    param._identity.datablock_entry_name = lambda: db
    param._identity.category_code = cat
    if entry:
        param._identity.category_entry_name = lambda: entry
    else:
        param._identity.category_entry_name = lambda: ''
    if user_constrained:
        param._user_constrained = True
    if symmetry_constrained:
        param._set_symmetry_constrained(value=True)
    return param


def _make_int_descriptor(db, cat, entry, name, val):
    """Build a read-only IntegerDescriptor (e.g. atom_site.multiplicity)."""
    from easydiffraction.core.display_handler import DisplayHandler
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import IntegerDescriptor
    from easydiffraction.io.cif.handler import CifHandler

    descriptor = IntegerDescriptor(
        name=name,
        value_spec=AttributeSpec(default=None, allow_none=True),
        cif_handler=CifHandler(names=[f'_{cat}.{name}']),
        display_handler=DisplayHandler(),
    )
    descriptor.value = val
    descriptor._identity.datablock_entry_name = lambda: db
    descriptor._identity.category_code = cat
    descriptor._identity.category_entry_name = (lambda: entry) if entry else (lambda: '')
    return descriptor


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

    monkeypatch.setattr(
        analysis_mod.TableRenderer, 'get', staticmethod(lambda: FakeTableRenderer())
    )
    Analysis(Project()).display.all_params()

    assert len(rendered) == 2
    experiment_categories = rendered[1]['category', 'left'].tolist()
    experiment_parameters = rendered[1]['parameter', 'left'].tolist()
    assert experiment_categories == ['instrument']
    assert experiment_parameters == ['wavelength']


def test_all_params_marks_constrained_parameters_not_fittable(monkeypatch):
    import easydiffraction.analysis.analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    refinable_param = _make_param('s1', 'cell', '', 'length_a', 4.0)
    user_constrained_param = _make_param('s1', 'cell', '', 'length_b', 4.0, user_constrained=True)
    symmetry_constrained_param = _make_param(
        's1',
        'cell',
        '',
        'length_c',
        4.0,
        symmetry_constrained=True,
    )

    class Coll:
        def __init__(self, params):
            self.parameters = params

        def __iter__(self):
            return iter(())

    class Project:
        def __init__(self):
            self.structures = Coll([
                refinable_param,
                user_constrained_param,
                symmetry_constrained_param,
            ])
            self.experiments = Coll([])

    rendered = []

    class FakeTableRenderer:
        def render(self, df):
            rendered.append(df)

    monkeypatch.setattr(
        analysis_mod.TableRenderer, 'get', staticmethod(lambda: FakeTableRenderer())
    )
    Analysis(Project()).display.all_params()

    structure_df = rendered[0]
    assert structure_df['parameter', 'left'].tolist() == ['length_a', 'length_b', 'length_c']
    assert structure_df['fittable', 'left'].tolist() == [True, False, False]


def test_fittable_params_excludes_symmetry_constrained_parameters(monkeypatch):
    import easydiffraction.analysis.analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    visible_param = _make_param('s1', 'cell', '', 'length_a', 4.0)
    symmetry_constrained_param = _make_param(
        's1',
        'cell',
        '',
        'length_c',
        4.0,
        symmetry_constrained=True,
    )

    class Coll:
        def __init__(self, params, fittable_params):
            self.parameters = params
            self.fittable_parameters = fittable_params

        def __iter__(self):
            return iter(())

    class Project:
        def __init__(self):
            self.structures = Coll(
                [visible_param, symmetry_constrained_param],
                [visible_param],
            )
            self.experiments = Coll([], [])

    rendered = []

    class FakeTableRenderer:
        def render(self, df):
            rendered.append(df)

    monkeypatch.setattr(
        analysis_mod.TableRenderer, 'get', staticmethod(lambda: FakeTableRenderer())
    )
    Analysis(Project()).display.fittable_params()

    structure_df = rendered[0]
    assert structure_df['parameter', 'left'].tolist() == ['length_a']


def test_free_params_uses_display_units_for_structures_and_experiments(monkeypatch):
    import easydiffraction.analysis.analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    structure_param = _make_param(
        's1',
        'cell',
        '',
        'length_a',
        4.0,
        units='angstrom_squared',
        display_units='Å²',
    )
    experiment_param = _make_param(
        'e1',
        'time_of_flight',
        '',
        'time_offset',
        12.0,
        units='microseconds',
        display_units='μs',
    )

    class Coll:
        def __init__(self, params):
            self.parameters = params
            self.free_parameters = params

        def __iter__(self):
            return iter(())

    class Project:
        def __init__(self):
            self.structures = Coll([structure_param])
            self.experiments = Coll([experiment_param])

    rendered = []

    class FakeTableRenderer:
        def render(self, df):
            rendered.append(df)

    monkeypatch.setattr(
        analysis_mod.TableRenderer, 'get', staticmethod(lambda: FakeTableRenderer())
    )
    Analysis(Project()).display.free_params()

    free_df = rendered[0]
    assert free_df['parameter', 'left'].tolist() == ['length_a', 'time_offset']
    assert free_df['units', 'left'].tolist() == ['Å²', 'μs']


def test_summary_parameters_excludes_space_group_wyckoff():
    from easydiffraction.analysis.analysis import AnalysisDisplay

    visible = _make_param('lbco', 'cell', '', 'length_a', 4.0)
    # The derived space_group_Wyckoff table (read-only, with unreadably
    # long coords_xyz) must not clutter the parameter summary tables.
    wyckoff = _make_param('lbco', 'space_group_Wyckoff', '48n', 'coords_xyz', 0.0)

    summary = AnalysisDisplay._summary_parameters([visible, wyckoff])

    assert [param._identity.category_code for param in summary] == ['cell']


def test_all_params_renders_integer_descriptors_without_nan(monkeypatch):
    import easydiffraction.analysis.analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    occupancy = _make_param('lbco', 'atom_site', 'O', 'occupancy', 1.0)
    # IntegerDescriptors (e.g. atom_site.multiplicity) used to render as
    # all-nan rows; None multiplicity occurs for an untabulated group.
    multiplicity = _make_int_descriptor('lbco', 'atom_site', 'O', 'multiplicity', 3)
    multiplicity_none = _make_int_descriptor('lbco', 'atom_site', 'X', 'multiplicity', None)

    class Coll:
        def __init__(self, params):
            self.parameters = params

        def __iter__(self):
            return iter(())

    class Project:
        def __init__(self):
            self.structures = Coll([occupancy, multiplicity, multiplicity_none])
            self.experiments = Coll([])

    rendered = []

    class FakeTableRenderer:
        def render(self, df):
            rendered.append(df)

    monkeypatch.setattr(
        analysis_mod.TableRenderer, 'get', staticmethod(lambda: FakeTableRenderer())
    )
    Analysis(Project()).display.all_params()

    structure_df = rendered[0]
    assert structure_df['parameter', 'left'].tolist() == [
        'occupancy',
        'multiplicity',
        'multiplicity',
    ]
    # Integer value rendered as-is; None renders blank; no nan cells.
    assert structure_df['value', 'right'].tolist() == [1.0, 3, '']
    assert int(structure_df.isna().sum().sum()) == 0


def test_how_to_access_and_cif_uids_include_integer_descriptors(monkeypatch):
    import easydiffraction.analysis.analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    # An IntegerDescriptor used to be dropped from both tables by a
    # too-narrow isinstance guard; it must now appear in each.
    multiplicity = _make_int_descriptor('lbco', 'atom_site', 'O', 'multiplicity', 3)

    class Coll:
        def __init__(self, params):
            self.parameters = params

    class Project:
        _varname = 'proj'

        def __init__(self):
            self.structures = Coll([multiplicity])
            self.experiments = Coll([])

    captured = {}

    def fake_render_table(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(analysis_mod, 'render_table', fake_render_table)
    a = Analysis(Project())
    a.display.how_to_access_parameters()

    access_rows = [' '.join(map(str, row)) for row in captured.get('columns_data') or []]
    assert any("proj.structures['lbco'].atom_site['O'].multiplicity" in row for row in access_rows)

    captured.clear()
    a.display.parameter_cif_uids()

    uid_rows = [' '.join(map(str, row)) for row in captured.get('columns_data') or []]
    assert any('multiplicity' in row for row in uid_rows)

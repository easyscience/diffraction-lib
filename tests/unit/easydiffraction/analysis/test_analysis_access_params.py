# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause


def test_how_to_access_parameters_prints_paths_and_uids(capsys):
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.core.parameters import Parameter
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import DataTypes
    from easydiffraction.io.cif.handler import CifHandler

    # Build two parameters with identity metadata set directly
    def make_param(db, cat, entry, name, val):
        p = Parameter(
            name=name,
            value_spec=AttributeSpec(value=val, type_=DataTypes.NUMERIC, default=0.0),
            cif_handler=CifHandler(names=[f'_{cat}.{name}']),
        )
        # Inject identity metadata (avoid parent chain)
        p._identity.datablock_entry_name = lambda: db
        p._identity.category_code = cat
        if entry:
            p._identity.category_entry_name = lambda: entry
        else:
            p._identity.category_entry_name = lambda: ''
        return p

    p1 = make_param('db1', 'catA', '', 'alpha', 1.0)
    p2 = make_param('db2', 'catB', 'row1', 'beta', 2.0)

    class Coll:
        def __init__(self, params):
            self.parameters = params

    class Project:
        _varname = 'proj'

        def __init__(self):
            self.sample_models = Coll([p1])
            self.experiments = Coll([p2])

    a = Analysis(Project())
    a.how_to_access_parameters()
    out = capsys.readouterr().out
    assert 'How to access parameters' in out
    # Expect code path strings
    assert "proj.sample_models['db1'].catA.alpha" in out
    assert "proj.experiments['db2'].catB['row1'].beta" in out
    # Expect CIF uid (owner.unique_name) present for both
    assert 'db1.catA.alpha' in out
    assert 'db2.catB.row1.beta' in out

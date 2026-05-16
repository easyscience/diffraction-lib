# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Additional unit tests for analysis.py to cover patch gaps."""


def _make_project():
    class ExpCol:
        def __init__(self):
            self._names = []

        @property
        def names(self):
            return self._names

        @property
        def parameters(self):
            return []

        @property
        def fittable_parameters(self):
            return []

        @property
        def free_parameters(self):
            return []

    class P:
        experiments = ExpCol()
        structures = ExpCol()
        _varname = 'proj'
        verbosity = 'full'

    return P()


# ------------------------------------------------------------------
# AnalysisDisplay.as_cif
# ------------------------------------------------------------------


class TestAnalysisDisplayAsCif:
    def test_as_cif_renders(self, capsys, monkeypatch):
        import easydiffraction.analysis.analysis as mod
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        # Mock render_cif to avoid rendering issues
        rendered = {}

        def fake_render_cif(text):
            rendered['text'] = text

        monkeypatch.setattr(mod, 'render_cif', fake_render_cif)
        a.display.as_cif()
        out = capsys.readouterr().out
        assert 'Analysis' in out or 'cif' in out.lower()
        assert 'text' in rendered


# ------------------------------------------------------------------
# AnalysisDisplay.constraints (with items)
# ------------------------------------------------------------------


class TestAnalysisDisplayConstraints:
    def test_empty_constraints_warns(self, capsys):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        a.display.constraints()
        out = capsys.readouterr().out
        assert 'No constraints' in out

    def test_constraints_with_items(self, capsys, monkeypatch):
        import easydiffraction.analysis.categories.constraints.default as constraints_mod
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())

        # Create a fake constraint with expression
        class FakeExpr:
            value = 'x = y + 1'

        class FakeConstraint:
            expression = FakeExpr()

        a.constraints._items = [FakeConstraint()]

        captured = {}

        def fake_render_table(**kwargs):
            captured.update(kwargs)

        monkeypatch.setattr(constraints_mod, 'render_table', fake_render_table)
        a.display.constraints()
        out = capsys.readouterr().out
        assert 'User defined constraints' in out
        assert 'columns_data' in captured
        assert captured['columns_data'][0][0] == 'x = y + 1'


# ------------------------------------------------------------------
# Analysis._discover_property_rows / _discover_method_rows
# ------------------------------------------------------------------


class TestDiscoverHelpers:
    def test_discover_property_rows(self):
        from easydiffraction.analysis.analysis import _discover_property_rows

        class MyClass:
            @property
            def alpha(self):
                """Alpha property."""
                return 1

            @property
            def beta(self):
                """Beta property."""
                return 2

            @beta.setter
            def beta(self, value):
                pass

        rows = _discover_property_rows(MyClass)
        assert len(rows) == 2
        names = [row[1] for row in rows]
        assert 'alpha' in names
        assert 'beta' in names
        # beta is writable
        beta_row = next(r for r in rows if r[1] == 'beta')
        assert beta_row[2] == '✓'

    def test_discover_method_rows(self):
        from easydiffraction.analysis.analysis import _discover_method_rows

        class MyClass:
            def do_thing(self):
                """Do a thing."""

            def _private(self):
                pass

            @property
            def prop(self):
                """Not a method."""
                return 1

        rows = _discover_method_rows(MyClass)
        names = [row[1] for row in rows]
        assert 'do_thing()' in names
        assert '_private()' not in names
        assert 'prop()' not in names


# ------------------------------------------------------------------
# Analysis.minimizer_type setter
# ------------------------------------------------------------------


class TestCurrentMinimizerSetter:
    def test_setter_changes_minimizer(self, capsys):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())
        assert a.fitting.minimizer_type.value == 'lmfit (leastsq)'
        a.fitting.minimizer_type = 'lmfit (leastsq)'
        out = capsys.readouterr().out
        assert 'Current minimizer changed to' in out


# ------------------------------------------------------------------
# Analysis._snapshot_params
# ------------------------------------------------------------------


class TestSnapshotParams:
    def test_snapshot_stores_values(self):
        from easydiffraction.analysis.analysis import Analysis

        a = Analysis(project=_make_project())

        class FakeParam:
            unique_name = 'p1'
            value = 1.23
            uncertainty = 0.01
            units = 'Å'

        class FakeResults:
            parameters = [FakeParam()]

        a._snapshot_params('expt1', FakeResults())
        assert 'expt1' in a._parameter_snapshots
        assert a._parameter_snapshots['expt1']['p1']['value'] == 1.23
        assert a._parameter_snapshots['expt1']['p1']['uncertainty'] == 0.01

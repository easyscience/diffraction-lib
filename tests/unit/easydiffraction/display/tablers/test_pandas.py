# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for display/tablers/pandas.py (PandasTableBackend)."""

import re

import pandas as pd


def _backend():
    from easydiffraction.display.tablers.pandas import PandasTableBackend

    return PandasTableBackend()


def _indexed(data):
    df = pd.DataFrame(data)
    df.index += 1
    return df


class TestPandasTableBackend:
    def test_build_renderable_returns_table_html(self):
        html = _backend().build_renderable(['left', 'right'], _indexed({'A': [1.0], 'B': [2.0]}))
        assert isinstance(html, str)
        assert '<table' in html
        assert '<thead' in html
        assert '<tbody>' in html

    def test_table_is_wrapped_in_horizontal_scroll_container(self):
        """A wrapping ``overflow-x: auto`` div keeps wide tables scrolling.

        Forcing ``display: table`` (below) drops Material's
        ``inline-block``, which is what provided horizontal scrolling for
        wide tables; the wrapper restores it.
        """
        html = _backend().build_renderable(['left'], _indexed({'A': [1.0]}))
        assert html.startswith('<div style="overflow-x: auto')
        assert html.rstrip().endswith('</div>')

    def test_table_forces_display_table_for_border_collapse(self):
        """``display: table`` defeats Material's ``inline-block`` rule.

        Without it the table leaves the collapsing-border model and the
        header divider darkens and stops short of the right edge.
        """
        html = _backend().build_renderable(['left'], _indexed({'A': [1.0]}))
        assert 'border-collapse: collapse' in html
        assert 'display: table' in html

    def test_thead_zeroes_border_so_divider_matches_outer_border(self):
        """Host opaque ``thead`` borders (JupyterLab) must not recolour it."""
        html = _backend().build_renderable(['left'], _indexed({'A': [1.0]}))
        assert '<thead style="border-bottom: 0">' in html

    def test_no_style_or_script_block_survives_untrusted_reopen(self):
        """All styling is inline -- no <style>/<script> to be stripped.

        JupyterLab strips ``<style>``/``<script>`` from untrusted
        (reopened, not-yet-re-run) outputs, which made saved tables lose
        their theming until re-execution. Inline styles survive that.
        """
        html = _backend().build_renderable(['left'], _indexed({'A': [1.0]}))
        assert '<style' not in html
        assert '<script' not in html
        assert 'style="' in html

    def test_index_is_dimmed_and_non_bold(self):
        from easydiffraction.display.tablers.pandas import INDEX_COLOR

        html = _backend().build_renderable(['left'], _indexed({'A': [1.0]}))
        index_th = re.search(r'<th style="([^"]*)">1</th>', html)
        assert index_th is not None
        style = index_th.group(1)
        assert INDEX_COLOR in style
        assert 'font-weight: normal' in style

    def test_border_and_divider_use_translucent_grey(self):
        from easydiffraction.display.tablers.pandas import BORDER_COLOR

        html = _backend().build_renderable(['left'], _indexed({'A': [1.0]}))
        assert f'border: 1px solid {BORDER_COLOR}' in html
        assert f'border-bottom: 1px solid {BORDER_COLOR}' in html

    def test_cells_do_not_wrap_so_wide_tables_scroll(self):
        """Cells stay on one line; wide tables scroll, not fold to rows."""
        html = _backend().build_renderable(['left'], _indexed({'A': [1.0]}))
        assert 'white-space: nowrap' in html

    def test_per_column_alignment_is_inline(self):
        html = _backend().build_renderable(['left', 'right'], _indexed({'A': ['x'], 'B': ['y']}))
        assert 'text-align: left' in html
        assert 'text-align: right' in html

    def test_rows_override_host_striping(self):
        html = _backend().build_renderable(['left'], _indexed({'A': [1, 2, 3]}))
        # header row + 3 body rows each pin a transparent background
        assert html.count('background-color: transparent') >= 4

    def test_rich_markup_becomes_inline_colour(self):
        html = _backend().build_renderable(['left'], _indexed({'A': ['[red]warn[/red]']}))
        assert 'color: red' in html
        assert 'warn' in html
        assert '[red]' not in html

    def test_floats_use_fixed_precision(self):
        html = _backend().build_renderable(['left'], _indexed({'A': [1.23456789]}))
        assert '1.23457' in html

    def test_html_special_characters_are_escaped(self):
        html = _backend().build_renderable(['left'], _indexed({'A': ['<b>&x']}))
        assert '&lt;b&gt;&amp;x' in html
        assert '<b>' not in html

    def test_render_displays_inline_html(self, monkeypatch):
        import easydiffraction.display.tablers.pandas as mod

        captured = {}
        monkeypatch.setattr(mod, 'HTML', lambda payload: ('HTML', payload))
        monkeypatch.setattr(mod, 'display', lambda obj: captured.__setitem__('obj', obj))

        mod.PandasTableBackend().render(['left'], _indexed({'A': [1.0]}))

        assert captured['obj'][0] == 'HTML'
        assert '<table' in captured['obj'][1]
        assert '<style' not in captured['obj'][1]

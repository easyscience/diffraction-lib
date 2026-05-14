# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for display/progress.py."""

from __future__ import annotations

from easydiffraction.utils.enums import VerbosityEnum


def test_make_display_handle_uses_terminal_live_when_available(monkeypatch):
    import easydiffraction.display.progress as progress_mod

    class FakeLive:
        def __init__(
            self,
            renderable=None,
            *,
            console,
            auto_refresh,
            refresh_per_second,
            get_renderable=None,
        ):
            self.renderable = renderable
            self.console = console
            self.auto_refresh = auto_refresh
            self.refresh_per_second = refresh_per_second
            self.get_renderable = get_renderable
            self.started = False
            self.stopped = False
            self.refresh_calls = 0

        def start(self):
            self.started = True

        def stop(self):
            self.stopped = True

        def refresh(self):
            self.refresh_calls += 1

    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: False)
    monkeypatch.setattr(progress_mod, 'Live', FakeLive)
    monkeypatch.setattr(progress_mod.ConsoleManager, 'get', lambda: 'console')

    handle = progress_mod.make_display_handle()

    assert isinstance(handle, progress_mod._TerminalLiveHandle)
    assert handle._live.console == 'console'
    assert handle._live.auto_refresh is True
    assert handle._live.get_renderable is not None
    assert handle._live.started is True

    handle.update('content')

    assert handle._live.refresh_calls == 1
    assert handle._live.get_renderable() == 'content'

    handle.close()

    assert handle._live.stopped is True


def test_activity_indicator_silent_does_not_create_handles():
    from easydiffraction.display.progress import ActivityIndicator

    indicator = ActivityIndicator(verbosity=VerbosityEnum.SILENT)
    indicator.start()

    assert indicator._live is None
    assert indicator._display_handle is None


def test_activity_indicator_html_style_prevents_stretching():
    import easydiffraction.display.progress as progress_mod

    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    style = indicator._html_style()

    assert 'align-items: flex-start;' in style
    assert progress_mod.ACTIVITY_ACCENT_COLOR in style
    assert 'font-weight: 400;' in style
    assert 'var(--jp-ui-font-family' in style


def test_activity_indicator_terminal_line_uses_accent_style():
    import easydiffraction.display.progress as progress_mod

    indicator = progress_mod.ActivityIndicator(label='Fitting...', verbosity=VerbosityEnum.FULL)
    indicator._running = True

    line = indicator._terminal_indicator_line()

    assert line is not None
    assert line.style == progress_mod.ACTIVITY_TERMINAL_STYLE
    assert 'bold' not in str(line.style)


def test_activity_indicator_terminal_live_uses_dynamic_renderable(monkeypatch):
    import easydiffraction.display.progress as progress_mod

    class FakeLive:
        def __init__(
            self,
            renderable=None,
            *,
            console,
            auto_refresh,
            refresh_per_second,
            get_renderable=None,
        ):
            self.renderable = renderable
            self.console = console
            self.auto_refresh = auto_refresh
            self.refresh_per_second = refresh_per_second
            self.get_renderable = get_renderable
            self.refresh_calls = 0
            self.started = False

        def start(self):
            self.started = True

        def stop(self):
            self.started = False

        def refresh(self):
            self.refresh_calls += 1

    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: False)
    monkeypatch.setattr(progress_mod, 'Live', FakeLive)
    monkeypatch.setattr(progress_mod.ConsoleManager, 'get', lambda: 'console')

    indicator = progress_mod.ActivityIndicator(label='Fitting...', verbosity=VerbosityEnum.FULL)
    indicator.start()
    indicator._current_frame = lambda: 'X'

    assert indicator._live is not None
    assert indicator._live.get_renderable is not None
    assert indicator._live.renderable is None
    assert indicator._live.get_renderable().plain == 'X Fitting...'

    indicator.update(label='Sampling...')

    assert indicator._live.refresh_calls == 1
    assert indicator._live.get_renderable().plain == 'X Sampling...'


def test_activity_indicator_render_html_uses_current_label():
    from easydiffraction.display.progress import ActivityIndicator

    indicator = ActivityIndicator(label='Fitting...', verbosity=VerbosityEnum.FULL)
    indicator._running = True

    html = indicator._render_html()

    assert 'Fitting...' in html

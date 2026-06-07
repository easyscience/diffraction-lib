# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Supplementary coverage tests for display/progress.py."""

from __future__ import annotations

import easydiffraction.display.progress as progress_mod
from easydiffraction.utils.enums import VerbosityEnum

_BOOM = 'boom'


class _FakeHTML:
    """Minimal stand-in for ``IPython.display.HTML``."""

    def __init__(self, data):
        self.data = data


class _FakeJavascript:
    """Minimal stand-in for ``IPython.display.Javascript``."""

    def __init__(self, data):
        self.data = data


class _FakeDisplayHandle:
    """Minimal stand-in for ``IPython.display.DisplayHandle``."""

    def __init__(self):
        self.displayed = []
        self.updated = []

    def display(self, obj):
        self.displayed.append(obj)

    def update(self, obj):
        self.updated.append(obj)


# ---------------------------------------------------------------------------
# resolve_activity_terminal_style
# ---------------------------------------------------------------------------


def test_resolve_activity_terminal_style_default_when_no_console():
    style = progress_mod.resolve_activity_terminal_style(None)

    assert style == progress_mod.ACTIVITY_TERMINAL_STYLE


def test_resolve_activity_terminal_style_fallback_for_standard():
    class FakeConsole:
        color_system = 'standard'

    style = progress_mod.resolve_activity_terminal_style(FakeConsole())

    assert style == progress_mod.ACTIVITY_TERMINAL_FALLBACK_STYLE


def test_resolve_activity_terminal_style_fallback_for_windows():
    class FakeConsole:
        color_system = 'windows'

    style = progress_mod.resolve_activity_terminal_style(FakeConsole())

    assert style == progress_mod.ACTIVITY_TERMINAL_FALLBACK_STYLE


def test_resolve_activity_terminal_style_accent_for_truecolor():
    class FakeConsole:
        color_system = 'truecolor'

    style = progress_mod.resolve_activity_terminal_style(FakeConsole())

    assert style == progress_mod.ACTIVITY_TERMINAL_STYLE


# ---------------------------------------------------------------------------
# make_display_handle (Jupyter branch)
# ---------------------------------------------------------------------------


def test_make_display_handle_returns_display_handle_in_jupyter(monkeypatch):
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: True)
    monkeypatch.setattr(progress_mod, 'DisplayHandle', _FakeDisplayHandle)
    monkeypatch.setattr(progress_mod, 'HTML', _FakeHTML)

    handle = progress_mod.make_display_handle()

    assert isinstance(handle, _FakeDisplayHandle)
    # An empty HTML payload was displayed to reserve the output area.
    assert len(handle.displayed) == 1
    assert isinstance(handle.displayed[0], _FakeHTML)
    assert handle.displayed[0].data == ''


# ---------------------------------------------------------------------------
# _TerminalLiveHandle internals
# ---------------------------------------------------------------------------


def test_terminal_live_handle_resolves_callable_renderable(monkeypatch):
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: False)
    monkeypatch.setattr(progress_mod.ConsoleManager, 'get', lambda: 'console')

    captured = {}

    class FakeLive:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.refresh_calls = 0

        def start(self):
            pass

        def stop(self):
            pass

        def refresh(self):
            self.refresh_calls += 1

    monkeypatch.setattr(progress_mod, 'Live', FakeLive)

    handle = progress_mod.make_display_handle()
    # A callable renderable is invoked lazily by the live get_renderable hook.
    handle.update(lambda: 'lazy-value')

    assert captured['get_renderable']() == 'lazy-value'


def test_terminal_live_handle_close_suppresses_stop_errors(monkeypatch):
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: False)
    monkeypatch.setattr(progress_mod.ConsoleManager, 'get', lambda: 'console')

    class FakeLive:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            raise RuntimeError(_BOOM)

        def refresh(self):
            pass

    monkeypatch.setattr(progress_mod, 'Live', FakeLive)

    handle = progress_mod.make_display_handle()
    # Errors raised by Live.stop() are swallowed so teardown never fails.
    handle.close()


# ---------------------------------------------------------------------------
# ActivityIndicator.start (Jupyter branch) and update/stop
# ---------------------------------------------------------------------------


def test_activity_indicator_start_in_jupyter_displays_html(monkeypatch):
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: True)
    monkeypatch.setattr(progress_mod, 'DisplayHandle', _FakeDisplayHandle)
    monkeypatch.setattr(progress_mod, 'HTML', _FakeHTML)

    indicator = progress_mod.ActivityIndicator(label='Fitting...', verbosity=VerbosityEnum.FULL)
    indicator.start()

    assert isinstance(indicator._display_handle, _FakeDisplayHandle)
    assert indicator._live is None
    assert len(indicator._display_handle.displayed) == 1
    assert 'Fitting...' in indicator._display_handle.displayed[0].data


def test_activity_indicator_start_is_idempotent_when_running(monkeypatch):
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: True)
    monkeypatch.setattr(progress_mod, 'DisplayHandle', _FakeDisplayHandle)
    monkeypatch.setattr(progress_mod, 'HTML', _FakeHTML)

    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    indicator.start()
    first_handle = indicator._display_handle

    indicator.start()

    # A second start() while running must not replace the handle.
    assert indicator._display_handle is first_handle


def test_activity_indicator_update_keeps_label_and_content_when_none(monkeypatch):
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: True)
    monkeypatch.setattr(progress_mod, 'DisplayHandle', _FakeDisplayHandle)
    monkeypatch.setattr(progress_mod, 'HTML', _FakeHTML)

    indicator = progress_mod.ActivityIndicator(label='Fitting...', verbosity=VerbosityEnum.FULL)
    indicator.start()
    indicator.update(content='partial output')

    assert indicator._label == 'Fitting...'
    assert indicator._content == 'partial output'

    indicator.update()  # both None: label and content unchanged

    assert indicator._label == 'Fitting...'
    assert indicator._content == 'partial output'


def test_activity_indicator_update_replaces_label(monkeypatch):
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: True)
    monkeypatch.setattr(progress_mod, 'DisplayHandle', _FakeDisplayHandle)
    monkeypatch.setattr(progress_mod, 'HTML', _FakeHTML)

    indicator = progress_mod.ActivityIndicator(label='Fitting...', verbosity=VerbosityEnum.FULL)
    indicator.start()
    indicator.update(label='Sampling...')

    assert indicator._label == 'Sampling...'


def test_activity_indicator_stop_with_final_label_keeps_label(monkeypatch):
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: True)
    monkeypatch.setattr(progress_mod, 'DisplayHandle', _FakeDisplayHandle)
    monkeypatch.setattr(progress_mod, 'HTML', _FakeHTML)

    indicator = progress_mod.ActivityIndicator(label='Fitting...', verbosity=VerbosityEnum.FULL)
    indicator.start()
    indicator.stop(final_label='Done')

    assert indicator._running is False
    assert indicator._keep_stopped_label is True
    assert indicator._label == 'Done'
    assert indicator._display_handle is None


def test_activity_indicator_stop_without_final_label(monkeypatch):
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: False)
    monkeypatch.setattr(progress_mod.ConsoleManager, 'get', lambda: 'console')

    class FakeLive:
        def __init__(self, **kwargs):
            self.stopped = False

        def start(self):
            pass

        def stop(self):
            self.stopped = True

        def refresh(self):
            pass

    monkeypatch.setattr(progress_mod, 'Live', FakeLive)

    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    indicator.start()
    live = indicator._live
    indicator.stop()

    assert indicator._running is False
    assert indicator._keep_stopped_label is False
    assert live.stopped is True
    assert indicator._live is None


def test_activity_indicator_stop_suppresses_live_stop_errors(monkeypatch):
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: False)
    monkeypatch.setattr(progress_mod.ConsoleManager, 'get', lambda: 'console')

    class FakeLive:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            raise RuntimeError(_BOOM)

        def refresh(self):
            pass

    monkeypatch.setattr(progress_mod, 'Live', FakeLive)

    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    indicator.start()
    # stop() must not propagate Live.stop() errors.
    indicator.stop()

    assert indicator._live is None


# ---------------------------------------------------------------------------
# _terminal_renderable
# ---------------------------------------------------------------------------


def test_terminal_renderable_empty_when_idle():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    # Not running, no content, no kept label -> empty Text.
    result = indicator._terminal_renderable()

    assert isinstance(result, progress_mod.Text)
    assert result.plain == ''


def test_terminal_renderable_single_indicator_line():
    indicator = progress_mod.ActivityIndicator(
        label='Fitting...', verbosity=VerbosityEnum.FULL, animated=False
    )
    indicator._running = True
    result = indicator._terminal_renderable()

    # Only the indicator line present -> returned directly, not grouped.
    assert isinstance(result, progress_mod.Text)
    assert result.plain == 'Fitting...'


def test_terminal_renderable_groups_content_and_indicator():
    indicator = progress_mod.ActivityIndicator(
        label='Fitting...', verbosity=VerbosityEnum.FULL, animated=False
    )
    indicator._running = True
    indicator._content = 'iteration 5'
    result = indicator._terminal_renderable()

    # Content plus indicator line -> a Rich Group.
    assert isinstance(result, progress_mod.Group)


def test_terminal_renderable_content_only_when_stopped():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    content = progress_mod.Text('final output')
    indicator._content = content
    result = indicator._terminal_renderable()

    # Stopped with no kept label: only the content renderable remains, and a
    # single renderable is returned directly rather than wrapped in a Group.
    assert result is content
    assert not isinstance(result, progress_mod.Group)


# ---------------------------------------------------------------------------
# _terminal_content
# ---------------------------------------------------------------------------


def test_terminal_content_none_returns_none():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)

    assert indicator._terminal_content() is None


def test_terminal_content_passes_through_renderable():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    renderable = progress_mod.Text('already renderable')
    indicator._content = renderable

    assert indicator._terminal_content() is renderable


def test_terminal_content_wraps_non_renderable_in_text():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    indicator._content = 12345

    result = indicator._terminal_content()

    assert isinstance(result, progress_mod.Text)
    assert result.plain == '12345'


# ---------------------------------------------------------------------------
# _terminal_indicator_line edge cases
# ---------------------------------------------------------------------------


def test_terminal_indicator_line_keeps_stopped_label():
    indicator = progress_mod.ActivityIndicator(label='Done', verbosity=VerbosityEnum.FULL)
    indicator._running = False
    indicator._keep_stopped_label = True

    line = indicator._terminal_indicator_line()

    assert line is not None
    assert line.plain == 'Done'


def test_terminal_indicator_line_none_when_idle_and_no_label():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    indicator._running = False
    indicator._keep_stopped_label = False

    assert indicator._terminal_indicator_line() is None


def test_terminal_indicator_line_animated_uses_spinner_frame():
    indicator = progress_mod.ActivityIndicator(label='Fitting...', verbosity=VerbosityEnum.FULL)
    indicator._running = True
    indicator._current_frame = lambda: 'Z'

    line = indicator._terminal_indicator_line()

    assert line is not None
    assert line.plain == 'Z Fitting...'


# ---------------------------------------------------------------------------
# _current_frame
# ---------------------------------------------------------------------------


def test_current_frame_returns_valid_spinner_frame(monkeypatch):
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    indicator._started_at = 0.0
    # Elapsed time selects frame index deterministically.
    monkeypatch.setattr(progress_mod, 'monotonic', lambda: 0.25)

    frame = indicator._current_frame()

    expected_index = int(0.25 / progress_mod._SPINNER_FRAME_SECONDS) % len(
        progress_mod.SPINNER_FRAMES
    )
    assert frame == progress_mod.SPINNER_FRAMES[expected_index]


def test_current_frame_wraps_around(monkeypatch):
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    indicator._started_at = 0.0
    # Beyond a full cycle, index wraps back into range.
    monkeypatch.setattr(progress_mod, 'monotonic', lambda: 100.0)

    frame = indicator._current_frame()

    assert frame in progress_mod.SPINNER_FRAMES


# ---------------------------------------------------------------------------
# _render_html and helpers
# ---------------------------------------------------------------------------


def test_render_html_empty_when_idle():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    # Idle: no content and no indicator -> empty string.
    assert indicator._render_html() == ''


def test_render_html_includes_style_and_stack():
    indicator = progress_mod.ActivityIndicator(label='Fitting...', verbosity=VerbosityEnum.FULL)
    indicator._running = True

    html = indicator._render_html()

    assert html.startswith('<style>')
    assert 'ed-activity-stack' in html
    assert 'Fitting...' in html


def test_html_content_none_returns_empty():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)

    assert indicator._html_content() == ''


def test_html_content_str_passthrough():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    indicator._content = '<b>raw html</b>'

    assert indicator._html_content() == '<b>raw html</b>'


def test_html_content_uses_data_attribute():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    indicator._content = _FakeHTML('<div>from data</div>')

    assert indicator._html_content() == '<div>from data</div>'


def test_html_content_escapes_non_str_object():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)

    class NoData:
        def __str__(self):
            return '5 < 6 & 7 > 4'

    indicator._content = NoData()
    result = indicator._html_content()

    assert result.startswith('<pre class="ed-activity-pre">')
    assert '5 &lt; 6 &amp; 7 &gt; 4' in result


def test_html_indicator_animated_running_has_spinner():
    indicator = progress_mod.ActivityIndicator(label='Fit & go', verbosity=VerbosityEnum.FULL)
    indicator._running = True

    html = indicator._html_indicator()

    assert 'ed-activity-spinner' in html
    # Label is HTML-escaped.
    assert 'Fit &amp; go' in html


def test_html_indicator_static_running_has_no_spinner():
    indicator = progress_mod.ActivityIndicator(
        label='Fitting...', verbosity=VerbosityEnum.FULL, animated=False
    )
    indicator._running = True

    html = indicator._html_indicator()

    assert 'ed-activity-spinner' not in html
    assert 'Fitting...' in html


def test_html_indicator_keep_stopped_label():
    indicator = progress_mod.ActivityIndicator(label='Done', verbosity=VerbosityEnum.FULL)
    indicator._running = False
    indicator._keep_stopped_label = True

    html = indicator._html_indicator()

    assert 'ed-activity-spinner' not in html
    assert 'Done' in html


def test_html_indicator_empty_when_idle():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    indicator._running = False
    indicator._keep_stopped_label = False

    assert indicator._html_indicator() == ''


# ---------------------------------------------------------------------------
# _refresh / _refresh_display_handle branches
# ---------------------------------------------------------------------------


def test_refresh_noop_when_silent():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.SILENT)
    # Should return immediately and not touch any handle.
    indicator._refresh()

    assert indicator._display_handle is None
    assert indicator._live is None


def test_refresh_noop_when_no_handle_and_no_live():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    # Not silent, but nothing started: refresh falls through without error.
    indicator._refresh()

    assert indicator._display_handle is None
    assert indicator._live is None


def test_refresh_display_handle_updates_ipython_handle(monkeypatch):
    monkeypatch.setattr(progress_mod, 'HTML', _FakeHTML)
    monkeypatch.setattr(progress_mod, 'DisplayHandle', _FakeDisplayHandle)

    indicator = progress_mod.ActivityIndicator(label='Fitting...', verbosity=VerbosityEnum.FULL)
    indicator._running = True
    handle = _FakeDisplayHandle()
    indicator._display_handle = handle

    indicator._refresh_display_handle()

    assert len(handle.updated) == 1
    assert isinstance(handle.updated[0], _FakeHTML)
    assert 'Fitting...' in handle.updated[0].data


def test_refresh_display_handle_uses_callable_for_terminal_handle(monkeypatch):
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: False)
    monkeypatch.setattr(progress_mod.ConsoleManager, 'get', lambda: 'console')

    class FakeLive:
        def __init__(self, **kwargs):
            self.refresh_calls = 0

        def start(self):
            pass

        def stop(self):
            pass

        def refresh(self):
            self.refresh_calls += 1

    monkeypatch.setattr(progress_mod, 'Live', FakeLive)

    terminal_handle = progress_mod.make_display_handle()
    indicator = progress_mod.ActivityIndicator(
        label='Fitting...', verbosity=VerbosityEnum.FULL, animated=False
    )
    indicator._running = True
    indicator._display_handle = terminal_handle

    indicator._refresh_display_handle()

    # The terminal handle is fed the bound method, not a static renderable.
    assert terminal_handle._renderable == indicator._terminal_renderable


def test_refresh_display_handle_generic_handle(monkeypatch):
    # Neither IPython DisplayHandle nor _TerminalLiveHandle: generic update.
    monkeypatch.setattr(progress_mod, 'HTML', None)
    monkeypatch.setattr(progress_mod, 'DisplayHandle', None)

    class GenericHandle:
        def __init__(self):
            self.updated = []

        def update(self, renderable):
            self.updated.append(renderable)

    indicator = progress_mod.ActivityIndicator(
        label='Fitting...', verbosity=VerbosityEnum.FULL, animated=False
    )
    indicator._running = True
    handle = GenericHandle()
    indicator._display_handle = handle

    indicator._refresh_display_handle()

    assert len(handle.updated) == 1
    assert isinstance(handle.updated[0], progress_mod.Text)
    assert handle.updated[0].plain == 'Fitting...'


def test_refresh_display_handle_noop_when_none():
    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    # No handle set -> silently returns.
    indicator._refresh_display_handle()


def test_refresh_display_handle_suppresses_update_errors(monkeypatch):
    monkeypatch.setattr(progress_mod, 'HTML', _FakeHTML)
    monkeypatch.setattr(progress_mod, 'DisplayHandle', _FakeDisplayHandle)

    class BrokenHandle(_FakeDisplayHandle):
        def update(self, obj):
            raise RuntimeError(_BOOM)

    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    indicator._running = True
    indicator._display_handle = BrokenHandle()

    # Update errors are swallowed so refresh never crashes a fit.
    indicator._refresh_display_handle()


def test_refresh_calls_live_refresh(monkeypatch):
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: False)
    monkeypatch.setattr(progress_mod.ConsoleManager, 'get', lambda: 'console')

    class FakeLive:
        def __init__(self, **kwargs):
            self.refresh_calls = 0

        def start(self):
            pass

        def stop(self):
            pass

        def refresh(self):
            self.refresh_calls += 1

    monkeypatch.setattr(progress_mod, 'Live', FakeLive)

    indicator = progress_mod.ActivityIndicator(verbosity=VerbosityEnum.FULL)
    indicator.start()
    before = indicator._live.refresh_calls
    indicator._refresh()

    assert indicator._live.refresh_calls == before + 1


# ---------------------------------------------------------------------------
# _ActivityIndicatorContext / activity_indicator
# ---------------------------------------------------------------------------


def test_activity_indicator_context_manager_starts_and_stops():
    with progress_mod.activity_indicator(
        label='Fitting...', verbosity=VerbosityEnum.SILENT
    ) as indicator:
        assert isinstance(indicator, progress_mod.ActivityIndicator)
        assert indicator._label == 'Fitting...'

    assert indicator._running is False


def test_activity_indicator_context_default_label():
    ctx = progress_mod.activity_indicator(verbosity=VerbosityEnum.SILENT)

    assert isinstance(ctx, progress_mod._ActivityIndicatorContext)
    assert ctx._indicator._label == progress_mod.ACTIVITY_LABEL_PROCESSING


# ---------------------------------------------------------------------------
# NotebookFitStopControl
# ---------------------------------------------------------------------------


def test_notebook_fit_stop_control_factory_returns_instance(monkeypatch):
    monkeypatch.setattr(
        progress_mod.NotebookFitStopControl, '_current_kernel_id', staticmethod(lambda: '')
    )

    control = progress_mod.notebook_fit_stop_control(verbosity=VerbosityEnum.FULL)

    assert isinstance(control, progress_mod.NotebookFitStopControl)


def test_notebook_fit_stop_control_silent_does_not_display(monkeypatch):
    monkeypatch.setattr(
        progress_mod.NotebookFitStopControl, '_current_kernel_id', staticmethod(lambda: '')
    )
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: True)
    monkeypatch.setattr(progress_mod, 'DisplayHandle', _FakeDisplayHandle)
    monkeypatch.setattr(progress_mod, 'HTML', _FakeHTML)
    monkeypatch.setattr(progress_mod, 'Javascript', _FakeJavascript)
    monkeypatch.setattr(progress_mod, 'display', lambda obj: None)

    control = progress_mod.NotebookFitStopControl(verbosity=VerbosityEnum.SILENT)
    control.show()

    assert control._display_handle is None


def test_notebook_fit_stop_control_not_in_jupyter_does_not_display(monkeypatch):
    monkeypatch.setattr(
        progress_mod.NotebookFitStopControl, '_current_kernel_id', staticmethod(lambda: '')
    )
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: False)
    monkeypatch.setattr(progress_mod, 'DisplayHandle', _FakeDisplayHandle)
    monkeypatch.setattr(progress_mod, 'HTML', _FakeHTML)
    monkeypatch.setattr(progress_mod, 'Javascript', _FakeJavascript)
    monkeypatch.setattr(progress_mod, 'display', lambda obj: None)

    control = progress_mod.NotebookFitStopControl(verbosity=VerbosityEnum.FULL)
    control.show()

    assert control._display_handle is None


def test_notebook_fit_stop_control_shows_button_in_jupyter(monkeypatch):
    monkeypatch.setattr(
        progress_mod.NotebookFitStopControl,
        '_current_kernel_id',
        staticmethod(lambda: 'kernel-xyz'),
    )
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: True)
    monkeypatch.setattr(progress_mod, 'DisplayHandle', _FakeDisplayHandle)
    monkeypatch.setattr(progress_mod, 'HTML', _FakeHTML)
    monkeypatch.setattr(progress_mod, 'Javascript', _FakeJavascript)

    displayed = []
    monkeypatch.setattr(progress_mod, 'display', displayed.append)

    control = progress_mod.NotebookFitStopControl(verbosity=VerbosityEnum.FULL)
    control.show()

    assert isinstance(control._display_handle, _FakeDisplayHandle)
    # The button HTML was displayed and the interrupt JS was injected.
    assert len(control._display_handle.displayed) == 1
    assert 'Stop fitting' in control._display_handle.displayed[0].data
    assert len(displayed) == 1
    assert isinstance(displayed[0], _FakeJavascript)
    # The resolved kernel id is embedded in the injected JavaScript.
    assert 'kernel-xyz' in displayed[0].data


def test_notebook_fit_stop_control_close_clears_handle(monkeypatch):
    monkeypatch.setattr(
        progress_mod.NotebookFitStopControl,
        '_current_kernel_id',
        staticmethod(lambda: 'kernel-xyz'),
    )
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: True)
    monkeypatch.setattr(progress_mod, 'DisplayHandle', _FakeDisplayHandle)
    monkeypatch.setattr(progress_mod, 'HTML', _FakeHTML)
    monkeypatch.setattr(progress_mod, 'Javascript', _FakeJavascript)
    monkeypatch.setattr(progress_mod, 'display', lambda obj: None)

    control = progress_mod.NotebookFitStopControl(verbosity=VerbosityEnum.FULL)
    control.show()
    handle = control._display_handle
    control.close()

    assert control._display_handle is None
    # Closing clears the output area with an empty HTML payload.
    assert handle.updated[-1].data == ''


def test_notebook_fit_stop_control_close_noop_when_no_handle(monkeypatch):
    monkeypatch.setattr(
        progress_mod.NotebookFitStopControl, '_current_kernel_id', staticmethod(lambda: '')
    )
    control = progress_mod.NotebookFitStopControl(verbosity=VerbosityEnum.FULL)
    # No handle was ever shown -> close is a no-op.
    control.close()

    assert control._display_handle is None


def test_notebook_fit_stop_control_context_manager(monkeypatch):
    monkeypatch.setattr(
        progress_mod.NotebookFitStopControl,
        '_current_kernel_id',
        staticmethod(lambda: 'kernel-xyz'),
    )
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: True)
    monkeypatch.setattr(progress_mod, 'DisplayHandle', _FakeDisplayHandle)
    monkeypatch.setattr(progress_mod, 'HTML', _FakeHTML)
    monkeypatch.setattr(progress_mod, 'Javascript', _FakeJavascript)
    monkeypatch.setattr(progress_mod, 'display', lambda obj: None)

    with progress_mod.NotebookFitStopControl(verbosity=VerbosityEnum.FULL) as control:
        assert isinstance(control, progress_mod.NotebookFitStopControl)
        assert control._display_handle is not None

    # Leaving the context clears the handle.
    assert control._display_handle is None


def test_notebook_fit_stop_control_active_html_contains_element_ids(monkeypatch):
    monkeypatch.setattr(
        progress_mod.NotebookFitStopControl, '_current_kernel_id', staticmethod(lambda: '')
    )
    control = progress_mod.NotebookFitStopControl(verbosity=VerbosityEnum.FULL)
    html = control._active_html()

    assert control._element_id in html
    assert f'{control._element_id}-button' in html
    assert f'{control._element_id}-status' in html


def test_notebook_fit_stop_control_interrupt_javascript_embeds_ids(monkeypatch):
    monkeypatch.setattr(
        progress_mod.NotebookFitStopControl,
        '_current_kernel_id',
        staticmethod(lambda: 'kid-123'),
    )
    control = progress_mod.NotebookFitStopControl(verbosity=VerbosityEnum.FULL)
    js = control._interrupt_javascript()

    assert f'{control._element_id}-button' in js
    assert f'{control._element_id}-status' in js
    assert 'kid-123' in js
    assert 'interrupt' in js


def test_notebook_fit_stop_control_show_suppresses_display_errors(monkeypatch):
    monkeypatch.setattr(
        progress_mod.NotebookFitStopControl, '_current_kernel_id', staticmethod(lambda: '')
    )
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: True)

    class BrokenDisplayHandle(_FakeDisplayHandle):
        def display(self, obj):
            raise RuntimeError(_BOOM)

    monkeypatch.setattr(progress_mod, 'DisplayHandle', BrokenDisplayHandle)
    monkeypatch.setattr(progress_mod, 'HTML', _FakeHTML)
    monkeypatch.setattr(progress_mod, 'Javascript', _FakeJavascript)
    monkeypatch.setattr(progress_mod, 'display', lambda obj: None)

    control = progress_mod.NotebookFitStopControl(verbosity=VerbosityEnum.FULL)
    # Display errors are suppressed; show() still completes.
    control.show()


# ---------------------------------------------------------------------------
# _current_kernel_id / _kernel_id_from_connection_file
# ---------------------------------------------------------------------------


def test_kernel_id_from_connection_file_valid():
    result = progress_mod.NotebookFitStopControl._kernel_id_from_connection_file(
        '/run/runtime/kernel-abc123.json'
    )

    assert result == 'abc123'


def test_kernel_id_from_connection_file_wrong_prefix():
    result = progress_mod.NotebookFitStopControl._kernel_id_from_connection_file(
        '/run/runtime/notkernel-abc123.json'
    )

    assert result == ''


def test_kernel_id_from_connection_file_wrong_suffix():
    result = progress_mod.NotebookFitStopControl._kernel_id_from_connection_file(
        '/run/runtime/kernel-abc123.txt'
    )

    assert result == ''


def test_current_kernel_id_from_shell_kernel(monkeypatch):
    import sys
    import types

    class FakeKernel:
        kernel_id = 'shell-kernel-id'

    class FakeShell:
        kernel = FakeKernel()

    shell = FakeShell()

    def get_ipython():
        return shell

    fake_ipython = types.ModuleType('IPython')
    fake_ipython.get_ipython = get_ipython
    monkeypatch.setitem(sys.modules, 'IPython', fake_ipython)

    result = progress_mod.NotebookFitStopControl._current_kernel_id()

    assert result == 'shell-kernel-id'


def test_current_kernel_id_falls_back_to_connection_file(monkeypatch):
    import sys
    import types

    class FakeShell:
        kernel = None

    shell = FakeShell()

    def get_ipython():
        return shell

    fake_ipython = types.ModuleType('IPython')
    fake_ipython.get_ipython = get_ipython
    monkeypatch.setitem(sys.modules, 'IPython', fake_ipython)

    def get_connection_file():
        return '/run/kernel-from-file.json'

    fake_connect = types.ModuleType('ipykernel.connect')
    fake_connect.get_connection_file = get_connection_file
    fake_ipykernel = types.ModuleType('ipykernel')
    monkeypatch.setitem(sys.modules, 'ipykernel', fake_ipykernel)
    monkeypatch.setitem(sys.modules, 'ipykernel.connect', fake_connect)

    result = progress_mod.NotebookFitStopControl._current_kernel_id()

    assert result == 'from-file'


def test_current_kernel_id_empty_when_connection_file_raises(monkeypatch):
    import sys
    import types

    class FakeShell:
        kernel = None

    shell = FakeShell()

    def get_ipython():
        return shell

    fake_ipython = types.ModuleType('IPython')
    fake_ipython.get_ipython = get_ipython
    monkeypatch.setitem(sys.modules, 'IPython', fake_ipython)

    def boom():
        msg = 'no connection file'
        raise RuntimeError(msg)

    fake_connect = types.ModuleType('ipykernel.connect')
    fake_connect.get_connection_file = boom
    fake_ipykernel = types.ModuleType('ipykernel')
    monkeypatch.setitem(sys.modules, 'ipykernel', fake_ipykernel)
    monkeypatch.setitem(sys.modules, 'ipykernel.connect', fake_connect)

    # The suppressed exception falls through to the final empty-string return.
    result = progress_mod.NotebookFitStopControl._current_kernel_id()

    assert result == ''


def test_current_kernel_id_empty_when_ipython_missing(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == 'IPython':
            msg = 'no IPython'
            raise ImportError(msg)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', fake_import)

    result = progress_mod.NotebookFitStopControl._current_kernel_id()

    assert result == ''

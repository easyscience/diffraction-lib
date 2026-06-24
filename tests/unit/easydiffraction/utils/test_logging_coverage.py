# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Additional unit tests for logging.py to cover BLE001 branches."""

import logging
import sys

import pytest

from easydiffraction.utils.logging import ConsoleManager
from easydiffraction.utils.logging import ConsolePrinter
from easydiffraction.utils.logging import ExceptionHookManager
from easydiffraction.utils.logging import IconifiedRichHandler
from easydiffraction.utils.logging import Logger
from easydiffraction.utils.logging import _rich_markup_to_inline_html


class TestRenderMessageFallback:
    def test_valid_markup(self):
        """render_message should handle valid Rich markup."""
        import logging

        from easydiffraction.utils.logging import IconifiedRichHandler

        handler = IconifiedRichHandler(mode='compact')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='simple text',
            args=(),
            exc_info=None,
        )
        result = handler.render_message(record, 'simple text')
        assert str(result) == 'simple text'

    def test_invalid_markup_falls_back_to_plain_text(self):
        """render_message should fall back to plain Text on bad markup."""
        import logging

        from easydiffraction.utils.logging import IconifiedRichHandler

        handler = IconifiedRichHandler(mode='compact')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='bad [markup',
            args=(),
            exc_info=None,
        )
        result = handler.render_message(record, 'bad [markup')
        assert 'bad' in str(result)

    def test_verbose_mode_delegates_to_parent(self):
        """render_message in verbose mode delegates to RichHandler."""
        import logging

        from easydiffraction.utils.logging import IconifiedRichHandler

        handler = IconifiedRichHandler(mode='verbose')
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='test msg',
            args=(),
            exc_info=None,
        )
        result = handler.render_message(record, 'test msg')
        assert result is not None


class TestDetectWidth:
    def test_returns_at_least_min_width(self):
        from easydiffraction.utils.logging import ConsoleManager

        width = ConsoleManager._detect_width()
        assert width >= ConsoleManager._MIN_CONSOLE_WIDTH
        assert isinstance(width, int)


class TestGetLevelText:
    def test_compact_mode_returns_icon(self):
        import logging

        from easydiffraction.utils.logging import IconifiedRichHandler

        handler = IconifiedRichHandler(mode='compact')
        record = logging.LogRecord(
            name='test',
            level=logging.WARNING,
            pathname='',
            lineno=0,
            msg='w',
            args=(),
            exc_info=None,
        )
        text = handler.get_level_text(record)
        assert text is not None

    def test_verbose_mode_returns_level_name(self):
        import logging

        from easydiffraction.utils.logging import IconifiedRichHandler

        handler = IconifiedRichHandler(mode='verbose')
        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='',
            lineno=0,
            msg='e',
            args=(),
            exc_info=None,
        )
        text = handler.get_level_text(record)
        assert text is not None


class TestLoggerConfigure:
    def test_configure_with_env_vars(self, monkeypatch):
        from easydiffraction.utils.logging import Logger

        monkeypatch.setenv('ED_LOG_MODE', 'verbose')
        monkeypatch.setenv('ED_LOG_LEVEL', 'DEBUG')
        monkeypatch.setenv('ED_LOG_REACTION', 'WARN')

        Logger._configured = False
        Logger.configure()
        assert Logger._mode == Logger.Mode.VERBOSE
        assert Logger._reaction == Logger.Reaction.WARN

        # Reset to defaults for other tests
        Logger.configure(
            mode=Logger.Mode.COMPACT,
            level=Logger.Level.WARNING,
            reaction=Logger.Reaction.RAISE,
        )

    def test_configure_with_invalid_env_vars(self, monkeypatch):
        from easydiffraction.utils.logging import Logger

        monkeypatch.setenv('ED_LOG_MODE', 'invalid_mode')
        monkeypatch.setenv('ED_LOG_LEVEL', 'INVALID_LEVEL')
        monkeypatch.setenv('ED_LOG_REACTION', 'INVALID')

        Logger._configured = False
        Logger.configure()
        # Should fall back to defaults
        assert Logger._mode == Logger.Mode.COMPACT
        assert Logger._reaction == Logger.Reaction.RAISE

        # Reset
        Logger.configure(
            mode=Logger.Mode.COMPACT,
            level=Logger.Level.WARNING,
            reaction=Logger.Reaction.RAISE,
        )


@pytest.fixture
def restore_logger_state():
    """Snapshot and restore Logger global state around a test.

    Logging is global; tests that call ``Logger.configure`` or mutate
    class attributes must not leak state into sibling test files.
    """
    saved_mode = Logger._mode
    saved_reaction = Logger._reaction
    saved_configured = Logger._configured
    saved_level = Logger._logger.level
    saved_excepthook = sys.excepthook
    saved_orig = getattr(Logger, '_orig_excepthook', None)
    saved_had_orig = hasattr(Logger, '_orig_excepthook')
    yield
    Logger._mode = saved_mode
    Logger._reaction = saved_reaction
    Logger._configured = saved_configured
    Logger._logger.setLevel(saved_level)
    sys.excepthook = saved_excepthook
    if saved_had_orig:
        Logger._orig_excepthook = saved_orig
    elif hasattr(Logger, '_orig_excepthook'):
        del Logger._orig_excepthook


def _make_record(level=logging.WARNING, msg='msg'):
    return logging.LogRecord(
        name='test',
        level=level,
        pathname='',
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None,
    )


class TestGetLevelTextWarp:
    def test_warp_pads_two_char_icons(self, monkeypatch):
        """In Warp (non-Jupyter) one-char icons get a trailing space."""
        monkeypatch.setattr('easydiffraction.utils.logging.in_warp', lambda: True)
        monkeypatch.setattr('easydiffraction.utils.logging.in_jupyter', lambda: False)
        handler = IconifiedRichHandler(mode='compact')
        text = handler.get_level_text(_make_record(level=logging.WARNING))
        # The warning icon should be padded with a trailing space.
        assert str(text).endswith(' ')
        assert str(text).startswith('⚠')

    def test_warp_does_not_pad_two_char_critical(self, monkeypatch):
        """Two-char icons (e.g. CRITICAL) are not padded in Warp."""
        monkeypatch.setattr('easydiffraction.utils.logging.in_warp', lambda: True)
        monkeypatch.setattr('easydiffraction.utils.logging.in_jupyter', lambda: False)
        handler = IconifiedRichHandler(mode='compact')
        text = handler.get_level_text(_make_record(level=logging.CRITICAL))
        assert str(text) == '💀'

    def test_unknown_level_falls_back_to_levelname(self):
        """Unknown levels render the level name, not an icon."""
        handler = IconifiedRichHandler(mode='compact')
        record = _make_record(level=15, msg='x')
        record.levelname = 'CUSTOM'
        text = handler.get_level_text(record)
        assert str(text) == 'CUSTOM'


class TestRenderMessageInvalidMarkupBranch:
    def test_unbalanced_close_tag_falls_back(self):
        """Markup that raises MarkupError falls back to plain text."""
        handler = IconifiedRichHandler(mode='compact')
        message = '[/]'
        result = handler.render_message(_make_record(), message)
        assert str(result) == message


class TestDetectWidthFallback:
    def test_falls_back_to_min_width_on_oserror(self):
        """When get_terminal_size raises, width clamps to the minimum."""
        import easydiffraction.utils.logging as mut

        def boom(*args, **kwargs):
            msg = 'no terminal'
            raise OSError(msg)

        # ``shutil.get_terminal_size`` is a global shared with the test
        # runner, so patch it only around the single call under test and
        # restore it immediately -- a monkeypatch teardown would still be
        # active while pytest formats results and would crash the run.
        original = mut.shutil.get_terminal_size
        mut.shutil.get_terminal_size = boom
        try:
            width = ConsoleManager._detect_width()
        finally:
            mut.shutil.get_terminal_size = original
        assert width == ConsoleManager._MIN_CONSOLE_WIDTH


class TestSetupHandlersJupyter:
    def test_installs_traceback_in_jupyter(self, monkeypatch):
        """In Jupyter, setup_handlers installs the rich traceback hook."""
        from easydiffraction.utils.logging import LoggerConfig

        monkeypatch.setattr('easydiffraction.utils.logging.in_jupyter', lambda: True)
        calls = []
        monkeypatch.setattr(
            'easydiffraction.utils.logging.traceback.install',
            lambda **kwargs: calls.append(kwargs),
        )
        scratch = logging.getLogger('easydiffraction.test.setup')
        LoggerConfig.setup_handlers(scratch, level=logging.INFO, rich_tracebacks=False)
        assert calls
        assert calls[0]['suppress'] == ['easydiffraction']
        scratch.handlers.clear()


class TestLoggerConfigVerboseNoTraceback:
    def test_verbose_without_rich_tracebacks_restores_hook(
        self, monkeypatch, restore_logger_state
    ):
        """VERBOSE mode without rich tracebacks restores the original hook."""
        from easydiffraction.utils.logging import LoggerConfig

        monkeypatch.setattr('easydiffraction.utils.logging.in_jupyter', lambda: False)
        restored = []
        monkeypatch.setattr(
            ExceptionHookManager,
            'restore_original_hook',
            staticmethod(lambda: restored.append(True)),
        )
        LoggerConfig.configure(
            Logger._logger,
            mode=Logger.Mode.VERBOSE,
            level=Logger.Level.WARNING,
            rich_tracebacks=False,
        )
        assert restored == [True]


class TestVerboseExceptionHook:
    def test_aligned_excepthook_logs_and_restores_args(self, monkeypatch, restore_logger_state):
        """The verbose hook logs the exception then restores exc.args."""
        if hasattr(Logger, '_orig_excepthook'):
            del Logger._orig_excepthook
        ExceptionHookManager.install_verbose_hook(Logger._logger)
        # Original hook is captured the first time.
        assert hasattr(Logger, '_orig_excepthook')

        logged = []
        monkeypatch.setattr(
            Logger._logger,
            'error',
            lambda msg, **kwargs: logged.append((msg, kwargs)),
        )
        exc = ValueError('boom')
        sys.excepthook(ValueError, exc, None)
        assert logged[0][0] == 'boom'
        assert 'exc_info' in logged[0][1]
        # exc.args restored after the hook finishes.
        assert exc.args == ('boom',)

    def test_aligned_excepthook_logging_failure_falls_back(
        self, monkeypatch, restore_logger_state
    ):
        """If logger.error raises, the hook falls back to logger.exception."""
        if hasattr(Logger, '_orig_excepthook'):
            del Logger._orig_excepthook
        ExceptionHookManager.install_verbose_hook(Logger._logger)

        def failing_error(msg, **kwargs):
            err = 'logging broke'
            raise RuntimeError(err)

        captured = []
        monkeypatch.setattr(Logger._logger, 'error', failing_error)
        monkeypatch.setattr(Logger._logger, 'exception', captured.append)
        sys.excepthook(ValueError, ValueError('x'), None)
        assert captured == ['Unhandled exception (logging failure)']

    def test_install_verbose_hook_keeps_existing_orig(self, restore_logger_state):
        """A second install must not overwrite the captured original hook."""
        sentinel = object()
        Logger._orig_excepthook = sentinel
        ExceptionHookManager.install_verbose_hook(Logger._logger)
        assert Logger._orig_excepthook is sentinel


class TestCompactExceptionHook:
    def test_compact_excepthook_logs_and_exits(self, monkeypatch, restore_logger_state):
        """The compact hook logs the message and raises SystemExit(1)."""
        if hasattr(Logger, '_orig_excepthook'):
            del Logger._orig_excepthook
        ExceptionHookManager.install_compact_hook(Logger._logger)
        logged = []
        monkeypatch.setattr(Logger._logger, 'error', logged.append)
        with pytest.raises(SystemExit) as excinfo:
            sys.excepthook(ValueError, ValueError('compact boom'), None)
        assert excinfo.value.code == 1
        assert logged == ['compact boom']


class TestRestoreOriginalHook:
    def test_restores_saved_hook(self, restore_logger_state):
        """restore_original_hook reinstates the saved sys.excepthook."""
        sentinel = lambda *a: None  # noqa: E731
        Logger._orig_excepthook = sentinel
        sys.excepthook = lambda *a: None
        ExceptionHookManager.restore_original_hook()
        assert sys.excepthook is sentinel

    def test_noop_when_no_saved_hook(self, restore_logger_state):
        """restore_original_hook is a no-op without a saved hook."""
        if hasattr(Logger, '_orig_excepthook'):
            del Logger._orig_excepthook
        before = sys.excepthook
        ExceptionHookManager.restore_original_hook()
        assert sys.excepthook is before


class TestSuppressTraceback:
    def test_logs_evalue_from_positional_args(self):
        """The Jupyter suppressor logs the evalue passed positionally."""
        logged = []

        class FakeLogger:
            def error(self, msg):
                logged.append(msg)

            def debug(self, *args):
                pass

        callback = ExceptionHookManager._suppress_traceback(FakeLogger())
        # IPython passes (shell, etype, evalue, tb, tb_offset)
        callback('shell', ValueError, ValueError('jvalue'), None, 0)
        assert logged == ['jvalue']

    def test_logs_evalue_from_kwargs(self):
        """The suppressor reads evalue from kwargs when not positional."""
        logged = []

        class FakeLogger:
            def error(self, msg):
                logged.append(msg)

            def debug(self, *args):
                pass

        callback = ExceptionHookManager._suppress_traceback(FakeLogger())
        callback(evalue=RuntimeError('kw'))
        assert logged == ['kw']

    def test_swallows_logger_error_via_debug(self):
        """If error() raises a handled error, it is routed to debug()."""
        debugged = []

        class FakeLogger:
            def error(self, msg):
                err = 'bad logger'
                raise TypeError(err)

            def debug(self, *args):
                debugged.append(args)

        callback = ExceptionHookManager._suppress_traceback(FakeLogger())
        callback('shell', ValueError, ValueError('v'), None, 0)
        assert debugged


class TestInstallJupyterTracebackSuppressor:
    def test_no_ipython_logs_debug(self, monkeypatch):
        """When IPython import fails, a debug message is emitted."""
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == 'IPython':
                err = 'no IPython'
                raise ImportError(err)
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, '__import__', fake_import)
        debugged = []

        class FakeLogger:
            def debug(self, msg):
                debugged.append(msg)

        ExceptionHookManager.install_jupyter_traceback_suppressor(FakeLogger())
        assert debugged
        assert 'Failed to install Jupyter traceback suppressor' in debugged[0]

    def test_sets_custom_exc_when_ipython_present(self, monkeypatch):
        """When IPython is present, set_custom_exc is wired up."""
        import types

        recorded = {}

        class FakeShell:
            def set_custom_exc(self, exc_types, handler):
                recorded['exc_types'] = exc_types
                recorded['handler'] = handler

        shell = FakeShell()
        fake_ipython = types.ModuleType('IPython')
        fake_ipython.get_ipython = lambda: shell
        monkeypatch.setitem(sys.modules, 'IPython', fake_ipython)

        ExceptionHookManager.install_jupyter_traceback_suppressor(Logger._logger)
        assert recorded['exc_types'] == (BaseException,)
        assert callable(recorded['handler'])

    def test_install_via_logger_classmethod(self, monkeypatch):
        """Logger._install_jupyter_traceback_suppressor delegates correctly."""
        called = []
        monkeypatch.setattr(
            ExceptionHookManager,
            'install_jupyter_traceback_suppressor',
            staticmethod(called.append),
        )
        Logger._install_jupyter_traceback_suppressor()
        assert called == [Logger._logger]


class TestModeAccessor:
    def test_mode_returns_current_mode(self, restore_logger_state):
        """Logger.mode() returns the active mode."""
        Logger._mode = Logger.Mode.VERBOSE
        assert Logger.mode() is Logger.Mode.VERBOSE
        Logger._mode = Logger.Mode.COMPACT
        assert Logger.mode() is Logger.Mode.COMPACT


class TestHandleRouting:
    def test_userwarning_in_pytest_emits_warning(self, monkeypatch, restore_logger_state):
        """UserWarning path warns (captured by pytest) when in pytest."""
        Logger._configured = True
        monkeypatch.setattr('easydiffraction.utils.logging.in_pytest', lambda: True)
        with pytest.warns(UserWarning, match='warn-path'):
            Logger.handle('warn-path', exc_type=UserWarning)

    def test_userwarning_outside_pytest_logs_warning(self, monkeypatch, restore_logger_state):
        """UserWarning path logs a warning when not in pytest."""
        Logger._configured = True
        monkeypatch.setattr('easydiffraction.utils.logging.in_pytest', lambda: False)
        logged = []
        monkeypatch.setattr(Logger._logger, 'warning', logged.append)
        Logger.handle('outside', exc_type=UserWarning)
        assert logged == ['outside']

    def test_reaction_warn_logs_and_continues(self, monkeypatch, restore_logger_state):
        """Reaction.WARN logs at the given level without raising."""
        Logger._configured = True
        Logger._reaction = Logger.Reaction.WARN
        logged = []
        monkeypatch.setattr(
            Logger._logger,
            'log',
            lambda level, msg: logged.append((level, msg)),
        )
        Logger.handle('keep-going', level=Logger.Level.ERROR)
        assert logged == [(int(Logger.Level.ERROR), 'keep-going')]

    def test_verbose_mode_raises_with_chain(self, restore_logger_state):
        """VERBOSE mode raises the requested exception type."""
        Logger._configured = True
        Logger._reaction = Logger.Reaction.RAISE
        Logger._mode = Logger.Mode.VERBOSE
        with pytest.raises(KeyError, match='boom'):
            Logger.handle('boom', exc_type=KeyError)

    def test_compact_mode_raises_suppressing_context(self, restore_logger_state):
        """COMPACT mode raises with the cause suppressed (from None)."""
        Logger._configured = True
        Logger._reaction = Logger.Reaction.RAISE
        Logger._mode = Logger.Mode.COMPACT
        with pytest.raises(ValueError, match='compact') as excinfo:
            Logger.handle('compact', exc_type=ValueError)
        assert excinfo.value.__suppress_context__ is True

    def test_no_exc_type_logs_message(self, monkeypatch, restore_logger_state):
        """With exc_type=None and RAISE reaction, the message is logged."""
        Logger._configured = True
        Logger._reaction = Logger.Reaction.RAISE
        Logger._mode = Logger.Mode.COMPACT
        logged = []
        monkeypatch.setattr(
            Logger._logger,
            'log',
            lambda level, msg: logged.append((level, msg)),
        )
        Logger.handle('plain', level=Logger.Level.INFO, exc_type=None)
        assert logged == [(int(Logger.Level.INFO), 'plain')]


class TestConvenienceCritical:
    def test_critical_raises_runtimeerror_by_default(self, restore_logger_state):
        """critical() raises RuntimeError by default in raise mode."""
        Logger._configured = True
        Logger._reaction = Logger.Reaction.RAISE
        Logger._mode = Logger.Mode.VERBOSE
        with pytest.raises(RuntimeError, match='fatal'):
            Logger.critical('fatal')


class TestRichMarkupToInlineHtml:
    def test_red_markup_becomes_span(self):
        """[red]…[/red] becomes a colored inline span."""
        out = _rich_markup_to_inline_html('[red]danger[/red]')
        assert out == '<span style="color:#dc3545">danger</span>'

    def test_dim_tags_are_stripped(self):
        """[dim]/[/dim] tags are removed entirely."""
        out = _rich_markup_to_inline_html('[dim]quiet[/dim]')
        assert out == 'quiet'

    def test_special_characters_are_escaped(self):
        """Angle brackets and ampersands are HTML-escaped."""
        out = _rich_markup_to_inline_html('a < b & c')
        assert '&lt;' in out
        assert '&amp;' in out


class TestConsolePrinterPrint:
    def test_print_joins_strings(self, monkeypatch):
        """Multiple string objects are space-joined."""
        captured = []
        monkeypatch.setattr(
            ConsolePrinter._console,
            'print',
            lambda renderable, **kwargs: captured.append(renderable),
        )
        ConsolePrinter.print('a', 'b', 'c')
        assert captured == ['a b c']

    def test_print_path_is_stringified(self, monkeypatch):
        """Path objects are converted to strings."""
        from pathlib import Path

        captured = []
        monkeypatch.setattr(
            ConsolePrinter._console,
            'print',
            lambda renderable, **kwargs: captured.append(renderable),
        )
        ConsolePrinter.print(Path('/some/dir/x'))
        # str(Path) is platform-specific (backslashes on Windows), so
        # compare against the stringified Path rather than a literal.
        assert captured == [str(Path('/some/dir/x'))]

    def test_print_mixed_uses_group(self, monkeypatch):
        """Mixed renderable and string objects render as a Group."""
        from rich.console import Group
        from rich.text import Text

        captured = []
        monkeypatch.setattr(
            ConsolePrinter._console,
            'print',
            lambda renderable, **kwargs: captured.append(renderable),
        )
        ConsolePrinter.print(Text('rich'), 42)
        assert isinstance(captured[0], Group)


class TestConsolePrinterParagraph:
    def test_quoted_substrings_unstyled(self, monkeypatch):
        """Single-quoted substrings render without the heading style."""
        monkeypatch.setattr('easydiffraction.utils.logging.in_jupyter', lambda: False)
        captured = []
        monkeypatch.setattr(
            ConsolePrinter._console,
            'print',
            lambda text, **kwargs: captured.append(text),
        )
        ConsolePrinter.paragraph("Refine 'param'")
        out = captured[0]
        # Terminal output is prefixed with a newline.
        assert out.startswith('\n')
        assert 'param' in out

    def test_jupyter_no_leading_newline(self, monkeypatch):
        """In Jupyter no leading newline is added to paragraphs."""
        monkeypatch.setattr('easydiffraction.utils.logging.in_jupyter', lambda: True)
        captured = []
        monkeypatch.setattr(
            ConsolePrinter._console,
            'print',
            lambda text, **kwargs: captured.append(text),
        )
        ConsolePrinter.paragraph('Heading')
        assert not captured[0].startswith('\n')


class TestConsolePrinterSection:
    def test_section_terminal(self, monkeypatch):
        """Section header is uppercased and underlined in the terminal."""
        monkeypatch.setattr('easydiffraction.utils.logging.in_jupyter', lambda: False)
        captured = []
        monkeypatch.setattr(
            ConsolePrinter._console,
            'print',
            lambda text, **kwargs: captured.append(text),
        )
        ConsolePrinter.section('intro')
        out = captured[0]
        assert out.startswith('\n')
        assert 'INTRO' in out
        assert '[bold green]' in out


class TestConsolePrinterSmall:
    def test_empty_lines_is_noop(self, monkeypatch):
        """small() with no lines prints nothing."""
        monkeypatch.setattr('easydiffraction.utils.logging.in_jupyter', lambda: False)
        captured = []
        monkeypatch.setattr(
            ConsolePrinter._console,
            'print',
            lambda text, **kwargs: captured.append(text),
        )
        ConsolePrinter.small()
        assert captured == []

    def test_terminal_lines_use_dim_markup(self, monkeypatch):
        """In a terminal, each line is wrapped in dim markup."""
        monkeypatch.setattr('easydiffraction.utils.logging.in_jupyter', lambda: False)
        captured = []
        monkeypatch.setattr(
            ConsolePrinter._console,
            'print',
            lambda text, **kwargs: captured.append(text),
        )
        ConsolePrinter.small('one', 'two')
        assert captured == ['[dim]one[/dim]', '[dim]two[/dim]']

    def test_jupyter_uses_html_display(self, monkeypatch):
        """In Jupyter, small() displays an HTML element with the lines."""
        import types

        monkeypatch.setattr('easydiffraction.utils.logging.in_jupyter', lambda: True)
        displayed = []

        fake_display_mod = types.ModuleType('IPython.display')
        fake_display_mod.HTML = lambda body: ('HTML', body)
        fake_display_mod.display = displayed.append
        fake_ipython = types.ModuleType('IPython')
        fake_ipython.display = fake_display_mod
        monkeypatch.setitem(sys.modules, 'IPython', fake_ipython)
        monkeypatch.setitem(sys.modules, 'IPython.display', fake_display_mod)

        ConsolePrinter.small('[red]warn[/red]', 'note')
        assert displayed
        kind, body = displayed[0]
        assert kind == 'HTML'
        assert '<span style="color:#dc3545">warn</span>' in body
        assert '<br>' in body


class TestConsolePrinterChapter:
    def test_chapter_terminal(self, monkeypatch):
        """Chapter header is centered, magenta, and uppercased."""
        monkeypatch.setattr('easydiffraction.utils.logging.in_jupyter', lambda: False)
        captured = []
        monkeypatch.setattr(
            ConsolePrinter._console,
            'print',
            lambda text, **kwargs: captured.append(text),
        )
        ConsolePrinter.chapter('overview')
        out = captured[0]
        assert out.startswith('\n')
        assert 'OVERVIEW' in out
        assert '[bold magenta]' in out

    def test_chapter_jupyter_no_newline(self, monkeypatch):
        """In Jupyter the chapter header has no leading newline."""
        monkeypatch.setattr('easydiffraction.utils.logging.in_jupyter', lambda: True)
        captured = []
        monkeypatch.setattr(
            ConsolePrinter._console,
            'print',
            lambda text, **kwargs: captured.append(text),
        )
        ConsolePrinter.chapter('overview')
        assert not captured[0].startswith('\n')

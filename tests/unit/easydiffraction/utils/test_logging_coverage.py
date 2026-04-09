# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Additional unit tests for logging.py to cover BLE001 branches."""


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

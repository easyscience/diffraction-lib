# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import logging
import os
import warnings
from contextlib import suppress
from enum import Enum
from enum import IntEnum
from enum import auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

import re
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.console import Group
from rich.console import RenderableType
from rich.logging import RichHandler
from rich.padding import Padding
from rich.text import Text

CONSOLE_WIDTH = 1000


class IconRichHandler(RichHandler):
    _icons = {
        logging.CRITICAL: '💀',
        logging.ERROR: '❌',
        logging.WARNING: '⚠️',
        logging.DEBUG: '💀',
        logging.INFO: 'ℹ️',
    }

    @staticmethod
    def in_warp() -> bool:
        return os.getenv('TERM_PROGRAM') == 'WarpTerminal'

    def get_level_text(self, record: logging.LogRecord) -> Text:
        icon = self._icons.get(record.levelno, record.levelname)
        if self.in_warp() and icon in ['⚠️', '⚙️', 'ℹ️']:
            icon = icon + ' '  # add space to avoid rendering issues in Warp
        return Text(icon)

    def render_message(self, record: logging.LogRecord, message: str) -> Text:
        icon = self._icons.get(record.levelno, record.levelname)
        record = logging.makeLogRecord(record.__dict__)
        record.levelname = icon
        return super().render_message(record, message)


class Logger:
    """Centralized logging with Rich formatting and two modes.

    Environment variables:
    ED_LOG_MODE: set default mode ('verbose' or 'compact')
    ED_LOG_LEVEL: set default level ('DEBUG', 'INFO', etc.)
    """

    class Mode(Enum):
        """Output modes (see :class:`Logger`)."""

        VERBOSE = 'verbose'  # rich traceback panel
        COMPACT = 'compact'  # single line; no traceback

    class Level(IntEnum):
        """Mirror stdlib logging levels."""

        DEBUG = logging.DEBUG
        INFO = logging.INFO
        WARNING = logging.WARNING
        ERROR = logging.ERROR
        CRITICAL = logging.CRITICAL

    class Reaction(Enum):
        """Reaction to errors (see :class:`Logger`)."""

        RAISE = auto()
        WARN = auto()

    _logger = logging.getLogger('easydiffraction')
    _configured = False
    _mode: 'Logger.Mode' = Mode.VERBOSE
    _reaction: 'Logger.Reaction' = Reaction.RAISE  # TODO: not default?
    _console = Console(width=CONSOLE_WIDTH, force_jupyter=False)

    @classmethod
    def print2(cls, *objects, **kwargs):
        """Print objects to the console with left padding.

        - Renderables (Rich types like Text, Table, Panel, etc.) are
            kept as-is.
        - Non-renderables (ints, floats, Path, etc.) are converted to
            str().
        """
        safe_objects = []
        for obj in objects:
            if isinstance(obj, (str, RenderableType)):
                safe_objects.append(obj)
            elif isinstance(obj, Path):
                # Rich can render Path objects, but str() ensures
                # consistency
                safe_objects.append(str(obj))
            else:
                safe_objects.append(str(obj))

        # Join with spaces, like print()
        padded = Padding(*safe_objects, (0, 0, 0, 3))
        cls._console.print(padded, **kwargs)

    @classmethod
    def print(cls, *objects, **kwargs):
        """Print objects to the console with left padding."""
        safe_objects = []
        for obj in objects:
            if isinstance(obj, RenderableType):
                safe_objects.append(obj)
            elif isinstance(obj, Path):
                safe_objects.append(str(obj))
            else:
                safe_objects.append(str(obj))

        # If multiple objects, join with spaces
        renderable = (
            ' '.join(str(o) for o in safe_objects)
            if all(isinstance(o, str) for o in safe_objects)
            else Group(*safe_objects)
        )

        padded = Padding(renderable, (0, 0, 0, 3))
        cls._console.print(padded, **kwargs)

    # ---------------- environment detection ----------------
    @staticmethod
    def _in_jupyter() -> bool:  # pragma: no cover - heuristic
        try:
            from IPython import get_ipython

            return get_ipython() is not None
        except Exception:  # noqa: BLE001
            return False

    @staticmethod
    def _in_pytest() -> bool:
        import sys

        return 'pytest' in sys.modules

    # ---------------- configuration ----------------
    @classmethod
    def configure(
        cls,
        *,
        mode: 'Logger.Mode' | None = None,
        level: 'Logger.Level' | None = None,
        reaction: 'Logger.Reaction' | None = None,
        rich_tracebacks: bool | None = None,
    ) -> None:
        """Configure logger.

        mode: default COMPACT in Jupyter else VERBOSE
        level: minimum log level
        rich_tracebacks: override automatic choice

        Environment variables:
        ED_LOG_MODE: set default mode ('verbose' or 'compact')
        ED_LOG_LEVEL: set default level ('DEBUG', 'INFO', etc.)
        """
        env_mode = os.getenv('ED_LOG_MODE')
        env_level = os.getenv('ED_LOG_LEVEL')
        env_reaction = os.getenv('ED_LOG_REACTION')

        if mode is None and env_mode is not None:
            with suppress(ValueError):
                mode = cls.Mode(env_mode.lower())

        if level is None and env_level is not None:
            with suppress(KeyError):
                level = cls.Level[env_level.upper()]

        if reaction is None and env_reaction is not None:
            with suppress(KeyError):
                reaction = cls.Reaction[env_reaction.upper()]

        if mode is None:
            # Default to VERBOSE even in Jupyter unless explicitly set
            mode = cls.Mode.VERBOSE
        if level is None:
            level = cls.Level.INFO
        if reaction is None:
            reaction = cls.Reaction.RAISE
        cls._mode = mode
        cls._reaction = reaction

        if rich_tracebacks is None:
            rich_tracebacks = mode == cls.Mode.VERBOSE

        log = cls._logger
        log.handlers.clear()
        log.propagate = False
        log.setLevel(int(level))

        from rich.console import Console

        # Enable rich tracebacks inside Jupyter environments
        if cls._in_jupyter():
            from rich import traceback

            traceback.install(
                show_locals=False,
                suppress=['easydiffraction'],
                # max_frames=10 if mode == cls.Mode.VERBOSE else 1,
                # word_wrap=False,
                # extra_lines=0,  # no extra context lines
                # locals_max_length=0,  # no local vars shown
                # locals_max_string=0,  # no local string previews
            )
        console = Console(
            width=CONSOLE_WIDTH,
            # color_system="truecolor",
            force_jupyter=False,
            # force_terminal=False,
            # force_interactive=True,
            # legacy_windows=False,
            # soft_wrap=True,
        )
        handler = RichHandler(
            rich_tracebacks=rich_tracebacks,
            markup=True,
            show_time=False,  # show_time=(mode == cls.Mode.VERBOSE),
            show_path=False,  # show_path=(mode == cls.Mode.VERBOSE),
            tracebacks_show_locals=False,
            tracebacks_suppress=['easydiffraction'],
            tracebacks_max_frames=10,
            console=console,
        )
        handler.setFormatter(logging.Formatter('%(message)s'))
        log.addHandler(handler)
        cls._configured = True

        import sys

        if rich_tracebacks and mode == cls.Mode.VERBOSE:
            if not hasattr(cls, '_orig_excepthook'):
                cls._orig_excepthook = sys.excepthook  # type: ignore[attr-defined]

            def _aligned_excepthook(
                exc_type: type[BaseException],
                exc: BaseException,
                tb: TracebackType | None,
            ) -> None:
                original_args = getattr(exc, 'args', tuple())
                message = str(exc)
                with suppress(Exception):
                    exc.args = tuple()
                try:
                    cls._logger.error(message, exc_info=(exc_type, exc, tb))
                except Exception:  # pragma: no cover
                    cls._logger.error('Unhandled exception (logging failure)')
                with suppress(Exception):
                    exc.args = original_args

            sys.excepthook = _aligned_excepthook  # type: ignore[assignment]
        elif mode == cls.Mode.COMPACT:
            import sys

            if not hasattr(cls, '_orig_excepthook'):
                cls._orig_excepthook = sys.excepthook  # type: ignore[attr-defined]

            def _compact_excepthook(
                _exc_type: type[BaseException],
                exc: BaseException,
                _tb: TracebackType | None,
            ) -> None:
                # Use Rich logger to keep formatting in terminal
                cls._logger.error(str(exc))
                raise SystemExit(1)

            sys.excepthook = _compact_excepthook  # type: ignore[assignment]

            # Disable Jupyter/IPython tracebacks properly
            cls._install_jupyter_traceback_suppressor()
        else:
            if hasattr(cls, '_orig_excepthook'):
                sys.excepthook = cls._orig_excepthook  # type: ignore[attr-defined]

    @classmethod
    def _install_jupyter_traceback_suppressor(cls) -> None:
        """Install traceback suppressor in Jupyter, safely and lint-
        clean.
        """
        try:
            from IPython import get_ipython

            ip = get_ipython()
            if ip is not None:

                def _suppress_jupyter_traceback(
                    _shell,
                    _etype,
                    _evalue,
                    _tb,
                    _tb_offset=None,
                ):
                    cls._logger.error(str(_evalue))
                    return None

                ip.set_custom_exc((BaseException,), _suppress_jupyter_traceback)
        except Exception as err:
            msg = f'Failed to install Jupyter traceback suppressor: {err!r}'
            cls._logger.debug(msg)

    # ---------------- helpers ----------------
    @classmethod
    def set_mode(cls, mode: 'Logger.Mode') -> None:
        cls.configure(mode=mode, level=cls.Level(cls._logger.level))

    @classmethod
    def set_level(cls, level: 'Logger.Level') -> None:
        cls.configure(mode=cls._mode, level=level)

    @classmethod
    def mode(cls) -> 'Logger.Mode':
        return cls._mode

    @classmethod
    def _lazy_config(cls) -> None:
        if not cls._configured:  # pragma: no cover - trivial
            cls.configure()

    # ---------------- text formatting helpers ----------------
    @staticmethod
    def _chapter(title: str) -> str:
        """Formats a chapter header with bold magenta text, uppercase,
        and padding.
        """
        width = 80
        symbol = '─'
        full_title = f' {title.upper()} '
        pad_len = (width - len(full_title)) // 2
        padding = symbol * pad_len
        line = f'[bold magenta]{padding}{full_title}{padding}[/bold magenta]'
        if len(line) < width:
            line += symbol
        formatted = f'{line}'
        from easydiffraction.utils.env import is_notebook as in_jupyter

        if not in_jupyter():
            formatted = f'\n{formatted}'
        return formatted

    @staticmethod
    def _section(title: str) -> str:
        """Formats a section header with bold green text."""
        full_title = f'{title.upper()}'
        line = '━' * len(full_title)
        formatted = f'[bold green]{full_title}\n{line}[/bold green]'

        # Avoid injecting extra newlines; callers can separate sections
        return formatted

    @staticmethod
    def _paragraph(message: str) -> Text:
        parts = re.split(r"('.*?')", message)
        text = Text()
        for part in parts:
            if part.startswith("'") and part.endswith("'"):
                text.append(part)
            else:
                text.append(part, style='bold blue')
        formatted = f'{text.markup}'

        # Paragraphs should not force an extra leading newline; rely on
        # caller
        return formatted

    # ---------------- core routing ----------------
    @classmethod
    def handle(
        cls,
        message: str,
        *,
        level: 'Logger.Level' = Level.ERROR,
        exc_type: type[BaseException] | None = AttributeError,
    ) -> None:
        """Route a log message (see class docs for policy)."""
        cls._lazy_config()
        if exc_type is not None:
            if exc_type is UserWarning:
                if cls._in_pytest():
                    # Always issue a real warning so pytest can catch it
                    warnings.warn(message, UserWarning, stacklevel=2)
                else:
                    # Outside pytest → normal Rich logging
                    cls._logger.warning(message)
                return
            if cls._mode is cls.Mode.VERBOSE:
                raise exc_type(message)
            if cls._mode is cls.Mode.COMPACT:
                raise exc_type(message) from None
        cls._logger.log(int(level), message)

    # ---------------- convenience API ----------------
    @classmethod
    def debug(cls, *messages: str) -> None:
        for message in messages:
            cls.handle(message, level=cls.Level.DEBUG, exc_type=None)

    @classmethod
    def info(cls, *messages: str) -> None:
        for message in messages:
            cls.handle(message, level=cls.Level.INFO, exc_type=None)

    @classmethod
    def warning(cls, *messages: str, exc_type: type[BaseException] | None = None) -> None:
        for message in messages:
            cls.handle(message, level=cls.Level.WARNING, exc_type=exc_type)

    @classmethod
    def error(cls, *messages: str, exc_type: type[BaseException] = AttributeError) -> None:
        for message in messages:
            if cls._reaction is cls.Reaction.RAISE:
                cls.handle(message, level=cls.Level.ERROR, exc_type=exc_type)
            elif cls._reaction is cls.Reaction.WARN:
                cls.handle(message, level=cls.Level.WARNING, exc_type=UserWarning)

    @classmethod
    def critical(cls, *messages: str, exc_type: type[BaseException] = RuntimeError) -> None:
        for message in messages:
            cls.handle(message, level=cls.Level.CRITICAL, exc_type=exc_type)

    @classmethod
    def exception(cls, message: str) -> None:
        """Log current exception from inside ``except`` block."""
        cls._lazy_config()
        cls._logger.error(message, exc_info=True)

    @classmethod
    def paragraph(cls, message: str) -> None:
        cls.print(cls._paragraph(message))

    @classmethod
    def section(cls, message: str) -> None:
        cls.print(cls._section(message))

    @classmethod
    def chapter(cls, message: str) -> None:
        cls.info(cls._chapter(message))


log = Logger  # ergonomic alias

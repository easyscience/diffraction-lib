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

from rich.logging import RichHandler


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

    # ---------------- environment detection ----------------
    @staticmethod
    def _in_jupyter() -> bool:  # pragma: no cover - heuristic
        try:
            from IPython import get_ipython  # type: ignore[import-not-found]

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
            width=120,
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
            show_time=False,
            show_path=False,
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
    def debug(cls, message: str) -> None:
        cls.handle(message, level=cls.Level.DEBUG, exc_type=None)

    @classmethod
    def info(cls, message: str) -> None:
        cls.handle(message, level=cls.Level.INFO, exc_type=None)

    @classmethod
    def warning(cls, message: str, exc_type: type[BaseException] | None = None) -> None:
        cls.handle(message, level=cls.Level.WARNING, exc_type=exc_type)

    @classmethod
    def error(cls, message: str, exc_type: type[BaseException] = AttributeError) -> None:
        if cls._reaction is cls.Reaction.RAISE:
            cls.handle(message, level=cls.Level.ERROR, exc_type=exc_type)
        elif cls._reaction is cls.Reaction.WARN:
            cls.handle(message, level=cls.Level.WARNING, exc_type=UserWarning)

    @classmethod
    def critical(cls, message: str, exc_type: type[BaseException] = RuntimeError) -> None:
        cls.handle(message, level=cls.Level.CRITICAL, exc_type=exc_type)

    @classmethod
    def exception(cls, message: str) -> None:
        """Log current exception from inside ``except`` block."""
        cls._lazy_config()
        cls._logger.error(message, exc_info=True)


log = Logger  # ergonomic alias

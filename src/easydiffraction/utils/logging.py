from __future__ import annotations

import logging
import warnings
from contextlib import suppress
from enum import Enum
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

from rich.logging import RichHandler


class Logger:
    """Centralized logging with Rich formatting and two modes."""

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

    _logger = logging.getLogger('easydiffraction')
    _configured = False
    _mode: 'Logger.Mode' = Mode.VERBOSE

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
        level: 'Logger.Level' = Level.WARNING,
        rich_tracebacks: bool | None = None,
    ) -> None:
        """Configure logger.

        mode: default COMPACT in Jupyter else VERBOSE
        level: minimum log level
        rich_tracebacks: override automatic choice
        """
        if mode is None:
            mode = cls.Mode.COMPACT if cls._in_jupyter() else cls.Mode.VERBOSE
        cls._mode = mode

        if rich_tracebacks is None:
            rich_tracebacks = mode == cls.Mode.VERBOSE

        log = cls._logger
        log.handlers.clear()
        log.propagate = False
        log.setLevel(int(level))

        from rich.console import Console

        console = Console(width=120)
        handler = RichHandler(
            rich_tracebacks=rich_tracebacks,
            markup=True,
            show_time=True,
            show_path=True,
            tracebacks_show_locals=False,
            tracebacks_suppress=['easydiffraction'],
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
            if not hasattr(cls, '_orig_excepthook'):
                cls._orig_excepthook = sys.excepthook  # type: ignore[attr-defined]

            def _compact_excepthook(
                _exc_type: type[BaseException],
                exc: BaseException,
                _tb: TracebackType | None,
            ) -> None:
                cls._logger.error(str(exc))
                raise SystemExit(1)

            sys.excepthook = _compact_excepthook  # type: ignore[assignment]
        else:
            if hasattr(cls, '_orig_excepthook'):
                sys.excepthook = cls._orig_excepthook  # type: ignore[attr-defined]

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
        cls.handle(message, level=cls.Level.ERROR, exc_type=exc_type)

    @classmethod
    def critical(cls, message: str, exc_type: type[BaseException] = RuntimeError) -> None:
        cls.handle(message, level=cls.Level.CRITICAL, exc_type=exc_type)

    @classmethod
    def exception(cls, message: str) -> None:
        """Log current exception from inside ``except`` block."""
        cls._lazy_config()
        cls._logger.error(message, exc_info=True)


log = Logger  # ergonomic alias

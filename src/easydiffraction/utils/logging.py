from __future__ import annotations

import logging
import warnings
from enum import Enum
from enum import IntEnum

try:
    from rich.logging import RichHandler  # optional dependency
except Exception:
    RichHandler = None


class Logger:
    """Centralized logging + policy (can raise on errors)."""

    class Mode(Enum):
        """Logging behaviour policy.

        Values:
        * ``RAISE``: raise on level >= ERROR.
        * ``LOG``: never raise, only log.
        * ``PRETTY``: rich formatted logs if Rich is available,
          else ``LOG``.
        """

        RAISE = 'raise'
        LOG = 'log'
        PRETTY = 'pretty'

    class Level(IntEnum):
        """Log severity levels (mirror :mod:`logging`)."""

        DEBUG = logging.DEBUG
        INFO = logging.INFO
        WARNING = logging.WARNING
        ERROR = logging.ERROR
        CRITICAL = logging.CRITICAL

    _logger = logging.getLogger('easydiffraction')
    _configured = False
    _mode: 'Logger.Mode' = Mode.RAISE

    @staticmethod
    def _in_jupyter() -> bool:
        try:
            from IPython import get_ipython  # type: ignore[import-not-found]

            return get_ipython() is not None
        except Exception:
            return False

    @classmethod
    def configure(
        cls,
        *,
        mode: 'Logger.Mode' | None = None,
        level: 'Logger.Level' = Level.WARNING,
        rich_tracebacks: bool = False,
    ) -> None:
        """Configure the central logger.

        Parameters
        ----------
        mode:
            Behaviour mode (defaults to PRETTY in notebooks else RAISE).
        level:
            Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        rich_tracebacks:
            Enable rich tracebacks when in PRETTY mode.
        """
        if mode is None:
            mode = cls.Mode.PRETTY if cls._in_jupyter() else cls.Mode.RAISE
        cls._mode = mode

        log = cls._logger
        log.handlers.clear()
        log.propagate = False
        log.setLevel(int(level))

        if mode == cls.Mode.PRETTY and RichHandler is not None:
            handler = RichHandler(rich_tracebacks=rich_tracebacks, markup=True)
        else:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

        log.addHandler(handler)
        cls._configured = True

    # Helper methods to tweak policy/level without full reconfigure
    @classmethod
    def set_mode(cls, mode: 'Logger.Mode') -> None:
        cls.configure(mode=mode, level=cls.Level(cls._logger.level))  # preserve level

    @classmethod
    def set_level(cls, level: 'Logger.Level') -> None:
        cls.configure(mode=cls._mode, level=level)

    @classmethod
    def mode(cls) -> 'Logger.Mode':
        return cls._mode

    # --- Core routing ---
    @classmethod
    def _lazy_config(cls) -> None:
        if not cls._configured:
            cls.configure()  # pick sensible default based on environment

    @classmethod
    def handle(
        cls,
        message: str,
        *,
        level: 'Logger.Level' = Level.ERROR,
        exc_type: type[Exception] | None = AttributeError,
    ) -> None:
        """Route a log message with policy.

        If mode is RAISE:
        * ``exc_type`` is ``UserWarning`` -> emit ``warnings.warn``.
        * ``exc_type`` not ``None`` -> raise the exception instance.
        Otherwise the message is only logged.
        """
        cls._lazy_config()
        cls._logger.log(int(level), message)

        if cls._mode == cls.Mode.RAISE and exc_type:
            if exc_type is UserWarning:
                warnings.warn(message, UserWarning, stacklevel=2)
            else:
                raise exc_type(message)

    # --- Convenience methods (logging-like API) ---
    @classmethod
    def debug(cls, message: str) -> None:
        cls.handle(message, level=cls.Level.DEBUG, exc_type=None)

    @classmethod
    def info(cls, message: str) -> None:
        cls.handle(message, level=cls.Level.INFO, exc_type=None)

    @classmethod
    def warning(cls, message: str, exc_type: type[Exception] | None = None) -> None:
        cls.handle(message, level=cls.Level.WARNING, exc_type=exc_type)

    @classmethod
    def error(cls, message: str, exc_type: type[Exception] = AttributeError) -> None:
        cls.handle(message, level=cls.Level.ERROR, exc_type=exc_type)

    @classmethod
    def critical(cls, message: str, exc_type: type[Exception] = RuntimeError) -> None:
        cls.handle(message, level=cls.Level.CRITICAL, exc_type=exc_type)


# Short alias for ergonomic, notebook-friendly usage:
log = Logger

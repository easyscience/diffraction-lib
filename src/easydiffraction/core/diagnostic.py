# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Diagnostics helpers for logging validation messages.

This module centralizes human-friendly error and debug logs for
attribute validation and configuration checks.
"""

import difflib

from easydiffraction.utils.logging import log


class Diagnostics:
    """Centralized logger for attribute errors and validation hints."""

    # ==============================================================
    # Configuration / definition diagnostics
    # ==============================================================

    @staticmethod
    def type_override_error(cls_name: str, expected: object, got: object) -> None:
        """
        Report an invalid DataTypes override.

        Used when descriptor and AttributeSpec types conflict.
        """
        expected_label = str(expected)
        got_label = str(got)
        msg = (
            f'Invalid type override in <{cls_name}>. '
            f'Descriptor enforces `{expected_label}`, '
            f'but AttributeSpec defines `{got_label}`.'
        )
        Diagnostics._log_error(msg, exc_type=TypeError)

    # ==============================================================
    # Attribute diagnostics
    # ==============================================================

    @staticmethod
    def readonly_error(
        name: str,
        key: str | None = None,
    ) -> None:
        """Log an attempt to change a read-only attribute."""
        Diagnostics._log_error(
            f"Cannot modify read-only attribute '{key}' of <{name}>.",
            exc_type=AttributeError,
        )

    @staticmethod
    def attr_error(
        name: str,
        key: str,
        allowed: set[str],
        label: str = 'Allowed',
    ) -> None:
        """Log unknown attribute access and suggest closest key."""
        suggestion = Diagnostics._build_suggestion(key, allowed)
        # Use consistent (label) logic for allowed
        hint = suggestion or Diagnostics._build_allowed(allowed, label=label)
        Diagnostics._log_error(
            f"Unknown attribute '{key}' of <{name}>.{hint}",
            exc_type=AttributeError,
        )

    # ==============================================================
    # Validation diagnostics
    # ==============================================================

    @staticmethod
    def type_mismatch(
        name: str,
        value: object,
        expected_type: object,
        current: object = None,
        default: object = None,
    ) -> None:
        """Log a type mismatch and keep current or default value."""
        got_type = type(value).__name__
        msg = (
            f'Type mismatch for <{name}>. '
            f'Expected `{expected_type}`, got `{got_type}` ({value!r}).'
        )
        Diagnostics._log_error_with_fallback(
            msg, current=current, default=default, exc_type=TypeError
        )

    @staticmethod
    def range_mismatch(
        name: str,
        value: object,
        ge: float,
        le: float,
        current: object = None,
        default: object = None,
    ) -> None:
        """Log range violation for a numeric value."""
        msg = f'Value mismatch for <{name}>. Provided {value!r} outside [{ge}, {le}].'
        Diagnostics._log_error_with_fallback(
            msg, current=current, default=default, exc_type=TypeError
        )

    @staticmethod
    def choice_mismatch(
        name: str,
        value: object,
        allowed: object,
        current: object = None,
        default: object = None,
    ) -> None:
        """Log an invalid choice against allowed values."""
        msg = f'Value mismatch for <{name}>. Provided {value!r} is unknown.'
        if allowed is not None:
            msg += Diagnostics._build_allowed(allowed, label='Allowed values')
        Diagnostics._log_error_with_fallback(
            msg, current=current, default=default, exc_type=TypeError
        )

    @staticmethod
    def regex_mismatch(
        name: str,
        value: object,
        pattern: str,
        current: object = None,
        default: object = None,
    ) -> None:
        """Log a regex mismatch with the expected pattern."""
        msg = (
            f"Value mismatch for <{name}>. Provided {value!r} does not match pattern '{pattern}'."
        )
        Diagnostics._log_error_with_fallback(
            msg, current=current, default=default, exc_type=TypeError
        )

    @staticmethod
    def no_value(name: str, default: object) -> None:
        """Log that default will be used due to missing value."""
        Diagnostics._log_debug(f'No value provided for <{name}>. Using default {default!r}.')

    @staticmethod
    def none_value(name: str) -> None:
        """Log explicit None provided by a user."""
        Diagnostics._log_debug(f'Using `None` explicitly provided for <{name}>.')

    @staticmethod
    def none_value_skip_range(name: str) -> None:
        """Log that range validation is skipped due to None."""
        Diagnostics._log_debug(
            f'Skipping range validation as `None` is explicitly provided for <{name}>.'
        )

    @staticmethod
    def validated(name: str, value: object, stage: str | None = None) -> None:
        """Log that a value passed a validation stage."""
        stage_info = f' {stage}' if stage else ''
        Diagnostics._log_debug(f'Value {value!r} for <{name}> passed{stage_info} validation.')

    # ==============================================================
    # Helper log methods
    # ==============================================================

    @staticmethod
    def _log_error(msg: str, exc_type: type[Exception] = Exception) -> None:
        """Emit an error-level message via shared logger."""
        log.error(msg, exc_type=exc_type)

    @staticmethod
    def _log_error_with_fallback(
        msg: str,
        current: object = None,
        default: object = None,
        exc_type: type[Exception] = Exception,
    ) -> None:
        """Emit an error message and mention kept or default value."""
        if current is not None:
            msg += f' Keeping current {current!r}.'
        else:
            msg += f' Using default {default!r}.'
        log.error(msg, exc_type=exc_type)

    @staticmethod
    def _log_debug(msg: str) -> None:
        """Emit a debug-level message via shared logger."""
        log.debug(msg)

    # ==============================================================
    # Suggestion and allowed value helpers
    # ==============================================================

    @staticmethod
    def _suggest(key: str, allowed: set[str]) -> str | None:
        """Suggest closest allowed key using string similarity."""
        if not allowed:
            return None
        # Return the allowed key with smallest Levenshtein distance
        matches = difflib.get_close_matches(key, allowed, n=1)
        return matches[0] if matches else None

    @staticmethod
    def _build_suggestion(key: str, allowed: set[str]) -> str:
        s = Diagnostics._suggest(key, allowed)
        return f" Did you mean '{s}'?" if s else ''

    @staticmethod
    def _build_allowed(allowed: object, label: str = 'Allowed attributes') -> str:
        # allowed may be a set, list, or other iterable
        if allowed:
            allowed_list = list(allowed)
            if len(allowed_list) <= 10:
                s = ', '.join(map(repr, sorted(allowed_list)))
                return f' {label}: {s}.'
            else:
                return f' ({len(allowed_list)} {label.lower()} not listed here).'
        return ''

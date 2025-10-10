# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
import difflib

from easydiffraction import log


class Diagnostics:
    """Centralized logger for attribute errors and validation
    guidance.
    """

    # ==============================================================
    # Configuration / definition diagnostics
    # ==============================================================

    @staticmethod
    def type_override_error(cls_name: str, expected, got):
        msg = (
            f'Invalid type override in <{cls_name}>. '
            f'Descriptor enforces `{expected.__name__}`, '
            f'but AttributeSpec defines `{got.__name__}`.'
        )
        Diagnostics._log_error(msg, exc_type=TypeError)

    # ==============================================================
    # Attribute diagnostics
    # ==============================================================

    @staticmethod
    def readonly_error(
        name: str,
        key: str | None = None,
    ):
        Diagnostics._log_error(
            f"Cannot modify read-only attribute '{key}' of <{name}>.",
            exc_type=AttributeError,
        )

    @staticmethod
    def attr_error(
        name: str,
        key: str,
        allowed: set[str],
        label='Allowed',
    ):
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
        value,
        expected_type,
        current=None,
        default=None,
    ):
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
        value,
        ge,
        le,
        current=None,
        default=None,
    ):
        msg = f'Value mismatch for <{name}>. Provided {value!r} outside [{ge}, {le}].'
        Diagnostics._log_error_with_fallback(
            msg, current=current, default=default, exc_type=TypeError
        )

    @staticmethod
    def choice_mismatch(
        name: str,
        value,
        allowed,
        current=None,
        default=None,
    ):
        msg = f'Value mismatch for <{name}>. Provided {value!r} is unknown.'
        if allowed is not None:
            msg += Diagnostics._build_allowed(allowed, label='Allowed values')
        Diagnostics._log_error_with_fallback(
            msg, current=current, default=default, exc_type=TypeError
        )

    @staticmethod
    def regex_mismatch(
        name: str,
        value,
        pattern,
        current=None,
        default=None,
    ):
        msg = (
            f"Value mismatch for <{name}>. Provided {value!r} does not match pattern '{pattern}'."
        )
        Diagnostics._log_error_with_fallback(
            msg, current=current, default=default, exc_type=TypeError
        )

    @staticmethod
    def none_value(name, default):
        Diagnostics._log_debug(f'No value provided for <{name}>. Using default {default!r}.')

    @staticmethod
    def validated(name, value, stage: str | None = None):
        stage_info = f' ({stage})' if stage else ''
        Diagnostics._log_debug(f'Value {value!r} for <{name}> passed validation{stage_info}.')

    # ==============================================================
    # Helper log methods
    # ==============================================================

    @staticmethod
    def _log_error(msg, exc_type=Exception):
        log.error(message=msg, exc_type=exc_type)

    @staticmethod
    def _log_error_with_fallback(
        msg,
        current=None,
        default=None,
        exc_type=Exception,
    ):
        if current is not None:
            msg += f' Keeping current {current!r}.'
        else:
            msg += f' Using default {default!r}.'
        log.error(message=msg, exc_type=exc_type)

    @staticmethod
    def _log_debug(msg):
        log.debug(message=msg)

    # ==============================================================
    # Suggestion and allowed value helpers
    # ==============================================================

    @staticmethod
    def _suggest(key: str, allowed: set[str]):
        if not allowed:
            return None
        # Return the allowed key with smallest Levenshtein distance
        matches = difflib.get_close_matches(key, allowed, n=1)
        return matches[0] if matches else None

    @staticmethod
    def _build_suggestion(key: str, allowed: set[str]):
        s = Diagnostics._suggest(key, allowed)
        return f" Did you mean '{s}'?" if s else ''

    @staticmethod
    def _build_allowed(allowed, label='Allowed attributes'):
        # allowed may be a set, list, or other iterable
        if allowed:
            allowed_list = list(allowed)
            if len(allowed_list) <= 10:
                s = ', '.join(map(repr, sorted(allowed_list)))
                return f' {label}: {s}.'
            else:
                return f' ({len(allowed_list)} {label.lower()} not listed here).'
        return ''

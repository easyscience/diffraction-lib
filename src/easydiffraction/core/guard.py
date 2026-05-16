# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING

from easydiffraction.core.diagnostic import Diagnostics
from easydiffraction.core.identity import Identity

if TYPE_CHECKING:
    from collections.abc import Generator


def _apply_help_filter(
    obj: object,
    properties: list[str],
    methods: list[str],
) -> tuple[list[str], list[str]]:
    """
    Apply an optional instance help filter that may only hide members.
    """
    help_filter = getattr(obj, '_help_filter', None)
    if not callable(help_filter):
        return properties, methods

    filtered_properties, filtered_methods = help_filter(list(properties), list(methods))
    invalid_properties = sorted(set(filtered_properties) - set(properties))
    invalid_methods = sorted(set(filtered_methods) - set(methods))
    if invalid_properties or invalid_methods:
        owner_name = type(obj).__name__
        msg = f'{owner_name}._help_filter() may only hide discovered members.'
        if invalid_properties:
            msg += f' Invalid properties: {invalid_properties}.'
        if invalid_methods:
            msg += f' Invalid methods: {invalid_methods}.'
        raise RuntimeError(msg)

    return filtered_properties, filtered_methods


class GuardedBase(ABC):
    """Base class enforcing controlled attribute access and linkage."""

    _diagnoser = Diagnostics()

    def __init__(self) -> None:
        super().__init__()
        self._identity = Identity(owner=self)

    def __str__(self) -> str:
        """Return the string representation of this object."""
        return f'<{self.unique_name}>'

    def __repr__(self) -> str:
        """Return the developer representation of this object."""
        return self.__str__()

    def __getattr__(self, key: str) -> None:
        """Raise a descriptive error for unknown attribute access."""
        # Private/dunder lookups should not trigger diagnostics —
        # raise AttributeError so getattr(obj, '_foo', default) works.
        if key.startswith('_'):
            raise AttributeError(key)
        cls = type(self)
        allowed = cls._public_attrs()
        if key not in allowed:
            type(self)._diagnoser.attr_error(
                self._log_name,
                key,
                allowed,
                label='Allowed readable/writable',
            )

    def __setattr__(self, key: str, value: object) -> None:
        """Set an attribute with access-control diagnostics."""
        # Always allow private or special attributes without diagnostics
        if key.startswith('_'):
            object.__setattr__(self, key, value)
            # Also maintain parent linkage for nested objects
            if key != '_parent' and isinstance(value, GuardedBase):
                object.__setattr__(value, '_parent', self)
            return

        # Handle public attributes with diagnostics
        cls = type(self)
        # Prevent modification of read-only attributes
        if key in cls._public_readonly_attrs():
            cls._diagnoser.readonly_error(
                self._log_name,
                key,
            )
            return
        # Prevent assignment to unknown attributes
        # Show writable attributes only as allowed
        if key not in cls._public_attrs():
            allowed = cls._public_writable_attrs()
            cls._diagnoser.attr_error(
                self._log_name,
                key,
                allowed,
                label='Allowed writable',
            )
            return

        self._assign_attr(key, value)

    def _assign_attr(self, key: str, value: object) -> None:
        """Low-level assignment with parent linkage."""
        object.__setattr__(self, key, value)  # noqa: PLC2801
        if key != '_parent' and isinstance(value, GuardedBase):
            object.__setattr__(value, '_parent', self)  # noqa: PLC2801

    @classmethod
    def _iter_properties(cls) -> Generator[tuple[str, property], None, None]:
        """
        Iterate over all public properties in the class hierarchy.

        Yields
        ------
        tuple[str, property]
            Each (key, property) pair for public attributes.
        """
        for base in cls.mro():
            for key, attr in base.__dict__.items():
                if key.startswith('_') or not isinstance(attr, property):
                    continue
                yield key, attr

    @classmethod
    def _public_attrs(cls) -> set[str]:
        """All public properties (read-only + writable)."""
        return {key for key, _ in cls._iter_properties()}

    @classmethod
    def _public_readonly_attrs(cls) -> set[str]:
        """Public properties without a setter."""
        return {key for key, prop in cls._iter_properties() if prop.fset is None}

    @classmethod
    def _public_writable_attrs(cls) -> set[str]:
        """Public properties with a setter."""
        return {key for key, prop in cls._iter_properties() if prop.fset is not None}

    def _allowed_attrs(
        self,
        *,
        writable_only: bool = False,
    ) -> set[str]:
        cls = type(self)
        if writable_only:
            return cls._public_writable_attrs()
        return cls._public_attrs()

    @property
    def _log_name(self) -> str:
        return self.unique_name or type(self).__name__

    @property
    def unique_name(self) -> str:
        """Fallback unique name: the class name."""
        return type(self).__name__

    # @property
    # def identity(self):
    #    """Expose a limited read-only view of identity attributes."""
    #    return SimpleNamespace(
    #        datablock_entry_name=self._identity.datablock_entry_name,
    #        category_code=self._identity.category_code,
    #        category_entry_name=self._identity.category_entry_name,
    #    )

    @property
    @abstractmethod
    def parameters(self) -> list:
        """Return a list of parameters (implemented by subclasses)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def as_cif(self) -> str:
        """Return CIF representation (implemented by subclasses)."""
        raise NotImplementedError

    @staticmethod
    def _first_sentence(docstring: str | None) -> str:
        """
        Extract the first paragraph from a docstring.

        Returns text before the first blank line, with continuation
        lines joined into a single string.
        """
        if not docstring:
            return ''
        first_para = docstring.strip().split('\n\n')[0]
        return ' '.join(line.strip() for line in first_para.splitlines())

    @classmethod
    def _iter_methods(cls) -> Generator[tuple[str, object], None, None]:
        """
        Iterate over public methods in the class hierarchy.

        Yields
        ------
        tuple[str, object]
            Each (name, function) pair.
        """
        seen: set = set()
        for base in cls.mro():
            for key, attr in base.__dict__.items():
                if key.startswith('_') or key in seen:
                    continue
                if isinstance(attr, property):
                    continue
                raw = attr
                if isinstance(raw, (staticmethod, classmethod)):
                    raw = raw.__func__
                if callable(raw):
                    seen.add(key)
                    yield key, raw

    def help(self) -> None:
        """Print a summary of public properties and methods."""
        from easydiffraction.utils.logging import console  # noqa: PLC0415
        from easydiffraction.utils.utils import render_table  # noqa: PLC0415

        cls = type(self)
        console.paragraph(f"Help for '{cls.__name__}'")

        # Deduplicate (MRO may yield the same name)
        seen: dict = {}
        for key, prop in cls._iter_properties():
            if key not in seen:
                seen[key] = prop

        property_names = sorted(seen)

        methods = dict(cls._iter_methods())
        method_names = sorted(methods)
        property_names, method_names = _apply_help_filter(self, property_names, method_names)

        prop_rows = []
        for i, key in enumerate(property_names, 1):
            prop = seen[key]
            writable = '✓' if prop.fset else '✗'
            doc = self._first_sentence(prop.fget.__doc__ if prop.fget else None)
            prop_rows.append([str(i), key, writable, doc])

        if prop_rows:
            console.paragraph('Properties')
            render_table(
                columns_headers=['#', 'Name', 'Writable', 'Description'],
                columns_alignment=['right', 'left', 'center', 'left'],
                columns_data=prop_rows,
            )

        method_rows = []
        for i, key in enumerate(method_names, 1):
            doc = self._first_sentence(getattr(methods[key], '__doc__', None))
            method_rows.append([str(i), f'{key}()', doc])

        if method_rows:
            console.paragraph('Methods')
            render_table(
                columns_headers=['#', 'Name', 'Description'],
                columns_alignment=['right', 'left', 'left'],
                columns_data=method_rows,
            )

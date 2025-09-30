# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Generic
from typing import Optional
from typing import TypeVar

from typeguard import typechecked

from easydiffraction import log
from easydiffraction.core.collections import CollectionBase
from easydiffraction.core.guards import GuardedBase
from easydiffraction.core.parameters import Descriptor
from easydiffraction.core.parameters import Parameter

CategoryItemT = TypeVar('CategoryItemT', bound='CategoryItem')


class AbstractCategory(ABC):
    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------
    _class_public_attrs = {
        'category_key',
        'datablock_name',
        'parameters',
        'as_cif',
    }

    # ------------------------------------------------------------------
    # Abstract API
    # ------------------------------------------------------------------
    @property
    @abstractmethod
    def category_key(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def datablock_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def parameters(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def as_cif(self) -> str:
        raise NotImplementedError


class CategoryItem(
    GuardedBase,
    AbstractCategory,
):
    """Base class for logical model components.

    Examples:
        Cell, Peak, SpaceGroup.

    Responsibilities:
        * Guard public attribute surface.
        * Propagate datablock / entry identifiers to children.
        * Provide uniform access to contained descriptors/parameters.
        * Offer CIF and dictionary export helpers.
    """

    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------
    _class_public_attrs = {
        'category_entry_name',
        'as_dict',
    }
    _MISSING_ATTR = object()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(self):
        """Initialize component with unset datablock and entry
        identifiers.
        """
        super().__init__()
        self._parent: Optional[Any] = None
        # TODO: should this be abstract to force subclasses to set it?
        self._category_entry_attr_name = None

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation of this component."""
        s = f'{self.__class__.__name__} ({len(self.parameters)} parameters)'
        for base in type(self).__mro__:
            if base is CategoryItem:
                s = f'{base.__name__}: {s}'
                break
        return s

    # TODO: Too complex; simplify
    def __setattr__(self, key: str, value: Any) -> None:
        """Controlled attribute assignment with reusable guard."""
        # To be sure that validation is done first
        if not self._validate_setattr(key):
            return
        # Need to check if attribute already exists
        try:
            attr = object.__getattribute__(self, key)
        except AttributeError:
            attr = self._MISSING_ATTR
        # If replacing or assigning any descriptor/parameter instance
        if isinstance(value, (Descriptor, Parameter)):
            value._parent = self
            object.__setattr__(self, key, value)
        # Dealing with existing descriptor/parameter instance
        elif attr is not self._MISSING_ATTR and isinstance(attr, (Descriptor, Parameter)):
            # Special pre-handling for category entry name attribute
            if key == self._category_entry_attr_name:
                old_name = self.category_entry_name
                if old_name == value:
                    log.warning('No change in name; skipping rename.')
                    return
                new_name = value
                if self._parent is not None:
                    if new_name in self._parent and self._parent[new_name] is not self:
                        log.warning(f'Cannot rename to {new_name}: name already exists in parent.')
                        return
                    # Perform the replace in parent collection
                    self._parent._replace_item(self, old_name, new_name)
            # Update the value of the existing descriptor/parameter
            attr.value = value
        # Setting any other attribute
        else:
            object.__setattr__(self, key, value)

    # ------------------------------------------------------------------
    # Abstract API
    # ------------------------------------------------------------------
    @property
    @abstractmethod
    def category_key(self) -> str:
        """Category key for this component (e.g., 'cell',
        'space_group').

        Must be implemented in subclasses to specify the EasyDiffraction
        category name. Distinct from CIF category names, which are tied
        to descriptors.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------
    @property
    def datablock_name(self) -> Optional[str]:
        """Read-only datablock name (delegated to parent)."""
        if self._parent is not None:
            return getattr(self._parent, 'datablock_name', None)
        return None

    @property
    def category_entry_name(self) -> Optional[str]:
        """Entry identifier (delegated to parent if available)."""
        if self._category_entry_attr_name is None:
            return None
        attr = getattr(self, self._category_entry_attr_name)
        name = attr.value
        return name

    @property
    def full_name(self) -> str:
        parts = []
        if self.datablock_name:
            parts.append(self.datablock_name)
        if self.category_key:
            parts.append(self.category_key)
        if self.category_entry_name:
            parts.append(str(self.category_entry_name))
        return '.'.join(parts)

    @property
    def parameters(self) -> list[Descriptor]:
        """Return all descriptor/parameter instances owned by this
        component.
        """
        return [v for v in self.__dict__.values() if isinstance(v, (Descriptor, Parameter))]

    @property
    def as_dict(self) -> dict[str, Any]:
        """Return mapping from parameter ``name`` to its current
        ``value``.
        """
        return {p.name: p.value for p in self.parameters if p.name is not None}

    @property
    def as_cif(self) -> str:
        """Return CIF tag/value lines for parameters with defined
        tags.
        """
        lines: list[str] = []
        for param in self.parameters:
            tags = getattr(param, 'full_cif_names', []) or []
            if not tags:
                continue
            value = param.value
            if value is None:
                continue
            key = tags[0]
            out_value = f'"{value}"' if isinstance(value, str) and ' ' in value else value
            lines.append(f'{key}  {out_value}')
        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def from_cif(self, block: Any, idx: int = 0) -> None:
        """Populate each parameter from CIF block at given loop
        index.
        """
        for param in self.parameters:
            param.from_cif(block, idx=idx)


class CategoryCollection(
    CollectionBase[CategoryItemT],
    AbstractCategory,
    Generic[CategoryItemT],
):
    """Handles loop-style category containers (e.g. AtomSites).

    Each item is a CategoryItem (component).
    """

    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------
    _class_public_attrs = {
        'parameters',
        'as_cif',
    }

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(self, item_type: type[CategoryItemT]) -> None:
        super().__init__(item_type)

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation of this component."""
        return f'{self.__class__.__name__} collection ({len(self)} sites)'

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------
    @property
    def category_key(self) -> str:
        return self._item_type().category_key

    @property
    def full_name(self) -> str:
        parts = []
        if self.datablock_name:
            parts.append(self.datablock_name)
        if self.category_key:
            parts.append(self.category_key)
        return '.'.join(parts)

    @property
    def datablock_name(self) -> Optional[str]:
        """Read-only datablock name (delegated to parent if
        available).
        """
        if self._parent is not None:
            return getattr(self._parent, 'datablock_name', None)
        return None

    @property
    def parameters(self) -> list[Descriptor]:
        params = []
        for item in self.values():
            if hasattr(item, 'parameters'):
                params.extend(item.parameters)
        return params

    # -----------
    # CIF methods
    # -----------
    @property
    def as_cif(self) -> str:
        lines: list[str] = []
        if self:
            # Header from first item attributes that expose CIF tags
            first_item = next(iter(self.values()))
            tag_attr_pairs: list[tuple[str, str]] = []  # (tag, attr_name)
            for attr_name in dir(first_item):
                if attr_name.startswith('_'):
                    continue
                attr_obj = getattr(first_item, attr_name)
                if not isinstance(attr_obj, (Descriptor, Parameter)):
                    continue
                tags = getattr(attr_obj, 'full_cif_names', []) or []
                if not tags:
                    continue
                tag_attr_pairs.append((tags[0], attr_name))
            if not tag_attr_pairs:
                return ''
            lines.append('loop_')
            header = '\n'.join(t for t, _ in tag_attr_pairs)
            lines.append(header)
            # Rows
            for item in self.values():
                values: list[str] = []
                for _, attr_name in tag_attr_pairs:
                    attr_obj = getattr(item, attr_name)
                    v = getattr(attr_obj, 'value', None)
                    if v is None:
                        values.append('.')
                    else:
                        s = f'{v}'
                        if isinstance(v, str) and ' ' in v:
                            s = f'"{s}"'
                        values.append(s)
                lines.append(' '.join(values))
        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------
    @typechecked
    def add(self, item: CategoryItemT) -> None:
        """Add an item to the collection."""
        item._parent = self
        self[item.category_entry_name] = item

    def add_from_args(self, *args, **kwargs) -> None:
        """Create and add a new child instance from the provided
        arguments.
        """
        child_obj = self._item_type(*args, **kwargs)
        self.add(child_obj)

    # TODO: from_cif or add_from_cif as above?
    def from_cif(self, block):
        # Derive loop size using category_entry_name first CIF tag alias
        if self._item_type is None:
            raise ValueError('Child class is not defined.')
        # TODO: Find a better way and then remove TODO in the AtomSite
        #  class
        # Create a temporary instance to access category_entry_name
        # attribute used as ID column for the items in this collection
        child_obj = self._item_type()
        entry_attr = getattr(child_obj, child_obj._category_entry_attr_name)
        # Try to find the value(s) from the CIF block iterating over
        # the possible cif names in order of preference.
        size = 0
        for name in entry_attr.full_cif_names:
            size = len(block.find_values(name))
            break
        # If no values found, nothing to do
        if not size:
            return
        # If values found, delegate to child class to parse each
        # row and add to collection
        for row_idx in range(size):
            child_obj = self._item_type()
            child_obj.from_cif(block, idx=row_idx)
            self.add(child_obj)

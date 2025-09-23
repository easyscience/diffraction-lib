from __future__ import annotations

from abc import abstractmethod
from typing import Any
from typing import Iterator
from typing import Optional

from easydiffraction.core.guards import AttributeAccessGuardMixin
from easydiffraction.core.guards import AttributeSetGuardMixin
from easydiffraction.core.guards import DiagnosticsMixin
from easydiffraction.core.guards import GuardedBase
from easydiffraction.core.parameters import Descriptor
from easydiffraction.core.parameters import Parameter


class CategoryItem(
    DiagnosticsMixin,
    AttributeAccessGuardMixin,
    AttributeSetGuardMixin,
    GuardedBase,
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
        'datablock_name',  # TODO: Needed?
        'category_entry_name',  # TODO: Needed?
    }
    _MISSING_ATTR = object()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(self):
        """Initialize component with unset datablock and entry
        identifiers.
        """
        self._parent: Optional[Any] = None
        self._category_entry_attr_name = None

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

    def __setattr__(self, key: str, value: Any) -> None:
        """Controlled attribute assignment with reusable guard."""
        if self._guarded_setattr(key, value):
            return
        try:
            attr = object.__getattribute__(self, key)
        except AttributeError:
            attr = self._MISSING_ATTR
        # If replacing or assigning a Descriptor instance
        if isinstance(value, Descriptor):
            value._parent = self
            object.__setattr__(self, key, value)
        # If updating the value of an existing Descriptor
        elif attr is not self._MISSING_ATTR and isinstance(attr, Descriptor):
            attr.value = value
        else:
            object.__setattr__(self, key, value)

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------
    @property
    def parameters(self) -> list[Descriptor]:
        """Return all descriptor/parameter instances owned by this
        component.
        """
        return [v for v in self.__dict__.values() if isinstance(v, Descriptor)]

    @property
    def datablock_name(self) -> Optional[str]:
        """Read-only datablock name (delegated to parent)."""
        if self._parent is not None:
            return getattr(self._parent, 'datablock_name', None)
        return None

    @datablock_name.setter
    def datablock_name(self, _):
        self._readonly_error()

    @property
    def category_entry_name(self) -> Optional[str]:
        """Entry identifier (delegated to parent if available)."""
        if self._category_entry_attr_name is None:
            return None
        attr = getattr(self, self._category_entry_attr_name)
        name = attr.value
        return name

    @category_entry_name.setter
    def category_entry_name(self, _) -> None:
        self._readonly_error()

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
    DiagnosticsMixin,
    AttributeAccessGuardMixin,
    AttributeSetGuardMixin,
    GuardedBase,
):
    """Handles loop-style category containers (e.g. AtomSites).

    Each item is a CategoryItem (component).
    """

    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------
    _class_public_attrs = {
        'datablock_name',
    }

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(self, child_class=None):
        self._parent: Optional[Any] = None
        self._items = {}
        self._child_class = child_class

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation of this component."""
        return f'CategoryCollection: {self.__class__.__name__} ({len(self._items)} sites)'

    def __getitem__(self, key: str) -> CategoryItem:
        return self._items[key]

    def __iter__(self) -> Iterator[CategoryItem]:
        return iter(self._items.values())

    def __setattr__(self, key: str, value: Any) -> None:
        if self._guarded_setattr(key, value):
            return
        object.__setattr__(self, key, value)

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------
    @property
    def parameters(self) -> list[Descriptor]:
        params = []
        for item in self._items.values():
            if hasattr(item, 'parameters'):
                params.extend(item.parameters)
        return params

    @property
    def datablock_name(self):
        """Read-only datablock name (delegated to parent if
        available).
        """
        if self._parent is not None:
            return getattr(self._parent, 'datablock_name', None)
        return None

    @datablock_name.setter
    def datablock_name(self, _):
        self._readonly_error()

    @property
    def as_cif(self) -> str:
        lines: list[str] = []
        if self._items:
            # Header from first item attributes that expose CIF tags
            first_item = next(iter(self._items.values()))
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
            for item in self._items.values():
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

    def add(self, item: CategoryItem | None = None, *args, **kwargs):
        """Add an item to the collection.

        Supports two forms:
        1. ``add(existing_item)`` – direct insertion
        2. ``add(*args, **kwargs)`` – construct child_class with the
           provided arguments (legacy convenience used in older tests)
        """
        if item is None:
            if self._child_class is None:
                raise ValueError('child_class is not defined for this collection')
            item = self._child_class(*args, **kwargs)
        item._parent = self
        self._items[item.category_entry_name] = item

    def add_from_args(self, *args, **kwargs):
        """Create and add a new child instance from the provided
        arguments.
        """
        child_obj = self._child_class(*args, **kwargs)
        self.add(child_obj)

    def from_cif(self, block):
        # Derive loop size using category_entry_name first CIF tag alias
        if self._child_class is None:
            raise ValueError('Child class is not defined.')
        # TODO: Find a better way and then remove TODO in the AtomSite
        #  class
        # Create a temporary instance to access category_entry_name
        # attribute used as ID column for the items in this collection
        child_obj = self._child_class()
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
            child_obj = self._child_class()
            child_obj.from_cif(block, idx=row_idx)
            self.add(child_obj)

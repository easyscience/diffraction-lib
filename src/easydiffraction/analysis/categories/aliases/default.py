# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Alias category for mapping friendly names to parameters.

Defines a small record type used by analysis configuration to refer to
parameters via readable ids instead of opaque identifiers. At runtime
each alias holds a direct object reference to the parameter; for CIF
serialization the parameter's ``unique_name`` is stored.
"""

from __future__ import annotations

from easydiffraction.analysis.categories.aliases.factory import AliasesFactory
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import TagSpec


class Alias(CategoryItem):
    """
    Single alias entry.

    Maps a human-readable ``id`` to a parameter object. The
    ``parameter_unique_name`` descriptor stores the parameter's
    ``unique_name`` for CIF serialization.
    """

    _category_code = 'alias'
    _category_entry_name = 'id'

    def __init__(self) -> None:
        """Initialize the alias descriptors and parameter reference."""
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Human-readable alias id for a parameter.',
            value_spec=AttributeSpec(
                default='_',  # TODO: Maybe None?
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            tags=TagSpec(
                edi_names=['_alias.id'], cif_names=['_easydiffraction_alias.id', '_alias.label']
            ),
        )
        self._parameter_unique_name = StringDescriptor(
            name='parameter_unique_name',
            description='Unique name of the referenced parameter.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_.]*$'),
            ),
            tags=TagSpec(
                edi_names=['_alias.parameter_unique_name'],
                cif_names=[
                    '_easydiffraction_alias.parameter_unique_name',
                    '_alias.param_unique_name',
                ],
            ),
        )

        # Direct reference to the Parameter object (runtime only).
        # Stored via object.__setattr__ to avoid parent-chain mutation.
        object.__setattr__(self, '_param_ref', None)

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> StringDescriptor:
        """
        Human-readable alias id (e.g. ``'biso_La'``).

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        """Set the alias id value."""
        self._id.value = value

    @property
    def param(self) -> object | None:
        """
        The referenced parameter object, or None before resolution.
        """
        return self._param_ref

    @property
    def parameter_unique_name(self) -> StringDescriptor:
        """
        Unique name of the referenced parameter (for CIF).

        Reading this property returns the underlying
        ``StringDescriptor`` object.
        """
        return self._parameter_unique_name

    def _set_param(self, param: object) -> None:
        """
        Store a direct reference to the parameter.

        Also updates ``parameter_unique_name`` from the parameter's
        ``unique_name`` for CIF round-tripping.
        """
        object.__setattr__(self, '_param_ref', param)  # noqa: PLC2801
        self._parameter_unique_name.value = param.unique_name

    @property
    def parameters(self) -> list:
        """
        Descriptors owned by this alias (excludes the param reference).
        """
        return [self._id, self._parameter_unique_name]


@AliasesFactory.register
class Aliases(CategoryCollection):
    """Collection of :class:`Alias` items."""

    type_info = TypeInfo(
        tag='default',
        description='Parameter alias mappings',
    )

    def __init__(self) -> None:
        """Create an empty collection of aliases."""
        super().__init__(item_type=Alias)

    def create(self, *, id: str, param: object) -> None:
        """
        Create a new alias mapping an id to a parameter.

        Parameters
        ----------
        id : str
            Human-readable alias name (e.g. ``'biso_La'``).
        param : object
            The parameter object to reference.
        """
        item = Alias()
        item.id = id
        item._set_param(param)
        self.add(item)

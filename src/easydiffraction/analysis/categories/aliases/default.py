# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Alias category for mapping friendly names to parameters.

Defines a small record type used by analysis configuration to refer to
parameters via readable labels instead of opaque identifiers. At runtime
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
from easydiffraction.io.cif.handler import CifHandler


class Alias(CategoryItem):
    """
    Single alias entry.

    Maps a human-readable ``label`` to a parameter object. The
    ``param_unique_name`` descriptor stores the parameter's
    ``unique_name`` for CIF serialization.
    """

    _category_code = 'alias'
    _category_entry_name = 'label'

    def __init__(self) -> None:
        super().__init__()

        self._label = StringDescriptor(
            name='label',
            description='Human-readable alias for a parameter.',
            value_spec=AttributeSpec(
                default='_',  # TODO, Maybe None?
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(names=['_alias.label']),
        )
        self._param_unique_name = StringDescriptor(
            name='param_unique_name',
            description='Unique name of the referenced parameter.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_.]*$'),
            ),
            cif_handler=CifHandler(names=['_alias.param_unique_name']),
        )

        # Direct reference to the Parameter object (runtime only).
        # Stored via object.__setattr__ to avoid parent-chain mutation.
        object.__setattr__(self, '_param_ref', None)

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def label(self) -> StringDescriptor:
        """
        Human-readable alias label (e.g. ``'biso_La'``).

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        self._label.value = value

    @property
    def param(self) -> object | None:
        """
        The referenced parameter object, or None before resolution.
        """
        return self._param_ref

    @property
    def param_unique_name(self) -> StringDescriptor:
        """
        Unique name of the referenced parameter (for CIF).

        Reading this property returns the underlying
        ``StringDescriptor`` object.
        """
        return self._param_unique_name

    def _set_param(self, param: object) -> None:
        """
        Store a direct reference to the parameter.

        Also updates ``param_unique_name`` from the parameter's
        ``unique_name`` for CIF round-tripping.
        """
        object.__setattr__(self, '_param_ref', param)  # noqa: PLC2801
        self._param_unique_name.value = param.unique_name

    @property
    def parameters(self) -> list:
        """
        Descriptors owned by this alias (excludes the param reference).
        """
        return [self._label, self._param_unique_name]


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

    def create(self, *, label: str, param: object) -> None:
        """
        Create a new alias mapping a label to a parameter.

        Parameters
        ----------
        label : str
            Human-readable alias name (e.g. ``'biso_La'``).
        param : object
            The parameter object to reference.
        """
        item = Alias()
        item.label = label
        item._set_param(param)
        self.add(item)

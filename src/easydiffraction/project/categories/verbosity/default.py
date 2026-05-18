"""Project fit-output verbosity category."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.project.categories.verbosity.factory import VerbosityFactory
from easydiffraction.utils.enums import VerbosityEnum


@VerbosityFactory.register
class Verbosity(CategoryItem):
    """Fit-output verbosity selection for a project."""

    _category_code = 'verbosity'

    type_info = TypeInfo(
        tag='default',
        description='Project verbosity category',
    )

    def __init__(self) -> None:
        super().__init__()

        self._fit = StringDescriptor(
            name='fit',
            description='Fitting process output verbosity',
            value_spec=AttributeSpec(
                default=VerbosityEnum.default().value,
                validator=MembershipValidator(
                    allowed=[member.value for member in VerbosityEnum],
                ),
            ),
            cif_handler=CifHandler(names=['_verbosity.fit']),
        )

    @property
    def fit(self) -> StringDescriptor:
        """Fitting process output verbosity."""
        return self._fit

    @fit.setter
    def fit(self, value: str) -> None:
        self._fit.value = VerbosityEnum(value).value

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this verbosity category."""
        return super().as_cif

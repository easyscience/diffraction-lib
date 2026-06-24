# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Sequential-fit extract-rule configuration.

Stores persisted rules for extracting diffrn metadata from sequential
fit input files.
"""

from __future__ import annotations

import re

from easydiffraction.analysis.categories.sequential_fit_extract.factory import (
    SequentialFitExtractFactory,
)
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import TagSpec

_TARGET_SEGMENT_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_EXTRACT_TARGET_SEGMENTS = 2


def _validate_extract_target_shape(value: str) -> None:
    """Validate the supported two-segment extract target form."""
    parts = value.split('.')
    if (
        len(parts) != _EXTRACT_TARGET_SEGMENTS
        or parts[0] != 'diffrn'
        or not _TARGET_SEGMENT_PATTERN.fullmatch(parts[1])
    ):
        msg = (
            'sequential_fit_extract.target must use the form '
            "'diffrn.<name>' with exactly two segments."
        )
        raise ValueError(msg)


def _validate_extract_pattern(value: str) -> None:
    """Validate that an extract pattern compiles and captures once."""
    try:
        compiled = re.compile(value)
    except re.error as error:
        msg = f'Invalid sequential_fit_extract.pattern {value!r}: {error}.'
        raise ValueError(msg) from error

    if compiled.groups != 1:
        msg = 'sequential_fit_extract.pattern must define exactly one capture group.'
        raise ValueError(msg)


class SequentialFitExtractItem(CategoryItem):
    """A single sequential-fit extract rule."""

    _category_code = 'sequential_fit_extract'
    _category_entry_name = 'id'

    def __init__(self) -> None:
        """Initialize the extract-rule descriptors."""
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier for this extract rule.',
            value_spec=AttributeSpec(
                default='_',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            tags=TagSpec(
                edi_names=['_sequential_fit_extract.id'],
                cif_names=['_easydiffraction_sequential_fit_extract.id'],
            ),
        )
        self._target = StringDescriptor(
            name='target',
            description='diffrn attribute updated by this extract rule.',
            value_spec=AttributeSpec(default='diffrn._'),
            tags=TagSpec(
                edi_names=['_sequential_fit_extract.target'],
                cif_names=['_easydiffraction_sequential_fit_extract.target'],
            ),
        )
        self._pattern = StringDescriptor(
            name='pattern',
            description='Regex used to extract one numeric capture group.',
            value_spec=AttributeSpec(default='(.*)'),
            tags=TagSpec(
                edi_names=['_sequential_fit_extract.pattern'],
                cif_names=['_easydiffraction_sequential_fit_extract.pattern'],
            ),
        )
        self._required = BoolDescriptor(
            name='required',
            description='Whether this extract rule must match every file.',
            value_spec=AttributeSpec(default=False),
            tags=TagSpec(
                edi_names=['_sequential_fit_extract.required'],
                cif_names=['_easydiffraction_sequential_fit_extract.required'],
            ),
        )

    @property
    def id(self) -> StringDescriptor:
        """Identifier for this extract rule."""
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        """Set the extract-rule identifier."""
        self._id.value = value

    @property
    def target(self) -> StringDescriptor:
        """Diffrn attribute updated by this extract rule."""
        return self._target

    @target.setter
    def target(self, value: str) -> None:
        """Set the diffrn attribute updated by this rule."""
        self._target.value = value

    @property
    def pattern(self) -> StringDescriptor:
        """Regex used to extract one numeric capture group."""
        return self._pattern

    @pattern.setter
    def pattern(self, value: str) -> None:
        """Set the extract-rule capture-group regex."""
        self._pattern.value = value

    @property
    def required(self) -> BoolDescriptor:
        """Whether this extract rule must match every file."""
        return self._required

    @required.setter
    def required(self, value: bool) -> None:
        """Set whether this extract rule must match every file."""
        self._required.value = value


@SequentialFitExtractFactory.register
class SequentialFitExtractCollection(CategoryCollection):
    """Collection of :class:`SequentialFitExtractItem` items."""

    type_info = TypeInfo(
        tag='default',
        description='Sequential-fit metadata extraction rules',
    )

    def __init__(self) -> None:
        """Create an empty collection of extract rules."""
        super().__init__(item_type=SequentialFitExtractItem)

    def create(
        self,
        *,
        id: str,
        target: str,
        pattern: str,
        required: bool = False,
    ) -> None:
        """Create a validated sequential-fit extract rule."""
        _validate_extract_target_shape(target)
        _validate_extract_pattern(pattern)

        item = SequentialFitExtractItem()
        item.id = id
        item.target = target
        item.pattern = pattern
        item.required = required
        self.add(item)

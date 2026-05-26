# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Sequential-fit configuration category.

Stores persisted settings for directory-based sequential fitting.
"""

from __future__ import annotations

from easydiffraction.analysis.categories.sequential_fit.factory import SequentialFitFactory
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


@SequentialFitFactory.register
class SequentialFit(CategoryItem):
    """Persisted settings for sequential fitting."""

    _category_code = 'sequential_fit'

    type_info = TypeInfo(
        tag='default',
        description='Sequential fitting settings',
    )

    def __init__(self) -> None:
        super().__init__()

        self._data_dir = StringDescriptor(
            name='data_dir',
            description='Directory containing sequential-fit data files.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(
                names=['_sequential_fit.data_dir'],
                iucr_name='_easydiffraction_sequential_fit.data_dir',
            ),
        )
        self._file_pattern = StringDescriptor(
            name='file_pattern',
            description='Glob pattern selecting sequential-fit files.',
            value_spec=AttributeSpec(default='*'),
            cif_handler=CifHandler(
                names=['_sequential_fit.file_pattern'],
                iucr_name='_easydiffraction_sequential_fit.file_pattern',
            ),
        )
        self._max_workers = StringDescriptor(
            name='max_workers',
            description='Worker-count token for sequential fitting.',
            value_spec=AttributeSpec(
                default='1',
                validator=RegexValidator(pattern=r'^(auto|[1-9]\d*)$'),
            ),
            cif_handler=CifHandler(
                names=['_sequential_fit.max_workers'],
                iucr_name='_easydiffraction_sequential_fit.max_workers',
            ),
        )
        self._chunk_size = StringDescriptor(
            name='chunk_size',
            description='Chunk-size token for sequential fitting.',
            value_spec=AttributeSpec(
                default='.',
                validator=RegexValidator(pattern=r'^([1-9]\d*|\.)$'),
            ),
            cif_handler=CifHandler(
                names=['_sequential_fit.chunk_size'],
                iucr_name='_easydiffraction_sequential_fit.chunk_size',
            ),
        )
        self._reverse = BoolDescriptor(
            name='reverse',
            description='Whether to process sequential-fit files in reverse.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(
                names=['_sequential_fit.reverse'],
                iucr_name='_easydiffraction_sequential_fit.reverse',
            ),
        )

    @property
    def data_dir(self) -> StringDescriptor:
        """Directory containing sequential-fit data files."""
        return self._data_dir

    @data_dir.setter
    def data_dir(self, value: str) -> None:
        self._data_dir.value = value

    @property
    def file_pattern(self) -> StringDescriptor:
        """Glob pattern selecting sequential-fit files."""
        return self._file_pattern

    @file_pattern.setter
    def file_pattern(self, value: str) -> None:
        self._file_pattern.value = value

    @property
    def max_workers(self) -> StringDescriptor:
        """Worker-count token for sequential fitting."""
        return self._max_workers

    @max_workers.setter
    def max_workers(self, value: str) -> None:
        self._max_workers.value = value

    @property
    def chunk_size(self) -> StringDescriptor:
        """Chunk-size token for sequential fitting."""
        return self._chunk_size

    @chunk_size.setter
    def chunk_size(self, value: str) -> None:
        self._chunk_size.value = value

    @property
    def reverse(self) -> BoolDescriptor:
        """Whether to process sequential-fit files in reverse."""
        return self._reverse

    @reverse.setter
    def reverse(self, value: bool) -> None:
        self._reverse.value = value

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this sequential-fit category."""
        return super().as_cif

    def from_cif(self, block: object, idx: int = 0) -> None:
        """Populate this sequential-fit category from a CIF block."""
        super().from_cif(block, idx)

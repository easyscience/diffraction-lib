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
from easydiffraction.io.cif.handler import TagSpec


@SequentialFitFactory.register
class SequentialFit(CategoryItem):
    """Persisted settings for sequential fitting."""

    _category_code = 'sequential_fit'

    type_info = TypeInfo(
        tag='default',
        description='Sequential fitting settings',
    )

    def __init__(self) -> None:
        """Initialize the sequential-fit setting descriptors."""
        super().__init__()

        self._data_dir = StringDescriptor(
            name='data_dir',
            description='Directory containing sequential-fit data files.',
            value_spec=AttributeSpec(default=''),
            tags=TagSpec(
                edi_names=['_sequential_fit.data_dir'],
                cif_names=['_easydiffraction_sequential_fit.data_dir'],
            ),
        )
        self._file_pattern = StringDescriptor(
            name='file_pattern',
            description='Glob pattern selecting sequential-fit files.',
            value_spec=AttributeSpec(default='*'),
            tags=TagSpec(
                edi_names=['_sequential_fit.file_pattern'],
                cif_names=['_easydiffraction_sequential_fit.file_pattern'],
            ),
        )
        self._max_workers = StringDescriptor(
            name='max_workers',
            description='Worker-count token for sequential fitting.',
            value_spec=AttributeSpec(
                default='1',
                validator=RegexValidator(pattern=r'^(auto|[1-9]\d*)$'),
            ),
            tags=TagSpec(
                edi_names=['_sequential_fit.max_workers'],
                cif_names=['_easydiffraction_sequential_fit.max_workers'],
            ),
        )
        self._chunk_size = StringDescriptor(
            name='chunk_size',
            description='Chunk-size token for sequential fitting.',
            value_spec=AttributeSpec(
                default='.',
                validator=RegexValidator(pattern=r'^([1-9]\d*|\.)$'),
            ),
            tags=TagSpec(
                edi_names=['_sequential_fit.chunk_size'],
                cif_names=['_easydiffraction_sequential_fit.chunk_size'],
            ),
        )
        self._reverse = BoolDescriptor(
            name='reverse',
            description='Whether to process sequential-fit files in reverse.',
            value_spec=AttributeSpec(default=False),
            tags=TagSpec(
                edi_names=['_sequential_fit.reverse'],
                cif_names=['_easydiffraction_sequential_fit.reverse'],
            ),
        )
        self._copy_data = BoolDescriptor(
            name='copy_data',
            description='Whether to copy matched data files into the project.',
            value_spec=AttributeSpec(default=False),
            tags=TagSpec(
                edi_names=['_sequential_fit.copy_data'],
                cif_names=['_easydiffraction_sequential_fit.copy_data'],
            ),
        )

    @property
    def data_dir(self) -> StringDescriptor:
        """Directory containing sequential-fit data files."""
        return self._data_dir

    @data_dir.setter
    def data_dir(self, value: str) -> None:
        """Set the sequential-fit data directory."""
        self._data_dir.value = value

    @property
    def file_pattern(self) -> StringDescriptor:
        """Glob pattern selecting sequential-fit files."""
        return self._file_pattern

    @file_pattern.setter
    def file_pattern(self, value: str) -> None:
        """Set the sequential-fit file glob pattern."""
        self._file_pattern.value = value

    @property
    def max_workers(self) -> StringDescriptor:
        """Worker-count token for sequential fitting."""
        return self._max_workers

    @max_workers.setter
    def max_workers(self, value: str) -> None:
        """Set the sequential-fit worker-count token."""
        self._max_workers.value = value

    @property
    def chunk_size(self) -> StringDescriptor:
        """Chunk-size token for sequential fitting."""
        return self._chunk_size

    @chunk_size.setter
    def chunk_size(self, value: str) -> None:
        """Set the sequential-fit chunk-size token."""
        self._chunk_size.value = value

    @property
    def reverse(self) -> BoolDescriptor:
        """Whether to process sequential-fit files in reverse."""
        return self._reverse

    @reverse.setter
    def reverse(self, value: bool) -> None:
        """Set whether to process sequential-fit files in reverse."""
        self._reverse.value = value

    @property
    def copy_data(self) -> BoolDescriptor:
        """Whether to copy matched data files into the project."""
        return self._copy_data

    @copy_data.setter
    def copy_data(self, value: bool) -> None:
        """Set whether to copy matched data files into the project."""
        self._copy_data.value = value

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this sequential-fit category."""
        return super().as_cif

    def from_cif(self, block: object, idx: int = 0) -> None:
        """Populate this sequential-fit category from a CIF block."""
        super().from_cif(block, idx)

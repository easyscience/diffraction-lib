# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Factory for creating sample models from simple inputs or CIF.

Supports three argument combinations: ``name``, ``cif_path``, or
``cif_str``. Returns a minimal ``SampleModelBase`` populated from CIF
when provided, or an empty model with the given name.
"""

from __future__ import annotations

import gemmi

from easydiffraction.core.factory import FactoryBase
from easydiffraction.sample_models.sample_model.base import SampleModelBase


class SampleModelFactory(FactoryBase):
    """Create ``SampleModelBase`` instances from supported inputs."""

    _ALLOWED_ARG_SPECS = [
        {'required': ['name'], 'optional': []},
        {'required': ['cif_path'], 'optional': []},
        {'required': ['cif_str'], 'optional': []},
    ]

    @classmethod
    def create(cls, **kwargs) -> SampleModelBase:
        """Create a model based on a validated argument combination.

        Keyword Args:
            name: Name of the sample model to create.
            cif_path: Path to a CIF file to parse.
            cif_str: Raw CIF string to parse.
            **kwargs: Extra args are ignored if None; only the above
                three keys are supported.

        Returns:
            SampleModelBase: A populated or empty model instance.
        """
        # Check for valid argument combinations
        user_args = {k for k, v in kwargs.items() if v is not None}
        cls._validate_args(user_args, cls._ALLOWED_ARG_SPECS, cls.__name__)

        if 'cif_path' in kwargs:
            return cls._create_from_cif_path(kwargs['cif_path'])
        elif 'cif_str' in kwargs:
            return cls._create_from_cif_str(kwargs['cif_str'])
        elif 'name' in kwargs:
            return SampleModelBase(name=kwargs['name'])

    # -------------------------------
    # Private creation helper methods
    # -------------------------------

    @classmethod
    def _create_from_cif_path(
        cls,
        cif_path: str,
    ) -> SampleModelBase:
        """Create a model by reading and parsing a CIF file."""
        doc = cls._cif_document_from_path(cif_path)
        block = cls._pick_sole_block(doc)
        return cls._model_from_block(block)

    @classmethod
    def _create_from_cif_str(
        cls,
        cif_str: str,
    ) -> SampleModelBase:
        """Create a model by parsing a CIF string."""
        doc = cls._cif_document_from_string(cif_str)
        block = cls._pick_sole_block(doc)
        return cls._model_from_block(block)

    # TODO: Move to io.cif.parse?

    # -------------
    # gemmi helpers
    # -------------

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @staticmethod
    def _cif_document_from_path(path: str) -> gemmi.cif.Document:
        """Read a CIF document from a file path."""
        return gemmi.cif.read_file(path)

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @staticmethod
    def _cif_document_from_string(text: str) -> gemmi.cif.Document:
        """Read a CIF document from a raw text string."""
        return gemmi.cif.read_string(text)

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @classmethod
    def _pick_sole_block(
        cls,
        doc: gemmi.cif.Document,
    ) -> gemmi.cif.Block:
        """Pick the sole data block from a CIF document."""
        return doc.sole_block()

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @classmethod
    def _name_from_block(cls, block: gemmi.cif.Block) -> str:
        """Extract a model name from the CIF block name."""
        # TODO: Need validator or normalization?
        return block.name

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @classmethod
    def _model_from_block(
        cls,
        block: gemmi.cif.Block,
    ) -> SampleModelBase:
        """Build a model instance from a single CIF block."""
        name = cls._name_from_block(block)
        sample_model = SampleModelFactory.create(name=name)
        for category in sample_model.categories:
            category.from_cif(block)
        return sample_model

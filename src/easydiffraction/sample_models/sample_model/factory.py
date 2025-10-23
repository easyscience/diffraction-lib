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
        doc = cls._read_cif_document_from_path(cif_path)
        block = cls._pick_first_structural_block(doc)
        return cls._create_model_from_block(block)

    @classmethod
    def _create_from_cif_str(
        cls,
        cif_str: str,
    ) -> SampleModelBase:
        """Create a model by parsing a CIF string."""
        doc = cls._read_cif_document_from_string(cif_str)
        block = cls._pick_first_structural_block(doc)
        return cls._create_model_from_block(block)

    # TODO: Move to io.cif.parse?

    # -------------
    # gemmi helpers
    # -------------

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @staticmethod
    def _read_cif_document_from_path(path: str) -> gemmi.cif.Document:
        """Read a CIF document from a file path."""
        return gemmi.cif.read_file(path)

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @staticmethod
    def _read_cif_document_from_string(text: str) -> gemmi.cif.Document:
        """Read a CIF document from a raw text string."""
        return gemmi.cif.read_string(text)

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @staticmethod
    def _has_structural_content(block: gemmi.cif.Block) -> bool:
        """Return True if the CIF block contains structural content."""
        # Basic heuristics: atom_site loop or full set of cell params
        loop = block.find_loop('_atom_site.fract_x')
        if loop is not None:
            return True
        required_cell = [
            '_cell.length_a',
            '_cell.length_b',
            '_cell.length_c',
            '_cell.angle_alpha',
            '_cell.angle_beta',
            '_cell.angle_gamma',
        ]
        return all(block.find_value(tag) for tag in required_cell)

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @classmethod
    def _pick_first_structural_block(
        cls,
        doc: gemmi.cif.Document,
    ) -> gemmi.cif.Block:
        """Pick the most likely structural block from a CIF document."""
        # Prefer blocks with atom_site loop; else first block with cell
        for block in doc:
            if cls._has_structural_content(block):
                return block
        # As a fallback, return the sole or first block
        try:
            return doc.sole_block()
        except Exception:
            return doc[0]

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @classmethod
    def _create_model_from_block(
        cls,
        block: gemmi.cif.Block,
    ) -> SampleModelBase:
        """Build a model instance from a single CIF block."""
        name = cls._extract_name_from_block(block)
        model = SampleModelBase(name=name)
        cls._set_space_group_from_cif_block(model, block)
        cls._set_cell_from_cif_block(model, block)
        cls._set_atom_sites_from_cif_block(model, block)
        return model

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @classmethod
    def _extract_name_from_block(cls, block: gemmi.cif.Block) -> str:
        """Extract a model name from the CIF block name."""
        return block.name or 'model'

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @classmethod
    def _set_space_group_from_cif_block(
        cls,
        model: SampleModelBase,
        block: gemmi.cif.Block,
    ) -> None:
        """Populate the model's space group from a CIF block."""
        model.space_group.from_cif(block)

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @classmethod
    def _set_cell_from_cif_block(
        cls,
        model: SampleModelBase,
        block: gemmi.cif.Block,
    ) -> None:
        """Populate the model's unit cell from a CIF block."""
        model.cell.from_cif(block)

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @classmethod
    def _set_atom_sites_from_cif_block(
        cls,
        model: SampleModelBase,
        block: gemmi.cif.Block,
    ) -> None:
        """Populate the model's atom sites from a CIF block."""
        model.atom_sites.from_cif(block)

    # TODO: How to automatically parce and populate all categories?
    #  for category in model.categories:
    #      cls._set_category_from_cif_block(category, block)

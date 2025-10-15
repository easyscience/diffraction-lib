# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import gemmi

from easydiffraction.core.factory import FactoryBase
from easydiffraction.sample_models.sample_model.base import SampleModelBase


class SampleModelFactory(FactoryBase):
    """Creates SampleModel instances with only relevant attributes."""

    _ALLOWED_ARG_SPECS = [
        {'required': ['name'], 'optional': []},
        {'required': ['cif_path'], 'optional': []},
        {'required': ['cif_str'], 'optional': []},
    ]

    @classmethod
    def create(cls, **kwargs) -> SampleModelBase:
        """Create a `SampleModelBase` using a validated argument
        combination.
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
        # Parse CIF and build model
        doc = cls._read_cif_document_from_path(cif_path)
        block = cls._pick_first_structural_block(doc)
        return cls._create_model_from_block(block)

    @classmethod
    def _create_from_cif_str(
        cls,
        cif_str: str,
    ) -> SampleModelBase:
        # Parse CIF string and build model
        doc = cls._read_cif_document_from_string(cif_str)
        block = cls._pick_first_structural_block(doc)
        return cls._create_model_from_block(block)

    # -------------
    # gemmi helpers
    # -------------

    @staticmethod
    def _read_cif_document_from_path(path: str) -> gemmi.cif.Document:
        return gemmi.cif.read_file(path)

    @staticmethod
    def _read_cif_document_from_string(text: str) -> gemmi.cif.Document:
        return gemmi.cif.read_string(text)

    @staticmethod
    def _has_structural_content(block: gemmi.cif.Block) -> bool:
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

    @classmethod
    def _pick_first_structural_block(
        cls,
        doc: gemmi.cif.Document,
    ) -> gemmi.cif.Block:
        # Prefer blocks with atom_site loop; else first block with cell
        for block in doc:
            if cls._has_structural_content(block):
                return block
        # As a fallback, return the sole or first block
        try:
            return doc.sole_block()
        except Exception:
            return doc[0]

    @classmethod
    def _create_model_from_block(
        cls,
        block: gemmi.cif.Block,
    ) -> SampleModelBase:
        name = cls._extract_name_from_block(block)
        model = SampleModelBase(name=name)
        cls._set_space_group_from_cif_block(model, block)
        cls._set_cell_from_cif_block(model, block)
        cls._set_atom_sites_from_cif_block(model, block)
        return model

    @classmethod
    def _extract_name_from_block(cls, block: gemmi.cif.Block) -> str:
        return block.name or 'model'

    @classmethod
    def _set_space_group_from_cif_block(
        cls,
        model: SampleModelBase,
        block: gemmi.cif.Block,
    ) -> None:
        model.space_group.from_cif(block)

    @classmethod
    def _set_cell_from_cif_block(
        cls,
        model: SampleModelBase,
        block: gemmi.cif.Block,
    ) -> None:
        model.cell.from_cif(block)

    @classmethod
    def _set_atom_sites_from_cif_block(
        cls,
        model: SampleModelBase,
        block: gemmi.cif.Block,
    ) -> None:
        model.atom_sites.from_cif(block)

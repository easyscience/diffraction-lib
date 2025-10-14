# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import Optional

import gemmi

from easydiffraction.sample_models.sample_model.base import SampleModelBase
from easydiffraction.utils.logging import log as logger


class SampleModelFactory:
    """Factory for creating `BaseSampleModel` instances with validated
    arguments.

    Valid argument combinations are mutually exclusive:
    - name (minimal model with defaults)
    - cif_path (CIF file path; name must not be provided)
    - cif_str (CIF content as string; name must not be provided)

    Any other combination is considered invalid.
    """

    VALID_ARG_SETS = (
        frozenset({'name'}),
        frozenset({'cif_path'}),
        frozenset({'cif_str'}),
    )

    @classmethod
    def _validate_args(
        cls,
        *,
        name: Optional[str] = None,
        cif_path: Optional[str] = None,
        cif_str: Optional[str] = None,
    ) -> None:
        present = frozenset(
            k
            for k, v in {'name': name, 'cif_path': cif_path, 'cif_str': cif_str}.items()
            if v is not None
        )
        if present not in cls.VALID_ARG_SETS:
            # Build helpful error message
            combos = ['(' + ', '.join(sorted(spec)) + ')' for spec in cls.VALID_ARG_SETS]
            allowed = ', '.join(combos)
            raise ValueError(
                'Invalid argument combination for SampleModel creation. '
                f'Provided={sorted(present)}. Allowed combinations: {allowed}. '
                "Note: Do not pass 'name' together with 'cif_path' or 'cif_str' "
                'since CIF contains the model name.'
            )

    @classmethod
    def create(
        cls,
        *,
        name: Optional[str] = None,
        cif_path: Optional[str] = None,
        cif_str: Optional[str] = None,
    ) -> SampleModelBase:
        """Create a `BaseSampleModel` using a validated argument
        combination.

        Args:
            name: Model identifier for a minimal model (no atoms by
                default).
            cif_path: Path to a CIF file used to build the model.
            cif_str: CIF content used to build the model.

        Returns:
            A constructed `BaseSampleModel` instance.

        Raises:
            ValueError: If the argument combination is invalid.
        """
        cls._validate_args(
            name=name,
            cif_path=cif_path,
            cif_str=cif_str,
        )
        if name is not None:
            return SampleModelBase(name=name)
        if cif_path is not None:
            return cls._create_from_cif_path(cif_path)
        if cif_str is not None:
            return cls._create_from_cif_str(cif_str)
        # Defensive: Should be unreachable due to validation above
        raise ValueError('No valid arguments provided to create SampleModel.')

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


class SampleModel:
    """User-facing API for creating a sample model.

    Use keyword-only arguments:
    - `name` for a minimal, empty model
    - `cif_path` to load from a CIF file
    - `cif_str` to load from CIF content
    """

    def __new__(cls, **kwargs):
        # Lazy import to avoid circular import at module load time

        try:
            return SampleModelFactory.create(**kwargs)
        except TypeError:
            logger.error(
                f'Invalid argument(s) for SampleModel: {kwargs}. '
                f"Did you mean 'name', 'cif_path', or 'cif_str'?",
                exc_type=TypeError,
            )

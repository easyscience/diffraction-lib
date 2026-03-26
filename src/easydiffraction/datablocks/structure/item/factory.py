# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Factory for creating structure instances from various inputs.

Provides individual class methods for each creation pathway:
``from_scratch``, ``from_cif_path``, or ``from_cif_str``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typeguard import typechecked

from easydiffraction.datablocks.structure.item.base import Structure
from easydiffraction.io.cif.parse import document_from_path
from easydiffraction.io.cif.parse import document_from_string
from easydiffraction.io.cif.parse import name_from_block
from easydiffraction.io.cif.parse import pick_sole_block
from easydiffraction.utils.logging import log

if TYPE_CHECKING:
    import gemmi


class StructureFactory:
    """Create :class:`Structure` instances from supported inputs."""

    def __init__(self):
        log.error(
            'Structure objects must be created using class methods such as '
            '`StructureFactory.from_cif_str(...)`, etc.'
        )

    # ------------------------------------------------------------------
    # Private helper methods
    # ------------------------------------------------------------------

    @classmethod
    # TODO: @typechecked fails to find gemmi?
    def _from_gemmi_block(
        cls,
        block: gemmi.cif.Block,
    ) -> Structure:
        """
        Build a structure from a single *gemmi* CIF block.


        Parameters
        ----------
        block : gemmi.cif.Block
            Parsed CIF data block.

        Returns
        -------
        Structure
            A fully populated structure instance.
        """
        name = name_from_block(block)
        structure = Structure(name=name)
        for category in structure.categories:
            category.from_cif(block)
        return structure

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    @classmethod
    @typechecked
    def from_scratch(
        cls,
        *,
        name: str,
    ) -> Structure:
        """
        Create a minimal default structure.


        Parameters
        ----------
        name : str
            Identifier for the new structure.

        Returns
        -------
        Structure
            An empty structure with default
            categories.
        """
        return Structure(name=name)

    # TODO: add minimal default configuration for missing parameters
    @classmethod
    @typechecked
    def from_cif_str(
        cls,
        cif_str: str,
    ) -> Structure:
        """
        Create a structure by parsing a CIF string.


        Parameters
        ----------
        cif_str : str
            Raw CIF content.

        Returns
        -------
        Structure
            A populated structure instance.
        """
        doc = document_from_string(cif_str)
        block = pick_sole_block(doc)
        return cls._from_gemmi_block(block)

    # TODO: Read content and call self.from_cif_str
    @classmethod
    @typechecked
    def from_cif_path(
        cls,
        cif_path: str,
    ) -> Structure:
        """
        Create a structure by reading and parsing a CIF file.


        Parameters
        ----------
        cif_path : str
            Filesystem path to a CIF file.

        Returns
        -------
        Structure
            A populated structure instance.
        """
        doc = document_from_path(cif_path)
        block = pick_sole_block(doc)
        return cls._from_gemmi_block(block)

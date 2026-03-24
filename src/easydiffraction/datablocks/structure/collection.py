# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Collection of structure data blocks."""

from typeguard import typechecked

from easydiffraction.core.datablock import DatablockCollection
from easydiffraction.datablocks.structure.item.base import Structure
from easydiffraction.datablocks.structure.item.factory import StructureFactory
from easydiffraction.utils.logging import console


class Structures(DatablockCollection):
    """Ordered collection of :class:`Structure` instances.

    Provides convenience ``add_from_*`` methods that mirror the
    :class:`StructureFactory` classmethods plus a bare :meth:`add` for
    inserting pre-built structures.
    """

    def __init__(self) -> None:
        """Initialise an empty structures collection."""
        super().__init__(item_type=Structure)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    # TODO: Make abstract in DatablockCollection?
    @typechecked
    def create(
        self,
        *,
        name: str,
    ) -> None:
        """Create a minimal structure and add it to the collection.

        Args:
            name (str): Identifier for the new structure.
        """
        structure = StructureFactory.from_scratch(name=name)
        self.add(structure)

    # TODO: Move to DatablockCollection?
    @typechecked
    def add_from_cif_str(
        self,
        cif_str: str,
    ) -> None:
        """Create a structure from CIF content and add it.

        Args:
            cif_str (str): CIF file content as a string.
        """
        structure = StructureFactory.from_cif_str(cif_str)
        self.add(structure)

    # TODO: Move to DatablockCollection?
    @typechecked
    def add_from_cif_path(
        self,
        cif_path: str,
    ) -> None:
        """Create a structure from a CIF file and add it.

        Args:
            cif_path (str): Filesystem path to a CIF file.
        """
        structure = StructureFactory.from_cif_path(cif_path)
        self.add(structure)


    # TODO: Move to DatablockCollection?
    def show_names(self) -> None:
        """List all structure names in the collection."""
        console.paragraph('Defined structures' + ' 🧩')
        console.print(self.names)

    # TODO: Move to DatablockCollection?
    def show_params(self) -> None:
        """Show parameters of all structures in the collection."""
        for structure in self.values():
            structure.show_params()

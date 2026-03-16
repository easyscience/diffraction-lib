# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typeguard import typechecked

from easydiffraction.core.datablock import DatablockCollection
from easydiffraction.datablocks.structure.item.base import Structure
from easydiffraction.datablocks.structure.item.factory import StructureFactory
from easydiffraction.utils.logging import console


class Structures(DatablockCollection):
    """Collection manager for multiple Structure instances."""

    def __init__(self) -> None:
        super().__init__(item_type=Structure)

    # --------------------
    # Add / Remove methods
    # --------------------

    # TODO: Move to DatablockCollection?
    # TODO: Disallow args and only allow kwargs?
    def add(self, **kwargs):
        structure = kwargs.pop('structure', None)

        if structure is None:
            structure = StructureFactory.create(**kwargs)

        self._add(structure)

    # @typechecked
    # def add_from_cif_path(self, cif_path: str) -> None:
    #    """Create and add a model from a CIF file path.#
    #
    #    Args:
    #        cif_path: Path to a CIF file.
    #    """
    #    structure = StructureFactory.create(cif_path=cif_path)
    #    self.add(structure)

    # @typechecked
    # def add_from_cif_str(self, cif_str: str) -> None:
    #    """Create and add a model from CIF content (string).
    #
    #    Args:
    #        cif_str: CIF file content.
    #    """
    #    structure = StructureFactory.create(cif_str=cif_str)
    #    self.add(structure)

    # @typechecked
    # def add_minimal(self, name: str) -> None:
    #    """Create and add a minimal model (defaults, no atoms).
    #
    #    Args:
    #        name: Identifier to assign to the new model.
    #    """
    #    structure = StructureFactory.create(name=name)
    #    self.add(structure)

    # TODO: Move to DatablockCollection?
    @typechecked
    def remove(self, name: str) -> None:
        """Remove a structure by its ID.

        Args:
            name: ID of the structure to remove.
        """
        if name in self:
            del self[name]

    # ------------
    # Show methods
    # ------------

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

# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause


from typeguard import typechecked

from easydiffraction.core.datablocks import DatablockCollection
from easydiffraction.sample_models.sample_model import SampleModel
from easydiffraction.sample_models.sample_model_types.base import BaseSampleModel
from easydiffraction.utils.formatting import paragraph


class SampleModels(DatablockCollection):
    """Collection manager for multiple SampleModel instances."""

    def __init__(self) -> None:
        super().__init__(item_type=BaseSampleModel)

    # --------------------
    # Add / Remove methods
    # --------------------

    @typechecked
    def add_from_cif_path(self, cif_path: str) -> None:
        """Create and add a model from a CIF file path.

        Args:
            cif_path: Path to a CIF file.
        """
        sample_model = SampleModel(cif_path=cif_path)
        self.add(sample_model)

    @typechecked
    def add_from_cif_str(self, cif_str: str) -> None:
        """Create and add a model from CIF content (string).

        Args:
            cif_str: CIF file content.
        """
        sample_model = SampleModel(cif_str=cif_str)
        self.add(sample_model)

    @typechecked
    def add_minimal(self, name: str) -> None:
        """Create and add a minimal model (defaults, no atoms).

        Args:
            name: Identifier to assign to the new model.
        """
        sample_model = SampleModel(name=name)
        self.add(sample_model)

    @typechecked
    def remove(self, name: str) -> None:
        """Remove a sample model by its ID.

        Args:
            name: ID of the model to remove.
        """
        if name in self:
            del self[name]

    # ------------
    # Show methods
    # ------------

    def show_names(self) -> None:
        """List all model names in the collection."""
        print(paragraph('Defined sample models' + ' 🧩'))
        print(self.names)

    def show_params(self) -> None:
        """Show parameters of all sample models in the collection."""
        for model in self.values():
            model.show_params()

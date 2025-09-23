# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import List

from easydiffraction.core.datablocks import DatablockCollection
from easydiffraction.sample_models.sample_model import BaseSampleModel
from easydiffraction.sample_models.sample_model import SampleModel
from easydiffraction.utils.decorators import enforce_type
from easydiffraction.utils.formatting import paragraph


class SampleModels(DatablockCollection):
    """Collection manager for multiple SampleModel instances."""

    def __init__(self) -> None:
        super().__init__()  # Initialize Collection
        self._models = self._datablocks  # Alias for legacy support

    @property
    def names(self) -> List[str]:
        """Return a list of all model names in the collection."""
        return list(self._models.keys())

    # --------------------
    # Add / Remove methods
    # --------------------

    @enforce_type
    def add(self, model: BaseSampleModel) -> None:
        """Add a pre-built SampleModel instance.

        Args:
            model: An existing SampleModel instance to add.
        """
        self._models[model.name] = model

    def add_from_cif_path(self, cif_path: str) -> None:
        """Create and add a model from a CIF file path.

        Args:
            cif_path: Path to a CIF file.
        """
        model = SampleModel(cif_path=cif_path)
        self.add(model)

    def add_from_cif_str(self, cif_str: str) -> None:
        """Create and add a model from CIF content (string).

        Args:
            cif_str: CIF file content.
        """
        model = SampleModel(cif_str=cif_str)
        self.add(model)

    def add_minimal(self, name: str) -> None:
        """Create and add a minimal model (defaults, no atoms).

        Args:
            name: Identifier to assign to the new model.
        """
        model = SampleModel(name=name)
        self.add(model)

    def remove(self, name: str) -> None:
        """Remove a sample model by its ID.

        Args:
            name: ID of the model to remove.
        """
        if name in self._models:
            del self._models[name]

    # -----------
    # CIF methods
    # -----------

    @property
    def as_cif(self) -> str:
        """Export all sample models to CIF format.

        Returns:
            CIF string representation of all sample models.
        """
        return '\n'.join([model.as_cif() for model in self._models.values()])

    # ------------
    # Show methods
    # ------------

    def show_names(self) -> None:
        """List all model names in the collection."""
        print(paragraph('Defined sample models' + ' 🧩'))
        print(self.names)

    def show_params(self) -> None:
        """Show parameters of all sample models in the collection."""
        for model in self._models.values():
            model.show_params()

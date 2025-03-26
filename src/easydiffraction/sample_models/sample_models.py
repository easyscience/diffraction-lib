from .space_group import SpaceGroup
from .cell import Cell
from .atom_sites import AtomSites, AtomSite
from easydiffraction.base_collection import BaseCollection
from easydiffraction.utils.structure_plotter import StructurePlotter
from easydiffraction.utils.utils import paragraph


class SampleModel:
    """
    Represents an individual structural/magnetic model of a sample.
    Wraps crystallographic information including space group, cell, and atomic sites.
    """

    def __init__(self, model_id=None, cif_path=None, cif_str=None):
        self.model_id = model_id or "sample_model"
        self.space_group = SpaceGroup()
        self.cell = Cell()
        self.atom_sites = AtomSites()

        if cif_path:
            self.load_from_cif_file(cif_path)
        elif cif_str:
            self.load_from_cif_string(cif_str)

    def load_from_cif_file(self, cif_path: str):
        """Load model data from a CIF file."""
        # TODO: Implement CIF parsing here
        print(f"Loading SampleModel from CIF file: {cif_path}")
        # Example: self.id = extract_id_from_cif(cif_path)

    def load_from_cif_string(self, cif_str: str):
        """Load model data from a CIF string."""
        # TODO: Implement CIF parsing from a string
        print("Loading SampleModel from CIF string.")

    def show_structure(self, plane='xy', grid_size=20):
        """
        Show an ASCII projection of the structure on a 2D plane.

        Args:
            plane (str): 'xy', 'xz', or 'yz' plane to project.
            grid_size (int): Size of the ASCII grid (default is 20).
        """

        print(paragraph(f"Sample model 🧩 '{self.model_id}' structure view"))
        print("Not implemented yet.")
        #plotter = StructurePlotter(grid_size=grid_size)
        #plotter.draw_from_cif(self.as_cif())

    def show_params(self):
        """Display structural parameters (space group, unit cell, atomic sites)."""
        print(f"\nSampleModel ID: {self.model_id}")
        print(f"Space group: {self.space_group.name}")
        print(f"Cell parameters: {self.cell.as_dict()}")
        print("Atom sites:")
        self.atom_sites.show()

    def as_cif(self) -> str:
        """
        Export the sample model to CIF format.
        Returns:
            str: CIF string representation of the sample model.
        """
        # Data block header
        cif_lines = [f"data_{self.model_id}"]

        # Space Group
        cif_lines += ["", self.space_group.as_cif()]

        # Unit Cell
        cif_lines += ["", self.cell.as_cif()]

        # Atom Sites
        cif_lines += ["", self.atom_sites.as_cif()]

        return "\n".join(cif_lines)

    def show_as_cif(self):
        cif_text = self.as_cif()
        lines = cif_text.splitlines()
        max_width = max(len(line) for line in lines)
        padded_lines = [f"│ {line.ljust(max_width)} │" for line in lines]
        top = f"╒{'═' * (max_width + 2)}╕"
        bottom = f"╘{'═' * (max_width + 2)}╛"

        print(paragraph(f"Sample model 🧩 '{self.model_id}' as cif"))
        print(top)
        print("\n".join(padded_lines))
        print(bottom)

class SampleModels(BaseCollection):
    """
    Collection manager for multiple SampleModel instances.
    """

    def __init__(self):
        super().__init__()  # Initialize BaseCollection
        self._models = self._items  # Alias for legacy support

    def add(self, model=None, model_id=None, cif_path=None, cif_str=None):
        """
        Add a new sample model to the collection.
        Dispatches based on input type: pre-built model or parameters for new creation.
        """
        if model:
            self._add_prebuilt_sample_model(model)
        else:
            self._create_and_add_sample_model(model_id, cif_path, cif_str)

    def remove(self, model_id):
        """
        Remove a sample model by its ID.
        """
        if model_id in self._models:
            del self._models[model_id]

    def get_ids(self):
        """
        Return a list of all model IDs in the collection.
        """
        return list(self._models.keys())

    def show_ids(self):
        """
        List all model IDs in the collection.
        """
        print(paragraph("Defined sample models" + " 🧩"))
        print(self.get_ids())

    def show_params(self):
        """
        Show parameters of all sample models in the collection.
        """
        for model in self._models.values():
            model.show_params()

    def as_cif(self) -> str:
        """
        Export all sample models to CIF format.
        """
        return "\n".join([model.as_cif() for model in self._models.values()])

    def __getitem__(self, model_id):
        """
        Access a sample model by its ID.
        """
        return self._models[model_id]

    # ==========================
    # Private helper methods
    # ==========================

    def _add_prebuilt_sample_model(self, model):
        """
        Add a pre-built SampleModel instance.
        """
        from easydiffraction.sample_models.sample_models import SampleModel  # avoid circular import
        if not isinstance(model, SampleModel):
            raise TypeError("Expected an instance of SampleModel")
        self._models[model.model_id] = model

    def _create_and_add_sample_model(self, model_id=None, cif_path=None, cif_str=None):
        """
        Create a SampleModel instance and add it to the collection.
        """
        from easydiffraction.sample_models.sample_models import SampleModel  # avoid circular import

        if cif_path:
            model = SampleModel(cif_path=cif_path)
        elif cif_str:
            model = SampleModel(cif_str=cif_str)
        elif model_id:
            model = SampleModel(model_id=model_id)
        else:
            raise ValueError("You must provide a model_id, cif_path, or cif_str.")

        self._models[model.model_id] = model
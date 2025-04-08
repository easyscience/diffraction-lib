from easydiffraction.crystallography import crystallography as ecr
from easydiffraction.core.objects import (
    Collection,
    Datablock
)
from easydiffraction.sample_models.standard_components.space_group import SpaceGroup
from easydiffraction.sample_models.standard_components.cell import Cell
from easydiffraction.sample_models.iterable_components.atom_sites import AtomSites
from easydiffraction.utils.formatting import paragraph


class SampleModel(Datablock):
    """
    Represents an individual structural/magnetic model of a sample.
    Wraps crystallographic information including space group, cell, and atomic sites.
    """

    def __init__(self, name, cif_path=None, cif_str=None):
        self.name = name
        self.space_group = SpaceGroup()
        self.cell = Cell()
        self.atom_sites = AtomSites()

        if cif_path:
            self.load_from_cif_file(cif_path)
        elif cif_str:
            self.load_from_cif_string(cif_str)

    def apply_symmetry_constraints(self):
        self._apply_cell_symmetry_constraints()
        self._apply_atomic_coordinates_symmetry_constraints()
        self._apply_atomic_displacement_symmetry_constraints()

    def _apply_cell_symmetry_constraints(self):
        dummy_cell = {'lattice_a': self.cell.length_a.value,
                      'lattice_b': self.cell.length_b.value,
                      'lattice_c': self.cell.length_c.value,
                      'angle_alpha': self.cell.angle_alpha.value,
                      'angle_beta': self.cell.angle_beta.value,
                      'angle_gamma': self.cell.angle_gamma.value}
        space_group_name = self.space_group.name_h_m.value
        ecr.apply_cell_symmetry_constraints(cell=dummy_cell,
                                            name_hm=space_group_name)
        self.cell.length_a.value = dummy_cell['lattice_a']
        self.cell.length_b.value = dummy_cell['lattice_b']
        self.cell.length_c.value = dummy_cell['lattice_c']
        self.cell.angle_alpha.value = dummy_cell['angle_alpha']
        self.cell.angle_beta.value = dummy_cell['angle_beta']
        self.cell.angle_gamma.value = dummy_cell['angle_gamma']

    def _apply_atomic_coordinates_symmetry_constraints(self):
        space_group_name = self.space_group.name_h_m.value
        space_group_coord_code = self.space_group.it_coordinate_system_code.value
        for atom in self.atom_sites:
            dummy_atom = {"fract_x": atom.fract_x.value,
                          "fract_y": atom.fract_y.value,
                          "fract_z": atom.fract_z.value}
            wl = atom.wyckoff_letter.value
            if not wl:
                #raise ValueError("Wyckoff letter is not defined for atom.")
                continue
            ecr.apply_atom_site_symmetry_constraints(atom_site=dummy_atom,
                                                     name_hm=space_group_name,
                                                     coord_code=space_group_coord_code,
                                                     wyckoff_letter=wl)
            atom.fract_x.value = dummy_atom['fract_x']
            atom.fract_y.value = dummy_atom['fract_y']
            atom.fract_z.value = dummy_atom['fract_z']

    def _apply_atomic_displacement_symmetry_constraints(self):
        pass

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

        print(paragraph(f"Sample model 🧩 '{self.name}' structure view"))
        print("Not implemented yet.")

    def show_params(self):
        """Display structural parameters (space group, unit cell, atomic sites)."""
        print(f"\nSampleModel ID: {self.name}")
        print(f"Space group: {self.space_group.name_h_m}")
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
        cif_lines = [f"data_{self.name}"]

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

        print(paragraph(f"Sample model 🧩 '{self.name}' as cif"))
        print(top)
        print("\n".join(padded_lines))
        print(bottom)



class SampleModels(Collection):
    """
    Collection manager for multiple SampleModel instances.
    """

    def __init__(self):
        super().__init__()  # Initialize Collection
        self._models = self._items  # Alias for legacy support

    def add(self, model=None, model_name=None, cif_path=None, cif_str=None):
        """
        Add a new sample model to the collection.
        Dispatches based on input type: pre-built model or parameters for new creation.
        """
        if model:
            self._add_prebuilt_sample_model(model)
        else:
            self._create_and_add_sample_model(model_name, cif_path, cif_str)

    def remove(self, name):
        """
        Remove a sample model by its ID.
        """
        if name in self._models:
            del self._models[name]

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

    def _add_prebuilt_sample_model(self, model):
        """
        Add a pre-built SampleModel instance.
        """
        from easydiffraction.sample_models.sample_models import SampleModel  # avoid circular import
        if not isinstance(model, SampleModel):
            raise TypeError("Expected an instance of SampleModel")
        self._models[model.name] = model

    def _create_and_add_sample_model(self, name=None, cif_path=None, cif_str=None):
        """
        Create a SampleModel instance and add it to the collection.
        """
        from easydiffraction.sample_models.sample_models import SampleModel  # avoid circular import

        if cif_path:
            model = SampleModel(cif_path=cif_path)
        elif cif_str:
            model = SampleModel(cif_str=cif_str)
        elif name:
            model = SampleModel(name=name)
        else:
            raise ValueError("You must provide a name, cif_path, or cif_str.")

        self._models[model.name] = model
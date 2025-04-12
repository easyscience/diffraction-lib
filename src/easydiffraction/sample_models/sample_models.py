from easydiffraction.core.objects import Collection
from easydiffraction.utils.formatting import paragraph
from easydiffraction.sample_models.sample_model import SampleModel

class SampleModels(Collection):
    """
    Collection manager for multiple SampleModel instances.
    """

    def __init__(self):
        super().__init__()  # Initialize Collection
        self._models = self._items  # Alias for legacy support

    def add(self, model=None, name=None, cif_path=None, cif_str=None):
        """
        Add a new sample model to the collection.
        Dispatches based on input type: pre-built model or parameters for new creation.
        """
        if model:
            self._add_prebuilt_sample_model(model)
        else:
            self._create_and_add_sample_model(name, cif_path, cif_str)

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

    def show_names(self):
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
        if not isinstance(model, SampleModel):
            raise TypeError("Expected an instance of SampleModel")
        self._models[model.name] = model

    def _create_and_add_sample_model(self, name=None, cif_path=None, cif_str=None):
        """
        Create a SampleModel instance and add it to the collection.
        """
        if cif_path:
            model = SampleModel(cif_path=cif_path)
        elif cif_str:
            model = SampleModel(cif_str=cif_str)
        elif name:
            model = SampleModel(name=name)
        else:
            raise ValueError("You must provide a name, cif_path, or cif_str.")

        self._models[model.name] = model
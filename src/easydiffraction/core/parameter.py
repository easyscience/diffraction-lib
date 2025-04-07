import random
import string
from easydiffraction.utils.formatting import warning


class Descriptor:
    """
    Base class for descriptors (non-refinable attributes).
    """

    def __init__(self,
                 value,
                 cif_name,
                 pretty_name=None,
                 block_name=None,
                 units=None,
                 description=None,
                 editable=True):
        self._value = value
        self._description = description
        self._editable = editable
        self._pretty_name = pretty_name,
        self.cif_name = cif_name
        self.units = units
        self.is_parameter = False  # Differentiates from Parameter class
        self.block_name = block_name
        self.uid = self._generate_unique_id()

    def _generate_unique_id(self):
        # TODO: Instead of generating a random string, we can use the
        #  name of the parameter and the block name to create a unique id.
        #  E.g.:
        #  - "block-id__category-name__parameter-name": "lbco__cell__length_a"
        #  - "block-id__category-name__row-id__parameter-name": "lbco__atom_site__ba__fract_x"
        length = 12
        letters = random.choices(string.ascii_lowercase, k=length)
        uid = ''.join(letters)
        return uid
        # self.uid is needed to make a list of free parameters for the
        # minimization engine, and then to be able to update the sample
        # models and experiments with the new values.
        # TODO: It is used in collection.py to generate a unique id for
        #  the parameter. Check if it is needed here. When called from
        #  __init__, block_name is not set yet?
        # TODO: Check if it works for the iterable components, such as
        #  atoms_sites, background, etc.
        # TODO: Check if we need to replace "-" with "_"
        # TODO: Check if we need make it lowercase
        raw_name = self.cif_name
        sanitized = (
            raw_name.replace("[", "_")
                    .replace("]", "")
                    .replace(".", "_")
                    .replace("'", "")
        )
        if self.block_name:
            sanitized = f"{self.block_name}_{sanitized}"
        return sanitized

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if self._editable:
            self._value = new_value
        else:
            print(warning(f"The parameter '{self.cif_name}' it is calculated automatically and cannot be changed manually."))

    @property
    def description(self):
        return self._description

    @property
    def editable(self):
        return self._editable

class Parameter(Descriptor):
    """
    A parameter with a value, uncertainty, units, and CIF representation.
    """

    def __init__(self,
                 value,
                 cif_name,
                 pretty_name=None,
                 block_name=None,
                 description=None,
                 uncertainty=0.0,
                 free=False,
                 units=None,
                 min_value=None,
                 max_value=None):
        super().__init__(value,
                         cif_name,
                         pretty_name,
                         block_name,
                         units,
                         description)
        self.uncertainty = uncertainty
        self.free = free
        self.is_parameter = True  # Flag to detect parameters
        self.min = min_value
        self.max = max_value

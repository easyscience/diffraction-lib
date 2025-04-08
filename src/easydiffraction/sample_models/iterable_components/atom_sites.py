from easydiffraction.core.objects import (
    Descriptor,
    Parameter,
    Component,
    Collection
)


class AtomSite(Component):
    """
    Represents a single atom site within the crystal structure.
    """

    def __init__(self,
                 label: str,
                 type_symbol: str,
                 fract_x: float,
                 fract_y: float,
                 fract_z: float,
                 wyckoff_letter: str = None,
                 occupancy: float = 1.0,
                 b_iso: float = 0.0,
                 adp_type: str = "Biso"):  # TODO: add support for Uiso, Uani and Bani
        super().__init__()

        self.label = Descriptor(
            value=label,
            cif_param_name="label"
        )
        self.type_symbol = Descriptor(
            value=type_symbol,
            cif_param_name="type_symbol"
        )
        self.adp_type = Descriptor(
            value=adp_type,
            cif_param_name="ADP_type"
        )
        self.wyckoff_letter = Descriptor(
            value=wyckoff_letter,
            cif_param_name="Wyckoff_letter"
        )
        self.fract_x = Parameter(
            value=fract_x,
            cif_param_name="fract_x"
        )
        self.fract_y = Parameter(
            value=fract_y,
            cif_param_name="fract_y"
        )
        self.fract_z = Parameter(
            value=fract_z,
            cif_param_name="fract_z"
        )
        self.occupancy = Parameter(
            value=occupancy,
            cif_param_name="occupancy"
        )
        self.b_iso = Parameter(
            value=b_iso,
            cif_param_name="B_iso_or_equiv"
        )

    @property
    def cif_category_key(self):
        return "atom_site"

    @property
    def category_key(self):
        return "atom_site"

    @property
    def _entry_id(self):
        return self.label.value


class AtomSites(Collection):
    """
    Collection of AtomSite instances.
    """
    @property
    def _type(self):
        return "category"  # datablock or category

    def add(self,
            label: str,
            type_symbol: str,
            fract_x: float,
            fract_y: float,
            fract_z: float,
            wyckoff_letter: str = None,
            occupancy: float = 1.0,
            b_iso: float = 0.0,
            adp_type: str = "Biso"):
        """
        Add a new atom site to the collection.
        """
        site = AtomSite(label,
                        type_symbol,
                        fract_x,
                        fract_y,
                        fract_z,
                        wyckoff_letter,
                        occupancy,
                        b_iso,
                        adp_type)
        self._items[site._entry_id] = site

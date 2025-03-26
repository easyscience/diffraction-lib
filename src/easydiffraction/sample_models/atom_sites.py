from typing import List, Union, Iterator
from easydiffraction.parameter import Parameter, Descriptor


class AtomSite:
    """
    Represents a single atom site within the crystal structure.
    """
    cif_category_name = "_atom_site"

    def __init__(
        self,
        label: str,
        type_symbol: str,
        fract_x: float,
        fract_y: float,
        fract_z: float,
        occupancy: float = 1.0,
        b_iso: float = 0.0,
        adp_type: str = "Biso"
    ):
        # Descriptors (static values, non-refinable)
        self.label = Descriptor(label, cif_name="label")
        self.type_symbol = Descriptor(type_symbol, cif_name="type_symbol")
        self.adp_type = Descriptor(adp_type, cif_name="ADP_type")

        # Parameters (refinable)
        self.fract_x = Parameter(fract_x, cif_name="fract_x")
        self.fract_y = Parameter(fract_y, cif_name="fract_y")
        self.fract_z = Parameter(fract_z, cif_name="fract_z")
        self.occupancy = Parameter(occupancy, cif_name="occupancy")
        self.b_iso = Parameter(b_iso, cif_name="B_iso_or_equiv")

    def as_cif(self) -> str:
        """
        Export this atom site as a CIF row string.
        """
        return (
            f"{self.label.value} {self.type_symbol.value} "
            f"{self.fract_x.value} {self.fract_y.value} {self.fract_z.value} "
            f"{self.occupancy.value} {self.adp_type.value} {self.b_iso.value}"
        )


class AtomSites:
    """
    Collection of AtomSite instances.
    Provides methods to add, show, and access atom sites.
    """

    def __init__(self):
        self.sites: List[AtomSite] = []

    def add(
        self,
        label: str,
        type_symbol: str,
        fract_x: float,
        fract_y: float,
        fract_z: float,
        occupancy: float = 1.0,
        b_iso: float = 0.0,
        adp_type: str = "Biso"
    ):
        """
        Add a new atom site to the collection.
        """
        site = AtomSite(label, type_symbol, fract_x, fract_y, fract_z, occupancy, b_iso, adp_type)
        self.sites.append(site)

    def show(self):
        """
        Print CIF rows for all atom sites.
        """
        print(f"{'Label':<8} {'Type':<6} {'fract_x':<10} {'fract_y':<10} {'fract_z':<10} "
              f"{'Occupancy':<10} {'ADP Type':<8} {'B_iso':<10}")
        print("-" * 80)
        for site in self.sites:
            print(site.as_cif_row())

    def __iter__(self) -> Iterator[AtomSite]:
        """
        Iterate through atom sites.
        """
        return iter(self.sites)

    def __getitem__(self, key: Union[int, str]) -> AtomSite:
        """
        Access an AtomSite by index or by label.
        """
        if isinstance(key, int):
            try:
                return self.sites[key]
            except IndexError:
                raise IndexError(f"No AtomSite at index {key}.")
        elif isinstance(key, str):
            for site in self.sites:
                if site.label.value == key:
                    return site
            raise KeyError(f"No AtomSite with label '{key}' found.")
        else:
            raise TypeError("Key must be an integer index or a string label.")

    def __len__(self) -> int:
        """
        Return the number of atom sites.
        """
        return len(self.sites)

    def as_cif(self) -> str:
        """
        Export all atom sites as a CIF loop string.
        """
        lines = [
            "loop_",
            "_atom_site.label",
            "_atom_site.type_symbol",
            "_atom_site.fract_x",
            "_atom_site.fract_y",
            "_atom_site.fract_z",
            "_atom_site.occupancy",
            "_atom_site.ADP_type",
            "_atom_site.B_iso_or_equiv"
        ]
        for site in self.sites:
            lines.append(site.as_cif())
        return "\n".join(lines)
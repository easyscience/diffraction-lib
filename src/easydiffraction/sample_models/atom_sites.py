from easydiffraction.parameter import Parameter, Descriptor

class AtomSite:
    cif_category_name = "_atom_site"

    def __init__(self, label, type_symbol, fract_x, fract_y, fract_z,
                 occupancy=1.0, b_iso=0.0, adp_type="Biso"):
        # Descriptors (static)
        self.label = Descriptor(label, cif_name="label")
        self.type_symbol = Descriptor(type_symbol, cif_name="type_symbol")
        self.adp_type = Descriptor(adp_type, cif_name="ADP_type")

        # Parameters (refinable)
        self.fract_x = Parameter(fract_x, cif_name="fract_x")
        self.fract_y = Parameter(fract_y, cif_name="fract_y")
        self.fract_z = Parameter(fract_z, cif_name="fract_z")
        self.occupancy = Parameter(occupancy, cif_name="occupancy")
        self.b_iso = Parameter(b_iso, cif_name="B_iso_or_equiv")

    def as_cif_row(self):
        return f"{self.label.value} {self.type_symbol.value} {self.fract_x.value} {self.fract_y.value} {self.fract_z.value} {self.occupancy.value} {self.adp_type.value} {self.b_iso.value}"

class AtomSites:


    def __init__(self):
        self.sites = []

    def add(self, label, type_symbol, fract_x, fract_y, fract_z, occupancy=1.0, b_iso=0.0):
        site = AtomSite(label, type_symbol, fract_x, fract_y, fract_z, occupancy, b_iso)
        self.sites.append(site)

    def show(self):
        for site in self.sites:
            print(site.as_cif_row())

    def __iter__(self):
        return iter(self.sites)

    def __getitem__(self, key):
        """
        Allow lookup by label (string) or index (int).
        """
        if isinstance(key, int):
            return self.sites[key]

        if isinstance(key, str):
            for site in self.sites:
                if site.label.value == key:
                    return site
            raise KeyError(f"No AtomSite with label '{key}' found.")

        raise TypeError("Key must be an integer index or a string label.")
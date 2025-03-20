"""
StructurePlotter: ASCII renderer for crystal structures from CIF strings, using gemmi.
"""

import gemmi
import numpy as np


class StructurePlotter:
    """
    ASCII-based renderer for crystal structures from CIF strings.
    Supports 'xy', 'xz', and 'yz' projection planes.
    """

    VALID_PLANES = {'xy', 'xz', 'yz'}

    def __init__(self, grid_size=20, plane='xz'):
        """
        Initialize the plotter.

        :param grid_size: Grid size for ASCII rendering (square grid).
        :param plane: Projection plane: 'xy', 'xz', or 'yz'.
        """
        if plane not in self.VALID_PLANES:
            raise ValueError(f"Invalid plane '{plane}'. Choose from {self.VALID_PLANES}.")
        self.grid_size = grid_size
        self.plane = plane
        self.axes = {'xy': (0, 1), 'xz': (0, 2), 'yz': (1, 2)}

    def draw_from_cif(self, cif_string):
        """
        Draws an ASCII structure from a CIF string using gemmi.

        :param cif_string: CIF content as a string.
        """
        try:
            doc = gemmi.cif.read_string(cif_string)
            block = doc.sole_block()
            struct = gemmi.make_structure_from_block(block)

            if len(struct) == 0:
                print("⚠️ No atoms found using gemmi.make_structure_from_block, falling back to manual parsing...")
                atoms = self._parse_atom_sites(block)
            else:
                atoms = self._extract_atoms_from_structure(struct)

            if not atoms:
                print("⚠️ No atoms found in CIF.")
                return

            self._draw(atoms)

        except Exception as e:
            print(f"❌ Error parsing CIF string: {e}")

    def _parse_atom_sites(self, block):
        atom_site_loop = block.find_loop('_atom_site.label')

        if not atom_site_loop:
            print("❌ No valid atom site loop found in CIF.")
            return []

        loop = atom_site_loop.get_loop()

        try:
            labels = loop.tags
        except Exception as e:
            print(f"❌ Failed to retrieve tags: {e}")
            return []

        print(f"✅ Found atom site tags: {labels}")

        if not labels:
            print("⚠️ Atom site loop is empty.")
            return []

        try:
            x_idx = labels.index('_atom_site.fract_x')
            y_idx = labels.index('_atom_site.fract_y')
            z_idx = labels.index('_atom_site.fract_z')
        except ValueError as e:
            print(f"❌ Required fractional coordinate fields not found: {e}")
            return []

        element_idx = (
            labels.index('_atom_site.type_symbol')
            if '_atom_site.type_symbol' in labels
            else labels.index('_atom_site.label')
        )

        atoms = []
        n_rows = loop.length()

        for i in range(n_rows):  # Iterate by row index
            try:
                atoms.append({
                    'symbol': loop[i, element_idx],
                    'frac': (
                        float(loop[i, x_idx]),
                        float(loop[i, y_idx]),
                        float(loop[i, z_idx])
                    )
                })
            except (ValueError, IndexError, TypeError) as e:
                print(f"⚠️ Skipping invalid atom site entry at row {i}: {e}")
                continue

        return atoms

    def _extract_atoms_from_structure(self, struct):
        """
        Extract atoms from gemmi.Structure object.

        :param struct: gemmi.Structure.
        :return: List of atoms as dictionaries with 'symbol' and 'frac'.
        """
        atoms = []
        for model in struct:
            for chain in model:
                for residue in chain:
                    for atom in residue:
                        atoms.append({
                            'symbol': atom.element.name,
                            'frac': (atom.frac.x, atom.frac.y, atom.frac.z)
                        })
        return atoms

    def _draw(self, atoms):
        """
        Render the ASCII plot from the given atoms.
        """
        ax1, ax2 = self.axes[self.plane]

        coords_ax1 = np.array([atom['frac'][ax1] for atom in atoms])
        coords_ax2 = np.array([atom['frac'][ax2] for atom in atoms])

        min_ax1, max_ax1 = coords_ax1.min(), coords_ax1.max()
        min_ax2, max_ax2 = coords_ax2.min(), coords_ax2.max()

        # Initialize empty grid
        grid = [[' ' for _ in range(self.grid_size)] for _ in range(self.grid_size)]

        for atom in atoms:
            frac = atom['frac']
            symbol = atom['symbol']

            norm_x = (frac[ax1] - min_ax1) / (max_ax1 - min_ax1 + 1e-8)
            norm_y = (frac[ax2] - min_ax2) / (max_ax2 - min_ax2 + 1e-8)

            x_idx = int(norm_x * (self.grid_size - 1))
            y_idx = int(norm_y * (self.grid_size - 1))

            x_idx = min(max(x_idx, 0), self.grid_size - 1)
            y_idx = min(max(y_idx, 0), self.grid_size - 1)

            grid[self.grid_size - 1 - y_idx][x_idx] = symbol[0]

        print("\n" + "-" * self.grid_size)
        for row in grid:
            print(''.join(row))
        print("-" * self.grid_size)
        print(f"Projection plane: {self.plane.upper()}")
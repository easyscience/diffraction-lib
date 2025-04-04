from sympy import symbols, sympify, simplify
from tabulate import tabulate
from .space_group_database import space_group_database
from .space_group_lookup_tables import (
    lookup_by_hm_ref_index,
    lookup_by_hm_alt_index,
    lookup_by_hall_symbol_index,
)


def normalize_hm_symbol(symbol: str) -> str:
    stripped = symbol.replace(" ", "")
    lowered = stripped.lower()
    return lowered


def get_space_group_by_hm_ref(hm_ref: str,
                              coord_code: str = None):
    key = (hm_ref, coord_code)
    sg_key = lookup_by_hm_ref_index.get(key)

    if sg_key is None:
        fallback_key = (hm_ref, None)
        sg_key = lookup_by_hm_ref_index.get(fallback_key)

    if sg_key is None:
        return None

    sg_entry = space_group_database.get(sg_key)
    return sg_entry


def get_space_group_by_hm_alt(hm_alt: str):
    norm_input = normalize_hm_symbol(hm_alt)

    for stored_symbol, sg_key in lookup_by_hm_alt_index.items():
        stored_normalized = normalize_hm_symbol(stored_symbol)

        if stored_normalized == norm_input:
            sg_entry = space_group_database.get(sg_key)
            return sg_entry

    return None


def get_space_group_by_hall_symbol(hall_symbol: str):
    sg_key = lookup_by_hall_symbol_index.get(hall_symbol)

    if sg_key is None:
        return None

    sg_entry = space_group_database.get(sg_key)
    return sg_entry


def get_space_group_by_it_number(it_number: int,
                                 coord_code: str = None):
    sg_key = (it_number, coord_code)
    sg_entry = space_group_database.get(sg_key)
    return sg_entry


def apply_cell_symmetry_constraints(cell: dict,
                                    space_group_entry: dict) -> dict:
    cs = space_group_entry.get("crystal_system", "unknown").lower()

    if cs == "cubic":
        a = cell["lattice_a"]
        cell["lattice_b"] = a
        cell["lattice_c"] = a
        cell["angle_alpha"] = 90
        cell["angle_beta"] = 90
        cell["angle_gamma"] = 90

    elif cs == "tetragonal":
        a = cell["lattice_a"]
        cell["lattice_b"] = a
        cell["angle_alpha"] = 90
        cell["angle_beta"] = 90
        cell["angle_gamma"] = 90

    elif cs == "orthorhombic":
        cell["angle_alpha"] = 90
        cell["angle_beta"] = 90
        cell["angle_gamma"] = 90

    elif cs in {"hexagonal", "trigonal"}:
        a = cell["lattice_a"]
        cell["lattice_b"] = a
        cell["angle_alpha"] = 90
        cell["angle_beta"] = 90
        cell["angle_gamma"] = 120

    elif cs == "monoclinic":
        cell["angle_alpha"] = 90
        cell["angle_gamma"] = 90

    elif cs == "triclinic":
        pass  # No constraints to apply

    else:
        error_msg = f"Unknown or unsupported crystal system: {cs}"
        raise ValueError(error_msg)

    return cell


def apply_atom_site_symmetry_constraints(atom_site: dict,
                                         space_group_entry: dict,
                                         wyckoff_letter: str) -> dict:
    x, y, z = symbols("x y z")

    wyckoff_data = space_group_entry.get("Wyckoff_positions", {})
    wyckoff = wyckoff_data.get(wyckoff_letter)

    if wyckoff is None:
        error_msg = f"Wyckoff letter '{wyckoff_letter}' not found."
        raise ValueError(error_msg)

    first_position = wyckoff["coords_xyz"][0]
    components = first_position.strip("()").split(",")
    parsed_exprs = [sympify(comp.strip()) for comp in components]

    x_val = sympify(atom_site["fract_x"])
    y_val = sympify(atom_site["fract_y"])
    z_val = sympify(atom_site["fract_z"])

    substitutions = {
        "x": x_val,
        "y": y_val,
        "z": z_val
    }

    axes = ("x", "y", "z")
    symbols_xyz = (x, y, z)

    for i, axis in enumerate(axes):
        symbol = symbols_xyz[i]
        is_free = any(symbol in expr.free_symbols for expr in parsed_exprs)

        if not is_free:
            evaluated = parsed_exprs[i].subs(substitutions)
            simplified = simplify(evaluated)
            atom_site[f"fract_{axis}"] = float(simplified)

    return atom_site


def show_wyckoff_positions_table(space_group_entry: dict):
    wyckoff_data = space_group_entry.get("Wyckoff_positions", {})
    headers = ["Letter", "Multiplicity", "Site Symmetry", "Fractional Coordinates"]

    rows = []

    for letter, data in sorted(wyckoff_data.items()):
        multiplicity = data["multiplicity"]
        symmetry = data["site_symmetry"]
        coords = ", ".join(data["coords_xyz"])

        row = [letter, multiplicity, symmetry, coords]
        rows.append(row)

    table = tabulate(rows,
                     headers=headers,
                     tablefmt="fancy_outline",
                     numalign="left",
                     showindex=False)
    print(table)
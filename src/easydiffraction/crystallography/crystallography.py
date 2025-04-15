from sympy import (
    symbols,
    sympify,
    simplify
)

from cryspy.A_functions_base.function_2_space_group import (
    get_crystal_system_by_it_number,
    get_it_number_by_name_hm_short,
    get_symop_pcentr_multiplicity_letter_site_symmetry_coords_xyz_2
)
from easydiffraction.crystallography.space_group_lookup_table import SPACE_GROUP_LOOKUP_DICT


def apply_cell_symmetry_constraints(cell: dict,
                                    name_hm: str) -> dict:
    it_number = get_it_number_by_name_hm_short(name_hm)
    if it_number is None:
        error_msg = f"Failed to get IT_number for name_H-M '{name_hm}'"
        print(error_msg)
        return cell

    crystal_system = get_crystal_system_by_it_number(it_number)
    if crystal_system is None:
        error_msg = f"Failed to get crystal system for IT_number '{it_number}'"
        print(error_msg)
        return cell

    if crystal_system == "cubic":
        a = cell["lattice_a"]
        cell["lattice_b"] = a
        cell["lattice_c"] = a
        cell["angle_alpha"] = 90
        cell["angle_beta"] = 90
        cell["angle_gamma"] = 90

    elif crystal_system == "tetragonal":
        a = cell["lattice_a"]
        cell["lattice_b"] = a
        cell["angle_alpha"] = 90
        cell["angle_beta"] = 90
        cell["angle_gamma"] = 90

    elif crystal_system == "orthorhombic":
        cell["angle_alpha"] = 90
        cell["angle_beta"] = 90
        cell["angle_gamma"] = 90

    elif crystal_system in {"hexagonal", "trigonal"}:
        a = cell["lattice_a"]
        cell["lattice_b"] = a
        cell["angle_alpha"] = 90
        cell["angle_beta"] = 90
        cell["angle_gamma"] = 120

    elif crystal_system == "monoclinic":
        cell["angle_alpha"] = 90
        cell["angle_gamma"] = 90

    elif crystal_system == "triclinic":
        pass  # No constraints to apply

    else:
        error_msg = f"Unknown or unsupported crystal system: {crystal_system}"
        print(error_msg)

    return cell


def apply_atom_site_symmetry_constraints(atom_site: dict,
                                         name_hm: str,
                                         coord_code,
                                         wyckoff_letter: str) -> dict:

    it_number = get_it_number_by_name_hm_short(name_hm)
    if it_number is None:
        error_msg = f"Failed to get IT_number for name_H-M '{name_hm}'"
        print(error_msg)
        return atom_site

    it_coordinate_system_code = coord_code
    if it_coordinate_system_code is None:
        error_msg = "IT_coordinate_system_code is not set"
        print(error_msg)
        return atom_site

    # 1 - OK
    # TODO: This is very slow!!!

    #result = get_symop_pcentr_multiplicity_letter_site_symmetry_coords_xyz_2(it_number, it_coordinate_system_code)
    # letter_list = result[3]
    # coords_xyz_list = result[5]

    # idx = letter_list.index(wyckoff_letter)
    # coords_xyz = coords_xyz_list[idx]
    #return atom_site
    # 2 - NOT OK

    space_group_entry = SPACE_GROUP_LOOKUP_DICT[(it_number, it_coordinate_system_code)]
    wyckoff_positions = space_group_entry["Wyckoff_positions"][wyckoff_letter]
    coords_xyz = wyckoff_positions["coords_xyz"]
    
    first_position = coords_xyz[0]
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
    x, y, z = symbols("x y z")
    symbols_xyz = (x, y, z)

    for i, axis in enumerate(axes):
        symbol = symbols_xyz[i]
        is_free = any(symbol in expr.free_symbols for expr in parsed_exprs)

        if not is_free:
            evaluated = parsed_exprs[i].subs(substitutions)
            simplified = simplify(evaluated)
            atom_site[f"fract_{axis}"] = float(simplified)

    return atom_site

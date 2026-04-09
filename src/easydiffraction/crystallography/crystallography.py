# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Any

from cryspy.A_functions_base.function_2_space_group import get_crystal_system_by_it_number
from cryspy.A_functions_base.function_2_space_group import get_it_number_by_name_hm_short
from sympy import Expr
from sympy import simplify
from sympy import symbols
from sympy import sympify

from easydiffraction.crystallography.space_groups import SPACE_GROUPS
from easydiffraction.utils.logging import log


def apply_cell_symmetry_constraints(
    cell: dict[str, float],
    name_hm: str,
) -> dict[str, float]:
    """
    Apply symmetry constraints to unit cell parameters.

    Parameters
    ----------
    cell : dict[str, float]
        Dictionary containing lattice parameters.
    name_hm : str
        Hermann-Mauguin symbol of the space group.

    Returns
    -------
    dict[str, float]
        The cell dictionary with applied symmetry constraints.
    """
    it_number = get_it_number_by_name_hm_short(name_hm)
    if it_number is None:
        error_msg = f"Failed to get IT_number for name_H-M '{name_hm}'"
        log.error(error_msg)  # TODO: ValueError? Diagnostics?
        return cell

    crystal_system = get_crystal_system_by_it_number(it_number)
    if crystal_system is None:
        error_msg = f"Failed to get crystal system for IT_number '{it_number}'"
        log.error(error_msg)  # TODO: ValueError? Diagnostics?
        return cell

    if crystal_system == 'cubic':
        a = cell['lattice_a']
        cell['lattice_b'] = a
        cell['lattice_c'] = a
        cell['angle_alpha'] = 90.0
        cell['angle_beta'] = 90.0
        cell['angle_gamma'] = 90.0

    elif crystal_system == 'tetragonal':
        a = cell['lattice_a']
        cell['lattice_b'] = a
        cell['angle_alpha'] = 90.0
        cell['angle_beta'] = 90.0
        cell['angle_gamma'] = 90.0

    elif crystal_system == 'orthorhombic':
        cell['angle_alpha'] = 90.0
        cell['angle_beta'] = 90.0
        cell['angle_gamma'] = 90.0

    elif crystal_system in {'hexagonal', 'trigonal'}:
        a = cell['lattice_a']
        cell['lattice_b'] = a
        cell['angle_alpha'] = 90.0
        cell['angle_beta'] = 90.0
        cell['angle_gamma'] = 120.0

    elif crystal_system == 'monoclinic':
        cell['angle_alpha'] = 90.0
        cell['angle_gamma'] = 90.0

    elif crystal_system == 'triclinic':
        pass  # No constraints to apply

    else:
        error_msg = f'Unknown or unsupported crystal system: {crystal_system}'
        log.error(error_msg)  # TODO: ValueError? Diagnostics?

    return cell


def _get_wyckoff_exprs(
    name_hm: str,
    coord_code: int,
    wyckoff_letter: str,
) -> list[Expr] | None:
    """
    Look up the first Wyckoff position and parse it into sympy Exprs.

    Parameters
    ----------
    name_hm : str
        Hermann-Mauguin symbol of the space group.
    coord_code : int
        Coordinate system code.
    wyckoff_letter : str
        Wyckoff position letter.

    Returns
    -------
    list[Expr] | None
        Three sympy expressions for x, y, z components, or ``None`` on
        failure.
    """
    it_number = get_it_number_by_name_hm_short(name_hm)
    if it_number is None:
        log.error(f"Failed to get IT_number for name_H-M '{name_hm}'")
        return None

    if coord_code is None:
        log.error('IT_coordinate_system_code is not set')
        return None

    entry = SPACE_GROUPS[it_number, coord_code]
    first_position = entry['Wyckoff_positions'][wyckoff_letter]['coords_xyz'][0]
    components = first_position.strip('()').split(',')
    return [sympify(comp.strip()) for comp in components]


def _apply_fract_constraints(
    atom_site: dict[str, Any],
    parsed_exprs: list[Expr],
) -> None:
    """
    Evaluate and apply fractional coordinate constraints in place.

    For each axis (x, y, z), if the coordinate is fully determined by
    symmetry (the symbol does not appear in any expression as a free
    symbol), substitutes the numeric values and overwrites the entry.

    Parameters
    ----------
    atom_site : dict[str, Any]
        Dictionary containing atom position data (mutated in place).
    parsed_exprs : list[Expr]
        Three sympy expressions from the Wyckoff position.
    """
    x, y, z = symbols('x y z')
    symbols_xyz = (x, y, z)
    axes = ('x', 'y', 'z')
    substitutions = {
        'x': sympify(atom_site['fract_x']),
        'y': sympify(atom_site['fract_y']),
        'z': sympify(atom_site['fract_z']),
    }

    for i, axis in enumerate(axes):
        is_free = any(symbols_xyz[i] in expr.free_symbols for expr in parsed_exprs)
        if not is_free:
            evaluated = simplify(parsed_exprs[i].subs(substitutions))
            atom_site[f'fract_{axis}'] = float(evaluated)


def apply_atom_site_symmetry_constraints(
    atom_site: dict[str, Any],
    name_hm: str,
    coord_code: int,
    wyckoff_letter: str,
) -> dict[str, Any]:
    """
    Apply symmetry constraints to atom site coordinates.

    Parameters
    ----------
    atom_site : dict[str, Any]
        Dictionary containing atom position data.
    name_hm : str
        Hermann-Mauguin symbol of the space group.
    coord_code : int
        Coordinate system code.
    wyckoff_letter : str
        Wyckoff position letter.

    Returns
    -------
    dict[str, Any]
        The atom_site dictionary with applied symmetry constraints.
    """
    parsed_exprs = _get_wyckoff_exprs(name_hm, coord_code, wyckoff_letter)
    if parsed_exprs is None:
        return atom_site

    _apply_fract_constraints(atom_site, parsed_exprs)
    return atom_site

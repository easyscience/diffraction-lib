# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from fractions import Fraction
from typing import Any

import numpy as np
from cryspy.A_functions_base.function_1_atomic_vibrations import vibration_constraints
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
    crystal_system = _crystal_system_from_name_hm(name_hm)
    if crystal_system is None:
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


_CELL_KEYS = (
    'lattice_a',
    'lattice_b',
    'lattice_c',
    'angle_alpha',
    'angle_beta',
    'angle_gamma',
)


def _crystal_system_from_name_hm(name_hm: str) -> str | None:
    """
    Resolve a crystal system from a Hermann-Mauguin symbol.

    Returns ``None`` and logs the error when the lookup fails.

    Parameters
    ----------
    name_hm : str
        Hermann-Mauguin symbol of the space group.

    Returns
    -------
    str | None
        Crystal system name (e.g. ``'cubic'``) or ``None`` on failure.
    """
    it_number = get_it_number_by_name_hm_short(name_hm)
    if it_number is None:
        log.error(f"Failed to get IT_number for name_H-M '{name_hm}'")
        return None
    crystal_system = get_crystal_system_by_it_number(it_number)
    if crystal_system is None:
        log.error(f"Failed to get crystal system for IT_number '{it_number}'")
        return None
    return crystal_system


_CELL_FIXED_AXES_BY_SYSTEM: dict[str, set[str]] = {
    'cubic': {'lattice_b', 'lattice_c', 'angle_alpha', 'angle_beta', 'angle_gamma'},
    'tetragonal': {'lattice_b', 'angle_alpha', 'angle_beta', 'angle_gamma'},
    'orthorhombic': {'angle_alpha', 'angle_beta', 'angle_gamma'},
    'hexagonal': {'lattice_b', 'angle_alpha', 'angle_beta', 'angle_gamma'},
    'trigonal': {'lattice_b', 'angle_alpha', 'angle_beta', 'angle_gamma'},
    'monoclinic': {'angle_alpha', 'angle_gamma'},
    'triclinic': set(),
}


def _cell_fixed_axes(crystal_system: str) -> set[str]:
    """
    Return cell keys that are dependent on others for a crystal system.

    Independent (free) parameters are excluded; dependent / constant
    parameters (e.g. ``lattice_b = lattice_a`` in cubic, or angles fixed
    to 90/120 degrees) are returned.

    Parameters
    ----------
    crystal_system : str
        Crystal system name.

    Returns
    -------
    set[str]
        Subset of cell keys that are fixed by symmetry.
    """
    return _CELL_FIXED_AXES_BY_SYSTEM.get(crystal_system, set())


def cell_symmetry_fixed_flags(name_hm: str) -> dict[str, bool]:
    """
    Return per-key flags indicating which cell parameters are fixed.

    Parameters
    ----------
    name_hm : str
        Hermann-Mauguin symbol of the space group.

    Returns
    -------
    dict[str, bool]
        Mapping of cell key to ``True`` when the parameter is fixed by
        symmetry (dependent on another parameter or set to a fixed
        angle), ``False`` when it is independent. Returns all keys
        ``False`` when the space group cannot be resolved.
    """
    crystal_system = _crystal_system_from_name_hm(name_hm)
    if crystal_system is None:
        return dict.fromkeys(_CELL_KEYS, False)
    fixed = _cell_fixed_axes(crystal_system)
    return {key: key in fixed for key in _CELL_KEYS}


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

    if (it_number, coord_code) not in SPACE_GROUPS:
        # Space group is not in the local SPACE_GROUPS table (e.g. P 1,
        # where cryspy reports no coordinate-system codes). Treat as
        # "no symmetry constraints to apply".
        return None

    entry = SPACE_GROUPS[it_number, coord_code]
    first_position = entry['Wyckoff_positions'][wyckoff_letter]['coords_xyz'][0]
    components = first_position.strip('()').split(',')
    return [sympify(comp.strip()) for comp in components]


def _fract_fixed_flags(parsed_exprs: list[Expr]) -> dict[str, bool]:
    """
    Return per-axis flags marking coordinates fixed by site symmetry.

    For each axis (x, y, z), the coordinate is considered fixed when the
    corresponding symbol does not appear as a free symbol in any of the
    Wyckoff position expressions.

    Parameters
    ----------
    parsed_exprs : list[Expr]
        Three sympy expressions from the Wyckoff position.

    Returns
    -------
    dict[str, bool]
        Mapping ``'fract_x' / 'fract_y' / 'fract_z'`` to ``True`` if
        that axis is fixed by symmetry.
    """
    x, y, z = symbols('x y z')
    symbols_xyz = (x, y, z)
    axes = ('x', 'y', 'z')
    flags: dict[str, bool] = {}
    for i, axis in enumerate(axes):
        is_free = any(symbols_xyz[i] in expr.free_symbols for expr in parsed_exprs)
        flags[f'fract_{axis}'] = not is_free
    return flags


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
    axes = ('x', 'y', 'z')
    substitutions = {
        'x': sympify(atom_site['fract_x']),
        'y': sympify(atom_site['fract_y']),
        'z': sympify(atom_site['fract_z']),
    }
    fixed_flags = _fract_fixed_flags(parsed_exprs)

    for i, axis in enumerate(axes):
        if fixed_flags[f'fract_{axis}']:
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


def atom_site_symmetry_fixed_flags(
    name_hm: str,
    coord_code: int,
    wyckoff_letter: str,
) -> dict[str, bool]:
    """
    Return per-axis flags marking coordinates fixed by site symmetry.

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
    dict[str, bool]
        Mapping ``'fract_x' / 'fract_y' / 'fract_z'`` to ``True`` if the
        axis is fully determined by site symmetry. Returns all ``False``
        when the Wyckoff position cannot be resolved.
    """
    parsed_exprs = _get_wyckoff_exprs(name_hm, coord_code, wyckoff_letter)
    if parsed_exprs is None:
        return {'fract_x': False, 'fract_y': False, 'fract_z': False}
    return _fract_fixed_flags(parsed_exprs)


# ------------------------------------------------------------------
#  ADP symmetry constraints
# ------------------------------------------------------------------


def _parse_rotation_matrix(expr_str: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Extract rotation and translation from a coordinate expression.

    Parses a symmetry-equivalent position string such as ``'(-x+1/2, y,
    -z+1/2)'`` into a 3x3 rotation matrix and a translation vector.

    Parameters
    ----------
    expr_str : str
        A single symmetry-equivalent position, e.g. ``'(x,y,z)'``.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        rotation : (3, 3) integer array. translation : (3,) float array
        (fractional).
    """
    inner = expr_str.strip().strip('()')
    parts = [p.strip() for p in inner.split(',')]

    rot = np.zeros((3, 3), dtype=int)
    trans = np.zeros(3)

    var_map = {'x': 0, 'y': 1, 'z': 2}
    for row, part in enumerate(parts):
        # Replace subtraction by addition of negative terms
        normalized = part.replace('-', '+-')
        tokens = [t for t in normalized.split('+') if t]
        for token in tokens:
            matched = False
            for var, col in var_map.items():
                if var in token:
                    coeff_str = token.replace(var, '').strip()
                    if coeff_str in {'', '+'}:
                        coeff = 1
                    elif coeff_str == '-':
                        coeff = -1
                    else:
                        coeff = int(coeff_str)
                    rot[row, col] = coeff
                    matched = True
                    break
            if not matched:
                trans[row] = float(Fraction(token))

    return rot, trans


def _get_general_position_ops(
    it_number: int,
    coord_code: str | None,
) -> list[tuple[np.ndarray, np.ndarray]] | None:
    """
    Return rotation matrices and translations for the general position.

    Parameters
    ----------
    it_number : int
        International Tables space group number.
    coord_code : str | None
        IT coordinate system code.

    Returns
    -------
    list[tuple[np.ndarray, np.ndarray]] | None
        List of (rotation, translation) pairs, or ``None`` on failure.
    """
    key = (it_number, coord_code)
    if key not in SPACE_GROUPS:
        log.error(f'Space group ({it_number}, {coord_code!r}) not found')
        return None

    entry = SPACE_GROUPS[key]
    wyckoff_positions = entry['Wyckoff_positions']
    # General position is the first key (highest multiplicity)
    general_letter = next(iter(wyckoff_positions))
    general_coords = wyckoff_positions[general_letter]['coords_xyz']
    return [_parse_rotation_matrix(c) for c in general_coords]


def _site_stabilizer_rotations(
    ops: list[tuple[np.ndarray, np.ndarray]],
    site_coords: tuple[float, float, float],
) -> list[np.ndarray]:
    """
    Return rotation matrices of operations that leave a site invariant.

    An operation (R, t) stabilises a site r when R·r + t ≡ r (mod 1).

    Parameters
    ----------
    ops : list[tuple[np.ndarray, np.ndarray]]
        All space group operations as (rotation, translation) pairs.
    site_coords : tuple[float, float, float]
        Fractional coordinates of the site.

    Returns
    -------
    list[np.ndarray]
        Rotation matrices of stabiliser operations.
    """
    r = np.array(site_coords, dtype=float)
    stabiliser = []
    for rot, trans in ops:
        image = rot @ r + trans
        diff = image - r
        diff_mod = diff - np.round(diff)
        if np.allclose(diff_mod, 0.0, atol=1e-6):
            stabiliser.append(rot)
    return stabiliser


def _calc_adp_constraint_number(stabiliser: list[np.ndarray]) -> int:
    """
    Derive ADP constraint type via the Peterse-Palm probe technique.

    A set of coprime probe values is transformed by each site-stabiliser
    rotation (Acta Cryst. 1966, 20, 147).  The algebraic relationships
    among the summed transformed components uniquely identify one of 19
    constraint types (0 = no constraint, 1-18 as defined in cryspy's
    ``vibration_constraints``).

    Parameters
    ----------
    stabiliser : list[np.ndarray]
        Rotation matrices of the site-stabiliser group.

    Returns
    -------
    int
        Constraint type number (0-18).
    """
    # Peterse-Palm probe values (coprime, pairwise distinct)
    b_vals = np.array([107, 181, 41, 7, 19, 1], dtype=float)
    b_matrix = np.array([
        [b_vals[0], b_vals[3], b_vals[4]],
        [b_vals[3], b_vals[1], b_vals[5]],
        [b_vals[4], b_vals[5], b_vals[2]],
    ])

    accumulated = np.zeros((3, 3))
    for rot in stabiliser:
        accumulated += rot @ b_matrix @ rot.T

    r_11 = round(accumulated[0, 0])
    r_22 = round(accumulated[1, 1])
    r_33 = round(accumulated[2, 2])
    r_12 = round(accumulated[0, 1])
    r_13 = round(accumulated[0, 2])
    r_23 = round(accumulated[1, 2])

    return _classify_constraint(r_11, r_22, r_33, r_12, r_13, r_23)


def _classify_constraint(
    r_11: int,
    r_22: int,
    r_33: int,
    r_12: int,
    r_13: int,
    r_23: int,
) -> int:
    """
    Map Peterse-Palm probe sums to a constraint type number.

    Rule table follows cryspy (Peterse & Palm, Acta Cryst. 1966).

    Parameters
    ----------
    r_11 : int
        Accumulated probe-tensor component (1,1).
    r_22 : int
        Accumulated probe-tensor component (2,2).
    r_33 : int
        Accumulated probe-tensor component (3,3).
    r_12 : int
        Accumulated probe-tensor component (1,2).
    r_13 : int
        Accumulated probe-tensor component (1,3).
    r_23 : int
        Accumulated probe-tensor component (2,3).

    Returns
    -------
    int
        Constraint type (0-18).
    """
    z13 = r_13 == 0
    z23 = r_23 == 0
    z12 = r_12 == 0
    eq_11_22 = r_11 == r_22
    eq_22_33 = r_22 == r_33
    eq_22_2x12 = r_22 == 2 * r_12
    eq_23_13 = r_23 == r_13
    eq_12_13 = r_12 == r_13
    neg_23_13 = r_23 == -r_13

    # Ordered from most specific to least; first match wins.
    rules = [
        (z13 and z23 and z12 and eq_11_22 and eq_22_33, 17),
        (z13 and z23 and z12 and eq_11_22, 8),
        (z13 and z23 and z12 and eq_22_33, 12),
        (z13 and z23 and z12, 4),
        (z13 and z23 and eq_11_22 and eq_22_2x12, 16),
        (z13 and z23 and eq_11_22, 5),
        (z13 and z23 and eq_22_2x12, 14),
        (z13 and z23, 2),
        (z13 and eq_22_33, 9),
        (z13, 3),
        (z23 and eq_22_2x12, 13),
        (z23, 1),
        (eq_23_13 and eq_22_33, 18),
        (eq_23_13, 6),
        (eq_12_13, 10),
        (neg_23_13, 7),
        (eq_22_33, 11),
        (eq_22_2x12, 15),
    ]
    for condition, result in rules:
        if condition:
            return result
    return 0


def apply_atom_site_aniso_symmetry_constraints(
    atom_site_aniso: dict[str, float],
    name_hm: str,
    coord_code: str | None,
    _wyckoff_letter: str,
    site_fract: tuple[float, float, float],
) -> tuple[dict[str, float], tuple[bool, ...]]:
    """
    Apply symmetry constraints to anisotropic ADP tensor components.

    Uses the Peterse-Palm probe technique to determine which tensor
    components are constrained by the site symmetry, then delegates to
    cryspy's ``vibration_constraints`` to enforce them.

    Parameters
    ----------
    atom_site_aniso : dict[str, float]
        Dictionary with keys ``'adp_11'`` … ``'adp_23'``.  Modified in
        place.
    name_hm : str
        Hermann-Mauguin symbol of the space group.
    coord_code : str | None
        IT coordinate system code.
    _wyckoff_letter : str
        Wyckoff position letter (unused, reserved).
    site_fract : tuple[float, float, float]
        Fractional coordinates of the atom site.

    Returns
    -------
    tuple[dict[str, float], tuple[bool, ...]]
        The *atom_site_aniso* dictionary with constrained values, and a
        6-tuple of booleans indicating which components remain free for
        refinement (``True`` = free, ``False`` = fixed by symmetry).
    """
    all_free = (True, True, True, True, True, True)

    it_number = get_it_number_by_name_hm_short(name_hm)
    if it_number is None:
        log.error(f"Failed to get IT_number for name_H-M '{name_hm}'")
        return atom_site_aniso, all_free

    ops = _get_general_position_ops(it_number, coord_code)
    if ops is None:
        return atom_site_aniso, all_free

    stabiliser = _site_stabilizer_rotations(ops, site_fract)
    if len(stabiliser) <= 1:
        # Identity only — no ADP constraints
        return atom_site_aniso, all_free

    numb = _calc_adp_constraint_number(stabiliser)
    if numb == 0:
        return atom_site_aniso, all_free

    param_i = (
        atom_site_aniso['adp_11'],
        atom_site_aniso['adp_22'],
        atom_site_aniso['adp_33'],
        atom_site_aniso['adp_12'],
        atom_site_aniso['adp_13'],
        atom_site_aniso['adp_23'],
    )
    sigma_i = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ref_i = (True, True, True, True, True, True)

    param_i, _sigma_i, ref_i, _constr_i = vibration_constraints(
        numb,
        param_i,
        sigma_i,
        ref_i,
    )

    keys = ('adp_11', 'adp_22', 'adp_33', 'adp_12', 'adp_13', 'adp_23')
    atom_site_aniso.update(dict(zip(keys, param_i, strict=False)))

    return atom_site_aniso, ref_i

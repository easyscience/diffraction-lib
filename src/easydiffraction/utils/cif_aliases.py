# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Callable
from typing import Optional

if TYPE_CHECKING:  # pragma: no cover - type checking only
    import gemmi

from easydiffraction.utils.formatting import warning

# Canonical key -> ordered list of CIF tag aliases
# Order matters: the first tag found is used.
ALIASES: dict[str, list[str]] = {
    # Space group
    'space_group_name_hm': [
        '_space_group.name_H-M_alt',
        '_symmetry.space_group_name_H-M',
    ],
    # Dotted canonical key using component category + ED attribute name
    'space_group.name_h_m': [
        '_space_group.name_H-M_alt',
        '_symmetry.space_group_name_H-M',
    ],
    'space_group_it_code': [
        '_space_group.IT_coordinate_system_code',
        '_symmetry.IT_coordinate_system_code',
    ],
    'space_group.it_coordinate_system_code': [
        '_space_group.IT_coordinate_system_code',
        '_symmetry.IT_coordinate_system_code',
    ],
    # Unit cell
    'cell_length_a': ['_cell.length_a'],
    'cell_length_b': ['_cell.length_b'],
    'cell_length_c': ['_cell.length_c'],
    'cell_angle_alpha': ['_cell.angle_alpha'],
    'cell_angle_beta': ['_cell.angle_beta'],
    'cell_angle_gamma': ['_cell.angle_gamma'],
    'cell.length_a': ['_cell.length_a'],
    'cell.length_b': ['_cell.length_b'],
    'cell.length_c': ['_cell.length_c'],
    'cell.angle_alpha': ['_cell.angle_alpha'],
    'cell.angle_beta': ['_cell.angle_beta'],
    'cell.angle_gamma': ['_cell.angle_gamma'],
    # Atom sites
    'atom_site_label': ['_atom_site.label'],
    'atom_site_type_symbol': ['_atom_site.type_symbol'],
    'atom_site_fract_x': ['_atom_site.fract_x'],
    'atom_site_fract_y': ['_atom_site.fract_y'],
    'atom_site_fract_z': ['_atom_site.fract_z'],
    'atom_site_occupancy': ['_atom_site.occupancy'],
    'atom_site_b_iso': ['_atom_site.B_iso_or_equiv'],
    'atom_site_u_iso': ['_atom_site.U_iso_or_equiv'],
    'atom_site_wyckoff': [
        '_atom_site.Wyckoff_letter',
        '_atom_site.Wyckoff_symbol',
        '_atom_site.wyckoff_symbol',
    ],
    # Dotted canonical for atom_site as well
    'atom_site.label': ['_atom_site.label'],
    'atom_site.type_symbol': ['_atom_site.type_symbol'],
    'atom_site.fract_x': ['_atom_site.fract_x'],
    'atom_site.fract_y': ['_atom_site.fract_y'],
    'atom_site.fract_z': ['_atom_site.fract_z'],
    'atom_site.occupancy': ['_atom_site.occupancy'],
    'atom_site.B_iso_or_equiv': ['_atom_site.B_iso_or_equiv'],
    'atom_site.U_iso_or_equiv': ['_atom_site.U_iso_or_equiv'],
    'atom_site.wyckoff_symbol': [
        '_atom_site.Wyckoff_letter',
        '_atom_site.Wyckoff_symbol',
        '_atom_site.wyckoff_symbol',
    ],
}

# Pretty labels for specific component.attribute pairs for
# user-facing warnings
_PRETTY_ATTR_LABELS: dict[tuple[str, str], str] = {
    ('space_group', 'name_h_m'): 'Hermann–Mauguin',
}


def cif_get_value(
    block: 'gemmi.cif.Block',
    key: str,
    default: Optional[str] = None,
    normalize: Optional[Callable[[str], str]] = None,
) -> Optional[str]:
    """Return the first value found among aliases for a canonical
    key.
    """
    for tag in ALIASES.get(key, []):
        try:
            value = block.find_value(tag)
        except Exception:
            value = None
        if value:
            return normalize(value) if normalize else value
    return default


def cif_get_values(
    block: 'gemmi.cif.Block',
    key: str,
    normalize: Optional[Callable[[str], str]] = None,
) -> list[str]:
    """Return the first non-empty list of values among aliases."""
    for tag in ALIASES.get(key, []):
        try:
            values = list(block.find_values(tag) or [])
        except Exception:
            values = []
        if values:
            return [normalize(v) for v in values] if normalize else values
    return []


# Normalizers


def strip_quotes(s: str) -> str:
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def normalize_wyckoff(s: str) -> str:
    s = s.strip().strip('?')
    if len(s) > 1 and s[-1].isalpha():
        return s[-1]
    return s


# Component-aware helpers


def _default_cif_tag_for(component: object, attr_name: str) -> Optional[str]:
    """Return the first explicit full CIF tag declared on the
    descriptor, if any.
    """
    descriptor = getattr(component, '__dict__', {}).get(attr_name)
    full_aliases = getattr(descriptor, 'full_cif_names', None)
    if full_aliases:
        return full_aliases[0]
    return None


def _gather_alias_tags(component: object, attr_name: str, default_tag: Optional[str]) -> list[str]:
    """Collect ordered alias tags for a component attribute."""
    tags: list[str] = []
    if default_tag:
        tags.append(default_tag)
    # Include all explicit per-descriptor aliases if defined
    descriptor = getattr(component, '__dict__', {}).get(attr_name)
    full_aliases = getattr(descriptor, 'full_cif_names', None)
    if full_aliases:
        tags.extend(full_aliases)
    # Dotted canonical
    category = getattr(component, 'category_key', None)
    dotted_key = f'{category}.{attr_name}' if category else None
    if dotted_key:
        tags.extend(ALIASES.get(dotted_key, []))
    # Legacy underscored
    # Legacy underscore key (deprecated forms) based on dotted key
    legacy_key = (dotted_key or '').replace('.', '_')
    if legacy_key:
        tags.extend(ALIASES.get(legacy_key, []))

    # Deduplicate preserving order
    seen = set()
    uniq: list[str] = []
    for t in tags:
        if t not in seen and t:
            seen.add(t)
            uniq.append(t)
    return uniq


def cif_get_value_for(
    block: 'gemmi.cif.Block',
    component: object,
    attr_name: str,
    normalize: Optional[Callable[[str], str]] = None,
) -> Optional[str]:
    """Resolve a value using the component's CIF tag and aliases.

    Falls back to the attribute's ``default_value`` when present. If
    neither a CIF value nor a ``default_value`` is available, raises a
    ``KeyError``.
    """
    default_tag = _default_cif_tag_for(component, attr_name)
    tags = _gather_alias_tags(component, attr_name, default_tag)
    for tag in tags:
        try:
            value = block.find_value(tag)
        except Exception:
            value = None
        if value:
            return normalize(value) if normalize else value
    # Fall back to the attribute's default_value
    descriptor = getattr(component, '__dict__', {}).get(attr_name)
    dv = getattr(descriptor, 'default_value', None)
    if dv is not None:
        s = str(dv)
        # Build a user-friendly warning message
        comp_key = getattr(component, 'category_key', 'component')
        comp_label = str(comp_key).replace('_', ' ').capitalize()
        attr_label = _PRETTY_ATTR_LABELS.get((comp_key, attr_name)) or str(attr_name).replace(
            '_', ' '
        )
        print(warning(f"{comp_label} {attr_label} not found in CIF; using default '{s}'."))
        return normalize(s) if (normalize and isinstance(s, str)) else s
    # Nothing found and no default available: error
    comp_name = getattr(component, 'category_key', 'component')
    raise KeyError(
        f"No CIF value found for '{comp_name}.{attr_name}' and no default_value is defined."
    )


def cif_get_values_for(
    block: 'gemmi.cif.Block',
    component: object,
    attr_name: str,
    normalize: Optional[Callable[[str], str]] = None,
) -> list[str]:
    """Resolve a list of values using the component's CIF tag and
    aliases.
    """
    default_tag = _default_cif_tag_for(component, attr_name)
    tags = _gather_alias_tags(component, attr_name, default_tag)
    for tag in tags:
        try:
            values = list(block.find_values(tag) or [])
        except Exception:
            values = []
        if values:
            return [normalize(v) for v in values] if normalize else values
    return []

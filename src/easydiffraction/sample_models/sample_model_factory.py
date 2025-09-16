# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet
from typing import Optional
from typing import Set
from typing import Tuple

import gemmi

from easydiffraction.sample_models.sample_model import BaseSampleModel


@dataclass(frozen=True)
class _ArgSpec:
    keys: FrozenSet[str]


class SampleModelFactory:
    """Factory for creating `BaseSampleModel` instances with validated
    arguments.

    Valid argument combinations are mutually exclusive:
    - name (minimal model with defaults)
    - cif_path (CIF file path; name must not be provided)
    - cif_str (CIF content as string; name must not be provided)

    Any other combination is considered invalid.
    """

    _valid_arg_sets: Tuple[_ArgSpec, ...] = (
        _ArgSpec(frozenset({'name'})),
        _ArgSpec(frozenset({'cif_path'})),
        _ArgSpec(frozenset({'cif_str'})),
    )

    @classmethod
    def _present_keys(
        cls,
        *,
        name: Optional[str] = None,
        cif_path: Optional[str] = None,
        cif_str: Optional[str] = None,
    ) -> Set[str]:
        present = {
            k
            for k, v in {'name': name, 'cif_path': cif_path, 'cif_str': cif_str}.items()
            if v is not None
        }
        return present

    @classmethod
    def _validate_args(
        cls,
        *,
        name: Optional[str] = None,
        cif_path: Optional[str] = None,
        cif_str: Optional[str] = None,
    ) -> None:
        present = frozenset(cls._present_keys(name=name, cif_path=cif_path, cif_str=cif_str))
        valid = {spec.keys for spec in cls._valid_arg_sets}
        if present not in valid:
            # Build helpful error message
            combos = ['(' + ', '.join(sorted(spec.keys)) + ')' for spec in cls._valid_arg_sets]
            allowed = ', '.join(combos)
            raise ValueError(
                'Invalid argument combination for SampleModel creation. '
                f'Provided={sorted(present)}. Allowed combinations: {allowed}. '
                "Note: Do not pass 'name' together with 'cif_path' or 'cif_str' "
                'since CIF contains the model name.'
            )

    @classmethod
    def create(
        cls,
        *,
        name: Optional[str] = None,
        cif_path: Optional[str] = None,
        cif_str: Optional[str] = None,
    ) -> BaseSampleModel:
        """Create a `BaseSampleModel` using a validated argument
        combination.

        Args:
            name: Model identifier for a minimal model (no atoms by
                default).
            cif_path: Path to a CIF file used to build the model.
            cif_str: CIF content used to build the model.

        Returns:
            A constructed `BaseSampleModel` instance.

        Raises:
            ValueError: If the argument combination is invalid.
        """
        cls._validate_args(name=name, cif_path=cif_path, cif_str=cif_str)
        if name is not None:
            return BaseSampleModel(name=name)
        if cif_path is not None:
            return cls._create_from_cif_path(cif_path)
        if cif_str is not None:
            return cls._create_from_cif_str(cif_str)
        # Defensive: Should be unreachable due to validation above
        raise ValueError('No valid arguments provided to create SampleModel.')

    # -------------------------------
    # Private creation helper methods
    # -------------------------------

    @classmethod
    def _create_from_cif_path(cls, cif_path: str) -> BaseSampleModel:
        # Parse CIF and build model
        doc = cls._read_cif_document_from_path(cif_path)
        block = cls._pick_first_structural_block(doc)
        return cls._create_model_from_block(block)

    @classmethod
    def _create_from_cif_str(cls, cif_str: str) -> BaseSampleModel:
        # Parse CIF string and build model
        doc = cls._read_cif_document_from_string(cif_str)
        block = cls._pick_first_structural_block(doc)
        return cls._create_model_from_block(block)

    # -------------
    # gemmi helpers
    # -------------

    @staticmethod
    def _read_cif_document_from_path(path: str) -> gemmi.cif.Document:
        # Prefer official API if available
        if hasattr(gemmi.cif, 'read_file'):
            return gemmi.cif.read_file(path)
        # Fallback: read as text and parse string
        text = Path(path).read_text(encoding='utf-8', errors='ignore')
        return gemmi.cif.read_string(text)

    @staticmethod
    def _read_cif_document_from_string(text: str) -> gemmi.cif.Document:
        if hasattr(gemmi.cif, 'read_string'):
            return gemmi.cif.read_string(text)
        # Fallback: return empty document if API is unavailable
        return gemmi.cif.Document()

    @staticmethod
    def _has_structural_content(block: gemmi.cif.Block) -> bool:
        # Basic heuristics: atom_site loop or full set of cell params
        loop = block.find_loop('_atom_site.fract_x')
        if loop is not None:
            return True
        required_cell = [
            '_cell.length_a',
            '_cell.length_b',
            '_cell.length_c',
            '_cell.angle_alpha',
            '_cell.angle_beta',
            '_cell.angle_gamma',
        ]
        return all(block.find_value(tag) for tag in required_cell)

    @classmethod
    def _pick_first_structural_block(cls, doc: gemmi.cif.Document) -> gemmi.cif.Block:
        # Prefer blocks with atom_site loop; else first block with cell
        for block in doc:
            if cls._has_structural_content(block):
                return block
        # As a fallback, return the sole or first block
        if hasattr(doc, 'sole_block'):
            return doc.sole_block()
        # Indexing works in gemmi: doc[0]
        return doc[0]

    @classmethod
    def _create_model_from_block(cls, block: gemmi.cif.Block) -> BaseSampleModel:
        name = cls._extract_name_from_block(block)
        model = BaseSampleModel(name=name)
        cls._apply_space_group_from_block(model, block)
        cls._apply_cell_from_block(model, block)
        cls._apply_atom_sites_from_block(model, block)
        return model

    @staticmethod
    def _as_float(val: str | None) -> float | None:
        if not val:
            return None
        try:
            return float(val)
        except Exception:
            try:
                return float(val.split('(')[0])
            except Exception:
                return None

    @classmethod
    def _extract_name_from_block(cls, block: gemmi.cif.Block) -> str:
        return getattr(block, 'name', None) or 'model'

    @classmethod
    def _apply_space_group_from_block(cls, model: BaseSampleModel, block: gemmi.cif.Block) -> None:
        sg_hm = (
            block.find_value('_space_group.name_H-M_alt')
            or block.find_value('_symmetry.space_group_name_H-M')
            or None
        )
        if not sg_hm:
            try:
                if hasattr(gemmi, 'make_small_structure_from_block'):
                    ss = gemmi.make_small_structure_from_block(block)
                    sg = (
                        getattr(ss, 'spacegroup', None)
                        or getattr(ss, 'get_spacegroup', lambda: None)()
                    )
                    sg_hm = getattr(sg, 'hm', None)
            except Exception:
                sg_hm = None
        if sg_hm:
            if (sg_hm.startswith('"') and sg_hm.endswith('"')) or (
                sg_hm.startswith("'") and sg_hm.endswith("'")
            ):
                sg_hm = sg_hm[1:-1]
            model.space_group.name_h_m = sg_hm

        it_code = (
            block.find_value('_space_group.IT_coordinate_system_code')
            or block.find_value('_symmetry.IT_coordinate_system_code')
            or None
        )
        if it_code:
            try:
                model.space_group.it_coordinate_system_code = int(it_code)
            except Exception:
                model.space_group.it_coordinate_system_code = it_code

    @classmethod
    def _apply_cell_from_block(cls, model: BaseSampleModel, block: gemmi.cif.Block) -> None:
        a = cls._as_float(block.find_value('_cell.length_a'))
        b = cls._as_float(block.find_value('_cell.length_b'))
        c = cls._as_float(block.find_value('_cell.length_c'))
        alpha = cls._as_float(block.find_value('_cell.angle_alpha'))
        beta = cls._as_float(block.find_value('_cell.angle_beta'))
        gamma = cls._as_float(block.find_value('_cell.angle_gamma'))

        if a is not None:
            model.cell.length_a = a
        if b is not None:
            model.cell.length_b = b
        if c is not None:
            model.cell.length_c = c
        if alpha is not None:
            model.cell.angle_alpha = alpha
        if beta is not None:
            model.cell.angle_beta = beta
        if gamma is not None:
            model.cell.angle_gamma = gamma

    @classmethod
    def _apply_atom_sites_from_block(cls, model: BaseSampleModel, block: gemmi.cif.Block) -> None:
        labels = list(block.find_values('_atom_site.label') or [])
        types = list(block.find_values('_atom_site.type_symbol') or [])
        xs = list(block.find_values('_atom_site.fract_x') or [])
        ys = list(block.find_values('_atom_site.fract_y') or [])
        zs = list(block.find_values('_atom_site.fract_z') or [])
        occs = list(block.find_values('_atom_site.occupancy') or [])
        bisos = list(block.find_values('_atom_site.B_iso_or_equiv') or [])
        uisos = list(block.find_values('_atom_site.U_iso_or_equiv') or [])
        wycks = (
            list(block.find_values('_atom_site.Wyckoff_letter') or [])
            or list(block.find_values('_atom_site.Wyckoff_symbol') or [])
            or list(block.find_values('_atom_site.wyckoff_symbol') or [])
        )

        if not any([labels, types, xs, ys, zs, occs, bisos, uisos, wycks]):
            return

        n = max([
            len(labels),
            len(types),
            len(xs),
            len(ys),
            len(zs),
            len(occs),
            len(bisos),
            len(uisos),
            len(wycks),
        ])

        for i in range(n):
            label = (
                (labels[i] if i < len(labels) and labels[i] else None)
                or (types[i] if i < len(types) and types[i] else None)
                or f'X{i + 1}'
            )
            type_symbol = (types[i] if i < len(types) and types[i] else None) or label
            fx = cls._as_float(xs[i]) if i < len(xs) else None
            fy = cls._as_float(ys[i]) if i < len(ys) else None
            fz = cls._as_float(zs[i]) if i < len(zs) else None
            occ = cls._as_float(occs[i]) if i < len(occs) else None
            b_iso = cls._as_float(bisos[i]) if i < len(bisos) else None
            if b_iso is None:
                u_iso = cls._as_float(uisos[i]) if i < len(uisos) else None
                if u_iso is not None:
                    b_iso = 8.0 * math.pi * math.pi * u_iso
            fx = 0.0 if fx is None else fx
            fy = 0.0 if fy is None else fy
            fz = 0.0 if fz is None else fz
            occ = 1.0 if occ is None else occ
            b_iso = 0.0 if b_iso is None else b_iso

            wyck = wycks[i] if i < len(wycks) else None
            if wyck:
                wyck = wyck.strip().strip('?')
                if len(wyck) > 1 and wyck[-1].isalpha():
                    wyck = wyck[-1]

            model.atom_sites.add(
                label=label,
                type_symbol=type_symbol,
                fract_x=fx,
                fract_y=fy,
                fract_z=fz,
                wyckoff_letter=wyck,
                b_iso=b_iso,
                occupancy=occ,
            )

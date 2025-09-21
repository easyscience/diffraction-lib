# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import math
from typing import Optional

import gemmi

from easydiffraction.sample_models.sample_model import BaseSampleModel
from easydiffraction.utils.cif_aliases import cif_get_values
from easydiffraction.utils.cif_aliases import normalize_wyckoff


class SampleModelFactory:
    """Factory for creating `BaseSampleModel` instances with validated
    arguments.

    Valid argument combinations are mutually exclusive:
    - name (minimal model with defaults)
    - cif_path (CIF file path; name must not be provided)
    - cif_str (CIF content as string; name must not be provided)

    Any other combination is considered invalid.
    """

    VALID_ARG_SETS = (
        frozenset({'name'}),
        frozenset({'cif_path'}),
        frozenset({'cif_str'}),
    )

    @classmethod
    def _validate_args(
        cls,
        *,
        name: Optional[str] = None,
        cif_path: Optional[str] = None,
        cif_str: Optional[str] = None,
    ) -> None:
        present = frozenset(
            k
            for k, v in {'name': name, 'cif_path': cif_path, 'cif_str': cif_str}.items()
            if v is not None
        )
        if present not in cls.VALID_ARG_SETS:
            # Build helpful error message
            combos = ['(' + ', '.join(sorted(spec)) + ')' for spec in cls.VALID_ARG_SETS]
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
        return gemmi.cif.read_file(path)

    @staticmethod
    def _read_cif_document_from_string(text: str) -> gemmi.cif.Document:
        return gemmi.cif.read_string(text)

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
        try:
            return doc.sole_block()
        except Exception:
            return doc[0]

    @classmethod
    def _create_model_from_block(cls, block: gemmi.cif.Block) -> BaseSampleModel:
        name = cls._extract_name_from_block(block)
        model = BaseSampleModel(name=name)
        cls._set_space_group_from_cif_block(model, block)
        cls._set_cell_from_cif_block(model, block)
        cls._set_atom_sites_from_cif_block(model, block)
        return model

    @classmethod
    def _extract_name_from_block(cls, block: gemmi.cif.Block) -> str:
        return block.name or 'model'

    @classmethod
    def _set_space_group_from_cif_block(
        cls,
        model: BaseSampleModel,
        block: gemmi.cif.Block,
    ) -> None:
        model.space_group.from_cif(block)

    @classmethod
    def _set_cell_from_cif_block(
        cls,
        model: BaseSampleModel,
        block: gemmi.cif.Block,
    ) -> None:
        model.cell.from_cif(block)

    @classmethod
    def _set_atom_sites_from_cif_block(
        cls,
        model: BaseSampleModel,
        block: gemmi.cif.Block,
    ) -> None:
        model.atom_sites.from_cif(block)

        return
        labels = list(block.find_loop('_atom_site.label'))

        loop = block.find_loop_item('_atom_site.label').loop
        return

        # loop = block.find_mmcif_category('_atom_site').loop
        # for row in range(loop.length()):
        #    [loop[row, col] for ]
        #    for col in range(loop.width()):
        #        loop[row, col]
        #
        #       block.find_mmcif_category('_atom_site').loop.tags

        for atom in loop:
            pass
            print(atom)

        # Use component-aware lookup keyed by AtomSite attribute names
        # Note: We don't have an AtomSite instance yet, but alias keys
        # support dotted/legacy paths
        labels = cif_get_values(block, 'atom_site_label')
        types = cif_get_values(block, 'atom_site_type_symbol')
        xs = cif_get_values(block, 'atom_site_fract_x')
        ys = cif_get_values(block, 'atom_site_fract_y')
        zs = cif_get_values(block, 'atom_site_fract_z')
        occs = cif_get_values(block, 'atom_site_occupancy')
        bisos = cif_get_values(block, 'atom_site_b_iso')
        uisos = cif_get_values(block, 'atom_site_u_iso')
        wycks = cif_get_values(block, 'atom_site_wyckoff', normalize=normalize_wyckoff)

        for i in range(len(types)):
            if wycks[i] is not None and wycks[i] == '?':
                wycks[i] = None

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

# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import gemmi

# Minimum raw-string length for CIF surrounding-quote detection
_MIN_QUOTED_LEN = 2


def document_from_path(path: str) -> gemmi.cif.Document:
    """Read a CIF document from a file path."""
    return gemmi.cif.read_file(path)


def document_from_string(text: str) -> gemmi.cif.Document:
    """Read a CIF document from a raw text string."""
    return gemmi.cif.read_string(text)


def pick_sole_block(doc: gemmi.cif.Document) -> gemmi.cif.Block:
    """Pick the sole data block from a CIF document."""
    return doc.sole_block()


def name_from_block(block: gemmi.cif.Block) -> str:
    """Extract a model name from the CIF block name."""
    # TODO: Need validator or normalization?
    return block.name


def read_cif_str(block: gemmi.cif.Block, tag: str) -> str | None:
    """
    Read a single string value from a CIF block by tag.

    Strips surrounding single or double quotes when present, and returns
    ``None`` for absent tags or CIF unknown/inapplicable markers
    (``?`` / ``.``).

    Parameters
    ----------
    block : gemmi.cif.Block
        Parsed CIF data block to read from.
    tag : str
        CIF tag to look up (e.g. ``'_peak.profile_type'``).

    Returns
    -------
    str | None
        Unquoted string value, or ``None`` if not found.
    """
    vals = list(block.find_values(tag))
    if not vals:
        return None
    raw: str = vals[0]
    if raw in {'?', '.'}:
        return None
    if len(raw) >= _MIN_QUOTED_LEN and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        return raw[1:-1]
    return raw


# def experiment_type_from_block(
#        exp_type: ExperimentType,
#        block: gemmi.cif.Block,
# ) -> dict:
#    """Extract experiment type information from a CIF block."""
#    for param in exp_type.parameters:
#        param.from_cif(block)

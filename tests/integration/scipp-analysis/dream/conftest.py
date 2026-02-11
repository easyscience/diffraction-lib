# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 DMSC
"""Shared fixtures for DREAM scipp-analysis integration tests.

This module provides pytest fixtures for downloading and parsing
reduced diffraction data from the DREAM instrument in CIF format.
"""

from pathlib import Path

import gemmi
import pytest
from pooch import retrieve

# Remote CIF file URL (regenerated nightly by scipp reduction pipeline)
CIF_URL = 'https://pub-6c25ef91903d4301a3338bd53b370098.r2.dev/dream_reduced.cif'

# Expected datablock name in the CIF file
DATABLOCK_NAME = 'reduced_tof'


@pytest.fixture(scope='module')
def cif_path(
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    """Download CIF file fresh each test session and return its path.

    Uses tmp_path_factory to avoid pooch caching, ensuring the latest
    version of the nightly-regenerated CIF file is always used.
    """
    tmp_dir = tmp_path_factory.mktemp('dream_data')
    return retrieve(url=CIF_URL, known_hash=None, path=tmp_dir)


@pytest.fixture(scope='module')
def cif_content(
    cif_path: str,
) -> str:
    """Read the CIF file content as text."""
    return Path(cif_path).read_text()


@pytest.fixture(scope='module')
def cif_document(
    cif_path: str,
) -> gemmi.cif.Document:
    """Read the CIF file with gemmi and return the document."""
    return gemmi.cif.read(cif_path)


@pytest.fixture(scope='module')
def cif_block(
    cif_document: gemmi.cif.Document,
) -> gemmi.cif.Block:
    """Return the 'reduced_tof' data block from the CIF document."""
    block = cif_document.find_block(DATABLOCK_NAME)
    assert block is not None, (
        f"Expected CIF datablock {DATABLOCK_NAME!r} was not found in the document."
    )
    return block

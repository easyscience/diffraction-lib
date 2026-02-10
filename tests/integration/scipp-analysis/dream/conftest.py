# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 DMSC
"""Shared fixtures for DREAM scipp-analysis integration tests."""

from pathlib import Path

import gemmi
import pytest
from pooch import retrieve

# CIF file URL and expected data block name
CIF_URL = 'https://pub-6c25ef91903d4301a3338bd53b370098.r2.dev/dream_reduced.cif'
DATABLOCK_NAME = 'reduced_tof'


@pytest.fixture(scope='module')
def cif_path() -> str:
    """Retrieve the CIF file and return its path."""
    return retrieve(url=CIF_URL, known_hash=None)


@pytest.fixture(scope='module')
def cif_content(cif_path: str) -> str:
    """Read the CIF file content as text."""
    return Path(cif_path).read_text()


@pytest.fixture(scope='module')
def cif_document(cif_path: str) -> gemmi.cif.Document:
    """Read the CIF file with gemmi and return the document."""
    return gemmi.cif.read(cif_path)


@pytest.fixture(scope='module')
def cif_block(cif_document: gemmi.cif.Document) -> gemmi.cif.Block:
    """Return the expected data block from the CIF document."""
    return cif_document.find_block(DATABLOCK_NAME)


@pytest.fixture(scope='module')
def data_loop(cif_block: gemmi.cif.Block) -> gemmi.cif.Loop:
    """Return the main data loop containing point_id, tof, and intensity data."""
    return cif_block.find(['_pd_data.point_id']).loop

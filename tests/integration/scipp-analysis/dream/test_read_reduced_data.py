# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 DMSC
"""Tests for reading reduced data from CIF files."""

import gemmi


def test_read_reduced_data__fetch_cif(cif_path: str) -> None:
    """Verify that the CIF file can be fetched from remote URL."""
    assert cif_path is not None
    assert len(cif_path) > 0


def test_read_reduced_data__py_read_cif(cif_content: str) -> None:
    """Verify that the CIF file can be read as text and has correct format."""
    assert len(cif_content) > 0  # Check file is not empty
    assert '#\\#CIF_1.1' in cif_content  # Check CIF version is 1.1


def test_read_reduced_data__gemmi_parse(cif_document: gemmi.cif.Document) -> None:
    """Verify that gemmi can parse the CIF document."""
    assert cif_document is not None
    assert len(cif_document) > 0

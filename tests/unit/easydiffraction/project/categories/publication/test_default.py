# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations


def test_publication_instantiates_and_serializes_to_cif():
    from easydiffraction.project.categories.publication.default import Publication

    publication = Publication()
    publication.body.title = 'Refinement report'
    publication.authors.add(name='Ada Lovelace')

    cif_text = publication.as_cif

    assert not cif_text.startswith('data_')
    assert '_publ_body.title' in cif_text
    assert 'Refinement report' in cif_text
    assert '_publ_author.name' in cif_text
    assert 'Ada Lovelace' in cif_text

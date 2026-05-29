# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import pytest


def test_load_publication_reads_toml_metadata(tmp_path):
    from easydiffraction.project.categories.publication.default import Publication
    from easydiffraction.project.publication_loader import load_publication

    path = tmp_path / 'publication.toml'
    path.write_text(
        """
journal_name_full = "Journal of Testing"
body_title = "Refinement report"
body_keywords = ["diffraction", "neutron"]

[[authors]]
name = "Ada Lovelace"
address = "London"
""".lstrip(),
        encoding='utf-8',
    )
    publication = Publication()

    load_publication(publication, path)

    assert publication.journal.name_full.value == 'Journal of Testing'
    assert publication.body.title.value == 'Refinement report'
    assert publication.body.keywords == ['diffraction', 'neutron']
    assert len(publication.authors) == 1
    assert publication.authors[0].name.value == 'Ada Lovelace'
    assert publication.authors[0].address.value == 'London'


def test_load_publication_rejects_unknown_extension(tmp_path):
    from easydiffraction.project.categories.publication.default import Publication
    from easydiffraction.project.publication_loader import load_publication

    path = tmp_path / 'publication.txt'
    path.write_text('body_title = "x"', encoding='utf-8')

    with pytest.raises(ValueError, match='Unsupported publication-info format'):
        load_publication(Publication(), path)


def test_load_publication_rejects_invalid_author_shape(tmp_path):
    from easydiffraction.project.categories.publication.default import Publication
    from easydiffraction.project.publication_loader import load_publication

    path = tmp_path / 'publication.json'
    path.write_text('{"authors": [{"address": "missing name"}]}', encoding='utf-8')

    with pytest.raises(ValueError, match=r"authors\[0\]\.name"):
        load_publication(Publication(), path)

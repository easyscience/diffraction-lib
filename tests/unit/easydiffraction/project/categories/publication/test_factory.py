# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import pytest


def test_publication_factory_default_and_create():
    from easydiffraction.project.categories.publication.default import Publication
    from easydiffraction.project.categories.publication.factory import PublicationFactory

    assert PublicationFactory.default_tag() == 'default'
    assert 'default' in PublicationFactory.supported_tags()

    publication = PublicationFactory.create('default')

    assert isinstance(publication, Publication)


def test_publication_factory_rejects_unknown_tag():
    from easydiffraction.project.categories.publication.factory import PublicationFactory

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        PublicationFactory.create('missing')

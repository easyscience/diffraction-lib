# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project publication metadata categories."""

from __future__ import annotations

import pathlib

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.category_owner import CategoryOwner
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.project.categories.publication.factory import PublicationFactory
from easydiffraction.project.publication_loader import load_publication


class PublicationItemBase(CategoryItem):
    """Base for optional publication metadata scalar categories."""

    def _optional_string(
        self,
        *,
        name: str,
        cif_name: str,
        description: str,
    ) -> StringDescriptor:
        """Create a nullable publication string descriptor."""
        return StringDescriptor(
            name=name,
            description=description,
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=[cif_name]),
        )


class PublicationJournal(PublicationItemBase):
    """Journal metadata for publication reports."""

    _category_code = 'journal'

    def __init__(self) -> None:
        super().__init__()
        self._name_full = self._optional_string(
            name='name_full',
            cif_name='_journal.name_full',
            description='Full journal name.',
        )
        self._year = self._optional_string(
            name='year',
            cif_name='_journal.year',
            description='Journal publication year.',
        )
        self._volume = self._optional_string(
            name='volume',
            cif_name='_journal.volume',
            description='Journal volume.',
        )
        self._issue = self._optional_string(
            name='issue',
            cif_name='_journal.issue',
            description='Journal issue.',
        )
        self._page_first = self._optional_string(
            name='page_first',
            cif_name='_journal.page_first',
            description='First journal page.',
        )
        self._page_last = self._optional_string(
            name='page_last',
            cif_name='_journal.page_last',
            description='Last journal page.',
        )
        self._paper_category = self._optional_string(
            name='paper_category',
            cif_name='_journal.paper_category',
            description='Journal paper category.',
        )
        self._paper_doi = self._optional_string(
            name='paper_doi',
            cif_name='_journal.paper_DOI',
            description='Journal paper DOI.',
        )
        self._coden_astm = self._optional_string(
            name='coden_astm',
            cif_name='_journal.coden_ASTM',
            description='Journal CODEN ASTM identifier.',
        )
        self._suppl_publ_number = self._optional_string(
            name='suppl_publ_number',
            cif_name='_journal.suppl_publ_number',
            description='Supplementary publication number.',
        )

    @property
    def name_full(self) -> StringDescriptor:
        """Full journal name."""
        return self._name_full

    @name_full.setter
    def name_full(self, value: str | None) -> None:
        self._name_full.value = value

    @property
    def year(self) -> StringDescriptor:
        """Journal publication year."""
        return self._year

    @year.setter
    def year(self, value: str | None) -> None:
        self._year.value = value

    @property
    def volume(self) -> StringDescriptor:
        """Journal volume."""
        return self._volume

    @volume.setter
    def volume(self, value: str | None) -> None:
        self._volume.value = value

    @property
    def issue(self) -> StringDescriptor:
        """Journal issue."""
        return self._issue

    @issue.setter
    def issue(self, value: str | None) -> None:
        self._issue.value = value

    @property
    def page_first(self) -> StringDescriptor:
        """First journal page."""
        return self._page_first

    @page_first.setter
    def page_first(self, value: str | None) -> None:
        self._page_first.value = value

    @property
    def page_last(self) -> StringDescriptor:
        """Last journal page."""
        return self._page_last

    @page_last.setter
    def page_last(self, value: str | None) -> None:
        self._page_last.value = value

    @property
    def paper_category(self) -> StringDescriptor:
        """Journal paper category."""
        return self._paper_category

    @paper_category.setter
    def paper_category(self, value: str | None) -> None:
        self._paper_category.value = value

    @property
    def paper_doi(self) -> StringDescriptor:
        """Journal paper DOI."""
        return self._paper_doi

    @paper_doi.setter
    def paper_doi(self, value: str | None) -> None:
        self._paper_doi.value = value

    @property
    def coden_astm(self) -> StringDescriptor:
        """Journal CODEN ASTM identifier."""
        return self._coden_astm

    @coden_astm.setter
    def coden_astm(self, value: str | None) -> None:
        self._coden_astm.value = value

    @property
    def suppl_publ_number(self) -> StringDescriptor:
        """Supplementary publication number."""
        return self._suppl_publ_number

    @suppl_publ_number.setter
    def suppl_publ_number(self, value: str | None) -> None:
        self._suppl_publ_number.value = value


class PublicationJournalDate(PublicationItemBase):
    """Journal editorial date metadata."""

    _category_code = 'journal_date'

    def __init__(self) -> None:
        super().__init__()
        self._accepted = self._optional_string(
            name='accepted',
            cif_name='_journal_date.accepted',
            description='Accepted date.',
        )
        self._from_coeditor = self._optional_string(
            name='from_coeditor',
            cif_name='_journal_date.from_coeditor',
            description='Date sent from coeditor.',
        )
        self._printers_final = self._optional_string(
            name='printers_final',
            cif_name='_journal_date.printers_final',
            description='Final printer date.',
        )

    @property
    def accepted(self) -> StringDescriptor:
        """Accepted date."""
        return self._accepted

    @accepted.setter
    def accepted(self, value: str | None) -> None:
        self._accepted.value = value

    @property
    def from_coeditor(self) -> StringDescriptor:
        """Date sent from coeditor."""
        return self._from_coeditor

    @from_coeditor.setter
    def from_coeditor(self, value: str | None) -> None:
        self._from_coeditor.value = value

    @property
    def printers_final(self) -> StringDescriptor:
        """Final printer date."""
        return self._printers_final

    @printers_final.setter
    def printers_final(self, value: str | None) -> None:
        self._printers_final.value = value


class PublicationJournalCoeditor(PublicationItemBase):
    """Journal coeditor metadata."""

    _category_code = 'journal_coeditor'

    def __init__(self) -> None:
        super().__init__()
        self._code = self._optional_string(
            name='code',
            cif_name='_journal_coeditor.code',
            description='Journal coeditor code.',
        )
        self._name = self._optional_string(
            name='name',
            cif_name='_journal_coeditor.name',
            description='Journal coeditor name.',
        )
        self._notes = self._optional_string(
            name='notes',
            cif_name='_journal_coeditor.notes',
            description='Journal coeditor notes.',
        )

    @property
    def code(self) -> StringDescriptor:
        """Journal coeditor code."""
        return self._code

    @code.setter
    def code(self, value: str | None) -> None:
        self._code.value = value

    @property
    def name(self) -> StringDescriptor:
        """Journal coeditor name."""
        return self._name

    @name.setter
    def name(self, value: str | None) -> None:
        self._name.value = value

    @property
    def notes(self) -> StringDescriptor:
        """Journal coeditor notes."""
        return self._notes

    @notes.setter
    def notes(self, value: str | None) -> None:
        self._notes.value = value


class PublicationContactAuthor(PublicationItemBase):
    """Publication contact-author metadata."""

    _category_code = 'publ_contact_author'

    def __init__(self) -> None:
        super().__init__()
        self._name = self._optional_string(
            name='name',
            cif_name='_publ_contact_author.name',
            description='Contact author name.',
        )
        self._address = self._optional_string(
            name='address',
            cif_name='_publ_contact_author.address',
            description='Contact author address.',
        )
        self._email = self._optional_string(
            name='email',
            cif_name='_publ_contact_author.email',
            description='Contact author email.',
        )
        self._phone = self._optional_string(
            name='phone',
            cif_name='_publ_contact_author.phone',
            description='Contact author phone.',
        )
        self._id_orcid = self._optional_string(
            name='id_orcid',
            cif_name='_publ_contact_author.id_ORCID',
            description='Contact author ORCID identifier.',
        )
        self._id_iucr = self._optional_string(
            name='id_iucr',
            cif_name='_publ_contact_author.id_IUCr',
            description='Contact author IUCr identifier.',
        )

    @property
    def name(self) -> StringDescriptor:
        """Contact author name."""
        return self._name

    @name.setter
    def name(self, value: str | None) -> None:
        self._name.value = value

    @property
    def address(self) -> StringDescriptor:
        """Contact author address."""
        return self._address

    @address.setter
    def address(self, value: str | None) -> None:
        self._address.value = value

    @property
    def email(self) -> StringDescriptor:
        """Contact author email."""
        return self._email

    @email.setter
    def email(self, value: str | None) -> None:
        self._email.value = value

    @property
    def phone(self) -> StringDescriptor:
        """Contact author phone."""
        return self._phone

    @phone.setter
    def phone(self, value: str | None) -> None:
        self._phone.value = value

    @property
    def id_orcid(self) -> StringDescriptor:
        """Contact author ORCID identifier."""
        return self._id_orcid

    @id_orcid.setter
    def id_orcid(self, value: str | None) -> None:
        self._id_orcid.value = value

    @property
    def id_iucr(self) -> StringDescriptor:
        """Contact author IUCr identifier."""
        return self._id_iucr

    @id_iucr.setter
    def id_iucr(self, value: str | None) -> None:
        self._id_iucr.value = value


class PublicationBody(PublicationItemBase):
    """Publication body metadata."""

    _category_code = 'publ_body'

    def __init__(self) -> None:
        super().__init__()
        self._title = self._optional_string(
            name='title',
            cif_name='_publ_body.title',
            description='Publication title.',
        )
        self._synopsis = self._optional_string(
            name='synopsis',
            cif_name='_publ_body.synopsis',
            description='Publication synopsis.',
        )
        self._abstract = self._optional_string(
            name='abstract',
            cif_name='_publ_body.abstract',
            description='Publication abstract.',
        )
        self._keywords = self._optional_string(
            name='keywords',
            cif_name='_publ_body.keywords',
            description='Publication keywords.',
        )

    @property
    def title(self) -> StringDescriptor:
        """Publication title."""
        return self._title

    @title.setter
    def title(self, value: str | None) -> None:
        self._title.value = value

    @property
    def synopsis(self) -> StringDescriptor:
        """Publication synopsis."""
        return self._synopsis

    @synopsis.setter
    def synopsis(self, value: str | None) -> None:
        self._synopsis.value = value

    @property
    def abstract(self) -> StringDescriptor:
        """Publication abstract."""
        return self._abstract

    @abstract.setter
    def abstract(self, value: str | None) -> None:
        self._abstract.value = value

    @property
    def keywords(self) -> list[str]:
        """Publication keywords."""
        value = self._keywords.value
        if value in {None, ''}:
            return []
        return str(value).splitlines()

    @keywords.setter
    def keywords(self, value: list[str]) -> None:
        self._keywords.value = '\n'.join(value)


class PublicationAuthor(PublicationItemBase):
    """Single publication author row."""

    _category_code = 'publ_author'
    _category_entry_name = 'name'

    def __init__(self) -> None:
        super().__init__()
        self._name = self._optional_string(
            name='name',
            cif_name='_publ_author.name',
            description='Publication author name.',
        )
        self._address = self._optional_string(
            name='address',
            cif_name='_publ_author.address',
            description='Publication author address.',
        )
        self._footnote = self._optional_string(
            name='footnote',
            cif_name='_publ_author.footnote',
            description='Publication author footnote.',
        )
        self._id_orcid = self._optional_string(
            name='id_orcid',
            cif_name='_publ_author.id_ORCID',
            description='Publication author ORCID identifier.',
        )
        self._id_iucr = self._optional_string(
            name='id_iucr',
            cif_name='_publ_author.id_IUCr',
            description='Publication author IUCr identifier.',
        )

    @property
    def name(self) -> StringDescriptor:
        """Publication author name."""
        return self._name

    @name.setter
    def name(self, value: str | None) -> None:
        self._name.value = value

    @property
    def address(self) -> StringDescriptor:
        """Publication author address."""
        return self._address

    @address.setter
    def address(self, value: str | None) -> None:
        self._address.value = value

    @property
    def footnote(self) -> StringDescriptor:
        """Publication author footnote."""
        return self._footnote

    @footnote.setter
    def footnote(self, value: str | None) -> None:
        self._footnote.value = value

    @property
    def id_orcid(self) -> StringDescriptor:
        """Publication author ORCID identifier."""
        return self._id_orcid

    @id_orcid.setter
    def id_orcid(self, value: str | None) -> None:
        self._id_orcid.value = value

    @property
    def id_iucr(self) -> StringDescriptor:
        """Publication author IUCr identifier."""
        return self._id_iucr

    @id_iucr.setter
    def id_iucr(self, value: str | None) -> None:
        self._id_iucr.value = value


class PublicationAuthors(CategoryCollection):
    """Publication author rows."""

    def __init__(self) -> None:
        """Create an empty publication-author collection."""
        super().__init__(item_type=PublicationAuthor)

    def add(
        self,
        *,
        name: str,
        address: str | None = None,
        footnote: str | None = None,
        id_orcid: str | None = None,
        id_iucr: str | None = None,
    ) -> PublicationAuthor:
        """
        Add or replace one publication author row.

        Parameters
        ----------
        name : str
            Author name.
        address : str | None, default=None
            Author address.
        footnote : str | None, default=None
            Author footnote.
        id_orcid : str | None, default=None
            Author ORCID identifier.
        id_iucr : str | None, default=None
            Author IUCr identifier.

        Returns
        -------
        PublicationAuthor
            The inserted author row.
        """
        author = PublicationAuthor()
        author.name = name
        author.address = address
        author.footnote = footnote
        author.id_orcid = id_orcid
        author.id_iucr = id_iucr
        super().add(author)
        return author


@PublicationFactory.register
class Publication(CategoryOwner):
    """Project publication metadata facade."""

    type_info = TypeInfo(
        tag='default',
        description='Project publication metadata',
    )

    def __init__(self) -> None:
        super().__init__()
        self._journal = PublicationJournal()
        self._journal_date = PublicationJournalDate()
        self._journal_coeditor = PublicationJournalCoeditor()
        self._contact_author = PublicationContactAuthor()
        self._body = PublicationBody()
        self._authors = PublicationAuthors()

    @property
    def journal(self) -> PublicationJournal:
        """Journal metadata."""
        return self._journal

    @property
    def journal_date(self) -> PublicationJournalDate:
        """Journal editorial date metadata."""
        return self._journal_date

    @property
    def journal_coeditor(self) -> PublicationJournalCoeditor:
        """Journal coeditor metadata."""
        return self._journal_coeditor

    @property
    def contact_author(self) -> PublicationContactAuthor:
        """Publication contact-author metadata."""
        return self._contact_author

    @property
    def body(self) -> PublicationBody:
        """Publication body metadata."""
        return self._body

    @property
    def authors(self) -> PublicationAuthors:
        """Publication author rows."""
        return self._authors

    def from_cif(self, block: object) -> None:
        """
        Populate publication metadata from a project CIF block.

        Parameters
        ----------
        block : object
            Parsed CIF block containing project-level publication tags.
        """
        for category in self.categories:
            category.from_cif(block)

    def load(self, path: str | pathlib.Path) -> None:
        """
        Load publication metadata from a TOML or JSON file.

        Parameters
        ----------
        path : str | pathlib.Path
            File path ending in ``.toml`` or ``.json``.

        Raises
        ------
        ValueError
            If the file extension, top-level shape, or any key is invalid.
        """
        load_publication(self, path)

# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Small link-aware table cell helpers."""

from __future__ import annotations

from collections import UserString


class TableLink(UserString):
    """Clickable table cell text with a target URL."""

    url: str
    title: str | None

    def __init__(
        self,
        text: str,
        url: str,
        title: str | None = None,
    ) -> None:
        """
        Initialize a string-like link cell.

        Parameters
        ----------
        text : str
            Visible cell text.
        url : str
            Link target.
        title : str | None, default=None
            Optional tooltip text.
        """
        super().__init__(text)
        self.url = url
        self.title = title

    @property
    def text(self) -> str:
        """Visible cell text."""
        return self.data


def parameter_docs_link(parameter: object) -> TableLink | str:
    """
    Return a documentation link cell for a parameter-like object.

    Parameters
    ----------
    parameter : object
        Descriptor or parameter object with ``name`` and optional
        ``url`` attributes.

    Returns
    -------
    TableLink | str
        Link-aware cell when a documentation URL is available, otherwise
        the plain parameter name.
    """
    name = str(getattr(parameter, 'name', 'N/A'))
    url = getattr(parameter, 'url', None)
    if isinstance(url, str) and url:
        return TableLink(text=name, url=url, title=f'Documentation for {name}')
    return name

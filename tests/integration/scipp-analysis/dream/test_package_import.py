# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for verifying package installation and version consistency.

These tests check that easydiffraction is installed and can be found on
PyPI.
"""

import importlib.metadata

import pytest
import requests

PACKAGE_NAMES = ['easydiffraction']
PYPI_URL = 'https://pypi.org/pypi/{}/json'


def get_installed_version(
    package_name: str,
) -> str | None:
    """Get the installed version of a package."""
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def get_latest_version(
    package_name: str,
) -> str | None:
    """Get the latest version of a package from PyPI."""
    response = requests.get(PYPI_URL.format(package_name), timeout=10)
    if response.status_code == 200:
        return response.json()['info']['version']
    return None


@pytest.mark.parametrize('package_name', PACKAGE_NAMES)
def test_package_import(
    package_name: str,
) -> None:
    """Verify  that the package is installed and can be fetched from PyPI."""
    installed_version = get_installed_version(package_name)
    latest_version = get_latest_version(package_name)

    assert installed_version is not None, f'Package {package_name} is not installed.'
    assert latest_version is not None, f'Could not fetch latest version for {package_name}.'

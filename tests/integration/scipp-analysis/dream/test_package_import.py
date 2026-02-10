# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 DMSC
"""Tests for verifying package installation and importability."""

import importlib.metadata

import pytest
import requests
from packaging.version import Version

PACKAGE_NAMES = ['easydiffraction', 'essdiffraction']
PYPI_URL = 'https://pypi.org/pypi/{}/json'


def get_installed_version(package_name: str) -> str | None:
    """Get the installed version of a package."""
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def get_latest_version(package_name: str) -> str | None:
    """Get the latest version of a package from PyPI."""
    response = requests.get(PYPI_URL.format(package_name), timeout=10)
    if response.status_code == 200:
        return response.json()['info']['version']
    return None


def get_base_version(version_str: str) -> str:
    """Extract MAJOR.MINOR.PATCH from version string, ignoring local identifiers."""
    v = Version(version_str)
    return v.base_version


@pytest.mark.parametrize('package_name', PACKAGE_NAMES)
def test_package_import__latest(package_name: str) -> None:
    """Verify installed package matches PyPI latest version (MAJOR.MINOR.PATCH)."""
    installed_version = get_installed_version(package_name)
    latest_version = get_latest_version(package_name)

    assert installed_version is not None, f'Package {package_name} is not installed.'
    assert latest_version is not None, f'Could not fetch latest version for {package_name}.'

    # Compare only MAJOR.MINOR.PATCH, ignoring local version identifiers
    installed_base = get_base_version(installed_version)
    latest_base = get_base_version(latest_version)

    assert installed_base == latest_base, (
        f'Package {package_name} is outdated: Installed={installed_base}, Latest={latest_base}'
    )

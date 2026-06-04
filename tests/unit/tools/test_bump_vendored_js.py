# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for tools/bump_vendored_js.py drift detection (no network)."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path


def _load_bump():
    repo_root = Path(__file__).resolve().parents[3]
    module_path = repo_root / 'tools' / 'bump_vendored_js.py'
    spec = importlib.util.spec_from_file_location('bump_vendored_js', module_path)
    module = importlib.util.module_from_spec(spec)
    # Register before exec so the module's dataclasses can resolve their
    # own module via sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _runtime(bump, dest_dir, content):
    asset = bump.VendoredAsset(
        'a.js',
        'https://example.invalid/a.js',
        hashlib.sha256(content).hexdigest(),
    )
    return bump.VendoredRuntime(
        name='Example',
        package='example',
        version='1.0.0',
        dest_dir=dest_dir,
        licence='MIT — Example.',
        assets=(asset,),
    )


def test_check_runtime_flags_missing_then_passes_then_detects_drift(tmp_path):
    bump = _load_bump()
    content = b'console.log("hi");\n'
    runtime = _runtime(bump, tmp_path, content)

    # Missing asset -> drift reported.
    assert bump._check_runtime(runtime)

    # Correct asset + regenerated licence -> clean.
    (tmp_path / 'a.js').write_bytes(content)
    (tmp_path / 'LICENSES.md').write_text(bump._license_text(runtime), encoding='utf-8')
    assert bump._check_runtime(runtime) == []

    # Tampered asset -> hash drift.
    (tmp_path / 'a.js').write_bytes(b'tampered\n')
    problems = bump._check_runtime(runtime)
    assert any('hash drift' in problem for problem in problems)

    # Restore asset, tamper licence -> licence drift.
    (tmp_path / 'a.js').write_bytes(content)
    (tmp_path / 'LICENSES.md').write_text('stale\n', encoding='utf-8')
    problems = bump._check_runtime(runtime)
    assert any('license drift' in problem for problem in problems)

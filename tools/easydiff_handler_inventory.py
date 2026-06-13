# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Generate an EasyDiff persistence-handler inventory."""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
DEFAULT_OUTPUT = (
    REPO_ROOT
    / 'docs'
    / 'dev'
    / 'adrs'
    / 'accepted'
    / 'edstar-project-persistence'
    / 'handler-inventory.json'
)

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@dataclass(frozen=True)
class InventoryEntry:
    """One descriptor declared with a ``CifHandler``."""

    context: str
    descriptor_path: str
    owner_class: str
    descriptor_class: str
    descriptor_name: str
    unique_name: str
    category_code: str | None
    category_entry_name: str | None
    project_name: str
    current_cif_names: list[str]
    import_names: list[str]
    read_names: list[str]
    iucr_name: str
    docs_page: str
    docs_anchor: str


def _import_registration_modules() -> None:
    """Import packages whose ``__init__`` files register classes."""
    import easydiffraction.analysis.categories.aliases  # noqa: F401
    import easydiffraction.analysis.categories.constraints  # noqa: F401
    import easydiffraction.analysis.categories.fit_parameter_correlations  # noqa: F401
    import easydiffraction.analysis.categories.fit_parameters  # noqa: F401
    import easydiffraction.analysis.categories.fit_result  # noqa: F401
    import easydiffraction.analysis.categories.fitting_mode  # noqa: F401
    import easydiffraction.analysis.categories.joint_fit  # noqa: F401
    import easydiffraction.analysis.categories.minimizer  # noqa: F401
    import easydiffraction.analysis.categories.sequential_fit  # noqa: F401
    import easydiffraction.analysis.categories.sequential_fit_extract  # noqa: F401
    import easydiffraction.analysis.categories.software  # noqa: F401
    import easydiffraction.datablocks.experiment.categories.background  # noqa: F401
    import easydiffraction.datablocks.experiment.categories.calculator  # noqa: F401
    import easydiffraction.datablocks.experiment.categories.data  # noqa: F401
    import easydiffraction.datablocks.experiment.categories.data_range  # noqa: F401
    import easydiffraction.datablocks.experiment.categories.diffrn  # noqa: F401
    import easydiffraction.datablocks.experiment.categories.excluded_regions  # noqa: F401
    import easydiffraction.datablocks.experiment.categories.experiment_type  # noqa: F401
    import easydiffraction.datablocks.experiment.categories.extinction  # noqa: F401
    import easydiffraction.datablocks.experiment.categories.instrument  # noqa: F401
    import easydiffraction.datablocks.experiment.categories.linked_structure  # noqa: F401
    import easydiffraction.datablocks.experiment.categories.linked_structures  # noqa: F401
    import easydiffraction.datablocks.experiment.categories.peak  # noqa: F401
    import easydiffraction.datablocks.experiment.categories.pref_orient  # noqa: F401
    import easydiffraction.datablocks.experiment.categories.refln  # noqa: F401
    import easydiffraction.datablocks.experiment.item  # noqa: F401
    import easydiffraction.datablocks.structure.categories.atom_site_aniso  # noqa: F401
    import easydiffraction.datablocks.structure.categories.atom_sites  # noqa: F401
    import easydiffraction.datablocks.structure.categories.cell  # noqa: F401
    import easydiffraction.datablocks.structure.categories.geom  # noqa: F401
    import easydiffraction.datablocks.structure.categories.space_group  # noqa: F401
    import easydiffraction.datablocks.structure.categories.space_group_wyckoff  # noqa: F401
    import easydiffraction.project.categories.metadata  # noqa: F401
    import easydiffraction.project.categories.rendering_plot  # noqa: F401
    import easydiffraction.project.categories.rendering_structure  # noqa: F401
    import easydiffraction.project.categories.rendering_table  # noqa: F401
    import easydiffraction.project.categories.report  # noqa: F401
    import easydiffraction.project.categories.structure_style  # noqa: F401
    import easydiffraction.project.categories.structure_view  # noqa: F401
    import easydiffraction.project.categories.verbosity  # noqa: F401


def _representative_roots() -> list[tuple[str, object]]:
    """Create representative owners whose context shapes descriptors."""
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.datablocks.experiment.item.factory import ExperimentFactory
    from easydiffraction.datablocks.structure.item.factory import StructureFactory
    from easydiffraction.project.project_config import ProjectConfig

    roots: list[tuple[str, object]] = [
        ('project', ProjectConfig()),
        ('analysis', Analysis(project=None)),
        ('structure', StructureFactory.from_scratch(name='inventory_structure')),
    ]
    experiment_cases = [
        (
            'experiment.bragg_pd_cwl',
            'powder',
            'constant wavelength',
            'bragg',
        ),
        ('experiment.bragg_pd_tof', 'powder', 'time-of-flight', 'bragg'),
        ('experiment.total_pd_cwl', 'powder', 'constant wavelength', 'total'),
        ('experiment.total_pd_tof', 'powder', 'time-of-flight', 'total'),
        (
            'experiment.bragg_sc_cwl',
            'single crystal',
            'constant wavelength',
            'bragg',
        ),
        (
            'experiment.bragg_sc_tof',
            'single crystal',
            'time-of-flight',
            'bragg',
        ),
    ]
    for context, sample_form, beam_mode, scattering_type in experiment_cases:
        roots.append(
            (
                context,
                ExperimentFactory.from_scratch(
                    name='inventory_experiment',
                    sample_form=sample_form,
                    beam_mode=beam_mode,
                    scattering_type=scattering_type,
                ),
            )
        )
    return roots


def _factory_roots() -> list[tuple[str, object]]:
    """Create registered category implementations where practical."""
    from easydiffraction.core.category import CategoryCollection
    from easydiffraction.core.category import CategoryItem
    from easydiffraction.core.factory import FactoryBase

    roots: list[tuple[str, object]] = []
    for factory in _factory_subclasses(FactoryBase):
        for tag, cls in sorted(factory._supported_map().items()):
            if not issubclass(cls, (CategoryItem, CategoryCollection)):
                continue
            instance = _instantiate_registered_class(cls)
            if instance is None:
                continue
            roots.append((f'factory.{factory.__name__}.{tag}', instance))
    return roots


def _factory_subclasses(cls: type) -> list[type]:
    """Return recursive subclasses sorted by class name."""
    result: list[type] = []
    for subclass in cls.__subclasses__():
        result.append(subclass)
        result.extend(_factory_subclasses(subclass))
    return sorted(result, key=lambda item: item.__name__)


def _instantiate_registered_class(cls: type) -> object | None:
    """Instantiate a registered category class when arguments are known."""
    if inspect.isabstract(cls):
        return None

    signature = inspect.signature(cls)
    constructor_args: dict[str, object] = {}
    for parameter in signature.parameters.values():
        if parameter.default is not inspect.Parameter.empty:
            continue
        if parameter.kind in {
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        }:
            continue
        if parameter.name == 'type':
            constructor_args['type'] = 'cryspy'
            continue
        if parameter.name == 'name':
            constructor_args['name'] = 'inventory'
            continue
        return None

    return cls(**constructor_args)


def collect_inventory() -> list[InventoryEntry]:
    """Collect the deterministic handler inventory."""
    _import_registration_modules()
    entries: list[InventoryEntry] = []
    for context, root in [*_representative_roots(), *_factory_roots()]:
        _walk_object(root, context, context, entries, set())
    return sorted(
        _deduplicate_entries(entries),
        key=lambda entry: (
            entry.context,
            entry.descriptor_path,
            entry.project_name,
            entry.iucr_name,
        ),
    )


def _walk_object(
    obj: object,
    context: str,
    path: str,
    entries: list[InventoryEntry],
    visited: set[int],
) -> None:
    """Walk an object graph and collect handler descriptors."""
    from easydiffraction.core.category import CategoryCollection
    from easydiffraction.core.guard import GuardedBase
    from easydiffraction.core.variable import GenericDescriptorBase

    if id(obj) in visited:
        return
    visited.add(id(obj))

    if isinstance(obj, GenericDescriptorBase):
        entries.append(_entry_for_descriptor(context, path, obj))
        return

    if isinstance(obj, CategoryCollection):
        _walk_collection_item_type(obj, context, path, entries, visited)

    if not isinstance(obj, GuardedBase):
        return

    for attr_name, value in sorted(vars(obj).items()):
        if attr_name in {'_identity', '_parent'}:
            continue
        child_path = f'{path}.{_path_segment(attr_name)}'
        if isinstance(value, GenericDescriptorBase):
            entries.append(_entry_for_descriptor(context, child_path, value))
            continue
        if isinstance(value, GuardedBase):
            _walk_object(value, context, child_path, entries, visited)


def _walk_collection_item_type(
    obj: object,
    context: str,
    path: str,
    entries: list[InventoryEntry],
    visited: set[int],
) -> None:
    """Collect descriptors from a collection's item prototype."""
    item_type = getattr(obj, '_item_type', None)
    if item_type is None:
        return
    try:
        item = item_type()
    except TypeError:
        return
    _walk_object(item, context, f'{path}[]', entries, visited)


def _path_segment(attr_name: str) -> str:
    """Return a stable path segment for a private storage name."""
    if attr_name == '_calculator_category':
        return 'calculator'
    return attr_name.removeprefix('_')


def _entry_for_descriptor(
    context: str,
    path: str,
    descriptor: object,
) -> InventoryEntry:
    """Build one inventory entry from a descriptor."""
    handler = descriptor._cif_handler
    identity = descriptor._identity
    return InventoryEntry(
        context=context,
        descriptor_path=path,
        owner_class=type(getattr(descriptor, '_parent', None)).__name__,
        descriptor_class=type(descriptor).__name__,
        descriptor_name=descriptor.name,
        unique_name=descriptor.unique_name,
        category_code=identity.category_code,
        category_entry_name=identity.category_entry_name,
        project_name=handler.project_name,
        current_cif_names=list(handler.names),
        import_names=list(handler.import_names),
        read_names=list(handler.read_names),
        iucr_name=handler.iucr_name,
        docs_page=handler.docs_page,
        docs_anchor=handler.docs_anchor,
    )


def _deduplicate_entries(entries: list[InventoryEntry]) -> list[InventoryEntry]:
    """Remove exact duplicate paths produced by overlapping roots."""
    unique_entries: dict[tuple[str, str, str, str], InventoryEntry] = {}
    for entry in entries:
        key = (
            entry.context,
            entry.descriptor_path,
            entry.project_name,
            entry.iucr_name,
        )
        unique_entries[key] = entry
    return list(unique_entries.values())


def _inventory_payload(entries: list[InventoryEntry]) -> dict[str, Any]:
    """Render the inventory JSON payload."""
    return {
        'schema': 'easydiff-handler-inventory-v1',
        'generated_by': 'tools/easydiff_handler_inventory.py',
        'entries': [asdict(entry) for entry in entries],
    }


def _serialized_payload(entries: list[InventoryEntry]) -> str:
    """Return canonical inventory JSON text."""
    return json.dumps(_inventory_payload(entries), indent=2, sort_keys=True) + '\n'


def write_inventory(path: Path) -> None:
    """Write the handler inventory to *path*."""
    entries = collect_inventory()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_serialized_payload(entries), encoding='utf-8')
    print(f'Wrote {len(entries)} entries to {path}')


def check_inventory(path: Path) -> int:
    """Return 0 when *path* matches the generated inventory."""
    expected = _serialized_payload(collect_inventory())
    actual = path.read_text(encoding='utf-8') if path.exists() else ''
    if actual == expected:
        print(f'{path} is up to date')
        return 0
    print(f'{path} is out of date')
    return 1


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--output',
        type=Path,
        default=DEFAULT_OUTPUT,
        help='Inventory JSON path to write or check.',
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check instead of rewriting the inventory file.',
    )
    args = parser.parse_args()

    if args.check:
        return check_inventory(args.output)
    write_inventory(args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

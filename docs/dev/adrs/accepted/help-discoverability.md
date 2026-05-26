# ADR: Help Method Discoverability

## Status

Accepted and implemented.

## Context

EasyDiffraction is used by scientists who often explore the API in
notebooks. The main object graph already exposes many focused objects:
projects, project metadata, structures, experiments, categories,
parameters, analysis helpers, reports, and display facades. Users need
a consistent way to discover the next useful operation from any of these
objects without reading source code.

Most model objects inherit `GuardedBase`, `CategoryItem`,
`CategoryCollection`, `DatablockItem`, or `DatablockCollection`, which
already provide `help()` output. Plain facade classes such as display
namespaces and reports do not inherit those base classes, so they need
the same discovery behavior explicitly.

## Decision

Every primary public object should provide a `help()` method. This
includes:

- parameters and descriptors
- category items and category collections
- datablock items and datablock collections
- project-level objects such as `Project`, `ProjectInfo`, `Analysis`,
  `Report`, and `Rendering`
- display facades such as `project.display`,
  `project.display.parameters`, `project.display.fit`,
  `project.display.posterior`, and `analysis.display`

`help()` output uses the existing console/table presentation style. It
lists public properties and methods discovered from the class MRO, uses
the first docstring paragraph as the description, and skips private
names. Specialized containers can append domain-specific tables, such as
collection items or datablock categories, after the generic section.

Plain helper and facade classes use `render_object_help()` so their
output stays consistent with `GuardedBase.help()` without forcing those
classes into the guarded object hierarchy.

## Consequences

Users can call `help()` while navigating through the object graph:

```python
project.help()
project.display.help()
project.display.parameters.help()
project.analysis.display.help()
project.report.help()
project.experiments.help()
project.experiments['hrpt'].help()
project.experiments['hrpt'].background.help()
project.experiments['hrpt'].background['1'].help()
```

New user-facing objects should either inherit an existing help-capable
base class or define `help()` by delegating to `render_object_help()`.
When a class represents a collection or owner, its help output should
guide users to the next object level where practical.

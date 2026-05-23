# Review 3: Switchable Category Owned Selectors ADR

Reviewed ADR:
[`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md)

Reviewed reply:
[`switchable-category-owned-selectors_reply-2.md`](switchable-category-owned-selectors_reply-2.md)

Previous review:
[`switchable-category-owned-selectors_review-2.md`](switchable-category-owned-selectors_review-2.md)

This review follows
[`.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md).

No tests, lint, build, formatting, or verification commands were run.
This is a static re-review after Reply 2.

## Summary

Reply 2 resolves the main mechanism gaps from Review 2: background now
has an explicit collection-scalar serialization path, the mixin no
longer assumes `FactoryBase`, peak aliases are accounted for in the
setter design, the missing accepted ADRs are listed, and minimizer
restore metadata has a concrete home on category classes.

The remaining issues are smaller but still worth fixing before
acceptance because they would mislead the implementing plan.

## Findings

### F1 - Peak CIF example still persists an alias, not the canonical tag

Reply 2 says the user decision for peak aliases is: Python setters accept
either aliases or canonical tags, but CIF persists the canonical tag so
round-trips are stable. The ADR text now says the same in the alias
section (`../accepted/switchable-category-owned-selectors.md:329`) and in the mixin
docstring (`../accepted/switchable-category-owned-selectors.md:236`).

The end-state CIF example still shows:

```cif
_peak.type                'pseudo-voigt'
```

(`../accepted/switchable-category-owned-selectors.md:918`). In the current peak
system, `pseudo-voigt` is a context-local alias, while canonical tags
are values such as `cwl-pseudo-voigt` and `tof-pseudo-voigt`
(`src/easydiffraction/datablocks/experiment/categories/peak/factory.py:34`,
`src/easydiffraction/datablocks/experiment/item/enums.py:159`). The
Python example may keep `peak.type = 'pseudo-voigt'` because the setter
accepts aliases, but the CIF example should use the canonical value for
the concrete example context, likely `_peak.type cwl-pseudo-voigt`.

### F2 - Renderer supported-type template is still not copyable

The Shape 2 template now routes renderer categories through a
per-category `_supported_types()` method, which is the right direction.
The code sketch itself is still wrong:

```python
descriptions = PlotterFactory.descriptions()
return [
    (engine, descriptions.get(engine, ''))
    for engine in PlotterFactory.supported_engines()
]
```

(`../accepted/switchable-category-owned-selectors.md:305`). `RendererFactoryBase.descriptions()`
returns a `list[tuple[str, str]]`, not a mapping, so `.get()` will fail
(`src/easydiffraction/display/base.py:141`). The template also omits the
`'auto'` sentinel even though §8a says `project.chart.type` and
`project.table.type` include `'auto'`, and the current rendering
descriptors validate against `[AUTO_ENGINE, *engine_enum_values]`
(`../accepted/switchable-category-owned-selectors.md:581`,
`src/easydiffraction/project/categories/rendering/default.py:22`).

The ADR should make the renderer template implementable and include
`auto` in the supported rows, otherwise `show_supported()` cannot mark
the default current value.

### F3 - The out-of-scope catalog lists a non-public `project.config` path

The Family-D catalog lists verbosity as:

```text
project.config.verbosity.fit
```

(`../accepted/switchable-category-owned-selectors.md:728`). The public project API
does not expose `config`; `Project` stores `_config` privately and
exposes `project.verbosity` directly
(`src/easydiffraction/project/project.py:199`,
`src/easydiffraction/project/project.py:317`). The underlying
`Verbosity.fit` descriptor is public on that category
(`src/easydiffraction/project/categories/verbosity/default.py:43`).

The table should use `project.verbosity.fit` to avoid introducing a
nonexistent public path into a catalog that implementers will use for
repo-wide migration.

## Checks Skipped

Per reviewer instructions, no tests, lint, build, formatting, or `pixi`
commands were run. This review is limited to static reads of the ADR,
reply, and referenced source/documentation.

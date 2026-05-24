# Review 2: Switchable Category Owned Selectors ADR

Reviewed ADR:
[`switchable-category-owned-selectors.md`](../accepted/switchable-category-owned-selectors.md)

Reviewed reply:
[`switchable-category-owned-selectors_reply-1.md`](switchable-category-owned-selectors_reply-1.md)

Previous review:
[`switchable-category-owned-selectors_review-1.md`](switchable-category-owned-selectors_review-1.md)

This review follows
[`.github/copilot-instructions.md`](../../../../.github/copilot-instructions.md).

No tests, lint, build, or verification commands were run. This is a
static re-review after Reply 1.

## Summary

Reply 1 resolves the original narrow instance-swap findings in spirit,
but the ADR now expands from switchable category selectors to every
writable selector-like surface, including rendering, table rendering,
calculator backend selection, and fitting mode. That broader scope
introduces new mechanism and documentation gaps that should be resolved
before acceptance.

## Findings

### F1 - `_background.type` still will not serialize through the generic path

The amended ADR says the `_type` descriptor is picked up automatically
by `category.parameters` and the generic CIF path, so no custom hook is
needed (`../accepted/switchable-category-owned-selectors.md:247`). That
is true for `CategoryItem`, but not for `CategoryCollection`. The
current collection implementation returns only parameters from its loop
items (`src/easydiffraction/core/category.py:230`), and
`category_collection_to_cif()` writes only a loop built from the first
item's parameters (`src/easydiffraction/io/cif/serialize.py:244`).

`background` is explicitly modeled as
`BackgroundBase(CategoryCollection, SwitchableCategoryBase)`
(`../accepted/switchable-category-owned-selectors.md:165`), so a
collection-level `_type` descriptor will not emit `_background.type` or
load back through the existing generic collection serializer. The ADR
needs either a collection-level scalar serialization contract, a custom
`BackgroundBase.as_cif`/`from_cif` rule, or a different persistence
shape for collection-backed switchables.

### F2 - The shared mixin still assumes `FactoryBase`, so it cannot cover Families B and C

The reply reframes the ADR around one public surface for Families A/B/C,
but the proposed mixin still requires
`_factory: ClassVar[type[FactoryBase]]` and renders by calling
`_factory._supported_map()` and `_factory.supported_for(**filters)`
(`../accepted/switchable-category-owned-selectors.md:185`,
`../accepted/switchable-category-owned-selectors.md:229`). That works
for current domain factories, but not for the newly in-scope renderer
and fitting mode selectors.

Renderer factories use `RendererFactoryBase`, whose public surface is
`_registry()`, `supported_engines()`, and `descriptions()`, not
`_supported_map()` / `supported_for()`
(`src/easydiffraction/display/base.py:104`). `PlotterFactory` and
`TableRendererFactory` implement `_registry()` only
(`src/easydiffraction/display/plotting.py:5955`,
`src/easydiffraction/display/tables.py:142`). `fitting_mode` is backed
by `FitModeEnum`, not a factory at all
(`src/easydiffraction/analysis/enums.py:10`).

As written, `project.chart.show_supported()`,
`project.table.show_supported()`, and
`project.analysis.fitting_mode.show_supported()` cannot use the proposed
mixin. The ADR should either keep the mixin scoped to Family A and
define separate Family-B/C adapters, or define a small common "supported
type provider" protocol that each category implements before the mixin
renders the table.

### F3 - Peak aliases are lost while examples still use alias values

The current peak API accepts context-local aliases such as
`'pseudo-voigt'` and canonicalizes them to concrete tags like
`'cwl-pseudo-voigt'` / `'tof-pseudo-voigt'`
(`src/easydiffraction/datablocks/experiment/categories/peak/factory.py:34`,
`src/easydiffraction/datablocks/experiment/item/base.py:532`). It also
prints those aliases in `show_peak_profile_types()`
(`src/easydiffraction/datablocks/experiment/item/base.py:568`).

The amended mixin renders raw `klass.type_info.tag` values and validates
against factory-supported tags
(`../accepted/switchable-category-owned-selectors.md:229`,
`../accepted/switchable-category-owned-selectors.md:247`). That removes
the local-alias behavior, but the ADR examples still show the alias
form: `_peak.type 'pseudo-voigt'` and
`project.experiments['hrpt'].peak.type = 'pseudo-voigt'`
(`../accepted/switchable-category-owned-selectors.md:767`,
`../accepted/switchable-category-owned-selectors.md:858`).

The ADR needs to choose and document one behavior: persist and expose
canonical tags such as `_peak.type cwl-pseudo-voigt`, or keep the
context-local alias UX by adding category-specific alias hooks to `type`
assignment, CIF serialization, and `show_supported()`.

### F4 - The structural expansion omits accepted ADRs that it supersedes

Reply 1 adds `Rendering -> Chart + Table`, removes `project.rendering`,
and replaces `_rendering.*` with `_chart.*` / `_table.*`
(`../accepted/switchable-category-owned-selectors.md:436`). That
directly supersedes the accepted Display UX ADR, which deliberately
moved serialized renderer settings into `project.rendering` and
`_rendering.*` (`../accepted/display-ux.md:44`), and the accepted
Category Owner Sections ADR, which lists `ProjectConfig` children as
`ProjectInfo` and `Rendering`, with public `project.rendering` and saved
`_rendering.*` (`../accepted/category-owner-sections.md:74`).

The "ADRs that need to be updated" list does not include either accepted
ADR (`../accepted/switchable-category-owned-selectors.md:654`). If the
widened scope stays, those ADRs need explicit amendments. Otherwise the
accepted documentation will continue to direct implementers toward the
old `project.rendering` object graph and CIF block.

### F5 - The method-name restoration contract points to a non-existent class constant

The amended ADR drops `_minimizer.optimizer_name` and
`_minimizer.method_name`, then says restored `FitResults` derives them
from `analysis.minimizer.type` and the engine's `DEFAULT_METHOD` class
constant (`../accepted/switchable-category-owned-selectors.md:151`).
Current minimizer implementations define `DEFAULT_METHOD` as a
module-level constant, not a class attribute
(`src/easydiffraction/analysis/minimizers/lmfit_leastsq.py:12`,
`src/easydiffraction/analysis/minimizers/bumps_lm.py:12`), while runtime
fit-state storage reads the actual engine instance fields
(`src/easydiffraction/analysis/analysis.py:1387`).

Dropping the persisted fields may be a valid beta cleanup, but the ADR
must define an implementable restore source. For example: derive both
values by constructing the matching minimizer engine through
`MinimizerFactory.create(tag)`, or move method metadata onto the
registered class as explicit class-level metadata before using it during
restore.

## Checks Skipped

Per reviewer instructions, no tests, lint, build, formatting, or `pixi`
commands were run. The next pass should remain static until the ADR is
accepted and an implementation plan is drafted.

# Architecture Decision Records

Project-specific ADRs are kept in this repository. Organization-wide ADR
indexing may exist separately, but repository decisions should stay near
the code they explain.

The index follows the EasyScience discussion guidance from
[discussion #47](https://github.com/orgs/easyscience/discussions/47):
group decisions by topic first, then use titles and short descriptions
to keep the list easy to scan. If a group becomes too broad, split it;
if a group stays small, keep it as a group rather than adding deeper
folders.

## Accepted ADRs

| Group                | Title                                     | Short description                                                                                                 | Link                                                                                    |
| -------------------- | ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Analysis and fitting | Fit Mode Categories and Fit Execution API | Splits fitting configuration from execution and defines active sibling fit-mode categories.                       | [`fit-mode-categories.md`](accepted/fit-mode-categories.md)                             |
| Analysis and fitting | Runtime Fit Results                       | Keeps full fit outputs runtime-only in the current design unless a narrower persistence ADR is accepted.          | [`runtime-fit-results.md`](accepted/runtime-fit-results.md)                             |
| Core model           | Category Owners and Real Datablocks       | Introduces `CategoryOwner` so singleton sections do not pretend to be real CIF datablocks.                        | [`category-owner-sections.md`](accepted/category-owner-sections.md)                     |
| Core model           | Enum-Backed Closed Value Sets             | Requires finite option sets to use `(str, Enum)` classes for validation and dispatch.                             | [`enum-backed-closed-values.md`](accepted/enum-backed-closed-values.md)                 |
| Core model           | Guarded Public Properties                 | Uses property setters as the public writability contract for guarded objects.                                     | [`guarded-public-properties.md`](accepted/guarded-public-properties.md)                 |
| Core model           | Two-Level Category Parameter Access       | Keeps parameter access to `datablock.category.parameter` or `datablock.collection[id].parameter`.                 | [`category-parameter-access.md`](accepted/category-parameter-access.md)                 |
| Documentation        | Descriptor Property Docstring Template    | Makes descriptor metadata the source of truth for public property docstrings and annotations.                     | [`property-docstring-template.md`](accepted/property-docstring-template.md)             |
| Documentation        | Development Documentation Structure       | Defines the `docs/dev` layout for ADRs, issues, plans, package structure, and roadmap.                            | [`development-docs-structure.md`](accepted/development-docs-structure.md)               |
| Documentation        | Help Method Discoverability               | Requires primary public objects and facades to expose consistent `help()` output.                                 | [`help-discoverability.md`](accepted/help-discoverability.md)                           |
| Documentation        | Notebook Generation Source of Truth       | Treats tutorial `.py` files as editable sources and notebooks as generated artifacts.                             | [`notebook-generation.md`](accepted/notebook-generation.md)                             |
| Experiment model     | Immutable Experiment Type                 | Makes experiment type axes creation-time state rather than mutable runtime state.                                 | [`immutable-experiment-type.md`](accepted/immutable-experiment-type.md)                 |
| Factories            | Factory Contracts and Metadata            | Standardizes factory construction, metadata, compatibility, and registration behavior.                            | [`factory-contracts.md`](accepted/factory-contracts.md)                                 |
| Naming               | Factory Tag Naming                        | Defines canonical factory tag style and standard abbreviations.                                                   | [`factory-tag-naming.md`](accepted/factory-tag-naming.md)                               |
| Persistence          | Free-Flag CIF Encoding                    | Encodes fit free/fixed state through CIF uncertainty syntax instead of a separate free list.                      | [`free-flag-cif-encoding.md`](accepted/free-flag-cif-encoding.md)                       |
| Persistence          | Project Facade and Persistence Layout     | Documents the current `Project` facade and saved directory layout.                                                | [`project-facade-and-persistence.md`](accepted/project-facade-and-persistence.md)       |
| Quality              | Lint Complexity Thresholds                | Treats ruff PLR complexity limits as design guardrails that should not be bypassed.                               | [`lint-complexity-thresholds.md`](accepted/lint-complexity-thresholds.md)               |
| Quality              | Test Strategy                             | Defines layered unit, functional, integration, script, and notebook testing.                                      | [`test-strategy.md`](accepted/test-strategy.md)                                         |
| Structure model      | Type-Neutral ADP Parameters               | Keeps ADP parameter object identities stable across B/U and iso/ani switches.                                     | [`type-neutral-adp-parameters.md`](accepted/type-neutral-adp-parameters.md)             |
| User-facing API      | Display UX Facade                         | Defines `project.display` and `project.rendering` responsibilities and display method names.                      | [`display-ux.md`](accepted/display-ux.md)                                               |
| User-facing API      | Selector Families                         | Distinguishes backend selectors, switchable-category selectors, and active-sibling selectors.                     | [`selector-families.md`](accepted/selector-families.md)                                 |
| User-facing API      | String Paths and Live Descriptors         | Separates persisted field selectors from references to live model parameters.                                     | [`string-paths-and-live-descriptors.md`](accepted/string-paths-and-live-descriptors.md) |
| User-facing API      | Switchable Category API                   | Places multi-type category selectors on the owner and omits public selectors for fixed or single-type categories. | [`switchable-category-api.md`](accepted/switchable-category-api.md)                     |

## ADR Suggestions

| Group                | Title                                                         | Short description                                                                                                  | Link                                                                                       |
| -------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| Analysis and fitting | Analysis CIF Fit State                                        | Proposes a persisted scalar projection of fit state in `analysis.cif`.                                             | [`analysis-cif-fit-state.md`](suggestions/analysis-cif-fit-state.md)                       |
| Analysis and fitting | Parameter Correlation Persistence                             | Proposes persisting deterministic and posterior correlation summaries.                                             | [`parameter-correlation-persistence.md`](suggestions/parameter-correlation-persistence.md) |
| Analysis and fitting | Parameter-Level Posterior Projection and Bayesian Persistence | Proposes saved Bayesian summaries and canonical posterior storage.                                                 | [`parameter-posterior-summary.md`](suggestions/parameter-posterior-summary.md)             |
| Analysis and fitting | Undo Fit                                                      | Proposes an analysis-owned rollback operation for the latest pre-fit scalar state.                                 | [`undo-fit.md`](suggestions/undo-fit.md)                                                   |
| Workspace model      | Workspace Root and Project Information Category               | Proposes renaming the top-level facade from `Project` to `Workspace` and reserving `project` for project metadata. | [`workspace-root-project-category.md`](suggestions/workspace-root-project-category.md)     |

# Review 1: Dataset-Driven Fit Modes and Sequential Redefinition

## Findings

### P1. Resolve the `sequential_fit` category before redefining `sequential`

The ADR redefines `sequential` to fit the already loaded experiments in
turn, but it also keeps `sequential_fit` and `sequential_fit_extract` as
mode-specific categories that remain visible and serializable when
sequential mode is relevant (`dataset-driven-fit-modes.md` lines
124-133). Those categories are not neutral today: the accepted fit-mode
ADR and persistence mapping define them around the folder sweep
(`data_dir`, `file_pattern`, `max_workers`, `chunk_size`, `reverse`, and
extraction rules), and the current code consumes those fields directly
when running sequential fits. At the same time, this ADR defers the
folder-sweep fate out of the first implementation
(`dataset-driven-fit-modes.md` lines 268-270).

That leaves the first implementation with two incompatible meanings for
the same public and persisted surface. If `sequential_fit` remains
visible for loaded-dataset sequential fits, users will see folder-input
fields that are irrelevant to the loaded experiments. If it is omitted,
Decision 5 is wrong. If it is serialized, old folder settings can
survive under a mode that no longer reads them. Please make the ADR
choose the first-step contract explicitly: either retire or hide the
folder-specific categories until a later input-source design, split the
folder sweep into a separate mode/workflow now, or define
`sequential_fit` as an input-source category whose loaded-dataset case
has a clear no-folder representation.

### P1. Define replay semantics so plotting does not corrupt live state

Decision 4 says issue 85 is fixed by applying an experiment's stored
parameter set to the shared structure before recomputing or plotting
that experiment (`dataset-driven-fit-modes.md` lines 114-122). Because
the project has one live structure object shared by all loaded
experiments, applying an earlier point's fitted parameters is itself a
state mutation. The ADR does not say whether that mutation is temporary,
whether the previous live state is restored after plotting, whether the
"current" project model becomes whichever point was plotted last, or how
this interacts with save and undo.

Without that rule, the proposed fix can replace issue 85 with a
different correctness bug: plotting experiment A can silently change the
structure values used for experiment B, subsequent calculations, and the
saved project. Please specify the replay contract in the ADR. For
example, require plot/calculation replay to apply stored per-dataset
parameters in a scoped temporary context that restores the pre-plot live
model, or choose a non-mutating storage strategy such as persisted
calculated arrays for each fitted dataset.

### P1. Specify what makes loaded experiments a valid sequential series

The availability table makes `sequential` available for any project with
at least two loaded experiments (`dataset-driven-fit-modes.md` lines
71-92), while fit-time validation only says "`sequential` with no
fittable series" should raise a clear error
(`dataset-driven-fit- modes.md` lines 143-152). The ADR never defines
the boundary between "two loaded experiments" and "a fittable series."
That matters because the scientific intent is "the same sample, fit per
point" (lines 29-30), but a project can contain multiple arbitrary
experiments, possibly with different experiment types, calculators,
measured-data state, structures, free-parameter sets, or intended
ordering.

Please make the sequential preconditions part of the decision rather
than leaving them to the plan. At minimum, the ADR should say whether
loaded-dataset sequential requires exactly one structure, measured data
on every experiment, compatible experiment/calculator types, a stable
experiment order, and a consistent carried-forward free-parameter set.
Those rules also need to feed `show_supported()` or the fit-time error
message so scientists are not offered a workflow that cannot be
explained from the loaded project state.

## Checks

Static review only. Per `AGENTS.md`, I did not run tests, lint,
formatters, build commands, or any `pixi` command.

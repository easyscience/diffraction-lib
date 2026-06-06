# Testing Guide

Practical placement rules for the easydiffraction test suite. The
rationale is recorded in the ADRs
[Test Strategy](adrs/accepted/test-strategy.md) and
[Test Suite and Validation Strategy](adrs/accepted/test-suite-and-validation.md).

## Layers — what goes where

A test belongs to the **lowest** layer whose constraints it can satisfy.

| Layer           | May use                                                                   | Must NOT use                                                                                  | Speed       |
| --------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ----------- |
| **unit**        | one module under test; in-process logic; `tmp_path`                       | real calculation engine; network / `download_data()`; filesystem outside `tmp_path`; `sleep`; subprocess | sub-second  |
| **functional**  | several modules / a workflow; small bundled fixtures                      | real calculation engine; network / `download_data()`                                          | seconds     |
| **integration** | real engines, real fits, real downloaded data (the only layer allowed network and real backends) | —                                                                            | slow        |
| **script**      | a full tutorial `.py` executed subprocess-isolated                        | —                                                                                             | slow        |
| **notebook**    | a generated `.ipynb` executed via `nbmake`                                | —                                                                                             | slow        |

Mocking a forbidden dependency (for example a mocked `download_data()`)
keeps a test in a lower layer **only when the mock is explicit**; an
accidental real call is a layer violation.

The unit tree mirrors `src/` one-to-one. `tools/test_structure_check.py`
enforces this and is gated in CI (`lint-format.yml`); create the mirror
test file for a new module with `tools/gen_tests_scaffold.py`.

## Where does this test go?

1. Does it call a real calculation engine (cryspy / crysfml / pdffit) or
   download data? → **integration**.
2. Does it run a whole tutorial `.py`? → **script** (and **notebook**
   for the generated `.ipynb`).
3. Does it exercise several modules together, in-process, with bundled
   fixtures only? → **functional**.
4. Otherwise — one module, in-process, fast? → **unit**, mirrored next
   to its source module.

## Cost tiers (orthogonal to layers)

Tiers select *when* a test runs in CI; they are independent of the layer.

| Tier        | Marker                  | Runs on                                          |
| ----------- | ----------------------- | ------------------------------------------------ |
| **fast**    | (none — the default)    | every push, every pull request, and nightly      |
| **pr**      | `@pytest.mark.pr`       | pull requests and `develop`/`master`             |
| **nightly** | `@pytest.mark.nightly`  | the scheduled nightly job only (`nightly.yml`)   |

Integration tests are `pr`-tier by default — they are auto-marked in
`tests/integration/conftest.py` because they use real engines. Escalate
an individual test to the heaviest tier with `@pytest.mark.nightly`.

CI marker selection:

- feature-branch push: `-m "not pr and not nightly"`
- pull request + `develop`/`master`: `-m "not nightly"`
- nightly schedule: `-m nightly`

## Numeric tolerances

Prefer the shared comparison fixtures in `tests/conftest.py` over ad-hoc
per-test tolerances: one documented `rtol`/`atol` pair for intra-engine
numerics, and one (looser) pair for cross-engine comparison.

## Input-domain coverage

User input is validated at runtime through `core/validation.py`
(`AttributeSpec` pairs a `TypeValidator` with a content `ValidatorBase`).
Aim input-domain tests at the validators directly — both that they accept
the full valid domain and that they reject (or fall back on) invalid
values. Use `hypothesis` (deterministic profile) for generative coverage
and explicit parametrised tables for the known-critical boundaries.

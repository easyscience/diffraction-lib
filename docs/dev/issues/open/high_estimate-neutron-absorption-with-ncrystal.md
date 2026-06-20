# 169. Estimate Neutron Absorption With NCrystal

**Priority:** `[priority] high`

**Type:** Physics / UX / Optional dependency

EasyDiffraction now has a user-facing sample-absorption model for
constant-wavelength powder Bragg experiments, but users still need to
provide `μR` directly. For neutron experiments this quantity is often
derivable from material composition, isotope mix, density, wavelength,
and sample radius:

```
μR = μ(λ, composition, density) · R
```

NCrystal could be useful as an optional helper for estimating this
quantity. It should not replace the fixed bound coherent neutron
scattering lengths used in the nuclear Bragg structure factor; those
remain atom/isotope properties. The wavelength dependence belongs to
absorption and transport cross sections.

**Motivation:**

- Scientists often know the sample formula, density, radius, and
  wavelength more readily than an already-computed `μR`.
- Absorption-sensitive isotope mixes (`H/D`, `B`, `Li`, `Cd`, `Gd`,
  rare-earths) can be difficult to estimate safely by hand.
- A diagnostic helper could explain when a dataset is absorption
  sensitive and suggest a starting value for
  `experiment.absorption.mu_r`.

**Proposed scope:**

- Keep NCrystal optional; do not make it a required dependency of the
  core calculator path.
- Provide an explicit helper or future category mode that estimates `μR`
  from:
  - wavelength,
  - composition / isotope composition,
  - density,
  - cylindrical sample radius.
- Store the resulting value in the existing absorption parameter rather
  than hiding it in calculator internals.
- Report assumptions clearly, especially natural abundance vs enriched
  isotopes and density source.
- Keep the existing manual `μR` path as the authoritative override.

**Non-goals:**

- Do not make neutron coherent scattering lengths wavelength-dependent.
- Do not replace cryspy/CrysFML neutron scattering-length tables in
  ordinary Bragg structure-factor calculations.
- Do not add NCrystal as a hard dependency without an accepted plan that
  names the dependency.
- Do not attempt full neutron transport, multiple scattering, or
  container/sample-environment simulation in this first step.

**Open questions:**

- Where should the helper live: `experiment.absorption`, a separate
  material/composition helper, or a calculator-independent utility?
- Which composition source should drive it: structure atom sites,
  chemical formula, explicit isotope fractions, or a future sample
  material category?
- Should the estimate be one-shot ("calculate and set `μR`") or a live
  derived value that updates when wavelength/radius/density changes?
- How should uncertainty or confidence be shown to non-programmer users?
- Can NCrystal provide the needed macroscopic absorption coefficient
  directly for our required assumptions, or do we need to combine its
  atom data/cross sections ourselves?

**Depends on:** the sample-absorption model in
[`highest_model-sample-absorption-debye-scherrer-r.md`](highest_model-sample-absorption-debye-scherrer-r.md).

**Recommended-priority note:** Marked **high** because it would improve
UX and reduce user error for neutron absorption, but it depends on the
existing absorption model and should remain optional.

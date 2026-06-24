# 166. cryspy vs FullProf: Bérar–Baldinozzi Empirical-Asymmetry Convention Mismatch

**Priority:** `[priority] medium`

**Type:** Correctness / External backend / Verification

## Summary

The four empirical peak-asymmetry parameters (`asym_beba_a0`,
`asym_beba_b0`, `asym_beba_a1`, `asym_beba_b1`; formerly `asym_empir_1`…
`4`) are the **Bérar–Baldinozzi (1993)** correction — FullProf's
`P1`…`P4`. When the _same_ parameter values are fed to cryspy and to
FullProf, the two codes produce **different** asymmetric profiles. A
controlled calculate-vs-calculate study pins the entire discrepancy to
exactly **two** independent causes, and — checked against the original
paper — shows that **cryspy is faithful to the published
Bérar–Baldinozzi functions while FullProf's executable departs from
them**. This is the root cause behind the long-standing "asymmetry
parameters don't agree" observation on the
`pd-neut-cwl_PbSO4_beba-asymmetry` Verification page.

This issue documents the finding and the evidence. It is primarily a
**document-and-report-upstream** item: no cryspy code lives in this
repository, and our own implementation is correct.

## The published model (Bérar & Baldinozzi, 1993)

Bérar, J.-F. & Baldinozzi, G. (1993). _Modeling of line-shape asymmetry
in powder diffraction._ J. Appl. Cryst. **26**, 128–129. The asymmetry
is a multiplicative correction built from **the odd derivatives of a
Gaussian** — explicitly the odd Hermite polynomials `H1 = 2z` and
`H3 = 8z³ − 12z`:

- `Fa(z) = 2z·exp(−z²)` — eq. (12), `= H1·exp(−z²)`
- `Fb(z) = (8z³ − 12z)·exp(−z²)` — eq. (13), `= H3·exp(−z²)`
- `g(dθ) = g0(dθ)·[1 + A(θ)·Fa(z) + B(θ)·Fb(z)]` — eqs. (11)/(14)
- `A(θ) = A0/tan(θ) + A1/tan(2θ)` — eq. (15) (likewise `B(θ)`), with the
  paper noting the second term may instead use `1/sin(2θ)`.
- `z = dθ/w` (deviation-to-width ratio).

The four refinable coefficients map onto the basis as
`(A0, B0, A1, B1) = (Fa/tan θ, Fb/tan θ, Fa/tan 2θ, Fb/tan 2θ)`, which
is FullProf's `(P1, P2, P3, P4)` and our
`(asym_beba_a0, asym_beba_b0, asym_beba_a1, asym_beba_b1)`.

## What each implementation actually uses

| Source                                             | `Fb(z)`                                  | Matches paper eq. (13)?           |
| -------------------------------------------------- | ---------------------------------------- | --------------------------------- |
| Paper eq. (13)                                     | `(8z³ − 12z)·exp(−z²)` (= `H3·exp(−z²)`) | — (definition)                    |
| **cryspy** `func_asymmetry_f_b` = `2(2z²−3)·Fa`    | `(8z³ − 12z)·exp(−z²)`                   | **Yes (exact)**                   |
| **FullProf manual** (`fp_text.htm`): `2(2z²−3)·Fa` | `(8z³ − 12z)·exp(−z²)`                   | **Yes (exact)**                   |
| **FullProf _program_** (inferred from output)      | `(8z³ − 6z)·exp(−z²)` (= `(4z²−3)·Fa`)   | **No** — not a Hermite polynomial |

`Fa(z) = 2z·exp(−z²)` is identical in all of them.

## How it was established

FullProf 8.40 (`/home/andrewsazonov/Applications/fullprof/fp2k`) was run
on a Y₂O₃ diagnostic structure, profile NPROF = 7 (TCH), with the
empirical asymmetry parameters set in five configurations: each of
`Asy1…Asy4` isolated (= 0.2, others 0) and one combined set. Each
FullProf **calculated** profile (`.prf`, background-subtracted) was then
reproduced in cryspy, comparing calculate-vs-calculate (no experimental
data, no fitting noise). cryspy's profile machinery was reproduced
inline and verified **byte-identical** to the installed cryspy (max abs
diff 0.0), so the inline knobs faithfully represent real cryspy edits.

Metric below is `profdiff% = 100·Σ|ref−calc| / Σ|ref|`; `0.27%` is the
numerical floor (`.prf` precision + background interpolation).

### Attribution sweep (paper's exact `Fa`/`Fb`, toggling sign + angular term)

| Config               | combined  | P1 (Fa/tanθ) | P2 (Fb/tanθ) | P3 (Fa/tan2θ) | P4 (Fb/tan2θ) |
| -------------------- | --------- | ------------ | ------------ | ------------- | ------------- |
| stock (s+, 1/tan2θ)  | 8.12%     | 30%          | 105%         | 13%           | 45%           |
| **sign flip only**   | 8.60%     | **0.27%**    | 46%          | **0.27%**     | 19%           |
| 1/sin2θ only         | 5.91%     | 30%          | 105%         | 15%           | 68%           |
| sign + 1/sin2θ       | 15.83%    | 0.27%        | 46%          | **9.9%**      | 57%           |
| sign + `Fb=(8z³−6z)` | **0.27%** | 0.27%        | 0.78%        | 0.27%         | 0.28%         |

### Reading the sweep

- With **only a sign flip**, the two **`Fa`** terms (P1, P3) transfer
  _perfectly_ (0.27%). That proves cryspy's `Fa` **and** both angular
  factors (`1/tan θ` _and_ `1/tan 2θ`) already match FullProf exactly.
- The two **`Fb`** terms (P2, P4) are the only things that break, and
  they break identically whether paired with `1/tan θ` or `1/tan 2θ` —
  so it is a pure `Fb`-shape problem, independent of angle.
- The **`1/sin 2θ` alternative is rejected**: it makes P3 _worse_ (0.27%
  → 9.9%). FullProf uses `1/tan 2θ`, exactly as cryspy does.
- Restoring `Fb = (8z³ − 6z)` fixes P2 and P4 (→ 0.78%, 0.28%).

A free four-parameter refit of cryspy to FullProf's combined profile
reaches **0.09%** (corr 0.999999), confirming the model is otherwise
identical; the parameter map is _not_ a simple sign flip (e.g. FullProf
`P = (0.177, 0.034, −0.05, 0.02)` → cryspy
`(−0.286, −0.035, 0.028, −0.014)`), which is precisely the
`Fb = paper + 3·Fa` admixture (`(8z³−6z) = (8z³−12z) + 3·(2z)`) plus the
sign.

## Root-cause decomposition

The entire discrepancy is **exactly two independent things**:

1. **Sign of `z`** — a convention; FullProf uses the opposite sign
   (equivalently, treats the published `P1…P4` as negated). Both choices
   are physically admissible (the paper sets the sign by fitting); they
   must merely be consistent to share parameter values.
2. **The `Fb` function** — a genuine discrepancy. The paper and cryspy
   use the odd Hermite `H3 = 8z³ − 12z`; FullProf's program behaves as
   `8z³ − 6z`, which is **not** a Hermite polynomial and so cannot be
   what eq. (13)'s "odd Hermite polynomials" construction intends.

Everything else — `Fa`, the `1/tan θ` first term, and the `1/tan 2θ`
second term — is identical between the codes.

## Verdict

- **cryspy is correct** w.r.t. Bérar–Baldinozzi: its `Fa` and `Fb` are
  verbatim eqs. (12)–(13).
- **The FullProf manual is correct** too (its printed `2(2z²−3)·Fa`
  equals eq. (13)).
- **FullProf's executable is the outlier** — its effective `Fb` linear
  term is `−6z` where the published, Hermite-mandated value is `−12z`.

Caveats: this is inferred from FullProf's _calculated output_, not its
(closed) source; the last ~0.5% (P2 at 0.78%) sits at `.prf` numerical
precision, so the program's `Fb` is `≈ (8z³−6z)` but not provably
exactly `−6z` vs, say, `−6.1z`.

## Practical implications

- Users who port FullProf `Asy1…4` into cryspy (or vice versa) get a
  **wrong** asymmetric profile; refining in cryspy recovers a good fit
  but with parameters that do not equal FullProf's (sign-mirrored and
  `Fb`-rescaled). These parameters are non-physical and rarely transfer
  between datasets in any case (see issue 133).
- A "make cryspy match FullProf" edit (`Fb: (8z³−12z) → (8z³−6z)` plus a
  `z` sign flip in cryspy's `powder_diffraction_const_wavelength.py`)
  would be **bug-for-bug compatibility** with FullProf, _not_ a
  correctness fix — it would make cryspy disagree with the published
  functions. Do **not** apply it to cryspy as a "fix" without labelling
  it as a FullProf-compatibility quirk.

## Recommended next steps

1. **Report upstream to cryspy** (ikibalin/cryspy#50): cryspy matches
   Bérar–Baldinozzi; the disagreement is with FullProf's executable
   (`Fb = 8z³−6z`, opposite sign). Attach the attribution table and the
   paper reference.
2. **Report upstream to FullProf** (Rodríguez-Carvajal): the executable
   appears to deviate from both eq. (13) and FullProf's own manual in
   the `Fb` linear term. If confirmed, this affects every FullProf user,
   not just cross-engine comparisons.
3. **Keep our docs honest**: the note and CI-skip on
   `pd-neut-cwl_PbSO4_beba-asymmetry` remain correct and cite this
   issue.
4. **Done:** the rename tracked by issue 133 landed — the parameters are
   now `asym_beba_{a0,b0,a1,b1}` (the `beba` model tag mirrors
   `asym_fcj_*`).

## Relations

- **Relates to** issue 133 (rename `asym_empir_*`; add physical FCJ
  model) — this issue supplies the confirmed physics/naming basis.
- **Relates to** the Verification page
  `pd-neut-cwl_PbSO4_beba-asymmetry` (CI-skipped; documents the
  convention difference).
- **Upstream:** cryspy issue
  [#50](https://github.com/ikibalin/cryspy/issues/50).

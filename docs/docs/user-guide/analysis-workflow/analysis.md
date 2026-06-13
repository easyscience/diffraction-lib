---
icon: material/calculator
---

# :material-calculator: Analysis

This section provides an overview of **diffraction data analysis** in
EasyDiffraction, focusing on model-dependent analysis, calculation
engines, and minimization techniques.

In EasyDiffraction, we focus on **model-dependent analysis**, where a
model is constructed based on prior knowledge of the studied system, and
its parameters are optimized to achieve the best agreement between
experimental and calculated diffraction data. Model-dependent analysis
is widely used in neutron and X-ray scattering data.

## Calculation

EasyDiffraction relies on third-party crystallographic libraries,
referred to as **calculation engines** or just **calculators**, to
perform the calculations.

The calculation engines are used to calculate the diffraction pattern
for the defined model of the studied structure using the instrumental
and other required experiment-related parameters, such as the
wavelength, resolution, etc.

You do not necessarily need the measured data to perform the
calculations, but you need a structural model and some details about the
type of experiment you want to simulate.

EasyDiffraction is designed as a flexible and extensible tool that
supports different **calculation engines** for diffraction pattern
calculations. Currently, we integrate CrysPy, CrysFML, and PDFfit2
libraries as calculation engines.

### CrysPy Calculator

[CrysPy](https://www.cryspy.fr) is a Python library originally developed
for analysing polarised neutron diffraction data. It is now evolving
into a more general purpose library and covers powders and single
crystals, nuclear and (commensurate) magnetic structures, unpolarised
neutron and X-ray diffraction.

### CrysFML Calculator

[CrysFML](https://code.ill.fr/scientific-software/CrysFML2008) library
is a collection of Fortran modules for crystallographic computations. It
is used in the software package
[FullProf](https://www.ill.eu/sites/fullprof/), and we are currently
working on its integration into EasyDiffraction.

### PDFfit2 Calculator

[PDFfit2](https://github.com/diffpy/diffpy.pdffit2/) is a Python library
for calculating the pair distribution function (PDF) from
crystallographic models.

### Set Calculator

The calculator is automatically selected based on the experiment type
(e.g., `cryspy` for Bragg diffraction, `pdffit` for total scattering).
To show the supported calculation engines for a specific experiment:

```python
project.experiments['hrpt'].calculator.show_supported()
```

Example output:

Calculator types

|     | Type   | Description                                      |
| --- | ------ | ------------------------------------------------ |
| \*  | cryspy | CrysPy library for crystallographic calculations |

To explicitly select a calculation engine for an experiment:

```python
project.experiments['hrpt'].calculator.type = 'cryspy'
```

## Minimization / Optimization

The process of refining model parameters involves iterating through
multiple steps until the calculated data sufficiently matches the
experimental data. This process is illustrated in the following diagram:

```mermaid
flowchart LR
    a(Propose<br/>structure)
    b(Set/change<br/>structure and<br/>experiment<br/>parameters)
    c(Calculate<br/>pattern)
    d(Compare<br/>calculated data to<br/>experimental<br/>data)
    e(Stop<br/>iteration)
    a --> b
    b --> c
    c --> d
    d-- Threshold<br/>not<br/>reached -->b
    d-- Threshold<br/>reached -->e
```

Like the calculation engines, EasyDiffraction is designed to utilize
various third-party libraries for model refinement and parameter
optimization. These libraries provide robust curve fitting and
uncertainty estimation tools.

### Lmfit Minimizer

Most of the examples in this section will use the
[lmfit](https://lmfit.github.io/lmfit-py/) package, which provides a
high-level interface to non-linear optimisation and curve fitting
problems for Python. It is one of the tools that can be used to fit
models to the experimental data.

### Bumps Minimizer

Another package that can be used for the same purpose is
[bumps](https://bumps.readthedocs.io/en/latest/). In addition to
traditional optimizers which search for the best minimum they can find
in the search space, bumps provides Bayesian uncertainty analysis which
explores all viable minima and finds confidence intervals on the
parameters based on uncertainty in the measured values.

### emcee Minimizer

[emcee](https://emcee.readthedocs.io/) is an affine-invariant ensemble
sampler for Bayesian posterior exploration. It is useful after a stable
least-squares model has been prepared and the goal is to inspect
credible intervals, correlations, and posterior-predictive uncertainty
rather than only one best-fit point.

### DFO-LS Minimizer

[DFO-LS](https://github.com/numericalalgorithmsgroup/dfols)
(Derivative-Free Optimizer for Least-Squares) is a Python library for
solving nonlinear least-squares minimization, without requiring
derivatives of the objective.

### Set Minimizer

To show the supported minimizers:

```python
project.analysis.minimizer.show_supported()
```

Example output:

Minimizer types

|     | Type                  | Description                                                   |
| --- | --------------------- | ------------------------------------------------------------- |
|     | lmfit                 | LMFIT library using the default Levenberg-Marquardt method    |
| \*  | lmfit (leastsq)       | LMFIT library with Levenberg-Marquardt least squares method   |
|     | lmfit (least_squares) | LMFIT library with SciPy's trust region reflective algorithm  |
|     | dfols                 | DFO-LS library for derivative-free least-squares optimization |
|     | bumps                 | BUMPS library using the default Levenberg-Marquardt method    |
|     | bumps (lm)            | BUMPS library with Levenberg-Marquardt method                 |
|     | bumps (dream)         | BUMPS library with DREAM Bayesian sampling                    |
|     | bumps (amoeba)        | BUMPS library with Nelder-Mead simplex method                 |
|     | bumps (de)            | BUMPS library with differential evolution method              |
|     | emcee                 | emcee affine-invariant ensemble Bayesian sampling             |

To select the desired minimizer, e.g., 'lmfit':

```python
project.analysis.minimizer.type = 'lmfit'
```

### Fit Mode

In EasyDiffraction, you can set the **fit mode** to control how the
refinement process is performed. The fit mode determines whether the
refinement is performed independently for each experiment or jointly
across all experiments.

The supported fit modes are:

| Mode       | Description                                                         |
| ---------- | ------------------------------------------------------------------- |
| single     | Independent fitting of each experiment; no shared parameters        |
| joint      | Simultaneous fitting of all experiments; some parameters are shared |
| sequential | Repeated single fits over a scan directory                          |

You can set the fit mode on the analysis owner:

```python
project.analysis.fitting_mode.type = 'joint'
```

To check the current fit mode:

```python
print(project.analysis.fitting_mode.type)
```

### Perform Fit

Refining the structure and experiment parameters against measured data
is usually divided into several steps, where each step involves adding
or removing parameters to be refined, calculating the diffraction
pattern, and comparing it to the experimental data as shown in the
diagram above.

To select the parameters to be refined, you can set the attribute `free`
of the parameters to `True`. This indicates that the parameter is free
to be optimized during the refinement process.

Here is an example of how to set parameters to be refined:

```python
# Set structure parameters to be refined.
project.structures['lbco'].cell.length_a.free = True

# Set experiment parameters to be refined.
project.experiments['hrpt'].linked_structures['lbco'].scale.free = True
project.experiments['hrpt'].instrument.calib_twotheta_offset.free = True
project.experiments['hrpt'].background['10'].y.free = True
project.experiments['hrpt'].background['165'].y.free = True
```

After setting the parameters to be refined, you can perform the fit
using the `fit` method of the `analysis` object:

```python
project.analysis.fit()
```

This method will iterate through the defined steps, adjusting the
parameters until the calculated data sufficiently matches the
experimental data.

An example of the output after performing the fit is:

```console
🚀 Starting fit process with 'lmfit (leastsq)'...
📈 Goodness-of-fit progress:
╒═══════════╤══════════╤═══════╤═════════════════╕
│ iteration │ time (s) │  χ²   │ change / status │
╞═══════════╪══════════╪═══════╪═════════════════╡
│     1     │   0.10   │ 164.6 │ initial         │
│    12     │   0.24   │ 33.4  │ 79.7 % ↓        │
│    21     │   0.38   │ 13.2  │ 60.4 % ↓        │
│    30     │   0.52   │  5.8  │ 56.3 % ↓        │
│    77     │   0.77   │  3.1  │ converged       │
╘═══════════╧══════════╧═══════╧═════════════════╛
🏆 Best goodness-of-fit (reduced χ²) is 3.14 at iteration 77
✅ Fitting complete.
📋 Least-squares fit results:
╒═════════════════════════════════╤════════════════╕
│ 🧪 Minimizer                    │ lmfit (leastsq)│
│ ✅ Overall status               │ success        │
│ ⏱️ Fitting time (seconds)       │ 0.77           │
│ 🔁 Iterations                   │ 77             │
│ 📏 Goodness-of-fit (reduced χ²) │ 3.14           │
│ 📏 R-factor (Rf, %)             │ 8.42           │
│ 📏 Weighted R-factor (wR, %)    │ 11.62          │
╘═════════════════════════════════╧════════════════╛
📈 Refined parameters:
```

Now, you can inspect the fitted parameters to see how they have changed
during the refinement process, select more parameters to be refined, and
perform additional fits as needed.

To plot the measured and calculated data after the fit, you can use the
`pattern` method of the `display` object:

```python
project.display.pattern(expt_name='hrpt')
```

### Re-estimating the Background

If you seeded the background automatically (see the
[Background Category](experiment.md#background-category) section), you
can improve it once a fit has produced a model. Calling `auto_estimate`
again after a fit automatically uses the fitted peaks (the default
`use_model=True`) to place better points, especially across crowded
regions where peaks overlap:

```python
# Re-estimate the background using the fitted model
project.experiments['hrpt'].background.auto_estimate()

# Optionally free some of the new (fixed) points and fit again
project.experiments['hrpt'].background['1'].y.free = True
project.analysis.fit()
```

This estimate → refine → re-estimate loop is safe to repeat: each call
overwrites the previous points with a fresh, fixed background.

## Bayesian Analysis

Bayesian minimizers sample a posterior distribution rather than only
optimizing to a single minimum. They are useful after a conventional
least-squares fit has produced a stable model and you want credible
intervals, parameter correlations, and posterior-predictive uncertainty.

Two minimizer types currently use Bayesian sampling:

- `bumps (dream)` uses the DREAM sampler through Bumps.
- `emcee` uses the affine-invariant ensemble sampler and can resume from
  a saved project.

Select a Bayesian minimizer through the same category-owned selector:

```python
project.analysis.minimizer.type = 'emcee'
project.save_as(dir_path='lbco_hrpt')  # required before an emcee fit
project.analysis.fit()
```

For a saved `emcee` project, resume the chain with extra steps:

```python
project.analysis.fit(resume=True, extra_steps=500)
```

After a Bayesian fit, inspect posterior summaries and plots:

```python
project.display.posterior.distribution()
project.display.posterior.pairs()
project.display.posterior.predictive(expt_name='hrpt')
```

When posterior or posterior-predictive arrays are persisted, they are
stored in `analysis/results.h5`. Scalar summaries remain in
`analysis/analysis.cif`.

## Constraints

In EasyDiffraction, you can define **constraints** on the structure or
experiment parameters to ensure that they remain within a specific range
or follow a certain relationship during the refinement process.

### Setting Aliases

Before setting constraints, you need to set aliases for the parameters
you want to constrain. This can be done using the `create` method of the
`aliases` object. Aliases are used to reference parameters in a more
readable way, making it easier to manage constraints.

An example of setting aliases for parameters in a structure:

```python
# Set aliases for the atomic displacement parameters
project.analysis.aliases.create(
    id='biso_La',
    param=project.structures['lbco'].atom_sites['La'].adp_iso,
)
project.analysis.aliases.create(
    id='biso_Ba',
    param=project.structures['lbco'].atom_sites['Ba'].adp_iso,
)

# Set aliases for the occupancies of the atom sites
project.analysis.aliases.create(
    id='occ_La',
    param=project.structures['lbco'].atom_sites['La'].occupancy,
)
project.analysis.aliases.create(
    id='occ_Ba',
    param=project.structures['lbco'].atom_sites['Ba'].occupancy,
)
```

### Setting Constraints

Now that you have set the aliases, you can define constraints using the
`create` method of the `constraints` object. Each constraint is a single
expression string of the form `lhs = rhs`, where the left-hand side is
an alias and the right-hand side is an expression involving other
aliases.

An example of setting constraints for the aliases defined above:

```python
project.analysis.constraints.create(expression='biso_Ba = biso_La')

project.analysis.constraints.create(expression='occ_Ba = 1 - occ_La')
```

These constraints ensure that the `biso_Ba` parameter is equal to
`biso_La`, and the `occ_Ba` parameter is equal to `1 - occ_La`. This
means that the occupancy of the Ba atom will always be adjusted based on
the occupancy of the La atom, and the isotropic displacement parameter
for Ba will be equal to that of La during the refinement process.

### Viewing Constraints

To view the defined constraints, you can use the `show` method on
`project.analysis.constraints`:

```python
project.analysis.constraints.show()
```

The example of the output is:

User defined constraints

| id      | expression          |
| ------- | ------------------- |
| biso_Ba | biso_Ba = biso_La   |
| occ_Ba  | occ_Ba = 1 - occ_La |

Constraints enabled: True

## Analysis as CIF

To inspect an analysis configuration in CIF format, use:

```python
# Show analysis as CIF
project.analysis.show_as_cif()
```

Example output:

```
╒════════════════════════════════════════════════╕
│ _fitting_mode.type           single            │
│ _minimizer.type              "lmfit (leastsq)" │
│                                                │
│ loop_                                          │
│ _alias.label                                   │
│ _alias.param_unique_name                       │
│ biso_La  lbco.atom_site.La.B_iso_or_equiv      │
│ biso_Ba  lbco.atom_site.Ba.B_iso_or_equiv      │
│ occ_La   lbco.atom_site.La.occupancy           │
│ occ_Ba   lbco.atom_site.Ba.occupancy           │
│                                                │
│ loop_                                          │
│ _constraint.id                                 │
│ _constraint.expression                         │
│ biso_Ba  "biso_Ba = biso_La"                   │
│ occ_Ba   "occ_Ba = 1 - occ_La"                 │
╘════════════════════════════════════════════════╛
```

## Saving an Analysis

Saving the project, as described in the [Project](project.md) section,
will also save the analysis settings to the `analysis.cif` inside the
project directory.

<br>

---

Now that the analysis is finished, you can proceed to the next step:
[Report](report.md).

---
icon: material/school
---

# :material-school: Tutorials

This section presents a collection of **Jupyter Notebook** tutorials
that demonstrate how to use EasyDiffraction for various tasks. These
tutorials serve as self-contained, step-by-step **guides** to help users
grasp the workflow of data analysis using EasyDiffraction.

Instructions on how to run the tutorials are provided in the
[:material-cog-box: Installation & Setup](../installation-and-setup/index.md#how-to-run-tutorials)
section of the documentation.

The tutorials are organized into the following categories:

## Getting Started

- [LBCO `quick` `code`](refine-lbco-hrpt-from-data.ipynb) – A minimal example intended as a
  quick reference for users already familiar with the EasyDiffraction
  API or who want to see an example refinement when both the structure
  and experiment are defined directly in code. This tutorial covers a
  Rietveld refinement of the La0.5Ba0.5CoO3 crystal structure using
  constant wavelength neutron powder diffraction data from HRPT at PSI.
- [LBCO `basic` `load`](refine-lbco-hrpt-from-cif.ipynb) – A basic example intended as a
  quick reference for users already familiar with the EasyDiffraction
  API or who want to see how Rietveld refinement of the La0.5Ba0.5CoO3
  crystal structure can be performed when both the structure and
  experiment are loaded from CIF files. Data collected from constant
  wavelength neutron powder diffraction at HRPT at PSI.
- [LBCO `complete`](refine-lbco-hrpt-report.ipynb) – Demonstrates the use of the
  EasyDiffraction API in a simplified, user-friendly manner that closely
  follows the GUI workflow for a Rietveld refinement of the
  La0.5Ba0.5CoO3 crystal structure using constant wavelength neutron
  powder diffraction data from HRPT at PSI. This tutorial provides a
  full explanation of the workflow with detailed comments and
  descriptions of every step, making it suitable for users who are new
  to EasyDiffraction or those who prefer a more guided approach.

## Load Project

- [LBCO Single Fit](load-and-fit-lbco-hrpt.ipynb) – The most minimal example showing how
  to load a previously saved project from a directory and continue
  working with it.
- [Co2SiO4 Sequential Fit](refine-cosio-d20-tscan-resumed.ipynb) – Resumes a sequential
  refinement from an existing `analysis/results.csv` after an incomplete
  previous run.

See also under [Bayesian Analysis](#bayesian-analysis):
[LBCO Bayesian Display (`bumps-dream`)](bayesian-dream-display-lbco-hrpt.ipynb) and
[LBCO Bayesian Resume (`emcee`)](bayesian-emcee-resume-lbco-hrpt.ipynb) — both load saved projects
containing Bayesian fit state.

## Powder Diffraction

- [Co2SiO4 `pd-neut-cwl`](refine-cosio-d20.ipynb) – Demonstrates a Rietveld
  refinement of the Co2SiO4 crystal structure using constant wavelength
  neutron powder diffraction data from D20 at ILL.
- [HS `pd-neut-cwl`](refine-hs-hrpt.ipynb) – Demonstrates a Rietveld refinement of
  the HS crystal structure using constant wavelength neutron powder
  diffraction data from HRPT at PSI.
- [Si `pd-neut-tof`](refine-si-sepd.ipynb) – Demonstrates a Rietveld refinement of
  the Si crystal structure using time-of-flight neutron powder
  diffraction data from SEPD at Argonne.
- [NCAF `pd-neut-tof`](refine-ncaf-wish.ipynb) – Demonstrates a Rietveld refinement
  of the Na2Ca3Al2F14 crystal structure using two time-of-flight neutron
  powder diffraction datasets (from two detector banks) of the WISH
  instrument at ISIS.

## Without Measured Data

- [LBCO `pd-neut-cwl`](simulate-lbco-cwl.ipynb) – Loads the La0.5Ba0.5CoO3 structure
  from a CIF and calculates a constant-wavelength neutron powder pattern
  over a chosen 2θ range, with background and Bragg markers and no
  measured data, then edits structure and profile parameters and
  recalculates to show the pattern update.
- [Si `pd-neut-tof`](simulate-si-tof.ipynb) – Calculates a time-of-flight neutron
  powder pattern for Si, with the calculation window derived from the
  instrument's TOF calibration and then set explicitly.
- [NaCl `pd-xray`](simulate-nacl-xray.ipynb) – The most minimal example: an X-ray
  powder pattern for NaCl using the default calculation range.

## Single Crystal Diffraction

- [Tb2TiO7 `sc-neut-cwl`](refine-tbti-heidi.ipynb) – Demonstrates structure
  refinement of Tb2TiO7 using constant wavelength neutron single crystal
  diffraction data from HEiDi at FRM II.
- [Taurine `sc-neut-tof`](refine-taurine-senju.ipynb) – Demonstrates structure
  refinement of Taurine using time-of-flight neutron single crystal
  diffraction data from SENJU at J-PARC.

## Pair Distribution Function

- [Ni `pd-neut-cwl`](pdf-ni-npd.ipynb) – Demonstrates a PDF analysis of Ni
  using data collected from a constant wavelength neutron powder
  diffraction experiment.
- [Si `pd-neut-tof`](pdf-si-nomad.ipynb) – Demonstrates a PDF analysis of Si
  using data collected from a time-of-flight neutron powder diffraction
  experiment at NOMAD at SNS.
- [NaCl `pd-xray`](pdf-nacl-xrd.ipynb) – Demonstrates a PDF analysis of NaCl
  using data collected from an X-ray powder diffraction experiment.

## Multiple Data Blocks

- [PbSO4 NPD+XRD](refine-pbso4-joint.ipynb) – Joint fit of PbSO4 using X-ray and
  neutron constant wavelength powder diffraction data.
- [Si Bragg+PDF](joint-si-bragg-pdf.ipynb) – Joint refinement of Si combining Bragg
  diffraction (SEPD) and pair distribution function (NOMAD) analysis. A
  single shared structure is refined simultaneously against both
  datasets.
- [Co2SiO4 Temperature scan](refine-cosio-d20-tscan.ipynb) – Sequential Rietveld
  refinement of Co2SiO4 using constant wavelength neutron powder
  diffraction data from D20 at ILL across a temperature scan.

## Simulated Data

- [LBCO+Si McStas](refine-lbco-si-mcstas.ipynb) – Multi-phase Rietveld refinement of
  La0.5Ba0.5CoO3 with Si impurity using time-of-flight neutron data
  simulated with McStas.
- [BEER McStas](calibrate-beer-ess.ipynb) – Rietveld refinement based on the data
  simulated with McStas for the BEER instrument at ESS.

## Bayesian Analysis

- [LBCO Bayesian (`bumps-dream`)](bayesian-dream-lbco-hrpt.ipynb) – Demonstrates how to
  perform a Bayesian analysis of the La0.5Ba0.5CoO3 crystal structure
  using constant wavelength neutron powder diffraction data from HRPT at
  PSI. Covers the use of Markov Chain Monte Carlo (MCMC) sampling with
  the bumps-DREAM minimizer to explore the posterior distribution of the
  refined parameters, providing insights into parameter uncertainties
  and correlations.
- [LBCO Bayesian Display (`bumps-dream`)](bayesian-dream-display-lbco-hrpt.ipynb) – Shows how to
  reopen the saved Bayesian project produced by the LBCO Bayesian
  tutorial and inspect persisted fit summaries, correlation matrix,
  posterior distribution plots, and predictive checks — without
  rerunning MCMC sampling.
- [LBCO Bayesian (`emcee`)](bayesian-emcee-lbco-hrpt.ipynb) – Two-stage workflow on the
  LBCO HRPT dataset: first a quick local refinement to obtain a point
  estimate and uncertainties, then full posterior sampling with the
  emcee minimizer. Covers credible intervals, parameter correlations,
  and propagation of uncertainty into the calculated diffraction
  pattern.
- [LBCO Bayesian Resume (`emcee`)](bayesian-emcee-resume-lbco-hrpt.ipynb) – Loads a Bayesian
  project that already contains an emcee chain, inspects the posterior,
  and resumes sampling with additional steps. The full project state
  (parameters, chain, plot caches) round-trips through disk. Resuming is
  currently supported only for emcee, not for bumps-DREAM.
- [Tb2TiO7 Bayesian (`emcee`)](bayesian-emcee-tbti-heidi.ipynb) – Another example of a
  Bayesian analysis, focused on the Tb2TiO7 crystal structure using
  constant wavelength neutron single crystal diffraction data from HEiDi
  at FRM II. Similar to the LBCO Bayesian tutorial, it covers MCMC
  sampling to explore the posterior distribution of the refined
  parameters, providing insights into parameter uncertainties and
  correlations in the context of single crystal diffraction data.

## Workshops & Schools

- [DMSC Summer School](fitting-exercise-si-lbco.ipynb) – A workshop tutorial that
  demonstrates a Rietveld refinement of the La0.5Ba0.5CoO3 crystal
  structure using time-of-flight neutron powder diffraction data
  simulated with McStas. This tutorial is designed for the ESS DMSC
  Summer School.

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

- [LBCO `quick` `load`](ed-18.ipynb) – The most minimal example showing
  how to load a previously saved project from a directory and run
  refinement. Useful when a project has already been set up and saved in
  a prior session.
- [LBCO `quick` `code`](ed-2.ipynb) – A minimal example intended as a
  quick reference for users already familiar with the EasyDiffraction
  API or who want to see an example refinement when both the structure
  and experiment are defined directly in code. This tutorial covers a
  Rietveld refinement of the La0.5Ba0.5CoO3 crystal structure using
  constant wavelength neutron powder diffraction data from HRPT at PSI.
- [LBCO `basic` `load`](ed-1.ipynb) – A basic example intended as a
  quick reference for users already familiar with the EasyDiffraction
  API or who want to see how Rietveld refinement of the La0.5Ba0.5CoO3
  crystal structure can be performed when both the structure and
  experiment are loaded from CIF files. Data collected from constant
  wavelength neutron powder diffraction at HRPT at PSI.
- [LBCO `complete`](ed-3.ipynb) – Demonstrates the use of the
  EasyDiffraction API in a simplified, user-friendly manner that closely
  follows the GUI workflow for a Rietveld refinement of the
  La0.5Ba0.5CoO3 crystal structure using constant wavelength neutron
  powder diffraction data from HRPT at PSI. This tutorial provides a
  full explanation of the workflow with detailed comments and
  descriptions of every step, making it suitable for users who are new
  to EasyDiffraction or those who prefer a more guided approach.

## Powder Diffraction

- [Co2SiO4 `pd-neut-cwl`](ed-5.ipynb) – Demonstrates a Rietveld
  refinement of the Co2SiO4 crystal structure using constant wavelength
  neutron powder diffraction data from D20 at ILL.
- [HS `pd-neut-cwl`](ed-6.ipynb) – Demonstrates a Rietveld refinement of
  the HS crystal structure using constant wavelength neutron powder
  diffraction data from HRPT at PSI.
- [Si `pd-neut-tof`](ed-7.ipynb) – Demonstrates a Rietveld refinement of
  the Si crystal structure using time-of-flight neutron powder
  diffraction data from SEPD at Argonne.
- [NCAF `pd-neut-tof`](ed-8.ipynb) – Demonstrates a Rietveld refinement
  of the Na2Ca3Al2F14 crystal structure using two time-of-flight neutron
  powder diffraction datasets (from two detector banks) of the WISH
  instrument at ISIS.

## Single Crystal Diffraction

- [Tb2TiO7 `sg-neut-cwl`](ed-14.ipynb) – Demonstrates structure
  refinement of Tb2TiO7 using constant wavelength neutron single crystal
  diffraction data from HEiDi at FRM II.
- [Taurine `sg-neut-tof`](ed-15.ipynb) – Demonstrates structure
  refinement of Taurine using time-of-flight neutron single crystal
  diffraction data from SENJU at J-PARC.

## Pair Distribution Function (PDF)

- [Ni `pd-neut-cwl`](ed-10.ipynb) – Demonstrates a PDF analysis of Ni
  using data collected from a constant wavelength neutron powder
  diffraction experiment.
- [Si `pd-neut-tof`](ed-11.ipynb) – Demonstrates a PDF analysis of Si
  using data collected from a time-of-flight neutron powder diffraction
  experiment at NOMAD at SNS.
- [NaCl `pd-xray`](ed-12.ipynb) – Demonstrates a PDF analysis of NaCl
  using data collected from an X-ray powder diffraction experiment.

## Multi-Structure & Multi-Experiment Refinement

- [PbSO4 NPD+XRD](ed-4.ipynb) – Joint fit of PbSO4 using X-ray and
  neutron constant wavelength powder diffraction data.
- [Si Bragg+PDF](ed-16.ipynb) – Joint refinement of Si combining Bragg
  diffraction (SEPD) and pair distribution function (NOMAD) analysis. A
  single shared structure is refined simultaneously against both
  datasets.
- [Co2SiO4 Temperature scan](ed-17.ipynb) – Sequential Rietveld
  refinement of Co2SiO4 using constant wavelength neutron powder
  diffraction data from D20 at ILL across a temperature scan.

## Simulated Data

- [LBCO+Si McStas](ed-9.ipynb) – Multi-phase Rietveld refinement of
  La0.5Ba0.5CoO3 with Si impurity using time-of-flight neutron data
  simulated with McStas.
- [BEER McStas](ed-20.ipynb) – Rietveld refinement based on the data
  simulated with McStas for the BEER instrument at ESS.

## Bayesian Analysis

- [LBCO Bayesian](ed-21.ipynb) – Demonstrates how to perform a Bayesian
  analysis of the La0.5Ba0.5CoO3 crystal structure using constant
  wavelength neutron powder diffraction data from HRPT at PSI. This
  tutorial covers the use of Markov Chain Monte Carlo (MCMC) sampling to
  explore the posterior distribution of the refined parameters,
  providing insights into parameter uncertainties and correlations.
- [Tb2TiO7 Bayesian](ed-22.ipynb) – Demonstrates how to perform a
  Bayesian analysis of the Tb2TiO7 crystal structure using constant
  wavelength neutron single crystal diffraction data from HEiDi at FRM
  II. This tutorial covers the use of Markov Chain Monte Carlo (MCMC)
  sampling to explore the posterior distribution of the refined
  parameters, providing insights into parameter uncertainties and
  correlations.

## Workshops & Schools

- [DMSC Summer School](ed-13.ipynb) – A workshop tutorial that
  demonstrates a Rietveld refinement of the La0.5Ba0.5CoO3 crystal
  structure using time-of-flight neutron powder diffraction data
  simulated with McStas. This tutorial is designed for the ESS DMSC
  Summer School.

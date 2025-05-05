---
icon: material/school
---

# :material-school: Tutorials

This section offers a collection of **Jupyter Notebook examples** illustrating
the usage of EasyDiffraction for various tasks. These tutorials act as
**step-by-step guides**, helping users grasp the workflow of diffraction data
analysis within EasyDiffraction.

An instruction on how to run the tutorials is provided in the
[:material-cog-box: Installation & Setup](../installation/index.md#running-tutorials)
section of the documentation.

The tutorials are categorized as follows.

## Basic vs. Advanced

- [LBCO `pd-neut-cwl`](basic_single-fit_pd-neut-cwl_LBCO-HRPT.ipynb) -
  Demonstrates usage of the EasyDiffraction API in a simplified,
  user-friendly manner that closely follows the GUI workflow for a Rietveld
  refinement of La0.5Ba0.5CoO3 crystal structure using constant wavelength
  neutron powder diffraction data from HRPT at PSI.
- [PbSO4 `pd-neut-xray-cwl`](advanced_joint-fit_pd-neut-xray-cwl_PbSO4.ipynb) -
  Demonstrates a more flexible and advanced approach to use the
  EasyDiffraction library, intended for users more comfortable with Python
  programming. This tutorial covers a Rietveld refinement of PbSO4 crystal
  structure based on the joint fit of both X-ray and neutron diffraction data.

## Standard Diffraction

- [HS `pd-neut-cwl`](cryst-struct_pd-neut-cwl_HS-HRPT.ipynb) -
  Demonstrates a Rietveld refinement of HS crystal structure using constant
  wavelength neutron powder diffraction data from HRPT at PSI.
- [Si `pd-neut-tof`](cryst-struct_pd-neut-tof_Si-SEPD.ipynb) -
  Demonstrates a Rietveld refinement of Si crystal structure using
  time-of-flight neutron powder diffraction data from SEPD at Argonne.
- [NCAF `pd-neut-tof`](cryst-struct_pd-neut-tof_NCAF-WISH.ipynb) -
  Demonstrates a Rietveld refinement of Na2Ca3Al2F14 crystal structure using
  time-of-flight neutron powder diffraction data from WISH at ISIS.

## Pair Distribution Function (PDF)

- [Ni `pd-neut-cwl`](pdf_pd-neut-cwl_Ni.ipynb) -
  Demonstrates a PDF analysis of Ni based on data collected from a constant
  wavelength neutron powder diffraction experiment.
- [Si `pd-neut-tof`](pdf_pd-neut-tof_Si-NOMAD.ipynb) -
  Demonstrates a PDF analysis of Si based on data collected from a
  time-of-flight neutron powder diffraction experiment at NOMAD at SNS.
- [NaCl `pd-xray`](pdf_pd-xray_NaCl.ipynb) -
  Demonstrates a PDF analysis of NaCl based on data collected from an X-ray
  powder diffraction experiment.

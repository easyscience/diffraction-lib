# Concept

Typical data processing in a diffraction experiment consists of three
main steps:  
**data acquisition**, **data reduction**, and **data analysis**.

```mermaid
flowchart LR
    a(Data Acquisition)
    b(Data Reduction)
    c(Data Analysis)
    a --> b
    b --> c
```

## Data Acquisition

Data acquisition involves collecting raw data from the diffractometer
(also referred to as the instrument) during a neutron or X-ray
diffraction experiment.

The data is recorded by a detector that measures the intensity of the
diffracted radiation as a function of angle or time. The radiation is
scattered by the crystalline specimen (also called the sample), whose
structural properties are being studied.

<!-- prettier-ignore-start -->
![](../assets/images/user-guide/data-acquisition_instrument.png){ width="450", loading=lazy }
/// caption
An illustration of the data acquisition step, where raw data is collected
by a 2D detector. The studied sample originates from Mars. 
Credits: DOI 10.1126/science.1238932
///
<!-- prettier-ignore-end -->

<!-- prettier-ignore-start -->
![](../assets/images/user-guide/data-acquisition_2d-raw-data.jpg){ width="400", loading=lazy }
/// caption
A 2D diffraction pattern collected by the detector. 
Credits: DOI 10.1126/science.1238932
///
<!-- prettier-ignore-end -->

## Data Reduction

Data reduction involves processing the raw data to remove background
noise, correct for instrumental effects, and convert the data into a
more usable format. The goal is to produce a clean and reliable dataset
suitable for analysis.

<!-- prettier-ignore-start -->
![](../assets/images/user-guide/data-reduction_1d-pattern.png){ width="450", loading=lazy }
/// caption
An illustration of a 1D diffraction pattern reduced from the measured 2D data. 
Credits: DOI 10.1126/science.1238932
///
<!-- prettier-ignore-end -->

## Data Analysis

Data analysis uses the reduced data to extract meaningful information
about the crystallographic structure. This may include determining the
crystal or magnetic structure, identifying phases, performing
quantitative analysis, etc.

Analysis often involves comparing experimental data with data calculated
from a crystallographic model to validate and interpret the results. For
powder diffraction, techniques such as Rietveld or Le Bail refinement
may be used.

In EasyDiffraction, we focus on this **model-dependent analysis**. A
model is built using prior knowledge of the system, and its parameters
are optimized to achieve the best agreement between experimental and
calculated diffraction data.

By "model", we usually refer to a **crystallographic model** of the
sample. This includes unit cell parameters, space group, atomic
positions, thermal parameters, and more. However, the term "model" also
encompasses experimental aspects such as instrumental resolution,
background, peak shape, etc. Therefore, EasyDiffraction separates the
model into two parts: the **structure** and the **experiment**.

The aim of data analysis is to refine the structural parameters of the
sample by minimizing the difference (or **residual**) between the
experimental and calculated data — and this is exactly where
EasyDiffraction comes into play.

## Least-Squares and Bayesian Analysis

Most refinements use least-squares minimization: EasyDiffraction varies
the selected free parameters and reports the best-fit values, standard
uncertainties, R-factors, and goodness-of-fit metrics. This is the usual
workflow for routine model refinement and is available through
minimizers such as `lmfit`, `dfols`, and several `bumps` optimizers.

Bayesian analysis answers a different question. Instead of reporting
only one best-fit point and a covariance estimate, a Bayesian sampler
explores the posterior distribution of the free parameters. This gives
credible intervals, correlations, posterior-predictive patterns, and
diagnostics such as r-hat and effective sample size. EasyDiffraction
currently exposes Bayesian workflows through `bumps (dream)` and
`emcee`; their posterior and predictive arrays are stored in
`analysis/results.h5` when available.

<!-- prettier-ignore-start -->
![](../assets/images/user-guide/data-analysis_refinement.png){ width="450", loading=lazy }
/// caption
An illustration of the data analysis step: the experimental data (blue)
is compared to the calculated data (red), and the residual (gray) is minimized. 
Credits: DOI 10.1126/science.1238932
///
<!-- prettier-ignore-end -->

<!-- prettier-ignore-start -->
![](../assets/images/user-guide/data-analysis_model.png){ width="450", loading=lazy }
/// caption
An example of a crystal structure model of the studied sample.
///
<!-- prettier-ignore-end -->

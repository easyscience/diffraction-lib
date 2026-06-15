---
title: minimizer
---

# :material-graph-outline: minimizer

## :material-tag: burn_in_steps { #minimizer-burn-in-steps }

| Access                                    | Source                    |
| ----------------------------------------- | ------------------------- |
| minimizer.burn_in_steps                   | [code][0]{:.label-cif}    |
| \_minimizer.burn_in_steps                 | [Edi][0]{:.label-cif}     |
| \_easydiffraction_minimizer.burn_in_steps | [coreCIF][0]{:.label-cif} |

Sampler iterations discarded as warm-up.

## :material-tag: initialization_method { #minimizer-initialization-method }

| Access                                            | Source                    |
| ------------------------------------------------- | ------------------------- |
| minimizer.initialization_method                   | [code][0]{:.label-cif}    |
| \_minimizer.initialization_method                 | [Edi][0]{:.label-cif}     |
| \_easydiffraction_minimizer.initialization_method | [coreCIF][0]{:.label-cif} |

Sampler initialization method. Supported values depend on the minimizer;
available values include `latin_hypercube`, `ball`, `uniform`, and
`prior`.

## :material-arrow-collapse-right: max_iterations { #minimizer-max-iterations }

| Access                                     | Source                    |
| ------------------------------------------ | ------------------------- |
| minimizer.max_iterations                   | [code][0]{:.label-cif}    |
| \_minimizer.max_iterations                 | [Edi][0]{:.label-cif}     |
| \_easydiffraction_minimizer.max_iterations | [coreCIF][0]{:.label-cif} |

Maximum solver iterations.

## :material-tag: parallel_workers { #minimizer-parallel-workers }

| Access                                       | Source                    |
| -------------------------------------------- | ------------------------- |
| minimizer.parallel_workers                   | [code][0]{:.label-cif}    |
| \_minimizer.parallel_workers                 | [Edi][0]{:.label-cif}     |
| \_easydiffraction_minimizer.parallel_workers | [coreCIF][0]{:.label-cif} |

Worker count; 0 uses all available CPUs.

## :material-tag: population_size { #minimizer-population-size }

| Access                                      | Source                    |
| ------------------------------------------- | ------------------------- |
| minimizer.population_size                   | [code][0]{:.label-cif}    |
| \_minimizer.population_size                 | [Edi][0]{:.label-cif}     |
| \_easydiffraction_minimizer.population_size | [coreCIF][0]{:.label-cif} |

Number of chains or walkers.

## :material-tag: proposal_moves { #minimizer-proposal-moves }

| Access                                     | Source                    |
| ------------------------------------------ | ------------------------- |
| minimizer.proposal_moves                   | [code][0]{:.label-cif}    |
| \_minimizer.proposal_moves                 | [Edi][0]{:.label-cif}     |
| \_easydiffraction_minimizer.proposal_moves | [coreCIF][0]{:.label-cif} |

Single emcee proposal move; move mixtures are not persisted in v1.

## :material-tag: random_seed { #minimizer-random-seed }

| Access                                  | Source                    |
| --------------------------------------- | ------------------------- |
| minimizer.random_seed                   | [code][0]{:.label-cif}    |
| \_minimizer.random_seed                 | [Edi][0]{:.label-cif}     |
| \_easydiffraction_minimizer.random_seed | [coreCIF][0]{:.label-cif} |

Random seed; None uses a system-derived seed.

## :material-tag: sampling_steps { #minimizer-sampling-steps }

| Access                                     | Source                    |
| ------------------------------------------ | ------------------------- |
| minimizer.sampling_steps                   | [code][0]{:.label-cif}    |
| \_minimizer.sampling_steps                 | [Edi][0]{:.label-cif}     |
| \_easydiffraction_minimizer.sampling_steps | [coreCIF][0]{:.label-cif} |

Total sampler iterations per chain.

## :material-tag: thinning_interval { #minimizer-thinning-interval }

| Access                                        | Source                    |
| --------------------------------------------- | ------------------------- |
| minimizer.thinning_interval                   | [code][0]{:.label-cif}    |
| \_minimizer.thinning_interval                 | [Edi][0]{:.label-cif}     |
| \_easydiffraction_minimizer.thinning_interval | [coreCIF][0]{:.label-cif} |

Sampler thinning interval.

## :material-shape: type { #minimizer-type }

| Access                           | Source                    |
| -------------------------------- | ------------------------- |
| minimizer.type                   | [code][0]{:.label-cif}    |
| \_minimizer.type                 | [Edi][0]{:.label-cif}     |
| \_easydiffraction_minimizer.type | [coreCIF][0]{:.label-cif} |

Minimizer category type. Supported values include `lmfit`,
`lmfit (leastsq)`, `lmfit (least_squares)`, `dfols`, `bumps`,
`bumps (lm)`, `bumps (dream)`, `bumps (amoeba)`, `bumps (de)`, and
`emcee`.

<!-- prettier-ignore-start -->
[0]: #
<!-- prettier-ignore-end -->

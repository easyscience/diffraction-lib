# :material-graph-outline: minimizer

## :material-tag: burn_in_steps { #minimizer-burn-in-steps }

| Access                    | Source                     |
| ------------------------- | -------------------------- |
| \_minimizer.burn_in_steps | [Edifa][0]{:.label-cif} |

Sampler iterations discarded as warm-up.

## :material-tag: initialization_method { #minimizer-initialization-method }

| Access                            | Source                     |
| --------------------------------- | -------------------------- |
| \_minimizer.initialization_method | [Edifa][0]{:.label-cif} |

Sampler initialization method. Supported values depend on the minimizer;
available values include `latin_hypercube`, `ball`, `uniform`, and
`prior`.

## :material-arrow-collapse-right: max_iterations { #minimizer-max-iterations }

| Access                     | Source                     |
| -------------------------- | -------------------------- |
| \_minimizer.max_iterations | [Edifa][0]{:.label-cif} |

Maximum solver iterations.

## :material-tag: parallel_workers { #minimizer-parallel-workers }

| Access                       | Source                     |
| ---------------------------- | -------------------------- |
| \_minimizer.parallel_workers | [Edifa][0]{:.label-cif} |

Worker count; 0 uses all available CPUs.

## :material-tag: population_size { #minimizer-population-size }

| Access                      | Source                     |
| --------------------------- | -------------------------- |
| \_minimizer.population_size | [Edifa][0]{:.label-cif} |

Number of chains or walkers.

## :material-tag: proposal_moves { #minimizer-proposal-moves }

| Access                     | Source                     |
| -------------------------- | -------------------------- |
| \_minimizer.proposal_moves | [Edifa][0]{:.label-cif} |

Single emcee proposal move; move mixtures are not persisted in v1.

## :material-tag: random_seed { #minimizer-random-seed }

| Access                  | Source                     |
| ----------------------- | -------------------------- |
| \_minimizer.random_seed | [Edifa][0]{:.label-cif} |

Random seed; None uses a system-derived seed.

## :material-tag: sampling_steps { #minimizer-sampling-steps }

| Access                     | Source                     |
| -------------------------- | -------------------------- |
| \_minimizer.sampling_steps | [Edifa][0]{:.label-cif} |

Total sampler iterations per chain.

## :material-tag: thinning_interval { #minimizer-thinning-interval }

| Access                        | Source                     |
| ----------------------------- | -------------------------- |
| \_minimizer.thinning_interval | [Edifa][0]{:.label-cif} |

Sampler thinning interval.

## :material-shape: type { #minimizer-type }

| Access           | Source                     |
| ---------------- | -------------------------- |
| \_minimizer.type | [Edifa][0]{:.label-cif} |

Minimizer category type. Supported values include `lmfit`,
`lmfit (leastsq)`, `lmfit (least_squares)`, `dfols`, `bumps`,
`bumps (lm)`, `bumps (dream)`, `bumps (amoeba)`, `bumps (de)`, and
`emcee`.

<!-- prettier-ignore-start -->
[0]: #
<!-- prettier-ignore-end -->

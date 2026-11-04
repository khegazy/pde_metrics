---
type: "EXP"
kind: "benchmark suite or dataset"
related: ["mse", "mae", "rmse", "nrmse", "max_error", "h1_seminorm", "spectrum_l2", "kinetic_energy", "enstrophy", "palinstrophy", "issues/004", "docs/datasets/reynolds_ladder_2d.md", "issues/078"]
seen_in: "Takamoto et al. 2022, NeurIPS 35 Datasets and Benchmarks, 1596-1611 (PDEBench), Sect. 3.3, 4.3, App. B; Ohana et al. 2024, NeurIPS 37 Datasets and Benchmarks, 44989-45037 (The Well), Sect. 4, App. E.3"
doi: "10.52202/068431-0117"
found_by: "update_metric_eval_principles, 2026-11-03"
---

# EXP: Model rollouts against the solver over many initial conditions

## What the experiment is

A test set of many trajectories of one problem, each started from a different initial
condition and solved by the reference solver, and a surrogate rolled out autoregressively
from each initial state. Every pairwise metric is computed between the rollout and the solver
at each prediction step, then averaged over the test trajectories, and reported both at one
step and as a curve against prediction step. This is how the two machine-learning benchmarks
these metrics come from evaluate a model:

- **PDEBench** (Takamoto et al. 2022) defines RMSE, nRMSE, maximum error, the RMSE of
  conserved quantities, the RMSE on the boundary and the RMSE in low, middle and high Fourier
  bands (Sect. 3.3, formulas in App. B). Its datasets hold 10,000 samples per 1-D problem and
  for 2-D Darcy flow, 1,000 for the 2-D problems and 100 for 3-D compressible Navier-Stokes
  (Table 1), split 90% for training and 10% for testing (Sect. 4.1). Section 4.3 plots the
  RMSE at each unrolled time step (Fig. 5).
- **The Well** (Ohana et al. 2024) reports VRMSE, the RMSE over the root-mean-square
  fluctuation of the truth about its spatial mean, per physical field and then averaged, and a
  binned spectral error in three logarithmically spaced wavenumber bands (App. E.3; Sect. 4.1,
  Fig. 6). Its trajectories are split 0.8/0.1/0.1 along initial conditions (Sect. 3), and
  rollouts start from the beginning of each simulation and are scored as VRMSE averaged over
  prediction-step windows 6:12 and 13:30 (Sect. 4, Table 3).

The kinet solver could produce the test set: the doubly periodic shear configuration of
`kinet_re5e4` with randomised initial perturbations, several tens of trajectories, each a few
hundred stored steps.

## What it tests

It tests the metrics on the failures a trained surrogate actually makes, which accumulate
over prediction steps and differ from case to case, instead of on hypothesised damage applied
to one snapshot. It gives each metric the two objects its field reports and that no existing
experiment here can produce: a mean and spread over many independent initial conditions, and
a growth curve against prediction step. For the single-field metrics (`kinetic_energy`,
`enstrophy`, `palinstrophy`), it gives the rollout's time series against the solver's, which is
how a decaying two-dimensional flow is compared (Boffetta & Ecke 2012, Eqs. 5-6, p. 430,
state the decay rates such series follow).

## Metrics it would test

`mse`, `mae`, `rmse`, `nrmse` (PDEBench's definition and the planned VRMSE sibling of The Well),
`max_error`, `h1_seminorm` (the relative H1 error that neural-operator work reports: Li et al.
2022 train with relative H1 and H2 losses and report L2, H1 and H2 test errors on Kolmogorov
flow, Sect. 3 Eqs. 3-4, App. A.3 Table 3), `spectrum_l2` beside The Well's binned spectral
error, and `kinetic_energy`, `enstrophy` and `palinstrophy` as time series. Every other
pairwise metric can run on it too.

## Why it is helpful

The forecast pairs (`forecast_re5e4`) are the only model output here: one surrogate, two starting
times, ten prediction steps each. That is enough for an error-against-step curve on two cases,
not for the mean over initial conditions that both benchmarks report, nor for the spread that
says whether one metric separates two models more reliably than another. Issue 004 asks for
independent realisations for a different reason (an unrelated field to score against); this
experiment needs them as test cases. Without it, a card can say how its metric orders a
degradation ladder but not how it would rank surrogates, which is what a user from PDEBench or
The Well would look for first.

## Cost and requirements

Several tens of solver runs at 256^2 (each the cost of one `kinet_re5e4`-like run, shortened to
the rollout horizon), a trained surrogate (none exists in the repository; issues 071 and 083 also
wait on one), and the forecast-pair reader (`fmeval/data/forecast.py`) generalised to many trajectories.
Alternatively, a dataset of The Well with many trajectories (Table 1 of Ohana et al.: for
example 1,120 for `shear_flow`, 10,000 for `euler_multi_quadrants`) and a published baseline
model's rollouts, read through the existing Well-format reader; licence to be checked per
dataset.

## References

- Takamoto, M., Praditia, T., Leiteritz, R., MacKinlay, D., Alesiani, F., Pflüger, D. &
  Niepert, M. (2022). PDEBench: An extensive benchmark for scientific machine learning.
  *Advances in Neural Information Processing Systems 35* (Datasets and Benchmarks Track),
  1596-1611. <https://doi.org/10.52202/068431-0117>; arXiv:2210.07182 (read in full, v7; section,
  table and figure numbers counted from the arXiv source).
- Ohana, R., McCabe, M., et al. (2024). The Well: a large-scale collection of diverse physics
  simulations for machine learning. *Advances in Neural Information Processing Systems 37*
  (Datasets and Benchmarks Track), 44989-45037. <https://doi.org/10.52202/079017-1430>;
  arXiv:2412.00568 (read in full, v2).
- Li, Z., Liu-Schiaffini, M., Kovachki, N., Liu, B., Azizzadenesheli, K., Bhattacharya, K.,
  Stuart, A. & Anandkumar, A. (2022). Learning chaotic dynamics in dissipative systems.
  *Advances in Neural Information Processing Systems 35*, 16768-16781.
  <https://doi.org/10.52202/068431-1220>; arXiv:2106.06898 (read in full).
- Boffetta, G. & Ecke, R. E. (2012). Two-dimensional turbulence. *Annual Review of Fluid
  Mechanics* 44, 427-451. <https://doi.org/10.1146/annurev-fluid-120710-101240> (read in full).

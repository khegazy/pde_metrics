# The forecast runs at three resolutions are not yet a grid-refinement sequence

**Category:** deferred functionality
**Priority:** medium
**Status:** open. Needs the provenance of the predictions before anything is computed.

## Context

`forecast_re5e4` reads three runs of real forecasts of the Re = 5e4 flow, at $256^2$, $128^2$
and $64^2$, with ten prediction steps at the same physical lead times
(`docs/datasets/reynolds_ladder_2d.md`, "Forecast pairs"). They look like a grid-refinement
sequence with ratio $r = 2$, from which an observed order of accuracy would follow,

$$
\hat{p} = \frac{\ln \left( \lVert E_{rh} \rVert / \lVert E_{h} \rVert \right)}{\ln r}, \tag{1}
$$

with $E_h$ the error against the exact solution on the grid of spacing $h$ (Roy 2005, *Journal
of Computational Physics* 205(1), 131–156, <https://doi.org/10.1016/j.jcp.2004.10.036>,
Sect. 2.5, Eq. 8, as read in `metrics/max_error/research_notes.md`; not reopened here).

The dataset page explains why the three runs are not that sequence as they stand. In short: the
$256^2$ run's target is the reference itself, so its error is not a discretisation error; only
a discretisation has an order, and who produced the predictions is not recorded; and the error
leaves the asymptotic range along the forecast, because the flow is chaotic.

## Evidence

Run `comparison_1793779575` (on `$PSCRATCH/fluid_metrics_results/`, a smoke run of this
branch): `python evaluate.py metrics=[mse,nrmse,enstrophy] dataset=forecast_re5e4
analysis_grid.resolution=64`. Equation (1) applied to the RMSE (square root of `mse`) of each
run against its own target, on the common $64^2$ grid, at the first and last of the ten
prediction steps:

| Field | Start t | $\hat{p}$, 64 against 128, first step | last step | $\hat{p}$, 128 against 256, first step | last step |
|---|---|---|---|---|---|
| density | 0 | 1.73 | 0.97 | 7.40 | 1.41 |
| density | 1.13 | 1.97 | 1.16 | 8.03 | 7.24 |
| velocity | 0 | 1.55 | 0.47 | 7.93 | 0.07 |
| velocity | 1.13 | 1.44 | 0.81 | 7.79 | 6.08 |
| vorticity | 0 | 1.42 | 0.14 | 7.83 | 0.28 |
| vorticity | 1.13 | 1.28 | 0.51 | 7.70 | 5.78 |

The coarse targets differ from the $256^2$ reference, block-averaged to $64^2$, by at most
$8 \times 10^{-6}$ rms in density at the first, fifth and last steps (measured from the files),
below every coarse-run RMSE behind the table except the density at the first step of the first
forecast at $128^2$ ($6.8 \times 10^{-6}$), so scoring against the reference instead changes the coarse pair's
$\hat{p}$ little there (1.79 instead of 1.73 for density at that step).

## What would settle it

1. Kareem confirms who produced each run's predictions. If a solver on the coarser grid, the
   two coarse runs scored against the $256^2$ reference are a two-grid sequence with a known
   reference, and Equation (1) applies at short lead; if a trained model, refinement does not
   apply (`docs/ideas/infrastructure/grid_convergence.md`, Pitfalls).
2. If it applies: a computation in `fmeval/analysis.py` of $\hat{p}$ per (metric, field,
   forecast start, prediction step) from rows that carry `param_resolution`, `lead_step` and
   `lead_time`, scored against one reference (the $256^2$ target, which needs the reader to pair
   a coarse prediction with the fine target), with the asymptotic range checked rather than
   assumed, for instance by requiring the order to be steady over the first steps.

## Related

`fmeval/data/forecast.py`; `docs/ideas/infrastructure/grid_convergence.md`.

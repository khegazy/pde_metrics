# Datasets

Every metric here is tested by damaging a trusted field in controlled steps and scoring the
damaged versions, and, on one dataset, by scoring real predictions against their targets. These
pages describe the trusted fields. There is one page per physical
problem, and each page lists every configuration of that problem: a different Reynolds number,
a different file format, or a development subset.

Two kinds of dataset appear:

- **Simulated.** The output of a fluid solver, read from a file. Only these are evidence about
  a flow.
- **Computed.** A closed-form solution or a generated field, evaluated on the fly whenever a
  frame is read. These check the evaluation harness against an answer known in advance, and
  a computed dataset ranks below every simulated one. A metric's page may cite two of them,
  and its run summary then names the kind of claim the numbers support:
  `synthetic_ensemble` as a **calibrated null**, for the probabilistic metrics, and
  `sod_shock_tube` as an **analytic check**, for the metrics that need a shock or pressure.
  Neither is evidence about turbulence. `taylor_green_2d` and `advecting_blobs` are never cited.

| Problem | Configurations | Kind | Grid | Boundaries |
|---|---|---|---|---|
| [Doubly periodic weakly compressible flow](reynolds_ladder_2d.md) | `kinet_re5e4`, `kinet_re5e4_dev`, `well_re5e4`, `kinet_re5e4_512`, `kinet_re1e6`, `forecast_re5e4` | simulated; `forecast_re5e4` pairs real predictions with their targets | $256^2$; $512^2$ in `kinet_re5e4_512`; $1024^2$ at $\mathrm{Re} = 10^6$; the forecasts also $128^2$ and $64^2$ | periodic |
| [Decaying two-dimensional isotropic turbulence](decaying_isotropic_2d.md) | `kinet_hit_re12p5k`, `kinet_hit_re25k`, `kinet_hit_re50k`, each with ten realisations by `dataset.trajectory` | simulated; not yet evidence | $256^2$ | periodic |
| [Turbulent radiative mixing layer](turbulent_radiative_layer_2d.md) | `well_radiative_layer_tcool0p32` | simulated (The Well, Athena++); not yet evidence | $128 \times 384$ | periodic $x$, open $y$ (Neumann) |
| [Sod shock tube](sod_shock_tube.md) | `sod_shock_tube`, `kinet_sod_gamma1p4`, `kinet_sod_gamma2` | `sod_shock_tube` computed: exact solution of the Euler equations; the kinet runs simulated, not yet evidence | 2048 cells, 1D; the kinet runs 3001 × 5 | Neumann walls; the kinet runs periodic across the tube |
| [Supersonic flow past a cylinder](supersonic_cylinder.md) | none: the one run stopped at step 155 of 1000 | simulated, not readable | 500 × 300 | inlet and Neumann |
| [Taylor–Green vortex](taylor_green_vortex.md) | `taylor_green_2d` | computed: exact solution of the Navier–Stokes equations | $256^2$ | periodic |
| [Synthetic exchangeable ensemble](synthetic_ensemble.md) | `synthetic_ensemble` | computed: a formula and a seed | $64^2$ | periodic |
| [Advecting Gaussian blobs](advecting_blobs.md) | `advecting_blobs` | computed: exact solution of passive advection, a test bed for time-dependent degradations | $64^2$ | periodic |

**Boundaries.** Each dataset states the boundary of each axis. On an axis that is not
periodic, the degradations act on the field extended across the boundary by that boundary's
rule. A metric that needs a periodic domain is not run on such a dataset.

**Choosing a dataset.** Pass the name of a configuration to an evaluation, for example
`python evaluate.py metrics=[mse] dataset=sod_shock_tube`.

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
  a computed dataset ranks below every simulated one.

Every configuration a metric's page may cite is in `evidence_datasets`
(`configs/cards/default.yaml`) with a label naming the kind of claim a run on it supports, and
the page's run summary quotes that label beside the numbers: `synthetic_ensemble` is a
**calibrated null**, `random_field` a **known-statistics null**, and the other computed
configurations **analytic checks**, none of them evidence about turbulence. Every dataset built
for the evaluation plan is registered (`docs/decisions.md`, "Every evaluation dataset is
evidence, under its label"), and so is `advecting_blobs`, the harness's test bed, as an analytic
check. Two are not: `taylor_green_2d`, whose frames are scalar multiples of one another, and
`well_radiative_layer_tcool0p32`, which no test of an existing metric needs. A registered dataset no metric has
been run on yet shows as *not yet run* on every metric's page.

| Problem | Configurations | Kind | Grid | Boundaries |
|---|---|---|---|---|
| [Doubly periodic weakly compressible flow](reynolds_ladder_2d.md) | `kinet_re5e4`, `kinet_re5e4_dev`, `well_re5e4`, `kinet_re5e4_512`, `kinet_re1e6`, `forecast_re5e4`, `kinet_shear_layer_refinement`, `kinet_shear_layer_ensemble` | simulated; `forecast_re5e4` pairs real predictions with their targets; `kinet_shear_layer_refinement` a coarser run against the $512^2$ run on nested cells; `kinet_shear_layer_ensemble` 16 perturbed runs against a 17th from each of three start states | $256^2$; $512^2$ in `kinet_re5e4_512`; $1024^2$ at $\mathrm{Re} = 10^6$; the forecasts also $128^2$ and $64^2$; $128^2$ and $256^2$ against $512^2$ in the refinement | periodic |
| [Decaying two-dimensional isotropic turbulence](decaying_isotropic_2d.md) | `kinet_hit_re12p5k`, `kinet_hit_re25k`, `kinet_hit_re50k`, each with ten realisations by `dataset.trajectory` | simulated | $256^2$ | periodic |
| [Turbulent radiative mixing layer](turbulent_radiative_layer_2d.md) | `well_radiative_layer_tcool0p32` | simulated (The Well, Athena++); not yet evidence | $128 \times 384$ | periodic $x$, open $y$ (Neumann) |
| [Sod shock tube](sod_shock_tube.md) | `sod_shock_tube`, `kinet_sod_gamma1p4`, `kinet_sod_gamma2`, `kinet_sod_refinement` | `sod_shock_tube` computed: exact solution of the Euler equations; the kinet runs simulated; `kinet_sod_refinement` a grid sequence, each run scored against the exact solution on its own nodes | 2048 cells, 1D; the kinet runs 3001 × 5; the sequence 751, 1501, 3001 × 5 | Neumann walls; the kinet runs periodic across the tube |
| [Viscous Burgers' equation, one-dimensional](burgers.md) | `burgers` | computed: exact Cole–Hopf solution, with a second-order scheme as the candidate of a grid-refinement sequence | 256 cells, 1D; the sequence 64 to 512 | periodic |
| [Sedov–Taylor blast wave, cylindrical](sedov_taylor.md) | `sedov_taylor` | computed: exact similarity solution of the Euler equations; a circular shock oblique to the grid at every angle | $128^2$ | Neumann |
| [Noh implosion, cylindrical](noh.md) | `noh` | computed: exact solution of the Euler equations; a circular shock of constant strength | $128^2$ | Neumann |
| [Supersonic flow past a cylinder](supersonic_cylinder.md) | `kinet_supersonic_cylinder`: the bow shock, in a window upstream of the body | simulated | the run 500 × 300; the window 144 × 288 | Neumann: the inlet (uniform, so exact) and three cuts |
| [Taylor–Green vortex](taylor_green_vortex.md) | `taylor_green_2d`, `helmholtz_mixture_2d`, `kinet_taylor_green_diffusive`, `kinet_taylor_green_fixed_mach` | computed: exact solution of the Navier–Stokes equations, not evidence; `helmholtz_mixture_2d` the vortex plus an exact acoustic mode, its solenoidal and dilatational parts known; the `kinet_taylor_green_*` grid sequences simulated, each run scored against the exact solution on its own cells | $256^2$; $64^2$ in `helmholtz_mixture_2d`; $64^2$ to $512^2$ in the grid sequences | periodic |
| [Synthetic exchangeable ensemble](synthetic_ensemble.md) | `synthetic_ensemble` | computed: a formula and a seed | $64^2$ | periodic |
| [Advecting Gaussian blobs](advecting_blobs.md) | `advecting_blobs`, `feature_population`, `transport_pairs` | computed: exact solution of passive advection, a test bed for time-dependent degradations; `feature_population` bumps, vortices and fronts with known answers; `transport_pairs` a density pair at an exactly known Wasserstein distance | $64^2$; $128^2$ in `feature_population` | periodic |
| [Periodic random fields with known statistics](random_field.md) | `random_field`, with its other families as reader options | computed: Gaussian and non-Gaussian random fields of prescribed spectrum with exact increment statistics | $256^2$ | periodic |

**Boundaries.** Each dataset states the boundary of each axis. On an axis that is not
periodic, the degradations act on the field extended across the boundary by that boundary's
rule. A metric that needs a periodic domain is not run on such a dataset.

**Choosing a dataset.** Pass the name of a configuration to an evaluation, for example
`python evaluate.py metrics=[mse] dataset=sod_shock_tube`.

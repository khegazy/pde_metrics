# Isentropic vortex

!!! note "Simulated, scored against the computed answer: a grid sequence"
    `kinet_isentropic_vortex_mu1em5` and `kinet_isentropic_vortex_mu1em7` are runs of kinet's
    finite-volume solver on several grids, each scored against the exact solution on its own
    cells, so every number is that run's error. Both are registered as evidence of a solver's
    observed order of accuracy, and of nothing about turbulence.

## The problem

A vortex is carried by a uniform flow across a doubly periodic box. In the frame moving with
the flow it is a steady solution of the compressible Euler equations: the pressure gradient
holds the swirl on its circles, and the entropy $p/\rho^\gamma$ is the same everywhere, which is
why the vortex is called isentropic. So the exact solution at any time is the initial field
moved by the flow's velocity times the time. It is the standard test of a compressible solver's
order of accuracy on a smooth flow (Spiegel, Huynh & DeBonis 2015), first used by Shu to compare
high-order schemes with a second-order one (as Spiegel et al. record, Sect. IV.A). The vortex
is smooth, so a second-order scheme's error should fall as the square of the cell size.

## Variations of this problem in the repository

| Configuration | What it is | Readable here |
|---|---|---|
| `kinet_isentropic_vortex_mu1em5` | kinet's case with its own viscosity $\mu = 10^{-5}$, on $64^2$, $128^2$ and $256^2$ cells, at $t = 10$, one period of the box; chosen with `dataset.trajectory=N64`, `N128`, `N256` | Yes, converted (5.6 MB) |
| `kinet_isentropic_vortex_mu1em7` | The same case at $\mu = 10^{-7}$ on $256^2$ and $512^2$ cells at $t = 2.5$, a quarter period; `N256`, `N512` | Yes, converted (21.0 MB) |

The files are under `/global/cfs/cdirs/m4790/Data/kinet/isentropic_vortex/compressible_fluids/`,
in `Pr-71en2_vuy-1.4_visc-1en5/` and `Pr-71en2_vuy-1.4_visc-1en7/`. Each holds the run's initial
condition and its last frame, density, velocity and the absolute pressure the solver writes. A
fifth run, $512^2$ at $\mu = 10^{-5}$ to $t = 2.5$, is not converted (below). No dynamics figure is
drawn: each configuration evaluates one frame per run, and the vortex at its last time is the
initial vortex moved back to its start (or a quarter of the way round).

## The runs

kinet's case `isentropic_vortex/default`, run by its finite-volume PonD solver (16 discrete
velocities, kinet's DUGKS transport with MP5 reconstruction, Courant number 0.2, an adaptive time step, Prandtl number 0.71), on $[0, 10]^2$, periodic in both
directions, cell $i$ centred at $(i + \tfrac12) L/N$. The solver writes the case's own physical
time and velocity; its files label them as steps and cells per step, which is wrong for this
solver (`docs/datasets/logs/kinet_runs/shocks_2d/checks/facts_fields_clock_boundaries.txt`). The
runs, their commands, and the job's checks are archived under
`docs/datasets/logs/kinet_runs/shocks_2d/`.

The solver's viscosity cannot be set to zero, while the exact solution is inviscid. At the case's
$\mu = 10^{-5}$ the order measured by the job between $256^2$ and $512^2$ at $t \approx 2.5$ falls to
0.9 to 1.6, against about 2 on the coarser pairs: on the finer grid the run's physical decay is
no longer small beside its discretisation error. Rerun at $\mu = 10^{-7}$, the same pair gives
1.94 to 2.00. So the dataset holds the two sequences whose errors are discretisation errors:
$64^2$ to $256^2$ at $\mu = 10^{-5}$, and $256^2$ and $512^2$ at $\mu = 10^{-7}$. The $512^2$ run at
$\mu = 10^{-5}$ is left out: it shares no saved time with the $256^2$ run (its end time is 2.5,
theirs 10), and against $256^2$ it measures the viscous mismatch, not the scheme.

## Equations

### Governing equations

The two-dimensional Euler equations of an ideal gas with $\gamma = 1.4$, in conservation form,
are equation (1) of `docs/datasets/sod_shock_tube.md` with the $y$-momentum added. The runs add
a viscosity, which the exact solution below does not have.

### The vortex

Spiegel, Huynh & DeBonis (2015, Sect. IV.A.1) superimpose on a uniform flow a perturbation of
velocity and temperature built from the Gaussian

$$
\Omega = \beta_S\, e^{f}, \qquad f = -\frac{1}{2\sigma^2}\left[\left(\frac{\bar x}{R}\right)^2
  + \left(\frac{\bar y}{R}\right)^2\right] \tag{1}
$$

(their Eqs. 20 and 21, with $\bar x = x - x_c$, $\bar y = y - y_c$ the distance from the vortex
centre, their Eq. 24), as

$$
\delta v_x = -\frac{\bar y}{R}\,\Omega, \qquad \delta v_y = \frac{\bar x}{R}\,\Omega, \qquad
\delta T = -\frac{(\gamma - 1)\,\Omega^2}{2} \tag{2}
$$

(their Eq. 22), and set $\rho = (1 + \delta T)^{1/(\gamma-1)}$ and
$p = (1 + \delta T)^{\gamma/(\gamma-1)}/\gamma$ (their Eq. 23), in units of the free-stream density,
the free-stream sound speed $a_\infty = \sqrt{\gamma p_\infty/\rho_\infty}$ and temperature. Here
$R$ is a length scale, $\sigma$ the Gaussian's width and $\beta_S$ the strength, in units of
$a_\infty$.

kinet writes the same vortex with the strength $\beta$ in units of the isothermal sound speed
$\sqrt{p_\infty/\rho_\infty}$, the convention of `kinet/reference/vortex.py`, which attributes it
to Shu's ICASE Report 98-32 (Sect. 4.5; that report was not opened here). With $r$ the distance
from the centre in units of $R$, $\rho_\infty = p_\infty = 1$, and $\boldsymbol U$ the carrying flow,

$$
\theta = 1 - \frac{(\gamma - 1)\,\beta^2}{8\gamma\pi^2}\, e^{1 - r^2}, \qquad
\rho = \theta^{1/(\gamma-1)}, \qquad p = \theta^{\gamma/(\gamma-1)}, \qquad
\boldsymbol u = \boldsymbol U + \frac{\beta}{2\pi}\, e^{(1 - r^2)/2}\,
  \frac{(-\bar y, \bar x)}{R}. \tag{3}
$$

This is Eqs. (1) and (2) with $\sigma = 1$ and $\beta_S = \beta\, e^{1/2}/(2\pi\sqrt\gamma)$, and
$\theta = 1 + \delta T$ (my conversion: equating the two swirl speeds gives $\beta_S$, and then
$\delta T$ equals $\theta - 1$ term by term). It is the convention the reader uses.

**Shu's parameters.** Spiegel et al.'s Table 1 gives, for Shu's version, $\rho_\infty = p_\infty
= T_\infty = 1$, $R = \sigma = 1$, the flow at $45°$ with Mach number $M_\infty = \sqrt{2/\gamma}$,
$\beta_S = M_\infty\, 5\sqrt2\, e^{1/2}/(4\pi)$, and a box of half-side $L = 5$. In Eq. (3) these
are $\beta = 5$, $\boldsymbol U = (1, 1)$ and a box of side 10, which is kinet's case
`isentropic_vortex/default` with the vortex at the centre, $(5, 5)$.

### The exact solution

"The exact solution to the problem is just the translation of the initial conditions based on
propagation speed and simulation time" (Spiegel et al. 2015, Sect. IV.B.1): at time $t$ the
centre is at $(x_c, y_c) + \boldsymbol U t$, and on the periodic box $\bar x$ and $\bar y$ are taken
to the nearest image. At $t = 10$ the vortex is back at its start. Five core radii from the
centre, the box's edge, the swirl is $e^{-12} \approx 6 \times 10^{-6}$ of its peak and $\theta - 1$
is $e^{-24}$ of its own (`dataset_specs/02_grid_refinement_known_solution.md`, Sect. 4.2), so the
images' overlap is far below the errors measured here.

## How a run is compared

The reader `isentropic_vortex_kinet` (`fmeval/data/analytic.py`) opens a converted run, takes its
cells, its clock and its $\gamma$, and evaluates Eq. (3) there. It refuses a run whose stored initial
condition differs from Eq. (3) at $t = 0$ by more than $10^{-12}$ in any field (on these runs the
difference is at most $4.4 \times 10^{-16}$), so a run of other parameters is never scored against
the wrong vortex. The run is its candidate, and each row is labelled with `param_resolution` N,
so the runs of one configuration give the observed order
$p = \ln(L_k/L_{k+1})/\ln 2$ through `fmeval.analysis.observed_order` (Roy 2005, Eq. 8).

**One time per run.** The solver's time step adapts to the flow, so the grids save their frames at
nearby but different times (2.47998 on $64^2$ against 2.47833 on $128^2$), and `observed_order`
pairs grids only at equal times. The end time is the one time every grid of a sequence saves, so
each configuration evaluates the last frame of each run, as the standard study measures the error
after one period (Spiegel et al. 2015, Fig. 2). Issue 149 holds the limit.

```bash
python evaluate.py -m dataset=kinet_isentropic_vortex_mu1em5 dataset.trajectory=N64,N128,N256 \
    'metrics=[rmse,max_error]' paths.results=<results root>
```

## What the evaluation sees

Through the pipeline and `observed_order` (2026-11-27), `rmse` and `max_error` on each field:

| Sequence | Pair | `rmse` density | `rmse` pressure | `rmse` velocity | `max_error` density | `max_error` pressure | `max_error` velocity |
|---|---|---|---|---|---|---|---|
| $\mu = 10^{-5}$, $t = 10$ | 64 to 128 | 2.000 | 1.964 | 2.039 | 2.135 | 2.095 | 2.364 |
| $\mu = 10^{-5}$, $t = 10$ | 128 to 256 | 1.900 | 1.774 | 1.906 | 1.761 | 1.699 | 1.938 |
| $\mu = 10^{-7}$, $t = 2.5$ | 256 to 512 | 1.958 | 1.937 | 1.992 | 1.998 | 1.988 | 1.995 |

The density and pressure orders equal those of the job's own check of the runs to its three
decimals. The density `rmse` at the end time is $7.64 \times 10^{-4}$, $1.91 \times 10^{-4}$ and
$5.12 \times 10^{-5}$ on the three coarser grids, and $1.90 \times 10^{-5}$ and $4.89 \times 10^{-6}$
on the $\mu = 10^{-7}$ pair. The fall of the order from 2.00 to 1.90 between the two coarser pairs
at $\mu = 10^{-5}$ is consistent with the viscous error beginning to show on $256^2$ (my reading).

The domain is doubly periodic, so every metric of the panel that runs on density, velocity or
pressure runs here; the panel costs are in the dataset's log. No degradation ladder is run: each
run is a candidate.

## References

- Spiegel, S. C., Huynh, H. T. & DeBonis, J. R. (2015). A survey of the isentropic Euler vortex
  problem using high-order methods. AIAA Paper 2015-2444, 22nd AIAA Computational Fluid Dynamics
  Conference. <https://ntrs.nasa.gov/citations/20150018403> (read: Sect. IV.A.1, Eqs. 20 to 24,
  Table 1, Sect. IV.B.1).
- Shu, C.-W. (1998). Essentially non-oscillatory and weighted essentially non-oscillatory
  schemes for hyperbolic conservation laws. In *Advanced Numerical Approximation of Nonlinear
  Hyperbolic Equations*, ed. A. Quarteroni, Lecture Notes in Mathematics 1697, Springer,
  325–432: the source Spiegel et al. cite (their reference 20). kinet's `kinet/reference/vortex.py`
  cites the ICASE report version, Report 98-32, Sect. 4.5. Neither was opened here.
- Roy, C. J. (2005). Review of code and solution verification procedures for computational
  simulation. *Journal of Computational Physics* 205(1), 131–156.
  <https://doi.org/10.1016/j.jcp.2004.10.036>

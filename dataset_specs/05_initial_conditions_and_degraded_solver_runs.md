# Dataset 05: trajectories from many initial conditions, with degraded solver runs as candidates

**What this dataset is.** Reference trajectories of one flow started from many initial
conditions, and, for each, candidate trajectories made by an analytic formula or by a solver
run degraded in a controlled way (a coarser grid, a wrong parameter, a more diffusive scheme, a
different solver). Every metric is computed between candidate and reference at every stored
step and averaged over the initial conditions. Everything here is analytic or simulated, with
kinet, OpenFOAM or another solver. Nothing is trained and no machine-learning model is used.

**Catalog clusters:** D2 (many initial conditions, scored step by step) and the data side of
G1 (the temporal ladder and windowed budgets). **Metrics served:** the thirteen cards that name
this experiment (`mse`, `mae`, `rmse`, `rmse_channel_mean`, `nrmse`, `vrmse`, `max_error`,
`max_error_channel_mean`, `h1_relative`, `spectrum_l2`, `kinetic_energy`, `enstrophy`,
`palinstrophy`), and every other pairwise metric as a by-product. **Ideas and issues served:**
the time-dependent family (valid prediction time, issue 078; temporal autocorrelation, 079;
invariant measure, 080; the trajectory input of 094). **Date:** 2026-11-26; rewritten the same
day to remove a misreading of the task. Quantities marked "measured" were read from files on
disk with `h5py` on 2026-11-26; "my arithmetic", "my derivation" and "my design" mark the
author's own work.

## 1. Purpose

Thirteen metric cards say their field reports them per step, averaged over many initial
conditions: the error of a candidate trajectory against the reference at each step, then a
mean and a spread over the set of starts (`metrics/nrmse/card.md` and `metrics/vrmse/card.md`,
"How its field reports it", citing Takamoto et al. 2022, Sect. 3.3, and Ohana et al. 2024,
App. E.3, for the definitions of nRMSE and VRMSE). The repository has one instance,
`forecast_re5e4`: three runs of unknown provenance, two starts, ten steps
(`docs/datasets/reynolds_ladder_2d.md`, "Forecast pairs"). That gives an error-against-step
curve on two cases, not a mean and spread over many, and no known answer.

The time-dependent ideas need the same input: a candidate and a reference trajectory from the
same start, long enough for the error to cross a threshold (078), to decorrelate (079), or to
sample a statistically settled state (080).

The dataset is therefore two things: (1) a set of **reference trajectories** from many initial
conditions, and (2) **candidate trajectories** from each start, made by a formula or a degraded
solver run whose provenance is recorded. This is the project's own protocol
(`CLAUDE.md`, "Evaluation protocol"): a trusted solver degraded in controlled steps.

## 2. What the dataset must provide

- **Reference set.** At least ten independent trajectories per physical configuration (my
  threshold for a mean and a spread over initial conditions). The set of trajectories used is
  fixed once and written down, and every candidate is scored on the same set.
- **Candidates of known provenance.** Each candidate file records what made it: the formula
  and its parameters, or the solver, grid, scheme and parameters; the start; the horizon. At
  least the reference candidates that need no solver (persistence, climatology, unrelated
  realisation, Sect. 3.4) and one degraded solver run.
- **Pairing.** Candidate and reference at the same steps, on a shared clock, with the grid,
  length and boundary of every axis recorded (Sect. 6).
- **Fields.** Density and velocity (vorticity is recomputed by the repository); pressure only
  where the solver writes a thermodynamic one.
- **Boundaries.** Periodic on every axis, so every metric (including `spectrum_l2`) runs.
- **Horizon and cadence.** From one step to several large-eddy turnover times, dense enough at
  short times to resolve early error growth and long enough for the time-dependent ideas.
- **Known in advance.** An exact error-against-step curve (Option A), or a known ordering of
  candidates (Options B and C).

## 3. Option A, the analytic ideal (a reader, computed on the fly)

Both the reference and a "candidate with a known error" are closed-form here, so by Kareem's rule
this is **not a dataset to make** but a reader in the `ClosedFormTrajectory` pattern of
`fmeval/data/analytic.py` that returns a reference trajectory and a candidate trajectory, as
`ForecastPairs` pairs two trajectories today (`fmeval/data/forecast.py`). Many "initial conditions"
are many seeds of a random-phase initial field.

### 3.1 A1: linear advection–diffusion with a wrong speed or a wrong diffusivity

On the periodic square $[0, L)^2$ a scalar $\rho$ (stored as `density`, so the repository's
density pipeline is exercised) obeys

$$
\partial_t \rho + \mathbf{c} \cdot \nabla \rho = \kappa \nabla^2 \rho , \tag{1}
$$

with $\mathbf{c}$ a uniform velocity and $\kappa$ a diffusivity. Writing the initial field as a
mean $\rho_0$ plus Fourier modes with wavevectors $\mathbf{k}_m = 2\pi \mathbf{m}/L$
(integer $\mathbf{m}$) and complex amplitudes $a_m$, the exact solution is

$$
\rho(\mathbf{x}, t) = \rho_0 + \sum_m a_m \, e^{i \mathbf{k}_m \cdot (\mathbf{x} - \mathbf{c} t)}
\, D_m(t), \qquad D_m(t) = e^{-\kappa |\mathbf{k}_m|^2 t} . \tag{2}
$$

The candidate is Equation (2) with $\mathbf{c}'$ and $\kappa'$ in place of $\mathbf{c}$ and
$\kappa$ (decay factors $D'_m$, speed error $\delta\mathbf{c} = \mathbf{c}' - \mathbf{c}$). By
Parseval's theorem, which holds exactly on the grid for modes below the Nyquist index, the
mean squared error over cells is (my derivation)

$$
\mathrm{MSE}(t) = \sum_m |a_m|^2 \Bigl[ D_m^2 + D_m'^2 - 2 D_m D'_m
\cos\bigl( \mathbf{k}_m \cdot \delta\mathbf{c} \, t \bigr) \Bigr] . \tag{3}
$$

For a single mode $\rho = \rho_0 + A \sin(\mathbf{k}\cdot(\mathbf{x} - \mathbf{c}t)) D$, with
phase error $\theta(t) = \mathbf{k}\cdot\delta\mathbf{c}\, t$:

- **Wrong speed only** ($\kappa' = \kappa$): the error is
  $2 A D \cos(\cdot) \sin(\theta/2)$, so
  $\mathrm{MSE} = 2A^2 D^2 \sin^2(\theta/2)$ and the continuum maximum error is
  $2 A D |\sin(\theta/2)|$. The error is **not monotone**: it returns to zero whenever
  $\theta = 2\pi n$, the phase-wrap form of the double penalty. A metric's
  error-against-step curve must reproduce this periodicity.
- **Wrong diffusivity only** ($\delta\mathbf{c} = 0$): $\mathrm{MSE} = \tfrac12 A^2 (D - D')^2$,
  which rises, peaks at $t^\ast = \ln(\kappa'/\kappa) / [(\kappa' - \kappa)|\mathbf{k}|^2]$ and
  decays to zero as both fields relax to the mean. A decaying flow can make a wrong candidate look
  better at long leads; this is the exact form of that effect.

From Equation (3) every normalised metric follows in closed form: `rmse` is its square root;
`nrmse` divides by $\sqrt{\rho_0^2 + \sum_m |a_m|^2 D_m^2}$ (the raw root mean square, mean not
removed, `metrics/nrmse/card.md` Eq. 1); `vrmse` divides by
$\sqrt{\tfrac{N}{N-1}\sum_m |a_m|^2 D_m^2 + \epsilon}$ with $\epsilon = 10^{-7}$
(`metrics/vrmse/card.md` Eq. 2); `h1_relative` weights each mode by
$w_m = 1 + \sum_j N_j^2 \sin^2(2\pi m_j / N_j)$, the symbol of the card's centred difference with
unit domain length (`metrics/h1_relative/card.md` Eq. 1), and adds $\rho_0^2 N$ to the
reference's zeroth-order term; `spectrum_l2` compares shell sums of $\tfrac12|a_m|^2 D_m^2$ and
$\tfrac12|a_m|^2 D_m'^2$ (`metrics/spectrum_l2/card.md` Eqs. 1 and 2), so it is **exactly zero
for a wrong speed at every lead** (the spectrum is phase-blind) and $|1 - (D'/D)^2|$ for a
single mode with a wrong diffusivity. `mae` and `max_error` are closed-form only for a single
mode (the reader evaluates the discrete sum and maximum over cell centres exactly; the continuum
values $\tfrac{4}{\pi}AD|\sin(\theta/2)|$ and $2AD|\sin(\theta/2)|$ are limits).

A useful corollary for the test-set statistics (my derivation): with the amplitudes $|a_m|$
fixed and only the phases drawn per seed, Equation (3) and every quantity built from mean
squares are **identical for every initial condition**, so their spread over the test set is
exactly zero, while `mae` and `max_error` vary from seed to seed. A harness that reports a
non-zero spread of `mse` on this reader has a bug.

### 3.2 A2: a real numerical scheme as the candidate (upwind and Lax–Friedrichs)

Take $\kappa = 0$, $\mathbf{c} = (c_x, c_y)$ with positive components, a grid of spacing
$\Delta x$, a step $\Delta t$ and Courant numbers $\nu_j = c_j \Delta t / \Delta x$. On a
periodic grid a linear constant-coefficient scheme multiplies each Fourier mode by its
amplification factor $g$ every step, so the scheme's output is closed-form, not approximately
but exactly (von Neumann analysis; my derivation, with the phase angle
$\theta_j = 2\pi m_j \Delta x / L$):

$$
g_{\mathrm{up}}(\theta; \nu) = 1 - \nu \bigl(1 - e^{-i\theta}\bigr), \qquad
|g_{\mathrm{up}}|^2 = 1 - 2\nu(1-\nu)(1 - \cos\theta), \tag{4}
$$

$$
g_{\mathrm{LF}}(\theta; \nu) = \cos\theta - i\nu \sin\theta, \qquad
|g_{\mathrm{LF}}|^2 = 1 - (1 - \nu^2)\sin^2\theta . \tag{5}
$$

In two dimensions the dimensionally split scheme (an $x$ sweep then a $y$ sweep) has
$G_m = g(\theta_x; \nu_x)\, g(\theta_y; \nu_y)$ exactly, because the two one-dimensional
operators commute. After $n$ steps the truth multiplies $a_m$ by
$e^{-i n (\nu_x\theta_x + \nu_y\theta_y)}$ and the scheme by $G_m^n$, so

$$
\mathrm{MSE}(n) = \sum_m |a_m|^2 \bigl| G_m^n - e^{-i n(\nu_x\theta_x + \nu_y\theta_y)} \bigr|^2 . \tag{6}
$$

Expanding Equation (4) for small $\theta$ and matching $|g|^2 \approx 1 - 2\nu_{\mathrm{num}}
k^2 \Delta t$ gives the numerical diffusivity of upwind, $\nu_{\mathrm{num}} = \tfrac12 c\,\Delta x
(1 - \nu)$, and from Equation (5) that of Lax–Friedrichs,
$\nu_{\mathrm{num}} = \tfrac{\Delta x^2}{2\Delta t}(1 - \nu^2)$ (my derivation). These are the
modified-equation coefficients the brief attributes to LeVeque (2002), Sect. 8.6; that book was
not opened, so the section number is not verified here. Equation (6) does not need them: it is
exact, and it also contains the dispersive (phase) error the modified equation drops. Two known
answers follow: as $n \to \infty$ every mode with $\theta \ne 0$ is damped to zero by upwind, so
the candidate tends to the mean and `vrmse` tends to $\sqrt{(N-1)/N}$, The Well's landmark of 1
(Ohana et al. 2024, Table 2 caption); and Lax–Friedrichs leaves the Nyquist mode $\theta = \pi$
undamped ($|g_{\mathrm{LF}}| = 1$ there), so a field with energy at the grid scale keeps an error
that never decays, a check on metrics that weigh small scales.

### 3.3 A3: the Taylor–Green vortex with a wrong viscosity, or with a phase drift

The repository's reader `taylor_green_2d` (`fmeval/data/analytic.py`; Taylor 1923, read via the
reader's docstring) gives on $[0, 2\pi)^2$, with $D = e^{-2\nu t}$,
$u = \sin x \cos y\, D$, $v = -\cos x \sin y\, D$, $\omega = 2 \sin x \sin y\, D$. A candidate
with viscosity $\nu'$ has $D' = e^{-2\nu' t}$. Then (my derivation; grid means of
$\sin^2 x\cos^2 y$ are exactly $\tfrac14$ at cell centres):

| Metric | Value |
|---|---|
| `mse` (two channels pooled), `rmse`, `rmse_channel_mean` | $\tfrac14 (D - D')^2$; $\tfrac12 |D - D'|$; $\tfrac12 |D - D'|$ |
| `mae` | $\tfrac{4}{\pi^2} |D - D'|$ in the continuum limit; the discrete sum on the grid |
| `max_error`, `max_error_channel_mean` | $\cos^2(\pi/N)\,|D - D'|$: the cell centres miss the continuum maximum by half a cell on each axis |
| `nrmse` | $|1 - D'/D|$, both channels alike |
| `vrmse` | $\tfrac12|D-D'| \big/ \sqrt{\tfrac{N^2}{N^2-1}\tfrac14 D^2 + \epsilon}$ ($N^2$ cells) |
| `h1_relative` | $2\,|1 - D'/D|$: one ratio per channel, summed over the two channels (card Eq. 2) |
| `spectrum_l2` | $|1 - (D'/D)^2|$: all energy is in the shell $\mathrm{rint}(\sqrt2) = 1$ |
| `kinetic_energy` | $E = D^2/4$, so $E'/E = e^{-4(\nu' - \nu)t}$ |
| `enstrophy` | $\Omega = D^2/2$ |
| `palinstrophy` | $P = D^2$, so $dE/dt = -2\nu\Omega$ and $d\Omega/dt = -2\nu P$ hold exactly (Boffetta and Ecke 2012, Eqs. 5 and 6, cited from `metrics/palinstrophy/card.md`) |

The single-field values assume the vorticity is recomputed with a spectral derivative; a centred
difference multiplies $\Omega$ by $(\sin h / h)^2$ with $h = 2\pi/N$.

**Phase drift.** A second candidate translates the exact vortex by a displacement
$\boldsymbol{\delta}(t) = \delta\mathbf{U}\, t$ that grows linearly with lead time, at unchanged
amplitude: $\mathbf{u}'(\mathbf{x}, t) = \mathbf{u}(\mathbf{x} - \boldsymbol{\delta}(t), t)$.
From $\langle f(\mathbf{x}) f(\mathbf{x} - \boldsymbol\delta)\rangle = \tfrac14\cos\delta_x
\cos\delta_y$ for $f = \sin x \cos y$ (my derivation),
$\mathrm{MSE} = \tfrac12 D^2 (1 - \cos\delta_x \cos\delta_y)$, while `kinetic_energy`,
`enstrophy`, `palinstrophy` and `spectrum_l2` are **identical to the truth at every lead**. It is
the cleanest known demonstration that the single-field and spectral metrics are blind to
position. (The translated field is an exact Navier–Stokes solution only together with a uniform
background flow, by Galilean invariance; here it is used as a candidate with a known error, not
as a solution.)

### 3.4 Reference candidates that need no solver

- **Persistence**: the candidate at every lead is the start frame,
  $\hat\rho(t) = \rho(0)$ (`docs/ideas/infrastructure/baseline_predictors.md`, item 1). On A1,
  $\mathrm{MSE}_{\mathrm{pers}}(t) = \sum_m |a_m|^2 \bigl[1 + D_m^2 - 2D_m\cos(\mathbf{k}_m\cdot
  \mathbf{c}\,t)\bigr]$ (my derivation).
- **Climatology**: the candidate is a mean state, the second standard reference of weather
  verification beside persistence (Rasp et al. 2020, Sect. 4.1, define both). Here the
  climatology is the spatial mean of the target, whose `vrmse` is exactly $\sqrt{(N-1)/N}$
  (`metrics/vrmse/card.md`), and on an isotropic set of trajectories the mean over
  trajectories, which tends to the same spatially uniform field.
- **Unrelated realisation**: the candidate is another trajectory at the same lead. For two
  independent fields with the same spectrum and random phases, the expected MSE is twice the
  variance (my derivation), so `vrmse` is about $\sqrt2$: the ceiling a fully decorrelated
  candidate reaches, and the value persistence saturates at once the flow forgets its start.
- **Skill score**: any metric $S$ (lower is better) is reported against a reference candidate as
  $1 - S_{\mathrm{candidate}}/S_{\mathrm{reference}}$ (`baseline_predictors.md`). Murphy (1988)
  defines the mean-squared-error skill score against climatology; that paper could not be opened
  (HTTP 403), so no equation number is quoted.

All three are computed from the reference on the fly, for every option below, and need no
storage.

### 3.5 What the reader needs, and its limits

**Reader** (my design): `analytic_trajectory_pairs`, a `ClosedFormTrajectory` with parameters
`problem` (`advection_diffusion` or `taylor_green`), `grid`, `length`, `n_frames`, `dt`,
`c`, `kappa` or `nu`, `amplitudes` (a list of $(\mathbf{m}, |a_m|)$ or a power-law spectrum),
`seeds` (one initial condition per seed), and `candidate` (`exact`, `wrong_speed`,
`wrong_diffusivity`, `upwind`, `lax_friedrichs`, `phase_drift`, `persistence`, `climatology`,
`unrelated`) with its parameter ($\mathbf{c}'$, $\kappa'$, $\nu'$, Courant number). Each frame is
one FFT multiply per field. It also returns the closed-form curve of Equations (3) and (6), so a
test can assert the harness's per-lead mean over seeds against it at a relative tolerance of
$10^{-12}$. Prototype quality is enough for the generator; the test that compares the harness to
the closed form is research-grade.

**Limits.** The dynamics are linear, so no energy moves between scales and no error grows
exponentially; there is no Lyapunov time, so the valid prediction time of issue 078 has a known
answer only in the trivial sense of a threshold crossing of a known curve. It tests the harness
and each metric's response to phase and amplitude error, not turbulence.
## 4. Options B to D: simulated reference sets and degraded solver runs

### 4.1 Option B: the on-disk kinet isotropic runs as the reference set, a coarse kinet run as the candidate

**The reference set exists.** `/global/cfs/cdirs/m4790/Data/neurde/hit_scaling/` holds decaying
2D isotropic turbulence at Re 12.5k, 25k and 50k, Ma 0.1, `k0: 4` (`00_how_to_use_kinet.md`,
"Read this first", item 2). Measured 2026-11-26: each Reynolds number has **100 complete
10 000-step runs** plus one complete 100 000-step long run. Re 12.5k and 25k are native 256²
under `tiers/full/rollout.h5`; Re 50k is `tiers/256/rollout.h5`, coarse-grained from 512² by
two in space and time (`time_stride: 2`). Every file holds `observables/{density, pressure,
velocity, vorticity, temperature}` of shape `(1, C, 10000, 256, 256)` with 1001 finite slots
(steps 1, 10, 20, ..., 10 000), the step-0 state under `initial_conditions/`, periodic
boundaries in the `boundary_conditions` attribute, and no populations. The seed of each run is
in its `config.yaml`. The stored pressure of these weakly compressible runs is the gauge value
(ρ − 1)c_s² (`00_how_to_use_kinet.md`, "Verified by running"), so it is not read.

**Time scales (measured on the first run of each Reynolds number).** With $u_{\mathrm{rms}}$ the
total root-mean-square speed and the integral length $\ell = L\langle k^{-1}\rangle_E$ from the
shell spectrum, the large-eddy turnover time $\tau = \ell/u_{\mathrm{rms}}$ is

| Re | $\tau$ at step 0 | step 2500 | step 5000 | step 10 000 | $u_{\mathrm{rms}}/U$ at 10 000 |
|---|---|---|---|---|---|
| 12.5k | 1206 steps (0.272) | 2057 (0.464) | 2640 (0.595) | 3635 (0.820) | 0.927 |
| 25k | 1245 (0.281) | 1886 (0.425) | 2449 (0.552) | 3561 (0.803) | 0.960 |
| 50k | 1159 (0.261) | 1867 (0.421) | 2644 (0.596) | 3702 (0.835) | 0.978 |

(steps at 256²; convective units $t\,U/L$ in parentheses, $U = \mathrm{Ma}\,c_s = 0.057735$). The
energy barely decays while the integral scale triples (the inverse cascade; the spectral peak
moves from $k = 4$ to $k = 1$). A full trajectory, 2.2553 convective units, is about **4.3
turnover times** (my trapezoid integral of $1/\tau$). By the end the energy sits at the box
scale, so late times probe a condensate-like state, not developed turbulence.

**Which trajectories.** All 100 per Reynolds number can be scored; there is nothing to hold out,
because no candidate is fitted to data. A fixed subset of 10 per Reynolds number (my choice,
drawn once with a recorded seed) keeps the first pass cheap. The three long runs serve the
invariant measure (issue 080). The primary start is step 0; starts at steps 2500 and 5000 are
a second stratum, reported apart, because a start inside a developed flow is a different
initial-condition distribution (`docs/ideas/evaluation_design.md`, the stress matrix). Report
every curve against time in frames, in convective units and in initial turnover times.

**The coarse-grid candidate.** The archive was made on a GPU, and the isotropic initial
condition differs between CPU and GPU for the same seed and between grids for the same seed
(`00_how_to_use_kinet.md`, "Verified by running", check 3). So the candidate must start from the
archive's own step-0 fields, block-averaged to the coarse grid, through kinet's Python
`initial_state` route, which works on unmodified kinet (same guide, check 7; script
`/pscratch/sd/k/khegazy/kinet_examples/_meta/branch_from_frame.py`). Physics notes: kinet keeps
$u_l = \mathrm{Ma}\,c_s$ fixed and derives $\nu_l = U N/\mathrm{Re}$ from the grid, so the same
Re on 64² is the same physical viscosity at lower resolution, and acoustic scaling makes 2500
steps at 64² and 5000 at 128² the same physical time as 10 000 at 256² (guide, Sect. 4; the
clock was verified to match across grids). Saving every 10 steps at 64² gives 251 frames;
every 5 steps at 128² gives 1001 frames. The populations are seeded from the block-averaged
macroscopic fields, so the coarse run starts with a short kinetic transient that the reference
did not have (from macroscopic fields alone the guide measured a velocity jump of about 8% of
the flow speed at step 1); this is part of the candidate's error and is recorded as such. The
comparison is on a 64² or 128² analysis grid, where the repository's conservative remap
block-averages the reference exactly as the initial condition was.

**Cost.** A 256² run of 10 000 steps took 95.6 s on one GPU (measured from a 2026-11-06
`simulate.log` of the archive), so a 64² or 128² run is at most minutes. Storage at 56 bytes per
cell per frame without populations (guide, "Verified by running"): about 58 MB per 64² run and
0.9 GB per 128² run, about 29 GB for both grids on 30 trajectories (my arithmetic).

**Known answer.** No exact curve. What is known: at step 0 the coarse candidate equals the
block-averaged reference to round-off; the persistence, climatology and unrelated-realisation
landmarks of Sect. 3.4; and an expected ordering, 64² worse than 128² at every time (reasoning,
not guaranteed: a coarser run can be accidentally closer at a time where both have decorrelated).

### 4.2 Option C: other degraded solver runs from the same starts (my design)

The coarse grid is one axis of degradation. The protocol asks for a second, independent one
(`CLAUDE.md`, "Evaluation protocol", step 2: "grid coarsening, plus an orthogonal axis such as
noise or artificial viscosity"). Each of the following starts from the same archive fields at
the reference's own grid through the same `initial_state` route, so the only difference from the
reference is the stated one:

- **Wrong viscosity.** The same run at Re 0.9, 0.75 and 0.5 times the reference's (an
  artificial-viscosity axis with an ordinal severity). Known in advance: the candidate's energy
  and enstrophy decay faster, and the error grows monotonically with the viscosity error at
  short times (reasoning).
- **A different collision model.** Plain BGK instead of entropic BGK, which kinet runs with one
  override (guide, Sect. 7 and "Verified by running", check 9). Known in advance: nothing exact;
  it measures how far two lattice-Boltzmann schemes of the same order disagree on one flow.
- **An independent solver.** The same initial velocity on the same periodic domain in OpenFOAM,
  an incompressible finite-volume code, with `cyclic` boundary patches on both axes and a solver
  such as `pisoFoam` or `icoFoam` at the same viscosity. OpenFOAM is available on Perlmutter as
  Shifter container images (`shifterimg images` lists `opencfd/openfoam-default:2406` and
  `:2112`, 2026-11-26). The initial velocity is written into the case's `0/U` field from the
  archive's step-0 array by a short script (my design; not tried). Known in advance: nothing
  exact; the difference between a weakly compressible lattice-Boltzmann run and an
  incompressible finite-volume run of the same flow is a solver-to-solver discrepancy, a
  realistic candidate error that no degradation operator imitates. **Not verified:** the OpenFOAM
  case setup, its run time, and how much of the difference is the Mach-0.1 compressibility of
  the reference.

Storage and cost per candidate are those of a reference run at its grid: about 3.6 GB per
256² run of 1001 frames at 56 bytes per cell (my arithmetic) and about a minute and a half of
GPU time for kinet.

### 4.3 Option D: public simulation data with many trajectories (reference sets only)

Two public collections hold many trajectories of one problem from different initial
conditions, and can serve as further reference sets. Only their simulation data is used here.

- **The Well, `shear_flow`** (Ohana et al. 2024, App. C.12; full text read): 1120 trajectories of
  200 steps on 256 × 512, periodic in both directions; data under CC-BY-4.0 (App. A.6). Not on
  disk; its dataset card gives both 114.7 GB and 471 GB as its size, and the Hugging Face v1.0
  copy has a split error, so download v2.0 with `the-well-download --base-path <dir> --dataset
  shear_flow`. Readable by the existing Well reader, which accepts periodic axes only
  (`fmeval/data/well.py`, lines 99 to 106).
- **PDEBench 2D compressible Navier–Stokes** (Takamoto et al. 2022, App. D.5, Table 1; read):
  periodic in both axes, density, velocity and pressure, Γ = 5/3; 1000 samples at 512² with 21
  stored steps; random-field initial conditions at Mach 0.1 and 1.0. Data at
  doi:10.18419/darus-2986, CC BY 4.0. A repository config names a 128² file, which conflicts with
  Table 1's 512²; check the file. The Mach 1.0 sets store an absolute pressure and are a
  candidate interim shock dataset (`03_two_dimensional_shocks.md`), unverified for shocklets.

Candidates on these sets are degraded solver runs as in Options B and C, which needs a solver
for each problem's equations; kinet does not run either configuration as shipped. Their value
is as reference sets with many initial conditions on a different flow.

### 4.4 The options side by side

| | A (reader) | B (kinet coarse grid) | C (other degraded runs) | D (public data) |
|---|---|---|---|---|
| Reference trajectories | any number of seeds | 100 per Re on disk; 10 per Re first | same as B | 1120 or 1000 |
| Grid | chosen | 64², 128² against 256² | 256² | 256 × 512; 512² |
| Frames per trajectory | chosen | 1001 stored; 251 or 1001 compared | 1001 | 200; 21 |
| Horizon | chosen | 4.3 turnovers | same | as stored |
| Fields | density or velocity | density, velocity | density, velocity | per dataset |
| New storage | none | about 29 GB | about 3.6 GB per run | download only |
| Known answer | exact curve | landmarks, ordering | ordering (viscosity); none (solver) | none |

## 5. Recommendation

1. **Build the Option A reader first** (a day): it pins the harness's per-step mean over initial
   conditions, the zero spread of mean-square metrics, the phase-blindness of the spectral and
   single-field metrics, and the closed-form curves of a real scheme, before any simulated
   candidate is trusted.
2. **Then Option B** (mostly the conversion of `BUILD_ORDER.md` step 1): the reference
   set is on disk, the reference candidates cost nothing, and 30 coarse runs take minutes.
3. **Then Option C's wrong-viscosity axis**, which gives the ordinal second axis the protocol
   asks for at the reference's own grid; the collision-model and OpenFOAM candidates after it.
4. **Option D** only if a second flow with many initial conditions is wanted.

## 6. What to store

Following `docs/recipes/add-a-dataset.md`:

- **Candidates converted to the existing `forecast` layout** (`fmeval/data/forecast.py`;
  `BUILD_ORDER.md`, "How data reaches the metrics"), one file per (trajectory, candidate, start),
  `forecast_t0-<start>.h5` with `pred_<step>` from the candidate run and `target_<step>` from the
  reference block-averaged to the candidate's grid, matched by `time/time_convection`. Each
  file's provenance is recorded in a sidecar (my design): `candidate` (for example `kinet-lbm-64`,
  `kinet-lbm-256-re0.75`, `kinet-bgk-256`, `openfoam-pisofoam-256`), `trajectory_id` (the
  archive's identity key) and `start_step`.
- **Fields:** `density` and `velocity`; no vorticity (recomputed); no weakly compressible
  pressure (a gauge value, not read).
- **Grid and boundaries:** the candidate's own grid, periodic on both axes; the analysis grid is
  the coarsest grid compared.
- **Trajectory list:** a committed list of the identity keys used per Reynolds number, with the
  seed that drew it, in `docs/datasets/` beside the dataset page.
- **Reference candidates:** not stored; persistence, climatology and unrelated realisation are
  computed by the reader from the reference.

## 7. References

- Takamoto, M., Praditia, T., Leiteritz, R., MacKinlay, D., Alesiani, F., Pflüger, D. &
  Niepert, M. (2022). PDEBench. *Advances in Neural Information Processing Systems 35*
  (Datasets and Benchmarks), 1596–1611. doi:10.52202/068431-0117; arXiv:2210.07182. Read via the
  arXiv v7 HTML (Sect. 3.3 for the nRMSE definition; App. D.5 and Table 1 for the 2D compressible
  data); data at doi:10.18419/darus-2986.
- Ohana, R., McCabe, M., et al. (2024). The Well. *Advances in Neural Information Processing
  Systems 37* (Datasets and Benchmarks), 44989–45037. doi:10.52202/079017-1430;
  arXiv:2412.00568. Full text of v2 read (App. E.3 for the VRMSE definition; App. C.12 for
  `shear_flow`; App. A.6 for the data licence); the `shear_flow` dataset card read.
- Rasp, S., Dueben, P. D., Scher, S., Weyn, J. A., Mouatadid, S. & Thuerey, N. (2020).
  WeatherBench. *Journal of Advances in Modeling Earth Systems* 12, e2020MS002203.
  doi:10.1029/2020MS002203; arXiv:2002.00469. arXiv v3 read, Sect. 4.1, for the persistence and
  climatology references.
- Murphy, A. H. (1988). Skill scores based on the mean square error and their relationships to
  the correlation coefficient. *Monthly Weather Review* 116, 2417–2424.
  doi:10.1175/1520-0493(1988)116<2417:SSBOTM>2.0.CO;2. **Not opened** (HTTP 403).
- LeVeque, R. J. (2002). *Finite Volume Methods for Hyperbolic Problems*. Cambridge University
  Press. **Not opened**; named for the modified equation, which Sect. 3.2 rederives instead.
- Warming, R. F. & Hyett, B. J. (1974). The modified equation approach to the stability and
  accuracy analysis of finite-difference methods. *Journal of Computational Physics* 14,
  159–179. doi:10.1016/0021-9991(74)90011-4. **Not opened** (publisher stub only).
- Taylor, G. I. (1923). On the decay of vortices in a viscous fluid. *Philosophical Magazine*
  (6) 46, 671–674. doi:10.1080/14786442308634295. Secondary: the docstring of
  `fmeval/data/analytic.py`.
- Boffetta, G. & Ecke, R. E. (2012). Two-dimensional turbulence. *Annual Review of Fluid
  Mechanics* 44, 427–451. doi:10.1146/annurev-fluid-120710-101240. Secondary: the repository's
  cards.
- kinet (read-only checkout `/global/u2/k/khegazy/projects/pde/kinet`) and
  `00_how_to_use_kinet.md`, including its "Verified by running" section.

## 8. Confidence

- **Sure** (read in code or measured on files): the `hit_scaling` inventory (100 complete runs
  plus one long run per Reynolds number, tiers, shapes, finite slots, no populations, periodic
  attribute); the turnover-time table; the 95.6 s run time; that the `initial_state` route works
  on unmodified kinet and that the isotropic initial condition depends on the device and the
  grid (measured by the guide's verification runs); the availability of OpenFOAM container
  images on Perlmutter.
- **My derivation, checked by hand but not by code:** Equations (3) and (6), the single-mode and
  Taylor–Green tables, the numerical diffusivities, the persistence and unrelated-realisation
  formulas, the zero-spread corollary, the 4.3-turnover integral, every storage number.
- **My design, to be checked by a smoke run:** block-averaging the archive's step-0 fields into a
  coarse `initial_state`; the wrong-viscosity severities; the OpenFOAM case and its initial
  condition; whether the kinet in the tree reproduces the archive's trajectories from the same
  seeds (it does not on CPU, by the device dependence above).
- **Not verified:** LeVeque's section and equation numbers; Murphy's definition; PDEBench's 2D
  file resolution; whether its Mach 1.0 sets contain shocklets.

**Connections.** Option A is the advection test that weather verification uses to separate phase
from amplitude error, and Equation (6) is von Neumann analysis read as an error curve. Options B
and C are the project protocol's "trusted solver degraded in controlled steps", run on many
initial conditions instead of one.

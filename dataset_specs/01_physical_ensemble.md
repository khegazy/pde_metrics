# Dataset 01: a physical ensemble and independent realisations of the same flow

**Catalog clusters:** D1 (physical ensemble and independent realisations), G9 (draws per
severity: this data is its physical counterpart), B1 (the solver job that produces it).
**Metrics served:** the 8 ensemble metrics (`crps`, `crps_skill_score`, `energy_score`,
`ensemble_mean_rmse`, `rank_histogram`, `rank_histogram_chi2`, `spread_skill`,
`variogram_score`) directly; every other metric through its damage anchor (issue 004,
judgement 001); `increment_flatness` and `tail_index`, whose anchors are undefined on a
constant field (issue 037). **Ideas served:** `docs/ideas/infrastructure/robustness.md`
(the solver half of the perturbation-response experiment).
**Date:** 2026-11-05. **Author:** research sub-agent (branch `update_metric_eval_principles`).

## 1. Purpose

The ensemble metrics have one piece of evidence, `synthetic_ensemble`: independent Gaussian
noise per cell around a drifting two-scale pattern, with one noise level and no lead time
(`docs/datasets/synthetic_ensemble.md`). That validates the estimators against arithmetic and
nothing else: the members have no spatial correlation, no growth of spread with lead time, no
flow dependence, and no coherent structure, so the figures the ensemble-forecasting field
draws first (spread and error against lead time; error binned by predicted spread) cannot be
drawn (`proposals/EXP-spread_skill-perturbed-initial-condition-ensemble.md`). Every other metric
has a second want: the "unrelated field" of its damage anchor. The anchor is now the spatial
mean (judgement 001) because the translated copy that stood in for an independent realisation
was measured not to be one (`energy_changed` of 1.64 to 3.05 against the 2 of a true
realisation; issue 004). An independent realisation at the same parameters would separate
"wrong phase" from "wrong realisation" and give every metric, position-blind ones included,
its genuine score for an unrelated field.

Both wants are met by the same kind of data: several runs of one flow that differ only by a
random draw. The *ensemble* use needs the draws to be small and the runs to share a start,
so the spread grows with lead time; the *anchor* use needs the draws to be large, so the runs
share only their statistics. This document specifies one analytic system (Option A) on which
every ensemble metric has a closed-form target at every lead time, and three simulated
systems (Options B to D) that supply the physical realism the analytic system lacks.

## 2. What the dataset must provide

- **Fields.** Density and velocity on a two-dimensional periodic grid, in the canonical
  vocabulary of `fmeval/data/base.py`; vorticity is recomputed, never stored for evaluation;
  pressure only if the solver stores one that is not a function of density (the kinet
  isothermal solver's pressure is density over three and carries no information).
- **Shape.** For the ensemble use, per frame: one reference field `(C, x, y)` and a member
  stack `(N, C, x, y)`, which is the `Frame.members` contract (`fmeval/data/base.py`, lines
  247 to 257). For the anchor use, a second trajectory at the same parameters.
- **Lead-time axis.** Members and reference share a start state and are stored at a common
  set of lead times, densely at short lead (the budget residuals of cluster G1 are windowed
  quantities) and sparsely to the end of the run.
- **Several starts.** Spread and error are averaged over cases (memo Sect. 2.2, below), and
  the flow decays, so at least three start states at different stages of the flow.
- **Known answers.** For an exchangeable ensemble (Section 3 below): expected squared error
  of the ensemble mean equal to (N + 1)/N times the true variance at every lead time and in
  every spread bin; a flat rank histogram; CRPS and the variogram score at their
  distribution-determined values. On the analytic system these are closed-form numbers; on
  the simulated systems they are relations between measured quantities.
- **Unrelated realisations.** Two or more runs at identical physical parameters from
  different seeds, so that `energy_changed` against the reference is 2 to within the
  frame-to-frame spread (issue 004's acceptance criterion).

## 3. The known answer and why exchangeability is load-bearing

Leutbecher and Palmer define a *perfect ensemble* as one in which "all ensemble members and
the true state of x are independent draws from the same distribution P(x)" and add that "a
sample of n realisations from the climate distribution will constitute a perfect ensemble"
(ECMWF Tech. Memo. 514, Sect. 2.2; read in full, see References). For M independent cases
j, each with truth x_{T,j} and N members drawn from a density p_j of standard deviation
σ_j, they define the RMS spread s_j and RMS error e_j of the ensemble mean by (their Eqs. 3
and 4, with ⟨·⟩_N the mean over members)

```
s_j^2 = < ( x_{k,j} - <x_{.,j}>_N )^2 >_N ,        e_j^2 = ( x_{T,j} - <x_{.,j}>_N )^2 ,
```

and show (their Eqs. 5 to 7; convergence in probability as M grows)

```
(1/M) sum_j [ s_j^2 - (N-1)/N  sigma_j^2 ] -> 0 ,            (5)
(1/M) sum_j [ e_j^2 - (N+1)/N  sigma_j^2 ] -> 0 ,            (6)
(1/M) sum_j [ e_j^2 - (N+1)/(N-1) s_j^2 ]  -> 0 .            (7)
```

They state that (7) holds "not only in an average sense over the entire sample of cases but
also for sufficiently large subsamples which are conditioned on the predicted spread", which
is the binned spread–error diagram of their Fig. 4 (20 equally populated bins of predicted
spread). The repository's `spread_skill` writes the same relation as Fortin et al. (2014),
with the square root of the mean ensemble variance and the factor sqrt((M + 1)/M)
(`metrics/spread_skill/card.md`, Eqs. 1 to 3; `metrics/spread_skill/metric.py`, line 91), so
a perfect ensemble reads 1 there and a flat rank histogram (Hamill 2001, abstract).

**Why the truth must be one more draw, never the unperturbed run** (the author's
derivation, confirming the reviewer's finding in catalog D1). Write the members as
x_i = m + ε_i, i = 1, …, N, with the ε_i independent, zero-mean, of variance σ². If the truth
is exchangeable, x_T = m + ε_0, then E e² = σ² + σ²/N = (N + 1)/N σ², which is Eq. (6). If
instead the truth is the *unperturbed* run, x_T = m, then E e² = E|⟨ε⟩_N|² = σ²/N. With
E s² = (N − 1)/N σ² from Eq. (5), the ratio e²/s² is 1/(N − 1) instead of (N + 1)/(N − 1): the
unperturbed truth under-reports the error by a factor N + 1. Beyond the linear regime the
perturbed cloud's centre drifts away from the unperturbed trajectory, so the ratio climbs
toward its exchangeable value, but at a lead time that depends on the flow and is not known
in advance. Therefore: **every run, including the one called truth, carries its own
independent perturbation, and each run is the truth in turn**, which multiplies the cases
at no cost. Plus–minus symmetric pairs, which the ECMWF ensemble uses so that the sample
mean perturbation is exactly zero (memo Sect. 4.2, around Eq. 23), must not be used here:
the mirror of the run called truth would not be exchangeable with it (the author's
reasoning).

**Correction (2026-11-27, after the runs of build-order step 21): "each run is the truth in
turn" tests nothing.** The first half of the paragraph above stands: no run may be unperturbed.
The second half does not. Pooled over all M = N + 1 choices of truth, the ratio of the ensemble
mean's squared error to the members' variance is (N + 1)/N identically, in every cell, for any
data. With x̄ the mean of the M runs, S = Σ_i (x_i − x̄)², and m_{−j}, v_{−j} the mean and
(ddof 1) variance of the M − 1 runs other than j:

```
x_j - m_{-j} = (M/(M-1)) (x_j - xbar)                     =>  sum_j e_j^2   = (M/(M-1))^2 S
(M-2) v_{-j} = S - (M/(M-1)) (x_j - xbar)^2               =>  sum_j v_{-j}  = M S / (M-1)
sum_j e_j^2 / sum_j v_{-j} = M/(M-1) = (N+1)/N
```

(the job agent's derivation, `docs/datasets/logs/kinet_runs/shear_layer_ensemble/ensemble_results.txt`;
the second line is the leave-one-out sum of squares, re-derived here). The runs measured
1.062500 = 17/16 at every lead, which is the identity, not a finding. The pooled rank histogram
is fixed the same way: the rank of x_j among the other M − 1 runs is its rank among all M, so
pooled over j every rank occurs once per cell and the histogram is exactly flat. Exchangeability
makes the *expected* ratio for one fixed truth (N + 1)/N (Eq. 6); it does not make a pooled
statistic a test of it.

What this means for the dataset (`kinet_shear_layer_ensemble`): it takes **one fixed truth per
start** (run `member_00`, a rule fixed before any score) and the other N = 16 runs as members.
One truth's ratio scatters widely: over the 51 single truths of the three starts the velocity
ratio spans 1.02 to 1.12 at short leads and 0.46 to 1.93 at lead 5000. With three starts the
dataset holds three cases per lead, so it **cannot** certify the ensemble's calibration (Eq. 6
or 7 averaged over cases) or draw a binned spread-error diagram, and a spread-to-skill ratio or
rank histogram read on it means something only against that scatter. It **can** show how each
metric reads a real spread that grows with lead time (16-fold from start 2000, 3- and 2-fold from
5000 and 8000), with the small scales decorrelating long before the vortex pair, and how each
responds to the ensemble ladder applied to physical members, which is a rank statistic within
each frame and needs no known calibration.

## 4. Option A, the analytic ideal: a linear stochastic PDE in Fourier space

No physical *flow* has ensemble statistics in closed form; chaotic error growth has none.
What does exist is a linear PDE with additive Gaussian noise, whose solution is a Gaussian
random field with covariance known at every lead time. Its ensemble is a perfect ensemble by
construction, and every ensemble metric has a closed-form or exactly computable target.

### 4.1 Governing equation

On the periodic square [0, L)² take the stochastic advection–diffusion equation with linear
damping,

```
du = ( nu Lap(u) - mu u - c . grad(u) ) dt + dW_Q(t),                       (A.1)
```

where u(x, t) is a real scalar field, ν > 0 the diffusivity, μ ≥ 0 a damping rate, c a
constant advection velocity, and W_Q a Q-Wiener process whose covariance operator Q is
diagonal in the Fourier basis with eigenvalues q_k². Equation (A.1) is Hairer's linear SPDE
dx = Lx dt + Q dW(t) (lecture notes, Eq. 6.1), with mild solution
x(t) = S(t)x_0 + ∫_0^t S(t − s) Q dW(s) (his Definition 6.5, Eq. 6.3); its law at time t is
Gaussian with covariance Q_t = ∫_0^t S(s) Q Q* S(s)* ds and an invariant measure exists if and
only if sup_t tr Q_t < ∞ (his Theorem 6.22). Hairer treats the stochastic heat equation
itself, ∂_t u = Δu + ξ with space-time white noise, in his Sect. 2.3 (Eq. 2.5) and shows
(Eq. 2.8) that white-in-space noise gives a field that is not function-valued in two
dimensions; hence the noise here is *coloured*, q_k decaying with |k|, so that
Σ_k q_k²/(2 Re λ_k) < ∞. A Whittle–Matérn colouring q_k² ∝ (κ² + |k|²)^{−α}, which makes
the stationary field Matérn-covariant, is the choice of Lindgren, Rue and Lindström (2011;
abstract and secondary summary only).

### 4.2 The closed-form solution (the author's derivation from Theorem 6.22, mode by mode)

Expand u(x, t) = Σ_k û_k(t) e^{ik·x} with û_{−k} = conj(û_k). Each mode is an independent
complex Ornstein–Uhlenbeck process,

```
d u_k = - lambda_k u_k dt + q_k d beta_k ,     lambda_k = nu |k|^2 + mu + i c . k ,     (A.2)
```

so that, conditional on the state at t_0, the mode at lead τ is Gaussian with

```
mean  e^{-lambda_k tau} u_k(t_0),     variance  v_k(tau) = q_k^2 (1 - e^{-2 Re(lambda_k) tau}) / (2 Re(lambda_k)).   (A.3)
```

Because the modes are independent and the field is homogeneous, the per-cell variance and
the spatial covariance at lead τ are

```
sigma^2(tau) = sum_k v_k(tau),        C(r, tau) = sum_k v_k(tau) e^{i k . r},            (A.4)
```

with the stationary limit σ_∞² = Σ_k q_k²/(2 Re λ_k) (set q_0 = 0 or μ > 0 so the k = 0 mode
is bounded). The exact time-stepping of (A.2) for any Δt is
û_k(t + Δt) = e^{−λ_k Δt} û_k(t) + sqrt(v_k(Δt)) ζ_k with ζ_k a complex standard normal
subject to conjugate symmetry (the exact Ornstein–Uhlenbeck update of Gillespie 1996;
abstract only). There is no discretisation error in time and none in space beyond the
truncation at the grid's Nyquist wavenumber, which the spectrum q_k makes negligible.

### 4.3 How the ensemble is drawn exchangeably

1. Draw a start state u(t_0) from the stationary measure (mode variances q_k²/(2 Re λ_k)),
   or from any fixed field; the start is shared by all runs.
2. Run N + 1 trajectories from that one state, each with its own independent noise stream
   (its own seed), and store all of them at the common lead times τ_1, …, τ_T.
3. Call each run the truth in turn; the other N are the members. Truth and members are
   independent draws from the same conditional Gaussian, so the ensemble is perfect at every
   lead and every case, and the spread *grows* with lead from 0 to σ_∞ as in a forecast.

A second variant, **A2**, puts the randomness in the initial condition instead: N + 1
independent Gaussian perturbations of spectrum p_k² added to one field, evolved under (A.1)
with no noise. Then v_k(τ) = p_k² e^{−2 Re λ_k τ}: the spread *decays*, and with ν = μ = 0 the
spread is constant while the whole field is advected by c, so the members and truth are
displaced copies of one another up to the perturbation: a double-penalty case for the
ensemble metrics with a known answer. A2 is the stochastic generalisation of the existing
`synthetic_ensemble`, which is A2 at ν = 0 with white p_k.

### 4.4 What is known exactly, per metric

| Metric | Target at lead τ (per case; averaged over cases and in every spread bin) | Source |
|---|---|---|
| `ensemble_mean_rmse` | E e² = (N + 1)/N σ²(τ), σ² from (A.4) | memo Eq. 6 |
| `spread_skill` | sqrt((N + 1)/N) · s/e → 1 | memo Eq. 7; `spread_skill` card Eq. 3 |
| `rank_histogram`, `rank_histogram_chi2` | flat; χ² at its null | memo Sect. 2.2; Hamill 2001 |
| `crps` | per cell, for a Gaussian predictive distribution of standard deviation σ(τ): crps = σ { z[2Φ(z) − 1] + 2φ(z) − 1/√π }, z = (y − m)/σ (Gneiting et al. 2005, Eq. 5). Averaged over an exchangeable truth the expectation is σ(τ)/√π (author's derivation from the kernel form CRPS = E\|X − y\| − ½E\|X − X′\|, Gneiting and Raftery 2007 as quoted in a secondary source) | Gneiting et al. 2005 |
| `crps_skill_score` | 1 − crps/crps_ref with crps_ref the climatological score, σ_∞/√π | as above |
| `variogram_score` | the forecast's E\|X_i − X_j\|^p is closed-form, since X_i − X_j is Gaussian with variance 2[σ²(τ) − C(x_i − x_j, τ)] and E\|Z\|^p = (2 Var)^{p/2} Γ((p + 1)/2)/√π (author's derivation; score definition from Scheuerer and Hamill 2015, abstract and secondary source) | Scheuerer & Hamill 2015 |
| `energy_score` | no closed form for a multivariate Gaussian; the target is a Monte Carlo average over exact draws, which cost nothing here | — |

The finite-ensemble ("fair") estimators of these scores have the same expectations when
members and truth are exchangeable (the author's reading of the cards' estimator choices;
not re-derived here).

### 4.5 Parameters (the author's proposal) and limits

Grid 128² or 256², L = 2π, ν = 10⁻³, μ = 0.05, c = (1, 0) for the advected variant and 0
otherwise, q_k² = A (κ² + |k|²)^{−2} with κ = 2 and A chosen so that σ_∞ = 0.02 on a
background of 1 (store `density = 1 + u`, which stays positive; the catalog's D6 "positive
background"), N = 16, three start states, lead times at every 10 steps to 1 000 and every 50
to 5 000 with Δt chosen so that 2 Re λ_k τ reaches about 3 at the largest scale by the
horizon (spread near saturation). None of these numbers come from a source; they are
chosen so that the spread passes through its growth and saturation within the stored window.

Limits: no nonlinearity, no intermittency, no coherent structure, no shock; a Gaussian field
scores identically under every phase-blind metric. Option A validates *estimators and the
lead-time machinery*, as `synthetic_ensemble` validates estimators today. It is a fixture
unless the team admits it as evidence (catalog, "Decisions only a person can take", item 5).

## 5. Options B to D: simulated systems

### 5.1 Option B: the kinet shear layer with N + 1 perturbed starts (the repository's own proposal)

**Equations and regime.** The weakly compressible isothermal lattice-Boltzmann flow of
`docs/datasets/reynolds_ladder_2d.md`: D2Q9, entropic BGK, 256² cells, Re = 5 × 10⁴, Ma = 0.1,
doubly periodic. Initial condition (kinet `initialization/shear_layer.py`, read in full):
u_x = U tanh(λ(y − 1/4)) below y = 1/2 and U tanh(λ(3/4 − y)) above, u_y = ε U sin(2π(x + 1/4)),
with λ = 80 and ε = 0.05 (`configs/dc804f.yaml` on disk), the double shear layer of Brown and
Minion (1995; cited by the kinet docstring, not opened). The solver seeds the populations
from these macroscopic fields.

**Members and starts.** N = 16 members plus one, 17 runs, from each of three start states:
the stored frames at solver steps 2 000, 5 000 and 8 000 (the catalog's guess; frame 2 000 is
where the pages' runs start and the flow is developed). 51 runs of 5 000 steps.

**How the perturbation is drawn (the author's choice; the ensemble-forecasting literature
scales perturbations to an estimate of the analysis error, memo Sect. 4.3, Eq. 25, which does
not exist here).** For each run draw an independent divergence-free velocity field δu: random
Gaussian Fourier coefficients on the modes 1 ≤ |k| ≤ 16, projected perpendicular to k,
rescaled so that rms(δu) = 10⁻³ u_rms, where u_rms is the rms velocity fluctuation of the
start frame. Density is not perturbed. Independent draws, no plus–minus pairs (Section 3).
The amplitude must sit above the solver's round-off (the catalog's "round-off ranking" of the
anchor measured it) and inside the linear regime for the first few hundred steps; a run at
10⁻² u_rms should be made once to confirm the spread curves are amplitude-independent after
rescaling, which is the check that the regime is linear.

**How the perturbation enters the solver (two routes).** *Update 2026-11-26:* both routes exist
in unmodified kinet through its Python `initial_state` function, verified by running
(`00_how_to_use_kinet.md`, Section 6 and "Verified by running", check 7). Route (i) reads the
populations from the existing `kinet_re5e4` file, which stores them at every step; the member
runs themselves save only macroscopic observables (`BUILD_ORDER.md`, "How kinet runs are
configured"). The text below is as first written.
(i) *Restart from stored populations*: `kinet_re5e4` stores the distribution functions, and
catalog B1 takes a restart as feasible; I found a `resume_from` field in
`kinet/config/run_models.py` but did not verify that it restarts a simulation from stored
populations. Perturb the macroscopic velocity and rebuild the populations as
f_i = f_i^eq(ρ, u + δu) + [f_i − f_i^eq(ρ, u)], keeping the stored non-equilibrium part, so
that the restart does not inject an initial-layer transient (the author's proposal).
(ii) *Perturb at t = 0*: add δu to the shear-layer initial condition before the solver seeds
the populations; this needs only a new seeded option on `DoubleShearLayerIC` and gives one
start state (t = 0, where the layers are straight) instead of three. Route (ii) is the
cheaper first step; route (i) gives the developed starts the pages use.

**Storage cadence (catalog B1).** Every 10th step for the first 1 000 steps, then every 50th
to 5 000: 180 frames per run. Fields: density and velocity only; vorticity is recomputed.

**Decorrelation checks (physical realism, not conditions on the known answer).**
1. Spread against lead: σ(τ) should grow about exponentially at first (an error-doubling
   time is the number to report), then saturate. The saturation level for independent
   realisations is E|u_a − u_b|² = 2 Var u, the `energy_changed` of 2 (issue 004).
2. Member–member correlation at the final lead: near zero if the members have forgotten the
   start. The catalog's reviewer expects the shear layer to roll up into the same vortex pair
   in the same place for every member, so the correlation may saturate well above zero,
   especially on density; that is why Option B does not supply the *unrelated* realisations.
3. The (N + 1)/N relation itself holds at every lead regardless of 1 and 2.

**Known answer.** Section 3, at every lead and in every spread bin; plus the ensemble
degradations (`spread_inflate`, `spread_deflate`, `bias`) on physical members.

*Corrected 2026-11-27 (Section 3, correction).* Check 3 and the known answer above assumed every
run is the truth in turn; pooled that way the relation holds as an algebraic identity and tests
nothing. As run (build-order step 21; records in
`docs/datasets/logs/kinet_runs/shear_layer_ensemble/`): 17 runs per start, perturbation as
described above at rms 10⁻³ u_rms plus one run at 10⁻² u_rms (linear to about lead 500), route
(i), saved every 10th step for all 5 000 steps (the cadence above was not used), density,
velocity and vorticity kept. Measured: check 1, the velocity spread from start 2000 doubles
every 455 steps and reaches 16 times its start by lead 4000 (3.0 and 2.0 times from 5000 and
8000), no ensemble saturates; check 2, at start 2000 and lead 5000 the member variance over the
mean energy is 0.37 at 64 < |k| ≤ 182 and 5.7e-5 at |k| ≤ 4, so the filaments decorrelate long
before the vortex pair. The dataset `kinet_shear_layer_ensemble` uses one fixed truth per start;
its three starts are three cases, read against the single-truth scatter of Section 3's
correction.

**Cost and size.** 51 runs of 5 000 steps at 256². Wall-clock: unknown; the on-disk
`slurm_logs` folders of both kinet configurations are empty, so one run must be timed before
the job is sized (catalog B1's blocker). Storage: 9 180 frames × 3 channels × 256² × 8 B =
13.8 GiB in float64 (the catalog's 14 GB), 6.9 GiB in float32.

**Reuses.** The `kinet_re5e4` trajectory (start frames, and the reference for the
`forecast_re5e4` lead times, 0.1128 to 1.1276, which fall inside the stored window).

### 5.2 Option C: two-dimensional decaying turbulence from random-phase spectra with different seeds

This is the source of *unrelated* realisations and, run as a climatological sample, a perfect
ensemble of the uninformative kind (memo Sect. 2.2: "a sample of n realisations from the
climate distribution will constitute a perfect ensemble").

**Standard configuration (San and Staples 2012, Sect. 6, read in full on ar5iv).** The
dimensionless vorticity equation with viscous term (1/Re)∇²ω (their Eq. 1) on the periodic
square of side 2π. Initial energy spectrum

```
E(k) = (a_s / 2) (1 / k_p) (k / k_p)^(2s+1) exp[ -(s + 1/2) (k / k_p)^2 ],   a_s = (2s+1)^(s+1) / (2^s s!),     (Eqs. 45, 46)
```

with s = 3 and k_p = 12; vorticity magnitude |ω̂(k)| = sqrt(k E(k)/π) (Eq. 47); phase
ω̂(k) = |ω̂(k)| e^{iζ(k)}, ζ(k) = ξ(k) + η(k) with ξ and η independent uniform in [0, 2π] in
the first quadrant and conjugate-symmetry sign relations in the others (Eqs. 48, 49);
resolution 1024²; Re = 100 to 6 000; Δt = 2 × 10⁻⁴; snapshots at t = 2 and 5. A different
seed for (ξ, η) is a different realisation of the same spectrum: that is the whole recipe.
The seminal setup is McWilliams (1984), from which later random-phase initial conditions
descend; only its abstract could be read here (the open copies are scanned images), so no
formula or parameter is attributed to it in this document. Bracco et al. (2000) extend it to
higher resolution (abstract only).

**The kinet analogue, already on disk (catalog Section 1.3).** The folder
`kinet/homogeneous_isotropic_turbulence/weakly_compressible_isoT_fluids/sys_Re-5e4_Ma-1en1/`
holds a two-dimensional D2Q9 run with a random-mode initial condition (`k0: 4`,
`random_seed: 42`, density 1, Re 5 × 10⁴, Ma 0.1) at 128² (5 000 steps), 256² (10 000 steps)
and 512² (20 000 steps), each to the same physical end time as `kinet_re5e4`. The reviewer
measured that the three are *different* fields (initial x-velocity correlation after block
averaging 0.12 and 0.005), so they are three independent realisations at three resolutions,
not a refinement sequence. The configuration fields `k0` and `random_seed` are declared in
`kinet_orig/kinet/config/components/scheme.py` (`CaseInitialConditions`); the generator that
consumes them was not located in the package source searched here, so how the random modes
are drawn (per cell, as the reviewer measured, or per mode) should be read from kinet before
new seeds are run.

**Proposed runs (the author's choice).** The on-disk configuration at 256² with seeds 1 to 8
(the existing seed 42 at 256² makes nine), 10 000 steps, stored every 50th step: 200 frames.
Store density and velocity. This gives (a) eight unrelated realisations for the anchor of
every metric, with `energy_changed` of 2 as the acceptance test, (b) a climatological perfect
ensemble of nine, (c) an isotropic reference for the isotropy half of issue 001. If the
isotropic flow is also wanted as a *perturbed* ensemble, apply Option B's recipe to one of its
developed frames; the members then do decorrelate, because nothing fixes where its vortices
sit.

**Cost and size.** Eight runs of 10 000 steps at 256²; wall-clock unknown (see Option B).
Storage: 8 × 200 × 3 × 256² × 8 B = 2.4 GiB.

### 5.3 Option D: forced two-dimensional Kolmogorov flow, with seeds or long windows

A statistically stationary flow gives independent realisations by *time*: windows of one
long run separated by many correlation times, as well as by seed. It also gives a perturbed
ensemble whose climatology does not decay, so one start state suffices.

**Standard configuration (Chandler and Kerswell 2013, Sect. 2, read in full on ar5iv; the
same equations in Lucas and Kerswell 2014, Eqs. 1 to 7).** Incompressible Navier–Stokes on
the torus [0, 2π]² with body force χ sin(2π n y*/L_y) x̂ (C&K Eq. 1); non-dimensionalised by
length L_y/2π and time sqrt(L_y/(2π χ)) to

```
du/dt + u . grad(u) + grad(p) = (1/Re) Lap(u) + sin(n y) x_hat,   div(u) = 0,     Re := (sqrt(chi)/nu) (L_y / 2 pi)^(3/2),   (C&K Eqs. 3 to 5)
```

with n = 4, solved in vorticity form (C&K Eq. 6) by a de-aliased pseudo-spectral code
(Bartello and Warn 1996), Crank–Nicolson for the viscous term and Heun's method for the
rest; N_x = N_y = 256; Δt = 0.005 at Re = 40, 0.003 at 60, 0.0025 at 80, 0.002 at 100
(their Table 1); random initial conditions; data sets of 10⁵ time units (3 × 10⁵ for the
longer series). Diagnostics: energy E = ½⟨u²⟩, dissipation D = (1/Re)⟨|∇u|²⟩, input
I = ⟨u sin(ny)⟩ (their Eqs. 13, 14); laminar values E_lam = Re²/(4n⁴), D_lam = Re/(2n²)
(Eq. 15), which normalise every reported statistic. Lucas and Kerswell (2014) report
128 modes per 2π, Δt = 0.05 at Re = 20 and 0.001 at Re = 120, and 2 × 10⁶ steps of a
512 × 128 grid in 63 minutes on one GPU (their Sect. II).

**Proposed runs (the author's choice).** Re = 40, n = 4, 256², one long run of 10⁴ time units
after a transient of 500 (C&K discard 500 and average over the next 1 000 in their Fig. 3
scan), stored every 0.5 time units; plus 17 perturbed runs of 50 time units from one
developed state by Option B's recipe. Known answers: the time-mean D/D_lam and I/D_lam of
the stationary state (reported in C&K's figures, not quoted here) as a check of
stationarity, and Section 3's relation for the ensemble. Windows for the anchor: separated
by at least 50 time units (the author's guess at several correlation times; measure the
autocorrelation of D(t) and set the separation from it, which is also issue 114's block
length).

**Cost and size.** By Lucas and Kerswell's timing, 2 × 10⁶ steps of 65 536 cells take about
an hour on one GPU; 10⁴ time units at Δt = 0.005 is 2 × 10⁶ steps, so the long run is about
an hour and the 17 short runs together about the same (the author's arithmetic). Storage:
2 × 10⁴ frames × 2 channels × 256² × 8 B = 20 GiB for the long run in float64; store every
2 time units instead for 5 GiB. **Solver:** not kinet as it stands. `kinet_orig` carries a
stochastic low-mode forcing law (`solver/common/forcing/laws/random_modes.py`, Eswaran–Pope
Ornstein–Uhlenbeck coefficients projected perpendicular to k), which partly answers the
catalog's open question on forcing, but no deterministic sin(ny) force and no large-scale
drag were found in the directories searched. A 256² pseudo-spectral code is a few hundred
lines and the configuration above is complete enough to write one.

### 5.4 Not acceptable

A chaotic low-dimensional system (Lorenz-63, Lorenz-96) embedded as a field on a grid is not
acceptable: the repository's metrics act on fields with spatial structure, spectra and
boundaries, and a tiled or interpolated scalar time series has none of them.

## 6. Recommendation

1. **Option A first** (days, no solver): it is the only system on which every ensemble
   metric has a closed-form target *along a lead-time axis*, which is what the cards cannot
   show today; it exercises the reader that assembles members from separate runs, the
   lead-time axis of the analysis, and the binned spread–error diagram, on data whose
   answer is exact. Build the reader in the `ClosedFormTrajectory` pattern of
   `fmeval/data/analytic.py` so the fields can be generated from a seed as well as stored.
2. **Option B next** (the catalog's build 1): the physical evidence for the eight ensemble
   cards, and the many-initial-condition trajectories of D2 and the windowed budgets of G1 from the same job. Time one
   run first. Route (i) is available (see the update in Section 5), so the three developed
   start states can be used.
3. **Option C alongside B**, because the shear layer will probably not supply unrelated
   realisations (Section 5.1, check 2) and the isotropic configuration already exists on
   disk with a seed option. Its reader also serves catalog B7.
4. **Option D later**, when a stationary flow is wanted for the base-period protocol and the
   block-length statistics (issues 042, 114); it is also the natural home of the forced
   turbulence of cluster D4 if a compressible forced run (B2) does not materialise.

## 7. What to store

Following `docs/recipes/add-a-dataset.md`:

- **Layout.** One HDF5 file per run, in the `kinet_raw` layout the existing reader
  (`fmeval/data/kinet_raw.py`) already parses for Options B and C; for Options A and D a
  new layout read by one reader. Fields under their canonical names: `density` `(T, x, y)`,
  `velocity` `(T, 2, x, y)`, channel-first with trailing spatial axes; the physical time of
  every frame; no vorticity for evaluation (recomputed on the analysis grid) and no pressure
  unless the solver stores one that is not a function of density.
- **Ensemble assembly.** A reader that opens the N + 1 run files of one start, takes run r as
  the reference and the other N as `members[name]` of shape `(N, C, x, y)`, exposes r as a
  configuration option so every run is the truth in turn, and sets `is_ensemble`. The lead
  time of each frame goes into the row as `lead_step` and `lead_time`, as the forecast
  reader (`fmeval/data/forecast.py`) already does. *Corrected 2026-11-27:* as built, the
  `kinet_raw` option `members` (a glob of the run files beside the truth) assembles the members,
  the truth is one fixed run (Section 3, correction), and the rows carry `lead_time` only: the
  analysis reads a `lead_step` as marking a candidate forecast's rows, which an ensemble's
  ladder rows are not.
- **Precision.** float64 as written by kinet and by the exact Ornstein–Uhlenbeck update;
  float32 copies are acceptable for the member stacks (the Well-format copy of `kinet_re5e4`
  is float32 and is checked identical to the raw run by a data-marked test).
- **Grid and boundaries.** `GridSpec.boundary = ("periodic", "periodic")` for every option;
  256² for B and C, 128² or 256² for A and D; the analysis grid at the run's own resolution.
- **Provenance per run.** The solver config hash (kinet writes `configs/<hash>.yaml`), the
  perturbation seed and amplitude, the start frame, and for Option A the parameters
  (ν, μ, c, κ, A), the noise seed and a table of σ²(τ) from (A.4) at the stored leads, as
  HDF5 attributes, so the known answer travels with the data.
- **Configuration.** `configs/dataset/<name>.yaml` per option, with a shared `_`-fragment
  for what the runs of one option share, and the `complexity` block naming the family.

## 8. References

- Leutbecher, M. and Palmer, T. N. (2008). Ensemble forecasting. *Journal of Computational
  Physics* 227(7), 3515–3539, https://doi.org/10.1016/j.jcp.2007.02.014. **Read in full as
  ECMWF Technical Memorandum 514 (2007)**,
  https://www.ecmwf.int/sites/default/files/elibrary/2007/10729-ensemble-forecasting.pdf;
  Sect. 2.2 (Eqs. 3 to 7, Fig. 4), Sect. 4.2 (plus–minus symmetric sampling, Eq. 23),
  Sect. 4.3 (amplitude scaling, Eq. 25). Equation numbers are the memorandum's; the journal
  numbering was not checked.
- Fortin, V., Abaza, M., Anctil, F. and Turcotte, R. (2014). Why should ensemble spread
  match the RMSE of the ensemble mean? *Journal of Hydrometeorology* 15(4), 1708–1713,
  https://doi.org/10.1175/JHM-D-14-0008.1. **Not opened here**; cited through
  `metrics/spread_skill/refs.bib`, whose author read it in full (Eqs. 9, 14 to 16).
- Hamill, T. M. (2001). Interpretation of rank histograms for verifying ensemble forecasts.
  *Monthly Weather Review* 129(3), 550–560. **Abstract and secondary summaries only.**
- Gneiting, T., Raftery, A. E., Westveld, A. H. and Goldman, T. (2005). Calibrated
  probabilistic forecasting using ensemble model output statistics and minimum CRPS
  estimation. *Monthly Weather Review* 133(5), 1098–1118,
  https://doi.org/10.1175/MWR2904.1. **Read in full** (University of Washington copy); the
  Gaussian closed form is their Eq. (5).
- Gneiting, T. and Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and
  estimation. *Journal of the American Statistical Association* 102(477), 359–378,
  https://doi.org/10.1198/016214506000001437. **Secondary source only** for the kernel
  form of the CRPS; its equation number was not verified.
- Scheuerer, M. and Hamill, T. M. (2015). Variogram-based proper scoring rules for
  probabilistic forecasts of multivariate quantities. *Monthly Weather Review* 143(4),
  1321–1334, https://doi.org/10.1175/MWR-D-14-00269.1. **Abstract and secondary source
  only.**
- Hairer, M. (2009, revised 2023). An introduction to stochastic PDEs. Lecture notes,
  arXiv:0907.4178, https://arxiv.org/abs/0907.4178. **Read in full** (Sect. 2.3, Eqs. 2.5
  and 2.8; Sect. 6, Eqs. 6.1 and 6.3, Definition 6.5, Theorem 6.22).
- Da Prato, G. and Zabczyk, J. (2014). *Stochastic Equations in Infinite Dimensions*, 2nd
  ed., Encyclopedia of Mathematics and its Applications 152, Cambridge University Press.
  **Not opened**; Hairer's Sect. 6 states that its material is in this monograph.
- Lord, G. J., Powell, C. E. and Shardlow, T. (2014). *An Introduction to Computational
  Stochastic PDEs*, Cambridge University Press. **Not opened**; no chapter or example is
  cited from it.
- Lindgren, F., Rue, H. and Lindström, J. (2011). An explicit link between Gaussian fields
  and Gaussian Markov random fields: the stochastic partial differential equation approach.
  *Journal of the Royal Statistical Society B* 73(4), 423–498,
  https://doi.org/10.1111/j.1467-9868.2011.00777.x. **Abstract and secondary summary
  only**; the Matérn form of q_k is from that summary.
- Gillespie, D. T. (1996). Exact numerical simulation of the Ornstein–Uhlenbeck process and
  its integral. *Physical Review E* 54(2), 2084–2091,
  https://doi.org/10.1103/PhysRevE.54.2084. **Abstract only**; the update in Sect. 4.2 is
  the standard exact transition, derived here from (A.2).
- McWilliams, J. C. (1984). The emergence of isolated coherent vortices in turbulent flow.
  *Journal of Fluid Mechanics* 146, 21–43, https://doi.org/10.1017/S0022112084001750.
  **Abstract only**; the open PDF copies are scanned images that could not be read here.
- Bracco, A., McWilliams, J. C., Murante, G., Provenzale, A. and Weiss, J. B. (2000).
  Revisiting freely decaying two-dimensional turbulence at millennial resolution. *Physics
  of Fluids* 12(11), 2931–2941, https://doi.org/10.1063/1.1290391. **Abstract only.**
- San, O. and Staples, A. E. (2012). High-order methods for decaying two-dimensional
  homogeneous isotropic turbulence. *Computers & Fluids* 63, 105–127,
  https://doi.org/10.1016/j.compfluid.2012.04.006; arXiv:1212.0920. **Read in full on
  ar5iv** (Sect. 6, Eqs. 45 to 49).
- Chandler, G. J. and Kerswell, R. R. (2013). Invariant recurrent solutions embedded in a
  turbulent two-dimensional Kolmogorov flow. *Journal of Fluid Mechanics* 722, 554–595,
  https://doi.org/10.1017/jfm.2013.122; arXiv:1207.4682. **Read in full on ar5iv**
  (Sect. 2, Eqs. 1 to 6 and 13 to 15; Table 1).
- Lucas, D. and Kerswell, R. R. (2014). Recurrent flow analysis of two-dimensional
  Kolmogorov flow. arXiv:1406.1820 (published in *Physics of Fluids* 27, 045106, 2015; the
  journal reference was not checked). **Read in full** (Sect. II, Eqs. 1 to 7, 10).
- Bartello, P. and Warn, T. (1996). Self-similarity of decaying two-dimensional turbulence.
  *Journal of Fluid Mechanics* 326, 357–372. **Not opened**; cited as C&K's code source.
- Eswaran, V. and Pope, S. B. (1988). An examination of forcing in direct numerical
  simulations of turbulence. *Computers & Fluids* 16(3), 257–278. **Not opened**; cited by
  kinet's `random_modes.py` docstring.
- Brown, D. L. and Minion, M. L. (1995). Performance of under-resolved two-dimensional
  incompressible flow simulations. *Journal of Computational Physics* 122, 165–183.
  **Not opened**; cited by kinet's `shear_layer.py` docstring for the profile.
- Repository sources read in full: `FUTURE_EXPERIMENTS_CATALOG.md` (Sects. 1.3, 2.1 D1, 2.2
  G9, 3.1 B1); `proposals/EXP-spread_skill-perturbed-initial-condition-ensemble.md`;
  `issues/003`, `issues/004`; `judgements/001`; `docs/datasets/synthetic_ensemble.md`,
  `docs/datasets/reynolds_ladder_2d.md`; `docs/recipes/add-a-dataset.md`;
  `metrics/spread_skill/{card.md,metric.py,refs.bib}`; `fmeval/data/base.py`; the kinet
  configs on disk (`dc804f.yaml`, `7a428c.yaml`, `8b7a9e.yaml`, `aaa638.yaml`, `b45da0.yaml`).

## 9. Confidence

**Sure of.** The perfect-ensemble relations and their numbering (memo Eqs. 3 to 7), the
20-bin spread–error diagram (Fig. 4), and the plus–minus sampling and amplitude-scaling
passages, all read from the memorandum's text. Hairer's Eq. 6.1, Definition 6.5 and Theorem
6.22 as the source of the Gaussian law and its covariance Q_t. The Gaussian CRPS closed form
as Eq. (5) of Gneiting et al. (2005). San and Staples' spectrum and random-phase recipe
(Eqs. 45 to 49, s = 3, k_p = 12, 1024², Δt = 2 × 10⁻⁴). Chandler and Kerswell's equations,
Re definition, n = 4, 256², time steps and 10⁵-time-unit data sets, and the laminar values.
Lucas and Kerswell's resolution and GPU timing. The kinet configurations on disk and the
shear-layer initial condition in the source. The absence of timings in the on-disk
`slurm_logs`.

**Reasoning, not sourced.** The factor N + 1 for an unperturbed truth (Section 3); the
mode-by-mode solution (A.2) to (A.4) and the exact update, which follow from Theorem 6.22
by diagonalising in Fourier modes; the expected CRPS σ/√π and the variogram-score target,
which are Gaussian moments; every parameter in Sect. 4.5 and every run count, amplitude,
cadence and window separation in Sects. 5.1 to 5.3; the arithmetic of sizes and the
GPU-hour estimate; the restart reconstruction f = f^eq(ρ, u + δu) + f^neq.

**Not checked.** The journal numbering of the memorandum's equations; whether kinet can
restart from stored populations (`resume_from` was seen, not understood) or accept a seeded
velocity perturbation; how kinet's random-mode initial condition is drawn (its generator was
not located; the catalog's reviewer measured per-cell draws); McWilliams (1984)'s initial
spectrum and parameters, which could not be read; Bracco et al. (2000)'s setup; Fortin et
al. (2014), Lord, Powell and Shardlow (2014), Da Prato and Zabczyk (2014), Gneiting and
Raftery (2007), Scheuerer and Hamill (2015) and Lindgren et al. (2011) beyond their
abstracts or secondary summaries; whether the fair estimators in the cards have the
expectations claimed in Sect. 4.4 under exchangeability; the wall-clock of one 256² kinet
run, which must be measured before Option B is sized.

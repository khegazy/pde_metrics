# Dataset 04: forced, statistically stationary turbulence with an inertial range

**Catalog clusters:** D4 (forced, statistically stationary turbulence with an inertial range,
forms (a) and (b)), B2 (the forced two-dimensional build), and the base period that
`EXP-tail_exceedance-base-period-climatology` asks for (indexed with G2; see the note at the end
of Section 1). **Metrics served:** the eight spectral, increment and tail metrics
(`spectrum_l2`, `spectral_energy_flux`, `increment_w1`, `increment_w1_by_separation`,
`increment_flatness`, `energy_distance`, `tail_index`, `tail_exceedance`). **Ideas and issues
served:** the two-dimensional cascade checks of issue 085, a physical separation scale for the
increment metrics (issue 128), the four-fifths law and structure-function rows of
`docs/ideas/README.md`. **Date:** 2026-11-26. **Author:** research sub-agent (branch
`build_datasets`). Nothing here was run; every number marked "my arithmetic" or "my design" is
an estimate to be checked on a pilot run.

## 1. Purpose

Each of the eight metrics comes from a field that defines it on stationary turbulence with a
scaling range: a spectrum drawn against $k^{-5/3}$ and $k^{-3}$ and compensated to read a
plateau (`metrics/spectrum_l2/card.md`, "How its field reports it"); a flux $\Pi(k)$ normalised
by the injection rate, with a plateau and a sign change at the forcing scale
(`metrics/spectral_energy_flux/card.md`, same section); the flatness of increments against
separation in units of the dissipation and integral scales (`metrics/increment_flatness/card.md`;
issue 128); and an exceedance rate against a threshold set on a separate base period
(`proposals/EXP-tail_exceedance-base-period-climatology.md`). Every flow in the repository
decays, so a card can show today only that its number moves under damage, not that it reads the
statistic its field defines (`FUTURE_EXPERIMENTS_CATALOG.md`, D4, "Serves").

A stationary record in two dimensions needs two things: a force at a chosen wavenumber $k_f$,
and a large-scale drag. Without the drag the inverse energy cascade carries energy to the box
scale, where it piles up as a pair of box-size vortices (a condensate) and the energy grows
without bound (Chertkov et al. 2007, read in full via ar5iv: zero friction, two box-size
vortices form after $\tau^* \sim \epsilon^{-1/3} L^{2/3}$, energy grows at the injection rate).
Kritsuk's forced compressible runs have no friction, and his Case B "is not statistically
stationary and continues to grow at a rate of approximately $0.33\,\epsilon_f$" over the
averaging window (Kritsuk 2019, Fig. 6 caption, read via the arXiv HTML), which is the
catalog reviewer's correction to B2.

*Note on G2.* The G2 entry of the catalog (Sect. 2.1, Pareto spikes and tail-only damage)
contains no base-period text in the copy read on 2026-11-26. The base period belongs to the
`tail_exceedance` proposal (catalog cross-reference table: D4 for data, H1 for the harness).
The link to G2 is mine: G2's tail axes have a known answer relative to a fixed climatological
threshold only if the reference's own tail is stationary, which is what this record supplies.

## 2. What the dataset must provide

- **Fields:** density and velocity on a periodic grid (two or three dimensions); pressure only
  where a solver writes a thermodynamic one (never computed from density, by repository rule,
  `docs/recipes/add-a-dataset.md`, Sect. 1).
- **Boundaries:** periodic on every axis, because `spectrum_l2` and `spectral_energy_flux` need
  a periodic transform and the increment metrics wrap.
- **Grid:** at least 1024² in 2D for a decade on each side of $k_f$ (Option B); 256³ cutouts or
  1024² periodic planes in 3D (Option D).
- **Stationarity:** a spin-up that is discarded, then a **base period** and a disjoint
  **evaluation period**, each at least ten correlation times of the large-scale energy (my
  choice of ten; the proposal says "several"), with a gap of one or more large-eddy times
  between them so the two are close to independent.
- **Cadence:** fine enough to measure the correlation time (at least ten frames per large-eddy
  time), coarse enough for storage.
- **Realisations:** one long run serves the base-period protocol; a second seed doubles the
  evaluation sample for the rank correlations.
- **Known in advance:** the spectral slopes on each side of $k_f$, the flux plateau values and
  their signs, the third-order structure-function laws, the forcing and dissipation scales in
  cells (so issue 128 can state a separation physically), and the injection rate that
  normalises the flux.

## 3. Option A, the analytic ideals

**There is no exact stationary turbulent solution.** The nearest known-answer objects are
scaling laws that a simulation must reproduce (A1, A2), and two synthetic stationary records
whose statistics are exact (A3, A4). By Kareem's rule, A3 is a reader that computes fields on
the fly, not a dataset; A4 is a cheap one-dimensional simulation that a reader can run from a
seed.

### 3.1 A1: the Kraichnan–Batchelor laws of forced 2D turbulence

The equation of motion of forced two-dimensional turbulence with a linear friction is, in
vorticity form (Boffetta and Musacchio 2010, Eq. 1; Boffetta 2007, Eq. 1; both read in full via
ar5iv),

$$\partial_t \omega + \mathbf{u}\cdot\nabla\omega = \nu \nabla^2 \omega - \alpha\,\omega + f_\omega \tag{1}$$

where $\omega$ is the vorticity, $\nu$ the kinematic viscosity, $\alpha$ the friction rate and
$f_\omega$ a forcing that is white in time and concentrated at the scale $\ell_f = 2\pi/k_f$.
Energy $E = \tfrac12\langle|\mathbf u|^2\rangle$ injected at rate $\epsilon_I$ splits into a
part $\epsilon_\alpha$ carried to large scales and removed by friction and a part
$\epsilon_\nu$ removed by viscosity; enstrophy injected at $\eta_I \simeq k_f^2\epsilon_I$ goes
mostly to small scales (Boffetta 2007, text after Eq. 2; Boffetta and Musacchio 2010, Table I:
$\epsilon_\alpha/\epsilon_I$ from 0.54 at 2048² to 0.98 at 32768², $\eta_\nu/\eta_I$ about
0.9). The energy spectra are (Boffetta and Ecke 2012, Eqs. 12–13, p. 431, as recorded in
`metrics/spectrum_l2/card.md`; the logarithmic factor is Kraichnan's, as Kritsuk 2019, Sect. 3,
writes it)

$$E(k) = C\,\epsilon^{2/3} k^{-5/3}\quad (k \ll k_f), \qquad
E(k) = C'\,\eta^{2/3} k^{-3}\,[\ln(k/k_f)]^{-1/3}\quad (k \gg k_f) \tag{2}$$

with $C \approx 6$ (Boffetta 2007, Fig. 2; Boffetta and Musacchio 2010, "independent of
resolution"; Boffetta and Ecke 2012, Fig. 5a, $6.0 \pm 0.4$, as recorded on the card). The
fluxes are constant across each range: $\Pi_E(k) = -\epsilon_\alpha$ for $k < k_f$ (inverse) and
$\Pi_Z(k) = \eta_\nu$ for $k > k_f$ (direct). The longitudinal third-order structure function
$S_3(r) = \langle(\delta_r u_L)^3\rangle$ obeys (Boffetta and Musacchio 2010, Eqs. 4–5)

$$S_3(r) = \tfrac32\,\epsilon_\alpha\, r \quad (r \gg \ell_f), \qquad
S_3(r) = \tfrac18\,\eta_\nu\, r^3 \quad (r \ll \ell_f) \tag{3}$$

both positive, which Lindborg (1999, abstract read) derived and tested on aircraft data. The
friction arrests the inverse cascade at

$$\ell_\alpha \simeq \epsilon_\alpha^{1/2}\,\alpha^{-3/2} \tag{4}$$

(Boffetta and Musacchio 2010, after Table I; Boffetta 2007). The viscous scale is
$\ell_\nu = \nu^{1/2}\eta_\nu^{-1/6}$ (same tables). Increments in the inverse range show "no
measurable intermittency correction" (Boffetta, Celani and Vergassola 2000, abstract read), and
their densities are close to Gaussian (Boffetta and Ecke 2012, p. 438, Fig. 6, as recorded in
`metrics/increment_flatness/card.md`); vorticity increments become intermittent when the flow
has friction (same, p. 444).

*Two caveats.* (i) Friction steepens the direct range: Boffetta and Musacchio (2010, Table I)
report a correction $\delta$ to the $-3$ exponent of 1.8, 1.1, 0.75, 0.50 and 0.35 as the
resolution rises from 2048² to 32768², and Boffetta (2007) saw about $-3.6$ at 16384²; a pure
$k^{-3}$ needs both ranges very long. (ii) These are incompressible laws; Option B is at Mach 0.1
and inherits them up to corrections of order Ma² (my reasoning, not checked against a source).

**What A1 gives the eight metrics:** reference curves for the figures (slopes, $C$, flux
plateaus, $S_3$), and the scales $\ell_f, \ell_\alpha, \ell_\nu$ in cells for issue 128. **What
it does not give:** a field. It is a check a simulated reference must pass before it is used.

### 3.2 A2: the four-fifths law and the 3D inertial range

For stationary, homogeneous, isotropic three-dimensional turbulence at high Reynolds number,
Kolmogorov's four-fifths law is

$$\langle(\delta_r u_L)^3\rangle = -\tfrac45\,\epsilon\, r \tag{5}$$

in the inertial range, with $E(k) = C_K\epsilon^{2/3}k^{-5/3}$ (Kolmogorov 1941; Frisch 1995,
ch. 6). Neither source was opened here: Eq. (5) is graduate textbook material and its equation
number in Frisch was not checked. The flatness of the longitudinal velocity gradient, the
smallest-separation limit of `increment_flatness`, fits $F \sim 1.14\,R_\lambda^{0.34}$ in DNS up
to $R_\lambda \approx 1130$ (Ishihara et al. 2007, abstract read), which is about 9.0 at the
Johns Hopkins $R_\lambda = 433$ (my arithmetic). **Gives:** the sign and size of the 3D flux and
$S_3$, the slope, and a flatness target at the dissipative end. **Does not give:** a field, or
any 2D answer (in 2D the energy flux is inverse and $S_3$ is positive, Eq. 3).

### 3.3 A3: a stationary Gaussian random field with a prescribed spectrum (a reader)

A synthetic stationary record with exactly known statistics, which is a **known null rather than
turbulence**. On an $N^2$ periodic grid, draw a streamfunction whose Fourier coefficients
$\hat\psi_{\mathbf k}(t)$ evolve as independent complex Ornstein–Uhlenbeck processes (my
construction):

$$d\hat\psi_{\mathbf k} = -\frac{\hat\psi_{\mathbf k}}{\tau_k}\,dt + \sqrt{\frac{2\sigma_k^2}{\tau_k}}\,dW_{\mathbf k},
\qquad \sigma_k^2 \propto \frac{E(k)}{k^3}, \qquad \hat{\mathbf u}_{\mathbf k} = i\,\mathbf k^\perp\hat\psi_{\mathbf k} \tag{6}$$

with Hermitian symmetry, $E(k) = A k^{-5/3}$ (or $k^{-3}$, or both on two sides of a $k_f$) on
$k_{\min} \le |\mathbf k| \le k_{\max}$, and $\tau_k$ a chosen correlation time per mode (for
example an eddy time $\propto k^{-2/3}$, my choice). The $k^{-3}$ factor turns the shell spectrum
of $\mathbf u$ into a per-mode variance of $\psi$ in 2D (my arithmetic: $|\hat{\mathbf u}|^2 =
k^2|\hat\psi|^2$ and a shell holds $\propto k$ modes). Starting the process from its stationary
law makes every frame stationary. A density channel is a second, independent field of the same
form around 1 (my choice), or uniform.

**Known exactly** (my derivations, from Gaussianity and the Wiener–Khinchin relation on the
periodic grid): the expected spectrum at every frame; the time correlation
$e^{-|\Delta t|/\tau_k}$ of each mode; zero expected energy flux and zero $S_3$ at every scale
(odd moments of a Gaussian vanish); Gaussian increments at every separation with flatness 3; the
increment variance along axis $j$, $S_2^{(j)}(r) = 2\sum_{\mathbf k}\langle|\hat u_j(\mathbf
k)|^2\rangle\,[1 - \cos(k_j r)]$; and the exceedance probability of a threshold $q$,
$P(|\delta_r u| > q) = \operatorname{erfc}\!\big(q/\sqrt{2S_2(r)}\big)$. **Gives the eight
metrics:** a null for each: `spectrum_l2` and the distribution distances between two seeds
measure only sampling noise; `spectral_energy_flux` must read zero; `increment_flatness` must
read 3 at every separation; `tail_index` must read a Hill estimate that tends to 0 (a Gaussian
has no power tail); `tail_exceedance` must find the same rate in and out of a base period, up to
the in-base bias of Zhang et al. (2005, abstract). **Does not give:** a cascade, a flux sign
change, intermittency or coherent structures. It is the time-resolved version of the
`gaussian_impostor` degradation (`degradations/gaussian_impostor/card.md`), and belongs with
BUILD_ORDER item 0.8 ("Random fields with known statistics", spec 09, not yet written); the
reader should be written once there and share the impostor's spectral code. **Reader needs:**
grid $N$, box length, spectrum form and exponent(s), $k_{\min}, k_{\max}$, amplitude (target
rms speed), $\tau_k$ law, number of frames and frame spacing, and a seed (issue 044 asks for the
run seed to reach readers).

### 3.4 A4: stationary one-dimensional Burgers turbulence (a cheap simulation)

The randomly forced Burgers equation, $\partial_t u + u\,\partial_x u = \nu\,\partial_x^2 u + f$,
with a Gaussian force $\langle f(x,t)f(x',t')\rangle = B(x-x')\,\delta(t-t')$ (Bec and Khanin
2007, Eq. 7.1, read in part via ar5iv). For a smooth (large-scale) $B$ "the solution reaches
exponentially fast a statistically stationary régime" (Sect. 7); their numerics force the first
three Fourier modes with equal variances (Fig. 40 caption). **Known:** structure functions
$\langle|\delta_r u|^p\rangle \propto r^{\zeta_p}$ with $\zeta_p = \min(p, 1)$, because "with a
probability $r/L_f$ the two points are sitting on different sides of a shock" (Sect. 7.1); hence
$E(k) \propto k^{-2}$ and an increment flatness growing as $r^{\zeta_4 - 2\zeta_2} = r^{-1}$ as
$r$ falls through the inertial range (both my derivations from $\zeta_p$); and a left tail of the
velocity-gradient density $p(\xi) \propto |\xi|^{-7/2}$, for which the review reports "strong
evidence" while recording competing predictions such as an exponent of 3 (Sects. 7.2–7.3).
**Gives:** a stationary flow with a known intermittent increment law and a known spectrum for
`increment_flatness`, `increment_w1_by_separation`, `spectrum_l2` and the base-period protocol.
**Does not give:** two dimensions, a cascade of a conserved quadratic invariant in the 2D sense,
or a closed form per frame. Whether the one-cell increments of a resolved run see the
$|\xi|^{-7/2}$ law, rather than the shock population, is my open question, so it is not offered
as a `tail_index` target. **Reader needs:** $N$ (for example $2^{14}$ on $[0, 2\pi)$, my
choice), $\nu$, the forced modes and their variance, the step, the seed, the spin-up and frame
spacing. A pseudo-spectral or Godunov integrator of about fifty lines suffices (Bec and Khanin
2007, Sect. 2.4.1, Godunov and related schemes); storing one run is cheaper than re-integrating
from $t = 0$ in a reader each time (my judgement). The 1D grid path exists (`sod_shock_tube` is
1D, `fmeval/data/analytic.py`).

## 4. Options B to E: simulated systems

### 4.1 Option B: kinet forced 2D weakly compressible turbulence with a drag (recommended)

**Equations.** kinet's `weakly_compressible_isothermal_fluids` physics on D2Q9 recovers the
isothermal compressible Navier–Stokes equations with a body force (kinet guide, Sect. 1;
`docs/kinetic-theory/weakly-compressible.qmd` there):

$$\partial_t\rho + \nabla\cdot(\rho\mathbf u) = 0, \qquad
\partial_t(\rho\mathbf u) + \nabla\cdot(\rho\mathbf u\mathbf u) = -\nabla p + \nabla\cdot\boldsymbol\tau
+ \rho\,\mathbf a(\mathbf x, t) - \alpha\,\rho\,(\mathbf u - \langle\mathbf u\rangle) \tag{7}$$

with $p = c_s^2\rho$, $c_s^2 = 1/3$ in lattice units, $\boldsymbol\tau$ the viscous stress of
viscosity $\nu$, $\mathbf a$ the `random_modes` acceleration (an Ornstein–Uhlenbeck process per
Fourier mode, projected solenoidal; Eswaran and Pope 1988, as kinet adapts it,
`kinet/forcing/laws/random_modes.py` docstring) and the last term the drag. In the
incompressible limit Eq. (7) is Eq. (1). The stationary energy balance is
$\epsilon_I = 2\alpha E + \epsilon_\nu$ (multiply Eq. (7) by $\mathbf u$; standard).

**Why `random_modes` and not `linear`.** Lundgren's linear forcing is $+r(\mathbf u -
\langle\mathbf u\rangle)$ and the drag is $-\alpha(\mathbf u - \langle\mathbf u\rangle)$: the
same operator with opposite sign, so together they are one net rate $r - \alpha$ acting on every
scale, with no forcing scale and no cascade between two ends (my reasoning). Only a force
confined to a band at $k_f$ gives the double cascade of Eq. (2).

**What kinet lacks (two small patches to kinet, not applied).**
1. **The drag.** The `linear` law with `rate_policy: constant` already computes
   `carrier * rate * (u - mean u)` and its half-step response (`kinet/forcing/laws/linear.py`,
   `_raw_force`, `acceleration_response`), and its half-step denominator $1 - \Delta t\,r/2$ is
   larger than 1 for a negative rate. Only the validator refuses it: `rate: float =
   Field(gt=0.0)` in `kinet/config/components/forcing.py`. The patch is to accept a nonzero rate
   and keep `rate > 0` for the adaptive policies, about ten lines (kinet guide, Sect. 7, "A linear
   drag ... is the `linear` law with a negative rate and the `gt=0.0` validator removed").
2. **A forcing shell.** `random_modes` forces every mode with integer radius **at most**
   `maximum_mode` (`_make_modes`), a ball that includes $|\mathbf n| = 1$. A force at the box
   scale feeds the condensate directly, so an inverse range needs a lower bound: a
   `minimum_mode: float = Field(default=0.0, ge=0.0)` key in `RandomModesForcingTermConfig` and
   one more `continue` in `_make_modes` (about five lines). Without it, Option B can run only its
   direct-cascade form (B-dir below).

**Configuration B-dc (double cascade, my design; calibrate on a pilot).** A new case file
`simulations/homogeneous_isotropic_turbulence/Re-2700_Ma-1en1_forced_drag_2d.yaml`, modelled
on the shipped `Re-1k_Ma-1en1_random_modes_forced_3d.yaml` (BGK, polynomial equilibrium, no
stabilizer), because the kinet docs say entropic BGK with a body force is about 100 times slower
per step and its stabilizer "measures the size of the force" (guide, Sect. 7):

```yaml
defaults:
  - /physics: weakly_compressible_isothermal_fluids
  - /collision: bgk
  - /lattice: d2q9
  - /equilibrium_closure/numeric@simulate_equilibrium_closure.F: polynomial
  - /forecast: very_long
id: Re-2700_Ma-1en1_forced_drag_2d
group: homogeneous_isotropic_turbulence
features: [turbulence]
units: lattice
N_simulations: 1
discretization:
  spatial: {grid: [1024, 1024], resolution: 1}
  temporal: {grid: 220000, resolution: 1}
physics:
  parameters: {mach: 0.1, reynolds: 2700, reference: {density: 1.0}}
  forcing_term:
    type: sum
    terms:
      - {type: random_modes, seed: 1729, correlation_time: 10.0, variance: 1.5e-10,
         minimum_mode: 31.0, maximum_mode: 33.0}      # minimum_mode needs patch 2
      - {type: linear, rate: -2.26e-4, rate_policy: constant}   # needs patch 1
initial_conditions: {density: 1.0, k0: 4, random_seed: 42}
boundary_conditions:
  Periodic: {axes: [x, y]}
```

run as

```bash
python -m kinet.apps.simulate case=homogeneous_isotropic_turbulence/Re-2700_Ma-1en1_forced_drag_2d \
    io.save_every_n=500 io.record_distributions=false io.record_equilibria=false \
    io=hdf5_async_compression paths.data_root=$SCRATCH/kinet_datasets
```

(`sum`, `random_modes` and `linear` are shipped laws, `kinet/forcing/laws/`; the override
spellings are the guide's, Sect. 3). A second realisation is `case.physics.forcing_term`'s
random seed changed; with `N_simulations > 1` the `random_modes` draw differs per member while
the initial field repeats (guide, Sect. 6c), which is acceptable after spin-up.

**How the numbers were chosen** (my design and arithmetic, lattice units, cell = step = 1):
1. **Mach.** Target total rms speed $u' = \mathrm{Ma}\,c_s = 0.0577$, the shipped HIT amplitude
   (turbulent Mach 0.1 on $c_s$); `reynolds: 2700` with `mach: 0.1` gives
   $\nu = u' N/\mathrm{Re} = 0.022$ and $\tau = 0.5 + 3\nu = 0.566$ (guide, Sect. 4).
2. **Forcing scale.** Shell $31 \le |\mathbf n| \le 33$, so $\ell_f = 32$ cells and $k_f =
   0.196$; 206 mode pairs (counted with the `_make_modes` rule).
3. **Drag.** Eq. (4) with $\epsilon_\alpha = 2\alpha E = \alpha u'^2$ gives
   $\ell_\alpha \simeq u'/\alpha$: the arrest scale is the distance a typical eddy moves in one
   friction time. For $\ell_\alpha = N/4 = 256$ cells, $\alpha = 2.26\times10^{-4}$ per step,
   well below the box so no condensate forms.
4. **Injection.** $\epsilon_\alpha = \alpha u'^2 = 7.5\times10^{-7}$; assuming
   $\epsilon_\alpha/\epsilon_I \approx 0.6$ at this resolution (Boffetta and Musacchio's 2048²
   run has 0.54), $\epsilon_I \approx 1.25\times10^{-6}$. For an OU force much shorter-correlated
   than the eddy time at $\ell_f$ (about 900 steps here), $\epsilon_I \approx \langle|\mathbf
   a|^2\rangle\tau_c$, and kinet states $\langle|\mathbf a|^2\rangle = 4\,P\,(D-1)\,\sigma^2$ for
   $P$ mode pairs (`random_modes.py` docstring); with $\tau_c = 10$ steps,
   $\sigma^2 = \epsilon_I/(4 \cdot 206 \cdot 10) \approx 1.5\times10^{-10}$.
5. **Viscous scale.** $\eta_\nu \approx 0.9\,k_f^2\epsilon_I = 4.3\times10^{-8}$ gives
   $\ell_\nu = \nu^{1/2}\eta_\nu^{-1/6} \approx 2.5$ cells, so $\ell_f/\ell_\nu \approx 13$
   (Boffetta 2007's 2048² run has 26) and $\ell_\alpha/\ell_f = 8$: about one decade each side,
   which is what 1024² allows. A 2048² run with the same $\ell_f$ in cells and $\ell_\alpha = 512$
   ($\alpha = 1.13\times10^{-4}$, `reynolds: 6800`) doubles the inverse range at four times the
   cells and twice the steps.

**Spin-up, record and cadence** (my arithmetic). The inverse cascade reaches $\ell_\alpha$ in
about $\epsilon^{-1/3}\ell_\alpha^{2/3} \approx 3700$ steps (the scaling of Chertkov et al. 2007);
the large-eddy time is $T_L = \ell_\alpha/u' \approx 4400$ steps and the energy relaxes on
$1/(2\alpha) \approx 2200$ steps. Plan 30 000 steps of spin-up (about $7T_L$), a base period of
90 000 steps ($20T_L$), a gap of 10 000 and an evaluation period of 90 000: 220 000 steps, 12.4
box crossings of the convective clock (`time/time_convection`, $5.64\times10^{-5}$ per step).
Save every 500 steps ($0.11T_L$): 440 frames, with a `save_burst` or a resumed segment at
`save_every_n=1` if a temporal metric needs consecutive steps (guide, Sect. 6e). **Accept the
record** only if $E(t)$ has no trend between the halves of each period, the measured
$\epsilon_\alpha = 2\alpha E$ and $\ell_\alpha$ match the design within a factor of two, and the
lowest shells do not grow (a growing $|\mathbf n| = 1$ shell is the condensate; Chertkov et al.
2007 see the spectrum steepen toward $k^{-3}$ at large scales when it forms).

**Configuration B-dir (direct cascade only, needs patch 1 only).** The same case with the shipped
low-mode force, `{type: random_modes, maximum_mode: 2.0, ...}`, and the drag. All energy is
injected at the box scale and removed there by the drag, so the record has a $k^{-3-\delta}$
direct range over most of the grid and no inverse range. It is the fallback if patch 2 is not
made; $\sigma^2$, $\alpha$ and Re must be recalibrated on a pilot for $u' \approx 0.058$ (not
designed here).

**Known in advance:** the slopes and constant of Eq. (2) with the friction correction $\delta$;
$\Pi_E = -\epsilon_\alpha$ below $k_f$ and $\Pi_Z = \eta_\nu$ above, so the flux changes sign at
$k_f$ (the figure `spectral_energy_flux` is built to draw); Eq. (3); near-Gaussian velocity
increments (flatness about 3) in the inverse range; $\ell_f, \ell_\alpha, \ell_\nu$ in cells. The
flux, spectrum and $S_3$ of the incompressible laws are approached up to Ma² corrections (my
reasoning).

**Kinet caveats** (guide, Sect. 7): plain BGK with the polynomial equilibrium, not entropic;
`solenoidal: true` is mandatory for the *linear forcing* law in long runs because the unprojected
law amplifies acoustic modes; a negative-rate drag damps those modes instead and need not be
projected (my reasoning). The shipped forced cases are 3D and the docs "do not claim ... 2D
turbulence"; `random_modes` is documented as numerically supported in 2D only
(`random_modes.py` docstring). The weakly compressible pressure is $\rho c_s^2$ and carries no
information (guide, Sect. 4), so no pressure is stored for the metrics. Its output is converted to the
existing `kinet_raw` layout first (`BUILD_ORDER.md`, "How data reaches the metrics"). The kinet branch `changes_while_running_hit` holds a 2D
`linear_forced` case with `rate_policy: k_feedback` and no drag; whether it ran is not recorded
(guide, Sect. 6c); it is not this option.

**Cost.** 1024² × 220 000 steps $\approx 2.3\times10^{11}$ cell updates. No measured kinet
throughput for 2D BGK was found, so time a 1000-step pilot on one Perlmutter GPU before
submitting (guide, Sect. 2, `submit_perlmutter.sh`; resumable on walltime, Sect. 3). Storage:
the weakly compressible run writes density, velocity, the degenerate pressure and temperature
(guide, Sect. 5), about 32 bytes per cell per frame in float64, so 440 frames of 1024² are about
15 GB uncompressed (my arithmetic). **On disk:** nothing.

### 4.2 Option C: forced 2D compressible turbulence with shocklets (not kinet)

**Published setup** (Falkovich and Kritsuk 2017, Supplement Sect. A and Table I; Kritsuk 2019,
Sect. 2 and Table 1; both read via the arXiv HTML). Compressible Euler equations with an ideal
gas at $\gamma = 1.001$ "to mimic an isothermal fluid", a force term in the momentum equation and
$\mathbf u\cdot\mathbf f$ in the energy equation; periodic unit box, $\rho_0 = 1$, sound speed
near 1, starting from rest; a "purely solenoidal, white-in-time random" force per unit mass at
$\lambda_f$, with correlation time about $10^4$ times shorter than the turnover time at
$\lambda_f$; **no bottom friction**; implicit large-eddy simulation with the piecewise parabolic
method, or an eighth-order central scheme with WENO dissipation (Kritsuk's Case B, code
ADPDIS3D). Falkovich and Kritsuk (Table I): N = 512 to 8192, $\lambda_f$ = 0.047 to 0.012,
$\epsilon_f$ = 0.001 to 0.008, end Mach numbers 0.52 to 0.62. Kritsuk (Table 1): Case A, 8192²,
$\lambda_f = 0.012$, $\epsilon_f = 0.001$, condensate at $t = 158$, saturated at 390, end at 450
with $M = 0.52$ (the text says 0.54); Case B, 16384², $\lambda_f = 0.006$, restarted from A at
$t = 124$, end at 180 with $M = 0.34$ (text: 0.33), no condensate. **These two Mach numbers are
end states of two separate runs, not an operating range** (catalog reviewer's correction,
confirmed). Shocklets appear in Case A for $t \in [50, 158]$ at $M \in [0.25, 0.3]$ (Kritsuk 2019,
Sect. 2), and shock dissipation matters once the rms Mach number exceeds 0.3 (Falkovich and
Kritsuk 2017, main text).

**Known:** the flux loop: below $k_f$ solenoidal kinetic energy goes to large scales, converts
to acoustic energy and cascades back to small scales, the net flux splitting into two roughly
equal parts (Kritsuk 2019, Sect. 3, Fig. 6); a $k^{-2}$ velocity spectrum below $k_f$ and the
Kraichnan $k^{-3}[\ln(k/k_f)]^{-1/3}$ solenoidal spectrum above (same, Figs. 1–2); a steady state
with a box-size vortex pair linked by shocks when the box is smaller than the scale where eddies
reach the sound speed (Falkovich and Kritsuk 2017, abstract). **Not stationary as published:**
Case B's energy grows at $0.33\epsilon_f$ (Fig. 6 caption), and Falkovich and Kritsuk label some
cases quasi-stationary; a base period needs an added linear drag, which neither paper has.

**Why kinet cannot run it as shipped.** The compressible physics does not map the force's energy
source into the thermal populations: "a compressible forced run with shocklets is not supported"
(guide, Sect. 7 and Sect. 8, citing kinet `docs/kinetic-theory/forcing-laws.qmd`). The weakly
compressible D2Q9 model is isothermal, which matches $\gamma \to 1$, but rms Mach 0.3 to 0.5 with
local Mach above 1 at shocks is far beyond the Ma 0.1 at which every shipped weakly compressible
case runs; I found no kinet statement of its Mach limit, so this is my reasoning, not a tested
limit.

**Codes that could.** (1) **Athena++** (Stone et al. 2020, ApJS 249, 4; arXiv abstract read):
`./configure.py --prob=turb -fft` with `--eos=isothermal`, and the `<turbulence>` block
(`turb_flag=3` continuous driving, `dedt`, `nlow`/`nhigh` for the forcing band, `tcorr` for the
OU correlation time, `f_shear` for the solenoidal fraction, `rseed`) (Athena++ wiki, "Turbulence
Driver" and "Configuring" pages, read). Whether the driver runs in 2D was not stated on those
pages, and the drag would be a user source term in the problem generator (not checked). (2)
**PLUTO** (Mignone et al. 2007, ApJS 170, 228–242; bibliographic record read), a Godunov-type
shock-capturing code in 1D to 3D with an isothermal option; its forcing interface was not
checked. Either is a new toolchain for the repository, hence Tier 3 in BUILD_ORDER (item 3.1).
**Cost:** Falkovich and Kritsuk's Case A at 512² to $t$ of order $10^3$ is about $10^6$ steps,
a day on one GPU (estimate of dataset 03, Sect. 4.5, not mine). **Store:** density, velocity and
the solver's pressure; at $\gamma = 1.001$ that pressure nearly equals $\rho c^2$ (dataset 03's
caveat). **Serves** also D3's shocklet tier (dataset 03, Option E).

### 4.3 Option D: Johns Hopkins forced isotropic 3D turbulence (public data)

**What the database provides** (Li et al. 2008, Table 1 and Sect. 2.1, read via ar5iv; JHTDB
dataset page and announcements, read 2026-11-26). Pseudo-spectral DNS on a $1024^3$ periodic
grid on $[0, 2\pi]^3$, forced by holding constant the energy in shells $|\mathbf k| \le 2$;
$\nu = 1.85\times10^{-4}$, DNS step 0.0002, frames every 0.002; $\epsilon = 0.0928$, $u' =
0.681$, Taylor scale $\lambda = 0.118$, $R_\lambda = 433$, Kolmogorov length $\eta_K = 0.00287$,
Kolmogorov time 0.0446, integral scale $L = 1.376$, integral time $T = 2.02$. Velocity and
pressure (a real, solver-written pressure) are stored. The original release covered $t \in [0,
2.048]$, "about one large-eddy turnover time" (Li et al.), which is the catalog's figure; **the
dataset `isotropic1024coarse` was extended on 2016-10-19 to $t = 10.056$, 5028 frames**, about
$5T$ (my arithmetic), which is enough for a base period and an evaluation period of about $2T$
each. **But** an announcement of 2018-10-09 reports an ingest bug for $t > 2.048$: the planes at
$x = 2\pi$ and $y = 2\pi$ were overwritten with the opposite planes; no fix is reported on the
announcements page. Before using $t > 2.048$, compare a frame's last and first planes with a
frame before 2.048.

**How to fetch a periodic cutout.** A sub-cube smaller than the box is not periodic, and the
periodic metrics would not run on it (`docs/recipes/add-a-dataset.md`, "Declare the boundary of
every axis"). Two periodic forms exist: (i) **full planes** $z = $ const of $1024^2$ points, three
velocity components, which are doubly periodic and fit the repository's 2D metrics directly,
12.6 MB per plane in float32 (my arithmetic); (ii) the full $1024^3$ volume, 12.9 GB per frame in
float32, coarsened by the existing conservative remap to $256^3$. Access is through the `giverny`
Python library (preinstalled on SciServer; `givernylocal` from PyPI locally) and its
`getCutout`, which replaced the deprecated `GetRaw`; `pyJHTDB` is deprecated (JHTDB announcements
of 2019-09-16 and 2025-01-22/27; JHTDB "Python SciServer" page). Cutouts are limited to sub-cubes
of $1024^3$ for the 8192³ set (2020-09-22) and the web cutout service was updated to "allow access
to all datasets" (2025-12-23). Queries need an authorisation token; a shared testing token
exists, and a personal one is requested from the JHTDB team (announcements, 2025-06). The exact
`getCutout` signature was not read; the demo notebook `DEMO_Getcutout_SciServer.ipynb` linked
from the SciServer page has it. The terms of use were not checked.

**Cost and a plan** (my choice). Two planes per frame ($z = 0$ and $z = \pi$, a separation of
about $2.3L$, so close to independent) every fourth stored frame ($\Delta t = 0.008$, 0.18 Kolmogorov times) over $t \in [0, 2.048]$: 257 frames,
6.5 GB. Add a few full volumes for the 3D spectrum and $S_3$ checks.

**What it gives the increment metrics.** The grid spacing is $2\pi/1024 = 0.0061 = 2.1\,\eta_K$,
$L$ is 224 cells and $\lambda$ 19 cells (my arithmetic), so separations can be stated in units of
$\eta$ and $L$ (issue 128). Flatness against separation should rise from 3 at $r \sim L$ toward the
gradient value of about 9.0 at the smallest separations (Ishihara et al. 2007 fit; Eq. 5 for
$S_3$, with the known $\epsilon$). Longitudinal and transverse increments are distinct and
isotropic. **What it does not give:** two dimensions, compressibility or shocklets, and on a
plane the 2D spectral flux is not the 3D flux (my reasoning: the out-of-plane triads are
missing), so `spectral_energy_flux` needs the volumes. **Also:** the issue-005 path (a 3D run
has never been made) is avoided by the planes.

### 4.4 Option E: kinet forced 3D weakly compressible turbulence as shipped

`homogeneous_isotropic_turbulence/Re-1k_Ma-1en1_random_modes_forced_3d` (and the `linear_forced`
twin): D3Q27, BGK with the polynomial equilibrium, 128³, Re 1000, Ma 0.1, `random_modes` with
`seed: 1729`, `correlation_time: 4.0`, `variance: 1.4e-9`, `maximum_mode: 2.0` (case file, read).
The kinet docs record that both laws reach a stationary state in 30 000 steps, with no inertial
range at Re 1000 (guide, Sect. 7). Run:

```bash
python -m kinet.apps.simulate case=homogeneous_isotropic_turbulence/Re-1k_Ma-1en1_random_modes_forced_3d \
    case.discretization.temporal.grid=60000 io.save_every_n=100 \
    io.record_distributions=false io.record_equilibria=false paths.data_root=$SCRATCH/kinet_datasets
```

**Gives:** a stationary 3D record cheaply, enough for the base-period protocol of
`tail_exceedance` (which needs stationarity, not a scaling range) and for exercising the 3D code
path of issue 005. **Does not give:** an inertial range, so no slope, plateau or four-fifths law
to recover; $\nu = 0.0074$ (my arithmetic, guide Sect. 4 rule) puts most of the spectrum in the
dissipation range. Storage: 128³ × 600 frames × 48 bytes (density, three velocity components, the
degenerate pressure and temperature, float64) is about 60 GB (my arithmetic). **On disk:** two
forced-3D folder names exist with no data (dataset 03, Sect. 4.5, citing catalog Sect. 1.3).

## 5. Recommendation

1. **Build the Option A3 reader first** (hours, inside spec 09): it gives every one of the eight
   metrics a stationary null with exact answers, including the base-period protocol, and needs
   no simulation.
2. **Then run Option B-dc** after the two kinet patches (drag, forcing shell): it is the only
   route to a 2D stationary record with an inverse and a direct range, a flux sign change at
   $k_f$, and known scales, in the solver and physics of the repository's reference. Do a 1000-step
   pilot for throughput and a 30 000-step pilot to calibrate $\sigma^2$ and $\alpha$ against
   $u' \approx 0.058$ and $\ell_\alpha \approx N/4$. If the shell patch is refused, B-dir is the
   fallback.
3. **Option D planes in parallel**, since they need only a reader and a token: the 3D increment
   and intermittency answers (flatness against separation in units of $\eta$, the four-fifths
   law) that no 2D flow can give.
4. **A4** if an intermittent known answer is wanted beyond 3D DNS; **E** only as a cheap
   stationary 3D base-period test; **C** only when the shocklet regime is pursued with another
   code, and then with an added drag.

## 6. What to store

Following `docs/recipes/add-a-dataset.md`:
- **Fields:** `density` `(T, x, y)` and `velocity` `(T, 2, x, y)` for B and E (E with three
  components and a third axis); `velocity` and the database's `pressure` for D; `density`,
  `velocity` and the solver's `pressure` for C. No pressure for B or E (the weakly compressible
  pressure is $\rho c_s^2$); no stored vorticity is needed (the repository recomputes it from
  velocity on the analysis grid). A3 and A4 are computed or stored by their reader.
- **Precision:** float64 from kinet; float32 from JHTDB as served.
- **Grid and boundaries:** `GridSpec.boundary = ("periodic", "periodic")` for B, C, D planes and
  A3; three periodic axes for E and D volumes; one periodic axis for A4. Stored on the solver's
  grid.
- **Cadence:** B every 500 steps over the whole run, spin-up included (the window is a person's
  decision, recipe Sect. 3; propose `start` at the end of spin-up and the base/evaluation split in
  the dataset YAML); D every fourth stored frame; E every 100 steps.
- **Provenance as attributes:** forcing law and its parameters ($k_f$ shell, $\sigma^2$,
  $\tau_c$, seed), $\alpha$, $\nu$, Re, Ma, measured $\epsilon_I$, $\epsilon_\alpha$,
  $\eta_\nu$, $\ell_f$, $\ell_\alpha$, $\ell_\nu$ in cells, the spin-up end and the base and
  evaluation periods, so the known answers travel with the data. For D: dataset name, plane
  positions, time indices, the token-free query script.

## 7. References

- Bec, J. and Khanin, K. (2007). Burgers turbulence. *Physics Reports* 447(1–2), 1–66.
  doi:10.1016/j.physrep.2007.04.002; arXiv:0704.1611. Read in part via ar5iv (Sects. 2.4,
  5–7, Eq. 7.1, Fig. 40 caption); the energy-spectrum statement was not found and is derived.
- Boffetta, G. (2007). Energy and enstrophy fluxes in the double cascade of two-dimensional
  turbulence. *J. Fluid Mech.* 589, 253–260. doi:10.1017/S0022112007008014; arXiv:nlin/0612035.
  Full text via ar5iv (Eq. 1, Table I).
- Boffetta, G., Celani, A. and Vergassola, M. (2000). Inverse energy cascade in two-dimensional
  turbulence: deviations from Gaussian behavior. *Phys. Rev. E* 61, R29. doi:10.1103/PhysRevE.61.R29;
  arXiv:chao-dyn/9906016. Abstract only.
- Boffetta, G. and Ecke, R. E. (2012). Two-dimensional turbulence. *Annu. Rev. Fluid Mech.* 44,
  427–451. doi:10.1146/annurev-fluid-120710-101240. **Not opened in this session** (the copy found
  had an expired certificate); Eqs. 12–13, p. 431, Fig. 5a, pp. 438 and 444 are cited as recorded
  in `metrics/spectrum_l2/card.md` and `metrics/increment_flatness/card.md`.
- Boffetta, G. and Musacchio, S. (2010). Evidence for the double cascade scenario in
  two-dimensional turbulence. *Phys. Rev. E* 82, 016307. doi:10.1103/PhysRevE.82.016307;
  arXiv:1006.4110 (titled "An update on the double cascade scenario..."). Full text via ar5iv
  (Eqs. 1, 4, 5, Table I); the published title was taken from the task brief, not the journal.
- Chertkov, M., Connaughton, C., Kolokolov, I. and Lebedev, V. (2007). Dynamics of energy
  condensation in two-dimensional turbulence. *Phys. Rev. Lett.* 99, 084501.
  doi:10.1103/PhysRevLett.99.084501; arXiv:nlin/0612052 ("Growing condensate in two-dimensional
  turbulence"). Full text via ar5iv.
- Eswaran, V. and Pope, S. B. (1988). An examination of forcing in direct numerical simulations
  of turbulence. *Computers & Fluids* 16(3), 257–278. doi:10.1016/0045-7930(88)90013-8.
  Bibliographic record and kinet's docstring only.
- Falkovich, G. and Kritsuk, A. G. (2017). How vortices and shocks provide for a flux loop in
  two-dimensional compressible turbulence. *Phys. Rev. Fluids* 2, 092603(R).
  doi:10.1103/PhysRevFluids.2.092603; arXiv:1709.00814. Full text via ar5iv (Supplement Sect. A,
  Table I).
- Frisch, U. (1995). *Turbulence: The Legacy of A. N. Kolmogorov*. Cambridge University Press.
  doi:10.1017/CBO9781139170666. Not read; chapter 6 cited for the four-fifths law.
- Ishihara, T., Kaneda, Y., Yokokawa, M., Itakura, K. and Uno, A. (2007). Small-scale statistics
  in high-resolution direct numerical simulation of turbulence: Reynolds number dependence of
  one-point velocity gradient statistics. *J. Fluid Mech.* 592, 335–366.
  doi:10.1017/S0022112007008531. Abstract only.
- JHTDB (Johns Hopkins Turbulence Databases). Forced isotropic turbulence dataset page,
  <https://turbulence.idies.jhu.edu/datasets/homogeneousTurbulence/isotropic>; announcements,
  <https://turbulence.idies.jhu.edu/staging/announcements>; Python on SciServer,
  <https://turbulence.idies.jhu.edu/database/pythonSciserver>. Read 2026-11-26. The README PDF
  could not be parsed.
- Kolmogorov, A. N. (1941). Dissipation of energy in the locally isotropic turbulence. *Dokl.
  Akad. Nauk SSSR*; English translation *Proc. R. Soc. Lond. A* 434, 15–17 (1991). Not read; the
  Doklady volume was not verified.
- Kritsuk, A. G. (2019). Energy transfer and spectra in simulations of two-dimensional
  compressible turbulence. In *Turbulent Cascades II*, ERCOFTAC Series 26, Springer, 61–70.
  doi:10.1007/978-3-030-12547-9_8; arXiv:1802.08228. Read via the arXiv HTML (Sects. 2–4,
  Table 1, Figs. 1–6 captions).
- Li, Y., Perlman, E., Wan, M., Yang, Y., Meneveau, C., Burns, R., Chen, S., Szalay, A. and
  Eyink, G. (2008). A public turbulence database cluster and applications to study Lagrangian
  evolution of velocity increments in turbulence. *J. Turbulence* 9, N31.
  doi:10.1080/14685240802376389; arXiv:0804.1703. Read via ar5iv (Table 1, Sect. 2).
- Lindborg, E. (1999). Can the atmospheric kinetic energy spectrum be explained by
  two-dimensional turbulence? *J. Fluid Mech.* 388, 259–288. doi:10.1017/S0022112099004851.
  Abstract only; no equation number is quoted from it.
- Mignone, A. et al. (2007). PLUTO: a numerical code for computational astrophysics.
  *Astrophys. J. Suppl.* 170, 228–242. doi:10.1086/513316; arXiv:astro-ph/0701854.
  Bibliographic record only.
- Stone, J. M., Tomida, K., White, C. J. and Felker, K. G. (2020). The Athena++ adaptive mesh
  refinement framework: design and magnetohydrodynamic solvers. *Astrophys. J. Suppl.* 249, 4.
  doi:10.3847/1538-4365/ab929b; arXiv:2005.06651. Abstract; plus the Athena++ GitHub wiki pages
  "Turbulence Driver" and "Configuring".
- Zhang, X., Hegerl, G., Zwiers, F. W. and Kenyon, J. (2005). *J. Climate* 18(11), 1641–1651.
  doi:10.1175/JCLI3366.1. Via the `tail_exceedance` proposal (abstract).
- kinet source read for this document: `kinet/forcing/laws/random_modes.py`, `linear.py`,
  `constant.py`, `sum.py` (header); `kinet/config/components/forcing.py`;
  `simulations/homogeneous_isotropic_turbulence/{Re-50k_Ma-1en1,Re-1k_Ma-1en1_random_modes_forced_3d}.yaml`;
  `configs/forcing/random_modes.yaml`; `simulations/testing/minimal_random_modes.yaml`.

## 8. Confidence

- **Sure** (read in the source): Eqs. (1), (3), (4) and the Table I values of Boffetta (2007) and
  Boffetta and Musacchio (2010); the Kritsuk and Falkovich–Kritsuk tables, the absence of
  friction, the Fig. 6 non-stationarity and the separate end-state Mach numbers; the JHTDB
  parameters, the extension to $t = 10.056$ and the ingest-bug notice; the $\zeta_p = \min(p,1)$
  and stationarity statements of Bec and Khanin; that kinet's `linear` law refuses a negative rate
  only in its validator and that `random_modes` forces a ball, not a shell.
- **From repository records, not re-read:** Boffetta and Ecke's Eqs. 12–13, Fig. 5a and pp. 438,
  444 (the review could not be opened); the published title of Boffetta and Musacchio (2010).
- **My reasoning or design, to be checked:** every Option B number (the $\ell_\alpha \simeq
  u'/\alpha$ identity, the injection formula for OU forcing, the assumed
  $\epsilon_\alpha/\epsilon_I = 0.6$, the step counts); that linear forcing and linear drag cancel
  into one rate; that Mach 0.3–0.5 is outside the D2Q9 weakly compressible model's range; the A3
  and A4 derived answers ($S_2$ sum, $k^{-2}$, flatness $\propto r^{-1}$); that the in-plane flux
  of a 3D slice is not the 3D flux.
- **Not checked:** kinet throughput for 2D BGK; whether the two patches pass kinet's tests;
  whether the stabilizer of the HIT 2D case must be removed when overriding to BGK (avoided by
  the new case file); the Athena++ driver in 2D and its source-term hook; PLUTO's forcing; the
  JHTDB `getCutout` signature, token terms and whether the ingest bug was fixed; Frisch's
  equation number for Eq. (5); the Kolmogorov 1941 Doklady volume.

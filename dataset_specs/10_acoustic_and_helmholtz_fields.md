# Dataset 10: acoustic and Helmholtz fields (exact solenoidal and dilatational parts)

**Catalog clusters:** G6 (the Helmholtz family) and its degradation X7; the acoustic-dipole row
of B7. **Metrics served:** the curl-based single-field metrics (`enstrophy`, `palinstrophy`), the
velocity metrics (`kinetic_energy`, `spectral_energy_flux`, `spectrum_l2`, `h1_seminorm`,
`h_minus_one`, the `mse` family), and the planned Helmholtz split
(`docs/ideas/physics_invariants/helmholtz_split.md`, issue 057) and solenoidal projection
(issue 024). **Not served:** issue 085 (helicity, potential vorticity and cascades need 3D, rotating
or forced data) and issue 088 (the log-density width needs supersonic turbulence); this dataset is
linear and at low Mach number. **Date:** 2026-11-26. **Author:** research sub-agent, branch
`build_datasets`. "My derivation" and "my design" mark the author's own work. Every number marked
"measured" was computed on 2026-11-26 with the repository's own functions in `.venv` on prototype
fields (scripts in the session scratchpad, `spec10/`), not with the reader specified here, which
does not exist yet.

## 1. Purpose

Every velocity field on a periodic domain splits uniquely into a solenoidal part (divergence-free;
it carries all the vorticity), a dilatational part (curl-free; it carries all the divergence), and
the spatial mean (Bhatia et al. 2013, a survey of this Helmholtz–Hodge decomposition). The
team ranks the Helmholtz split high (`helmholtz_split.md`), but issue 057 blocks it because "no
degradation changes that partition by design", and the catalog's G6 adds that the split is also
"a blind-axis test for every curl-based metric". Neither can be run today: the only field with a
compressive part is `kinet_re5e4`, whose dilatational part holds **1e-6 to 1e-5 of the
fluctuation kinetic energy** (measured at frames 2000, 5000 and 10000; exactly zero at frame 0,
because the shear-layer start is divergence-free). A degradation that rescales that part would
change the field by about 3e-3 of its RMS at most, so a response could not be told from
round-off-scale drift.

This dataset supplies fields whose two parts are set in closed form, with any energy fraction:
a purely solenoidal field (the existing Taylor–Green reader), purely dilatational fields (a
velocity potential, a plane acoustic wave, a Gaussian acoustic pulse), and their linear
superposition, which is the vortical-plus-acoustic decomposition of Kovásznay (1953) and Chu and
Kovásznay (1958). On these fields curl-based metrics must read exactly the solenoidal part,
divergence-based diagnostics exactly the dilatational part, and the planned split must return
each part. A kinet option measures the lattice-Boltzmann solver's acoustic accuracy against the
same exact solution. By `BUILD_ORDER.md`, decision 9, it is an evaluation dataset admitted to
`evidence_datasets` with a claim label (Sect. 6). Shocks are out of scope.

## 2. What the dataset must provide

- **Fields.** `velocity` (two components), `vorticity` (the closed form, which the harness
  replaces by its own spectral recomputation from velocity, `fmeval/derived.py`), `density` and
  `pressure` (a gauge pressure, zero mean, as `taylor_green_2d` stores now). Pressure is written by
  the reader from the closed form; it is never computed from density by the repository.
- **Grid and boundary.** The periodic box $[0, 2\pi)^2$ of `taylor_green_2d`, both axes
  `periodic`, 256² cells by default, cell centres at $(i + \tfrac12)\Delta x$, $\Delta x = 2\pi/N$.
- **Time.** Frames on a uniform time axis. The solenoidal part decays; the dilatational part
  oscillates and decays at a different rate, so no configuration's frames are scalar multiples of
  one another (the exclusion rule of `BUILD_ORDER.md`, "The task"), except the pure standing
  wave, which is kept out of the evidence list for that reason.
- **Realisations.** One per configuration; the fields are deterministic.
- **Known in advance, at every frame.** Each part separately, its energy, the curl and the
  divergence of the total, the per-shell spectrum of each part, and each metric's value on the
  reference and on every candidate of Sect. 3.6.

## 3. Option A, the analytic ideal: options on `taylor_green_2d`

### 3.1 The equations

The reference solves the linearised isothermal compressible Navier–Stokes equations about a
fluid at rest with density $\rho_0 = 1$ and sound speed $c$. With $\rho'$ the density
perturbation, $\mathbf{u}$ the velocity, $\nu$ the kinematic (shear) viscosity and $\nu_L$ the
longitudinal viscosity (shear plus bulk, the coefficient that damps compression):

$$
\partial_t \rho' + \rho_0 \nabla\cdot\mathbf{u} = 0, \qquad
\rho_0 \partial_t \mathbf{u} = -c^2 \nabla\rho' + \rho_0\nu\nabla^2\mathbf{u}_s
  + \rho_0\nu_L\nabla(\nabla\cdot\mathbf{u}). \tag{1}
$$

Write $\mathbf{u} = \bar{\mathbf{u}} + \mathbf{u}_s + \mathbf{u}_d$ with $\bar{\mathbf{u}}$ the
spatial mean (zero here), $\nabla\cdot\mathbf{u}_s = 0$ and $\mathbf{u}_d = \nabla\phi$ for a
periodic potential $\phi$. Taking the curl and the divergence of (1) separates it into two
uncoupled systems (my derivation; this is the linear decoupling into a vorticity mode and a sound
mode that Chu and Kovásznay (1958, abstract) state: "linearized equations of motion show that
in a viscous heat-conducting compressible medium three modes of fluctuations exist"; the third,
the entropy mode, is absent in an isothermal gas):

$$
\partial_t \mathbf{u}_s = \nu\nabla^2\mathbf{u}_s, \qquad
\partial_t \rho' = -\rho_0\nabla^2\phi, \quad
\partial_t \phi = -\frac{c^2}{\rho_0}\rho' + \nu_L\nabla^2\phi. \tag{2}
$$

The vortical mode carries no density in linear theory. Coupling between the modes enters only
through the nonlinear terms, which Chu and Kovásznay (1958) interpret as "interaction between the
three basic modes".

**The value of $\nu_L$.** For a fluid obeying the Stokes hypothesis in two dimensions,
$\nu_L = (2 - 2/d)\nu = \nu$. The D2Q9 BGK lattice Boltzmann scheme has a non-zero bulk viscosity
(Dellar 2001, abstract: "the isothermal constraint implies a nonzero 'bulk' viscosity"), and
kinet documents and measures $\nu_L = 2\nu$ for its D2Q9 physics
(`kinet/docs/utils/acoustic-reference.qmd`, "Lossy layers", citing its own
`tests/physics/acoustic/test_attenuation.py`). My own von Neumann check of the linearised D2Q9
BGK step (the operator written out in kinet's `tests/support/acoustic_dispersion.py`, after
Lallemand and Luo 2000) gives an amplitude decay rate $\gamma/(\nu k^2) = 1.0000$ at
$k \le 0.25$ rad/cell and $0.9957$ at $k = 1$ (measured), that is $\nu_L = 2\nu$. The reader
takes $\nu_L$ as a parameter whose default is $2\nu$, so its reference matches kinet; set it to
$\nu$ for the Stokes-hypothesis fluid.

### 3.2 The solenoidal part: Taylor–Green, as the reader gives it now

The existing reader's velocity, $\mathbf{u}_s = U(\sin x\cos y,\ -\cos x\sin y)\,e^{-2\nu t}$
(Taylor 1923, with the translation the reader's docstring derives), solves the first equation of
(2) exactly and is also an exact solution of the nonlinear incompressible equations with the
pressure $p_{TG} = U^2(\cos 2x + \cos 2y)e^{-4\nu t}/4$. The only change is a new amplitude
$U$ (the reader hard-codes $U = 1$ today); $U = 0$ removes the solenoidal part.

### 3.3 The dilatational part: the exact mode-by-mode solution of the sound system

On the torus every Fourier mode of (2) is a $2\times2$ linear system. With $\hat\rho$ and
$\hat\phi$ the discrete Fourier coefficients at wavevector $\mathbf{k}$ (from
`physical_wavenumber_grid`, the repository's one definition), $k = |\mathbf{k}|$,
$\gamma = \nu_L k^2/2$ and $\Omega = \sqrt{c^2k^2 - \gamma^2}$, the solution is the matrix
exponential (my derivation, for the $2\times2$ matrix of trace $-2\gamma$ and determinant
$c^2k^2$):

$$
\begin{aligned}
\hat\rho(t) &= e^{-\gamma t}\Bigl[\hat\rho_0\cos\Omega t
  + \bigl(\gamma\hat\rho_0 + \rho_0 k^2\hat\phi_0\bigr)\tfrac{\sin\Omega t}{\Omega}\Bigr],\\
\hat\phi(t) &= e^{-\gamma t}\Bigl[\hat\phi_0\cos\Omega t
  - \bigl(\gamma\hat\phi_0 + c^2\hat\rho_0/\rho_0\bigr)\tfrac{\sin\Omega t}{\Omega}\Bigr],
\end{aligned}
\qquad \hat{\mathbf{u}}_d = i\mathbf{k}\,\hat\phi. \tag{3}
$$

$\sin(\Omega t)/\Omega \to t$ at $\Omega = 0$, and a complex square root covers overdamped modes
($\gamma > ck$), which at the configurations' parameters lie beyond the Nyquist wavenumber. The
velocity is a spectral gradient of $\phi$, so no stream-function or Biot–Savart inversion is
involved (dataset 06, Sect. 3.3, owns that path for vortices). Measured: (3) satisfies the
continuity and momentum equations of (1) to $1\times10^{-11}$ of their terms (a centred time
difference); its velocity has a recomputed curl of $5\times10^{-14}$ or less; with $\nu_L = 0$ the
acoustic energy $\langle\tfrac12\rho_0|\mathbf{u}|^2 + \tfrac12 c^2\rho'^2/\rho_0\rangle$ is
constant to 16 digits. Three initial conditions, each a closed form sampled at cell centres and
transformed once:

1. **Plane wave**, mode $\mathbf{m} = (m, n)$ integers, $\mathbf{k}_m = (m, n)$ on $[0, 2\pi)^2$:
   - standing: $\rho'_0 = \varepsilon\cos(\mathbf{k}_m\cdot\mathbf{x})$, $\phi_0 = 0$, giving
     $\rho' = \varepsilon\cos(\mathbf{k}_m\cdot\mathbf{x})\cos(ck_m t)$ without viscosity;
   - travelling: in addition $\phi_0 = (\varepsilon c/\rho_0 k_m)\sin(\mathbf{k}_m\cdot\mathbf{x})$, so
     $\mathbf{u}_0 = (\varepsilon c/\rho_0)\hat{\mathbf{k}}_m\cos(\mathbf{k}_m\cdot\mathbf{x})$ and, without
     viscosity, $\rho' = \varepsilon\cos(\mathbf{k}_m\cdot\mathbf{x} - ck_m t)$,
     $\mathbf{u} = (\varepsilon c/\rho_0)\hat{\mathbf{k}}_m\cos(\mathbf{k}_m\cdot\mathbf{x} - ck_m t)$
     (linear acoustics; measured agreement of (3) with this form $6\times10^{-17}$ at $\varepsilon = 10^{-2}$).
2. **Potential twin of Taylor–Green**, $\phi_0 = A\cos(mx)\cos(ny)$, $\rho'_0 = 0$. For
   $m = n = 1$ the velocity at $t = 0$ is $-A(\sin x\cos y,\ \cos x\sin y)$, the mirror image of
   the Taylor–Green velocity: with $A = U$ the sum has $u_x \equiv 0$ (measured: 0.0), a field
   that looks one-component yet splits into two equal halves. Its energy is exactly
   $E_d(t) = \tfrac{A^2}{4}e^{-2\gamma t}\bigl[\cos\Omega t - (\gamma/\Omega)\sin\Omega t\bigr]^2$
   with $k^2 = 2$ (my derivation from (3); measured equal to 15 digits at $t = 0.3$ and $1.1$).
3. **Gaussian pulse**, $\rho'_0 = \varepsilon\exp(-r^2/2\sigma^2)$ with $r$ the minimum-image
   distance from the centre $\mathbf{x}_c$, $\phi_0 = 0$. This is the two-dimensional benchmark of
   the first computational-aeroacoustics workshop (Hardin, Ristorcelli and Tam 1995, cases 3.1
   and 3.2 according to Bakhvalov 2024; the proceedings were not readable, see Sect. 7). In free
   space, for the system $p_t + \nabla\cdot\mathbf{u} = 0$, $\mathbf{u}_t + \nabla p = 0$ with
   $p(0) = e^{-r^2/2}$, $\mathbf{u}(0) = 0$, Bakhvalov (2024, Eq. (3)) gives
   $p = \int_0^\infty \omega e^{-\omega^2/2}J_0(r\omega)\cos(t\omega)\,d\omega$ and
   $u_r = \int_0^\infty \omega e^{-\omega^2/2}J_1(r\omega)\sin(t\omega)\,d\omega$. Restoring
   $\varepsilon$, $\sigma$, $c$ and $\rho_0$ by the substitution $P = \rho'$,
   $\mathbf{U} = \rho_0\mathbf{u}/c$, $\tilde t = ct$ (my step):

$$
\rho'(r,t) = \varepsilon\sigma^2\!\int_0^\infty\!\kappa e^{-\kappa^2\sigma^2/2}J_0(\kappa r)\cos(c\kappa t)\,d\kappa,
\quad
u_r(r,t) = \frac{c}{\rho_0}\varepsilon\sigma^2\!\int_0^\infty\!\kappa e^{-\kappa^2\sigma^2/2}J_1(\kappa r)\sin(c\kappa t)\,d\kappa. \tag{4}
$$

   The often-quoted form $\exp(-\alpha r^2)$ with $\alpha = \ln 2/b^2$ (half-width $b$) is the
   same pulse with $\sigma^2 = 1/2\alpha$: the COMSOL application note citing Atkins (1995) and
   Atkins and Shu (1998) uses $\alpha = \ln 2/9$ ($b = 3$), amplitude 0.04 and a mean flow at
   Mach 0.5, and writes the integral as $\tfrac{\varepsilon}{2\alpha}\int_0^\infty
   e^{-\xi^2/4\alpha}\cos(\xi t)J_0(\xi r)\xi\,d\xi$ (secondary source; its Greek letters were
   lost in text extraction and are read from context). **The torus solution (3) is the exact
   periodic version of (4) including every periodic image**, so it is the reference at any time;
   (4) equals it while the images are negligible. Measured on 256² with $c = 1$, $\sigma = 0.1$
   (4.1 cells), $\varepsilon = 10^{-3}$: $|\rho'_{(3)} - \rho'_{(4)}| \le 9\times10^{-14}$ and
   $|u_{r,(3)} - u_{r,(4)}| \le 9\times10^{-14}$ at $t = 1.5$ for $r \le 2.4$ (quadrature by
   `scipy.integrate.quad`). My criterion for the overlap: $r + ct < 2\pi - 5\sigma$. The two
   discretisation errors of (3): the minimum image leaves a seam of
   $e^{-\pi^2/2\sigma^2}$ ($4\times10^{-18}$ at $\sigma = 0.35$), and the sampled Gaussian's
   spectrum at the Nyquist wavenumber is $e^{-\pi^2 s^2/2}$ for a width of $s$ cells
   ($6\times10^{-20}$ at $s = 3$). The reader refuses $\sigma$ outside $[3\Delta x, 0.35]$.
   The total acoustic energy is $c^2\varepsilon^2\sigma^2/(8\pi\rho_0)$ (per unit area, my
   derivation; measured $3.98\times10^{-10}$ against $3.98\times10^{-10}$).

### 3.4 The fields, the mixture and the vortex–acoustic superposition

The reader returns, at time $t$:

$$
\mathbf{u} = \mathbf{u}_s + \mathbf{u}_d, \quad
\omega = 2U\sin x\sin y\,e^{-2\nu t}, \quad
p = U^2 \tilde p_{TG}\,e^{-4\nu t} + c^2\rho', \quad
\rho = 1 + p/c^2, \tag{5}
$$

with $\tilde p_{TG} = (\cos 2x + \cos 2y)/4$. The pressure keeps the existing reader's
Taylor–Green term, so with no acoustic part every existing output is unchanged; the density
follows the isothermal gauge law $p = c^2(\rho - 1)$ exactly. The Taylor–Green term in the
density, $U^2\tilde p_{TG}/c^2$, is the low-Mach-number density response of the vortex (order
$\mathrm{Ma}^2$ with $\mathrm{Ma} = U/c$), exactly what kinet paints for its Taylor–Green start
(`simulations/taylor_green_vortex/initialize.py`, `init_tgv`: "density = rho0 + delta_p /
cs_squared", against the "spurious acoustic transient" of a uniform start). It is not part of the
linear solution (2), in which the vortical mode carries no density. **So the velocity and
vorticity are exact solutions of (1) and their split is exact at any amplitude; the density and
pressure are exact for the acoustic part and second-order accurate in Mach number for the
vortical part.**

**Energy fraction.** The parts are orthogonal mode by mode ($\hat{\mathbf{u}}_s \perp \mathbf{k}
\parallel \hat{\mathbf{u}}_d$), so $E = E_s + E_d$ exactly with
$E = \tfrac12\langle|\mathbf{u}|^2\rangle$ (measured: 0.5 = 0.25 + 0.25 with `kinetic_energy`),
and the dilatational fraction $f_d(t) = E_d/(E_s + E_d)$ is set by $A/U$ or $\varepsilon c/U$:
$f_d(0) = A^2/(U^2 + A^2)$ for the potential twin.

**The superposition of a vortex and an acoustic wave** (task item (ii)) is (5) with both parts
present. It is the Kovásznay decomposition: exact for the linear system (2), approximate for the
nonlinear equations, where the vortex convects and refracts the sound at first order in
$\mathrm{Ma}$ and the sound compresses the vorticity (Sect. 4.2). Kovásznay (1953) introduced the
vorticity, entropy and sound modes (secondary sources only; Sect. 7).

### 3.5 What each metric family reads (exact, at every frame)

"Measured" values are on 256² with the repository's metric functions; $\omega$ is always the
harness's recomputation.

| Metric | Pure dilatational ($U = 0$) | Mixture (5), $U > 0$ |
|---|---|---|
| `enstrophy` | 0 (measured $6\times10^{-29}$) | $U^2e^{-4\nu t}/2$, independent of the acoustic part (measured 0.5 at $U = 1$, with the potential twin or a pulse added) |
| `palinstrophy` | 0 | $U^2e^{-4\nu t}$ (measured 1.0000000000000002) |
| `kinetic_energy` | $E_d(t)$ from (3); the potential twin's closed form above | $U^2e^{-4\nu t}/4 + E_d(t)$ exactly |
| `spectral_energy_flux` | $\Pi(K) = 0$ for a single plane wave or a single Taylor–Green shell (one mode pair; my derivation); non-zero for the pulse (measured max $|\Pi|$ $1.8\times10^{-4}$ at a pulse speed of 0.3) | Taylor–Green alone gives a reference flux below round-off, so the metric returns NaN, as its card says; Taylor–Green plus a pulse is finite |
| Divergence of $\mathbf{u}$ (the planned split) | $\nabla^2\phi$ from (3) | the same: Taylor–Green contributes $6\times10^{-14}$ (measured) |
| Planned Helmholtz split | returns $\mathbf{u}_d$; solenoidal part 0 | returns each part to $10^{-15}$ (measured, Fourier projection) |

A pure dilatational field has zero vorticity, so every pairwise metric on vorticity has a zero
reference there; relative metrics return NaN by their own rules, which is the expected reading,
not a fault.

### 3.6 Candidates and their exact answers

**Existing operators** (no new code):

- **Any per-channel linear shift-invariant operator** (`gaussian_blur`, `box_blur`, `disk_blur`,
  `epanechnikov_blur`, the low-, high- and band-pass filters, `translate`,
  `translate_subpixel`) multiplies each Fourier mode of both components by the same number, so it
  commutes with the projection: the candidate's parts are the operator applied to each part, and
  the ladder's separately degraded vorticity is exactly the curl of the degraded velocity (my
  derivation). The dilatational fraction at each wavevector is unchanged. On the mixture of
  Taylor–Green (shell $\sqrt2$) and a travelling wave at $(3,2)$ (shell $\sqrt{13}$), a filter of
  gain $G(k)$ changes the overall fraction by the known factor $G(\sqrt{13})^2/G(\sqrt2)^2$.
  `translate` by whole cells also leaves every single-field metric exactly unchanged.
- **`gain`** scales both parts; **`bias`** changes only the mean, which belongs to neither part.
- **`additive_noise`** (independent white noise per channel) puts half of the noise energy into
  each part in expectation (issue 057 states it; my derivation agrees: at each wavevector the
  two independent components project equally).
- **`gaussian_impostor`** draws independent phases per channel, which destroys the relation
  $\hat{\mathbf{u}}_s\perp\mathbf{k}$: for a solenoidal input the expected dilatational fraction at a
  wavevector at angle $\theta$ is $2\hat k_x^2\hat k_y^2 = \tfrac12\sin^2 2\theta$, whose average over
  angles is 1/4 (my derivation). Measured on a broadband solenoidal field: 0.22 to 0.29 over five
  seeds; on Taylor–Green (four modes at 45°, expected 1/2): 0.10 to 0.91, single draws vary widely.
  This quantifies G3's "divergence defect" of the impostor.
- `coarsen`, `subsample` (not shift-invariant) and `median_blur` (nonlinear) mix the parts with
  no closed form.

**Closed-form candidates through the reader's `candidate` option** (no new mechanism). The
working tree of `build_datasets` (uncommitted when this was written) gives `ClosedFormTrajectory`
a `candidate` dictionary of changed parameters, returned by `predictions()` and scored as a
forecast, and gives `TaylorGreen2D` a `drift` (dataset 05, Sect. 3.3). The new options of
Sect. 9 are recorded in `params` under their keyword names, so they are candidate parameters
too, each with an error confined to one part (my derivation from (2)–(3)):

- `{sound_speed: c'}`: the solenoidal part is identical, so every metric on vorticity reads
  exactly zero difference and the velocity error is purely dilatational, a phase error growing
  as $|c' - c|\,k\,t$ per mode;
- `{nu: ν'}` with `longitudinal_viscosity` set explicitly: the error is purely solenoidal
  (Taylor–Green decaying at the wrong rate), and the divergence of the error is zero; with the
  default $\nu_L = 2\nu$ both parts change;
- `{drift: ...}`: the reader translates the acoustic part by the same $\mathbf{U}t$ (a factor
  $e^{-i\mathbf{k}\cdot\mathbf{U}t}$ on (3)), so the whole field is Galilean-translated and the
  candidate errors of dataset 05 hold part by part.

**The one new operator, `scale_dilatational` (G6, X7).** A `whole_frame=True` degradation on
velocity: split by Fourier projection, multiply the dilatational part by a factor $\lambda$,
recombine; every other field is returned unchanged, and the operator is the identity when
velocity is not among the fields. **Correction to X7, to fit the framework:** X7 asks for a
severity $s \in [-1, 1]$ on two ladder entries, but `DegradationSpec.sort_severities` orders
severities by value under one `severity_direction`, so the negative entry would be sorted in
decreasing-damage order. The severity is therefore the magnitude $s \in [0, 1]$, with
$\lambda = 1 - s$ by default (attenuate; $s = 1$ removes the part) and $\lambda = 1 + s$ under the
option `amplify: true`, as two ladder entries sharing one operator; `calibration=None`,
`zero_is_identity=True`, `preserves=("spatial_mean",)`. Exact answers on these references, with
$\delta = \lambda - 1$ (each measured equal on the potential-twin mixture):

- vorticity, density and pressure unchanged, so `enstrophy` and `palinstrophy` are invariant
  and every pairwise metric on those fields reads its identity value (the blind-axis test);
- `kinetic_energy` $= E_s + \lambda^2E_d$;
- `mse` on velocity $= \delta^2E_d$ (measured 0.0625 = 0.0625 at $\delta = 0.5$; `mse` averages
  the two channels, which turns the summed $2\delta^2E_d$ into $\delta^2E_d$);
- `h1_seminorm` $= |\delta|\,\bigl(\tfrac1C\langle\sum_c|\nabla u_{d,c}|^2\rangle\bigr)^{1/2}$, which
  for a single shell is $|\delta|\,k\,\mathrm{rms}(\mathbf{u}_d)$ (measured 0.35355 both ways);
- `spectrum_l2` on velocity $= |\lambda^2 - 1|\;\|E_d(k)\|/\|E_s(k) + E_d(k)\|$ over shells
  (measured 0.2, 0.15, 0.25, 0.6 against the same predictions at $\delta = -1, -0.5, 0.5, 1$);
- `spectral_energy_flux`: $\Pi(K)$ is a cubic form in $\mathbf{u}$, so on
  $\mathbf{u}_s + \lambda\mathbf{u}_d$ it is a cubic polynomial in $\lambda$ whose four coefficient
  curves come from the reference (measured: a cubic fitted at four $\lambda$ predicts the fifth to
  $6\times10^{-18}$ against a curve of size $4\times10^{-3}$).

## 4. Options B to D: simulated and on-disk data

### 4.1 Option B1: a Gaussian pulse at rest in kinet, against the exact solution

**System.** kinet's weakly compressible isothermal physics, D2Q9, $c_s^2 = 1/3$ in lattice units
(`00_how_to_use_kinet.md`, Sect. 1), periodic 256². Plain BGK with the polynomial equilibrium
(the overrides of `00_...`, Sect. 7: `collision@case.collision=bgk
'~collision/stabilizer@case.collision.stabilizer'
equilibrium_closure/numeric@case.simulate_equilibrium_closure.F=polynomial`), because its linear
operator is the one my oracle analyses; the shipped entropic collision agrees at linear order
(kinet's `acoustic_dispersion.py` docstring for the equilibria; that the entropic relaxation
parameter tends to the BGK value at small amplitude is my reasoning, not checked).

**Parameters (my design).** $\varepsilon = 10^{-3}$, $\sigma = 10$ cells, centre at the box
centre; Mach 0.1 sets only the viscosity, $\nu_l = \mathrm{Ma}\,c_s N/\mathrm{Re}$ (`00_...`,
Sect. 4): Re $5\times10^4$ ($\nu_l = 2.96\times10^{-4}$, dispersion-dominated) and Re $10^3$
($\nu_l = 1.48\times10^{-2}$, attenuation-dominated). 2000 steps (the pulse crosses the box about
4.5 times), saved every 5 steps.

**Route** (`00_...`, Sect. 6a, the Python `initial_state` route, verified unmodified there):
compose `case=taylor_green_vortex/Re-50k_Ma-1en1` with `case.discretization.spatial.grid=[256,256]`,
`case.discretization.temporal.grid=2000`, `case.physics.parameters.reynolds=<Re>`, the BGK
overrides above, `io.save_every_n=5 io.record_distributions=false io.record_equilibria=false`,
`case.physics.output_variables=[vorticity]`; build the simulator; paint with `macros(x, y)`
returning `density` $1 + \varepsilon e^{-r^2/2\sigma^2}$, `velocity` zero of shape `(X, Y, 2)`,
`temperature: 1/3`. Whether the route applies the case's non-equilibrium corrector `fneq_tgv` was
not checked, and does not matter here: that corrector reads the Taylor–Green amplitude by
projecting the velocity on the vortex shape (`initialize.py`, `fneq_tgv`), which is zero for a
fluid at rest, and the first-order non-equilibrium part of a density field at rest vanishes
(my derivation: $\partial_t f^{eq}_i$ and $\mathbf{c}_i\cdot\nabla f^{eq}_i$ cancel at $t = 0$).

**What is known in advance.** The linear D2Q9 BGK operator gives each Fourier mode's lattice
frequency and decay exactly (the von Neumann analysis of Lallemand and Luo 2000, as written in
kinet's oracle); measured with my implementation: the phase speed falls short of $c_s$ by
$-2.8\times10^{-4}$, $-7.8\times10^{-4}$, $-1.7\times10^{-3}$, $-7.0\times10^{-3}$,
$-2.9\times10^{-2}$ at $k = 0.1, 0.167, 0.25, 0.5, 1$ rad/cell (63 to 6 points per wavelength),
close to $-(k\Delta x)^2/36$ (my fit), and the decay is $\nu k^2$ to the digits above. Propagating
the pulse mode by mode with the lattice operator and with (3) gives the relative L² difference
between the run and the exact continuum solution that the run should reproduce, up to
nonlinear corrections of order $\varepsilon$:

| Re, grid, $\sigma$ | 100 steps | 200 | 1000 | 2000 |
|---|---|---|---|---|
| $5\times10^4$, 256², 10 cells | 0.40% | 0.77% | 4.3% | 7.2% |
| $10^3$, 256², 10 cells | 0.37% | 0.69% | 2.8% | 3.4% |
| $5\times10^4$, 256², 6 cells | 1.9% | 3.6% | 20% | 31% |
| $5\times10^4$, 256², 4 cells | 6.3% | 12% | 55% | 67% |

At Re $10^3$ the viscous attenuation itself changes the pulse by 3.6% at 200 steps and 28% at
2000 (viscous against inviscid continuum, $\sigma = 10$), so that run tests the attenuation and
the Re $5\times10^4$ run the dispersion. Marié, Ricot and Sagaut (2009) analyse the same
dissipation and dispersion of lattice-Boltzmann acoustics by von Neumann analysis and report the
method "less dissipative" than high-order Navier–Stokes schemes (abstract, via a bibliographic
record; their numbers were not read).

**Candidate.** The same physical problem at 128² ($\sigma = 5$ cells, 1000 steps, acoustic
scaling): the oracle predicts 1.6%, 3.1%, 17% and 29% at 50, 100, 500 and 1000 steps, four
times the 256² error at equal physical time, which is the $k^3t$ growth of a phase error
quadratic in $k$ (measured and reasoned). This is a degraded solver run with a known error
curve, in the sense of `BUILD_ORDER.md`.

**Mapping to the reader.** Reader length $2\pi$ for $N$ cells, sound speed 1: $x_r = 2\pi x/N$,
$t_r = 2\pi c_s n/N$ for step $n$, $\mathbf{u}_r = \mathbf{u}_l/c_s$, $\sigma_r = 2\pi\sigma/N$,
$\nu_r = 2\pi\mathrm{Ma}/\mathrm{Re}$, $U_r = \mathrm{Ma}$, and $\nu_L = 2\nu_r$ (my derivation;
it reproduces kinet's Taylor–Green decay $e^{-2\nu_l(2\pi/N)^2 n}$ and acoustic decay
$\nu_l k_l^2 n$ exactly). kinet paints Taylor–Green on $[0, 2\pi)$ cell centres
(`00_...`, Sect. 1, measured), so the grids coincide.

**Cost and output.** 256² × 2000 steps is $1.3\times10^8$ cell-steps, about 17 s at the
measured 7.6e6 cell-steps per second of BGK (`00_...`, "Verified by running"); every run of
Sect. 4 fits one debug job together. Stored: density, velocity, vorticity, 401 frames (steps 0,
5, ..., 2000; the always-saved step 1 is dropped in the conversion), about 0.84 GB per 256² run
(my arithmetic, 4 channels × 8 bytes).

### 4.2 Option B2: the pulse on a Taylor–Green background

Same route, with `macros` returning the Taylor–Green velocity of amplitude $U_l = \mathrm{Ma}\,c_s$
(Ma 0.1), density $1 + U_l^2\tilde p_{TG}/c_s^2 + \varepsilon e^{-r^2/2\sigma^2}$ (kinet's own
Taylor–Green density plus the pulse) with $\varepsilon = 10^{-2}$, so the pulse's density exceeds
the vortex's ($2.5\times10^{-3}$); Re $5\times10^4$, the case's own `initialization_policy:
analytic`. A companion run without the pulse isolates the background. What is known in advance:

- **The solenoidal part** stays the Taylor–Green vortex to within the solver's Taylor–Green error
  (decay rate within $6\times10^{-4}$ at 64², `00_...`, Sect. 4) plus the pulse's effect on the
  vorticity. In two-dimensional inviscid barotropic flow $\partial_t\omega + \mathbf{u}\cdot\nabla\omega
  = -\omega\nabla\cdot\mathbf{u}$ and $D\rho/Dt = -\rho\nabla\cdot\mathbf{u}$, so $D(\omega/\rho)/Dt = 0$:
  the passing pulse changes the vorticity by a relative amount of order $\varepsilon = 1\%$ (my
  derivation; an order of magnitude, not a closed form). Curl-based metrics therefore see the pulse
  only at that level.
- **The dilatational part** is the exact pulse (3) only while the vortex has not convected it
  by a fraction of its width, $t \ll \sigma/U$, about $173$ steps here (my estimate); after
  that the departure from the superposition is a physical vortex–sound interaction, first order in
  Mach number, with no closed form.

So B2 is evidence that a metric separates the parts on solver output, not a check of a known
number beyond the first ~170 steps.

### 4.3 Option C: kinet's driven acoustic monopole

kinet ships `simulations/acoustic/monopole.yaml`: the `acoustic` physics, D2Q9 BGK, 700²
periodic, 1000 steps, a Gaussian mass source of width 0.2 driven at frequency 0.121 with a ramp
(read from the YAML). A mass source enters only the continuity equation, so the velocity it drives
is curl-free in the continuum (my reasoning). kinet's `kinet.reference.acoustic` gives the exact
free-space pressure of point sources (`docs/utils/acoustic-reference.qmd`), valid until the wave
wraps around the box (about 600 steps from the centre, my arithmetic). It adds a forced,
time-harmonic dilatational field; it is not needed first.

### 4.4 Option D: the acoustic dipole on disk is not a purely dilatational field

The catalog (Sect. 1.3 and G6) names `acoustic/dipole/` as "a purely dilatational field". Its
config (`/global/cfs/cdirs/m4790/Data/acoustic/dipole/1d95f6/config.yaml`, read; the 3.1 GB
`rollout.h5` was not opened) shows a 700² run of only 20 steps (`temporal.grid: 20`), with
absorbing layers of 50 cells on all four faces alongside the periodic declaration, written in an
older config schema (`scheme: type: acoustic`, `tau: 0.501`). The dipole is a momentum source,
$\mathbf{F} = a\,g(\mathbf{x})\hat{\mathbf{d}}$ with a Gaussian $g$ (`kinet/forcing/laws/multipole.py`:
"``momentum`` -- dipole ``F_src``"), and $\nabla\times(g\hat{\mathbf{d}}) = \nabla g\times\hat{\mathbf{d}} \ne 0$,
so it drives vorticity at the source that stays there and diffuses (my derivation). The far field
is dilatational, the source region is not, and the sponge breaks periodicity. **It should not be
used as G6's known answer**; Options A and B replace it. `datasets/kinet/testing/acoustic_waves`
does not exist under the data root (checked 2026-11-26).

## 5. Recommendation

Build Option A first: one afternoon of code on the existing reader (Sect. 9), every answer of
Sects. 3.5 and 3.6 pinned by a test, and with it `scale_dilatational`, which then has a
reference whose dilatational fraction is 50% (potential twin), 100% (pulse) or a few percent
(vortex and pulse), instead of the $10^{-5}$ of `kinet_re5e4`. Then B1 at both Reynolds numbers
and the 128² candidate in one debug job, once jobs are approved: they are the repository's only
solver data with a closed-form acoustic answer. B2 next; C only if a forced field is wanted. A
broadband random dilatational field would be a one-line option on dataset 09's reader (velocity
from a potential instead of a stream function); that is a proposal for its builder, not specified
here.

## 6. What to store

Option A stores nothing. Configurations (my proposals), 256², periodic, all on `format:
taylor_green_2d`, each with `fields:` listing what it populates:

- `helmholtz_mixture_2d`: $U = 1$, potential twin $A = 1$ at mode (1, 1), $c = 2$, $\nu = 0.01$,
  $\nu_L$ default, $t \in [0, 10]$, 41 frames; fraction 1/2 at $t = 0$, then oscillating as
  $E_d(t)$ while $E_s$ decays.
- `acoustic_pulse_2d`: $U = 0$, pulse $\varepsilon = 0.01$, $\sigma = 0.1$, centre $(\pi, \pi)$,
  $c = 1$, $\nu = 10^{-4}$, $t \in [0, 3]$, 61 frames. Velocity, density, pressure (vorticity is
  zero by construction).
- `vortex_and_pulse_2d`: $U = 1$, $\nu = 0.01$, $c = 10$ (Mach 0.1, as kinet), pulse
  $\varepsilon = 0.2$, $\sigma = 0.3$, $t \in [0, 2]$, 101 frames; measured dilatational fraction
  0 at $t = 0$, then 1.5% to 3.1%.

Evidence entries in `configs/cards/default.yaml`: label "an exact-split check: the solenoidal and
dilatational parts of the velocity are set in closed form, so the evidence is whether a metric
reads the part it claims to read and is blind to the other, and nothing about turbulence";
properties `{periodic: true, ensemble: false}`. A page `docs/datasets/acoustic_helmholtz.md` with
Sect. 3. Option B: references in the `kinet_raw` layout under
`datasets/kinet/acoustic_pulse/weakly_compressible_isoT_fluids/<case>/` (density, velocity,
vorticity, `time`, `discretization`); the run scored against the exact solution goes in the
`forecast` layout, with the target written from the reader at the run's times through the mapping
of Sect. 4.1 (the `forecast` half of step 1's conversion script, not built yet). The weakly
compressible gauge pressure is not carried over (issue 101). HDF5 attributes: $\varepsilon$,
$\sigma$, centre, Re, Ma, collision, and the mapping constants. About 0.84 GB per 256² run, five
runs about 3.6 GB.

## 7. References

- Bakhvalov, P. (2024). Computation of the solution for the 2D acoustic pulse propagation.
  arXiv:2404.10489. **Read:** Eqs. (1)–(3) and the citations around them in the arXiv HTML, through
  a fetch tool's verbatim extraction.
- Hardin, J. C., Ristorcelli, J. R. and Tam, C. K. W. (eds.) (1995). *ICASE/LaRC Workshop on
  Benchmark Problems in Computational Aeroacoustics (CAA)*. NASA CP-3300,
  https://ntrs.nasa.gov/citations/19950023712. **Not read:** the PDF of Tam's "Benchmark problems
  and solutions" chapter is a scan with no text layer; the case numbers are Bakhvalov's.
- Tam, C. K. W. and Webb, J. C. (1993). Dispersion-relation-preserving finite difference schemes
  for computational acoustics. *J. Comput. Phys.* 107, 262–281,
  https://ntrs.nasa.gov/citations/19930067183. **Not opened;** cited by Bakhvalov for the split
  into acoustic, vortex and entropy components.
- Atkins, H. L. (1995), NASA CP-3300, pp. 15–26, and Atkins, H. L. and Shu, C.-W. (1998), *AIAA J.*
  36, 775–782. **Not opened;** cited through the COMSOL application note "Gaussian Pulse in 2D
  Uniform Flow" (COMSOL 5.5), whose text I extracted from its PDF (Greek symbols lost).
- Kovásznay, L. S. G. (1953). Turbulence in supersonic flow. *J. Aeronaut. Sci.* 20(10), 657–674,
  https://doi.org/10.2514/8.2793. **Not opened;** secondary sources only (search summaries).
- Chu, B.-T. and Kovásznay, L. S. G. (1958). Non-linear interactions in a viscous heat-conducting
  compressible gas. *J. Fluid Mech.* 3(5), 494–514, https://doi.org/10.1017/S0022112058000148.
  **Read:** the abstract.
- Dellar, P. J. (2001). Bulk and shear viscosities in lattice Boltzmann equations. *Phys. Rev. E*
  64, 031203, https://doi.org/10.1103/PhysRevE.64.031203. **Read:** the abstract.
- Lallemand, P. and Luo, L.-S. (2000). *Phys. Rev. E* 61, 6546. **Not opened;** cited as kinet's
  oracle cites it; I re-implemented the operator from kinet's docstring.
- Marié, S., Ricot, D. and Sagaut, P. (2009). Comparison between lattice Boltzmann method and
  Navier–Stokes high order schemes for computational aeroacoustics. *J. Comput. Phys.* 228(4),
  1056–1070, https://doi.org/10.1016/j.jcp.2008.10.021. **Not opened** (the publisher page did not
  load); abstract content from a bibliographic record.
- Xia, M. et al. (2022). *Geophysics* 87(6), T403. **Not opened;** cited through kinet's docs for
  the Kelvin–Voigt form.
- Bhatia, H., Norgard, G., Pascucci, V. and Bremer, P.-T. (2013). The Helmholtz–Hodge
  decomposition: a survey. *IEEE TVCG* 19(8), 1386–1404, https://doi.org/10.1109/TVCG.2012.316.
  **Read:** a search summary of the abstract.
- Taylor, G. I. (1923), as cited in `fmeval/data/analytic.py`.
- Repository and kinet sources read: `fmeval/data/analytic.py`, `fmeval/derived.py`,
  `fmeval/ladder.py` (whole-frame path, no-op test), `degradations/registry.py`,
  `degradations/_shared/filters.py`, `degradations/gaussian_impostor/degradation.py`, the Definition
  sections of the five cards named in the task, issues 024, 057, 085, 088, the dilatational-scaling
  proposal, the idea page, catalog G6, X7 and B7, specs 00, 06 and 09; in kinet (read only):
  `simulations/acoustic/{initialize.py,dipole.yaml,monopole.yaml,mvp.yaml}`,
  `simulations/taylor_green_vortex/{Re-50k_Ma-1en1.yaml,initialize.py}`,
  `kinet/forcing/laws/multipole.py`, `tests/support/acoustic_{dispersion,standing_wave}.py`,
  `docs/kinetic-theory/acoustic.qmd`, `docs/utils/acoustic-reference.qmd`,
  `docs/notes/plans/acoustic_weakly_compressible_one_physics.md`.

## 8. Confidence

- **Sure (exact algebra checked numerically with the repository's functions):** the split of
  (2); the propagator (3) and its residuals; the agreement of (3) with (4); the potential twin's
  $u_x \equiv 0$ and its energy curve; every entry of Sect. 3.5; the `scale_dilatational` answers
  for `mse`, `h1_seminorm`, `spectrum_l2` and the cubic flux; the $10^{-5}$ dilatational
  fraction of `kinet_re5e4`; the $\nu_L = 2\nu$ decay of the linear D2Q9 BGK operator and the
  oracle tables of Sect. 4.1.
- **Reasoning, not measured:** the commutation of per-channel convolutions with the projection
  (a one-line argument); the expected 1/2 and 1/4 dilatational fractions of `additive_noise` and the
  impostor (the latter's spread measured, its mean derived); the $O(\varepsilon)$ vorticity change and
  the 173-step validity of B2; the vorticity of the dipole source; the curl-free monopole field;
  that entropic BGK matches BGK at linear order.
- **Cited but not read in full:** the CAA workshop's own problem statement and parameters, Tam and
  Webb (1993), Kovásznay (1953), Marié et al. (2009). The formula (4) rests on Bakhvalov's Eq. (3)
  plus my rescaling, and the numerical agreement with (3).
- **Not checked:** whether the `initial_state` route applies `fneq_tgv` (argued irrelevant for B1);
  whether the dataset-figure test enumerates the reader's fields (Sect. 9); kinet's actual nonlinear
  departure from the oracle at $\varepsilon = 10^{-3}$; no kinet run was made.

## 9. Existing code reused and new code needed

| Piece | Existing file it extends | New lines (rough) |
|---|---|---|
| Options `amplitude` ($U$), `sound_speed` ($c$, absent means no acoustic part and the reader unchanged), `longitudinal_viscosity` (default $2\nu$), `acoustic` (a list of `{kind: plane \| potential \| pulse, ...}`), all recorded in `params` so `candidate` can change them; validation; $\hat\rho_0, \hat\phi_0$ built once; the propagator (3), with the `drift` phase factor, and (5) in `solution`, scaling the cached `_patterns` by $U$; `density` added to the instance's fields only when `sound_speed` is set | `TaylorGreen2D` in `fmeval/data/analytic.py` (its `drift`, `_patterns_at` and the `candidate`/`predictions()` of `ClosedFormTrajectory`, in the working tree); `physical_wavenumber_grid` | 60–70, a third docstring |
| `helmholtz_split(velocity, grid) -> (solenoidal, dilatational)`, the Fourier projection; the mean goes with the solenoidal part (my choice). Two callers now (the operator, the tests) and two planned (issue 024's option, issue 057's metric) | `fmeval/derived.py`, beside `vorticity_from_velocity`; `physical_wavenumber_grid` | 15 |
| `scale_dilatational` bundle: operator, `card.md`, `card.yaml`, `refs.bib` | `degradations/` by `AGENTS.md` §4; the whole-frame path of `fmeval/ladder.py` already exists and is tested (`tests/test_robustness.py`) | 15 code, about 90 card and metadata |
| Ladder entries `scale_dilatational_down`, `_up` | `LADDERS` in `tests/test_degradation_contract.py`; `TEST_DESCRIPTION.md` | 10 |
| Known-answer tests: Sect. 3.5 and 3.6 values, (3) against (4) and against the residual of (1), the potential-twin energy, the unchanged existing outputs | `tests/test_analytic_datasets.py`; closed forms beside `tests/analytic_fields.py` | 120 |
| Three configurations | `configs/dataset/taylor_green_2d.yaml` pattern | 75, mostly comments |
| Evidence labels and properties; the dataset page | `configs/cards/default.yaml`; `docs/datasets/` | 12; 80 of prose |
| B1, B2 run script (kept with the runs, outside the repository) | `$EX/_meta/branch_from_frame.py` pattern of `00_...`, Sect. 6a | 50 |
| B scored against A | the `forecast` half of the step-1 conversion (`fmeval/data/convert_kinet.py`), not built yet | counted under step 1 |

About 90 lines of production code, 120 of tests, and configuration and prose. No new reader and
no velocity-from-stream-function path: the solenoidal part is the reader's own closed form, and
the dilatational velocity is a spectral gradient. One existing test needs updating if the
dataset-figure generator enumerates the reader's fields rather than the config's (not checked):
the instance-level `density` keeps the default configuration's field list unchanged either way.

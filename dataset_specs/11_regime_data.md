# Dataset 11: regime data (wall-bounded flow, variable-density mixing, scalar and reacting mixing, line-of-sight projections)

**Catalog clusters:** none; the catalog records these needs in its "Regime data and references
with no proposal" paragraph at the end of `FUTURE_EXPERIMENTS_CATALOG.md` Sect. 2.1, and the
on-disk sets in Sect. 1.3. **Issues served:** 089 (wall-bounded), 090 (variable-density mixing),
091 (reacting and scalar mixing), 087 (line-of-sight projection), and the scalar half of 058
(Batchelor scale). **Ideas served:** `docs/ideas/regime_specific/wall_bounded_flows.md`,
`variable_density_mixing.md`, `reacting_flows.md`,
`docs/ideas/basis_decompositions/velocity_channel_analysis.md`. **Build-order step:** 27.
**Date:** 2026-11-26. **Author:** research sub-agent, branch `build_datasets`.

"My derivation", "my design", "my arithmetic" and "my judgement" mark the author's own work.
Every closed form marked "checked" was verified numerically on 2026-11-26 by finite differences
in the session scratchpad (`spec11/checks.py`, residuals at the finite-difference truncation
level). HDF5 facts were read from file headers and coordinate arrays only; no field values were
read. Shocks, shocklets and supersonic flow are out of scope (BUILD_ORDER decision 7), so the
supersonic MHD members and the Richtmyer–Meshkov case are excluded below. Nothing here trains,
runs or evaluates a machine-learning model.

## 1. Purpose

Four families of planned metrics wait on data the repository does not have. Wall diagnostics
(friction velocity, wall units, skin friction, separation, the log law) need the velocity
gradient at a solid wall (issue 089). Variable-density mixing diagnostics (mixing width, growth
laws, the molecular mixing fraction $\Theta$, the turbulent mass flux, anisotropy) need two
fluids of different density and their volume fractions (issue 090). Scalar-mixing and reacting
diagnostics (mixture fraction, scalar dissipation, conditional statistics, flame surface density,
flame index, the Batchelor scale) need a transported scalar or species (issues 091, 058).
Velocity channel analysis needs a reference that is a projection along a line of sight, with the
observation operator declared (issue 087). Every dataset is 2D or 3D; the repository's own data
are all doubly periodic, weakly compressible and single-fluid.

What a metric learns from each regime, in one line each: whether it survives a non-periodic
axis and a wall (most of today's metrics have only ever seen periodic data, and 13 declare
`requires_periodic` and are skipped there, `fmeval/pipeline.py` line 305); whether it sees
mixing that a density RMSE cannot (stirred versus molecularly mixed); whether it can score a
transported scalar whose small scales lie below the velocity's (the Batchelor regime); and
whether it can work in an observation space that is not the simulation's state space.

## 2. What every regime's data must provide (shared)

- **Fields in the repository vocabulary** (`fmeval/data/base.py`, `FIELDS`). Density, velocity
  and pressure exist. **A transported scalar does not**: regimes (b) and (c) need one new
  primitive entry, `scalar` (one channel; a volume fraction, mixture fraction, buoyancy or
  concentration, named in the dataset's notes). Regime (d) needs a second, `ppv`, described in
  Sect. 6. Pressure is stored only where the solver wrote it, never computed.
- **A declared boundary per axis.** `BOUNDARIES` holds `periodic` and `neumann` (even extension
  about the face). A wall, a free-slip lid and a zero-gradient outflow are all declared
  `neumann`; Sect. 3.6 explains what that does to the velocity at a no-slip wall and gives the
  one alternative.
- **Uniform spacing.** `GridSpec` has one spacing per axis. Data on stretched or Chebyshev grids
  must be interpolated onto a uniform grid by the conversion, and the interpolant recorded.
- **Unsteady frames.** A dataset whose frames are scalar multiples of one another stays out of
  `evidence_datasets` (BUILD_ORDER, "The task"). Steady laminar profiles (Couette, steady
  Poiseuille) are therefore not datasets by themselves; their start-up transients are.
- **An evidence label** naming the kind of claim each dataset supports
  (`configs/cards/default.yaml`, `evidence_datasets`), proposed per option below.

## 3. Regime (a): wall-bounded flow (issue 089)

**What the metrics learn.** Whether a metric handles a wall (the degradations act on the field
extended across it, `GridSpec.extend`); whether the planned wall diagnostics recover a known
wall stress $\tau_w$, friction velocity $u_\tau = \sqrt{\tau_w/\rho}$ and skin friction from
the near-wall gradient, at which resolution they fail, and whether the log law
$u^+ = \kappa^{-1}\ln y^+ + B$ is recovered with the constant appropriate to the flow.

### 3.1 Option A1, analytic: start-up plane Poiseuille flow and the oscillating Stokes layer

**Start-up Poiseuille flow.** Fluid at rest between no-slip walls at $y=0$ and $y=H$, driven
from $t=0$ by a uniform body force $g$ per unit mass along $x$, obeys
$\partial_t u = g + \nu\,\partial_y^2 u$, where $\nu$ is the kinematic viscosity. The steady
profile $u_s = \frac{g}{2\nu}y(H-y)$ is the one kinet's `simulations/poiseuille/analytic.py`
evaluates (it cites Batchelor, *An Introduction to Fluid Dynamics*, Sect. 4.2; not opened here).
Expanding $\eta(1-\eta)$, with $\eta = y/H$, in the sine modes that vanish at both walls
($b_n = 2\int_0^1\eta(1-\eta)\sin n\pi\eta\,d\eta = 8/(n\pi)^3$ for odd $n$, zero for even)
gives, by separation of variables (my derivation, checked):

$$
u(y,t) = \frac{gH^2}{2\nu}\Big[\eta(1-\eta) - \sum_{n\ \mathrm{odd}} \frac{8}{(n\pi)^3}
\sin(n\pi\eta)\,e^{-n^2\pi^2\nu t/H^2}\Big], \qquad v = 0, \tag{1}
$$

$$
\frac{\tau_w(t)}{\rho} = \nu\,\partial_y u\big|_{y=0} = \frac{gH}{2}\Big[1 - \sum_{n\ \mathrm{odd}}
\frac{8}{(n\pi)^2}\,e^{-n^2\pi^2\nu t/H^2}\Big]. \tag{2}
$$

At $t=0$ the bracket of (2) is zero because $\sum_{n\ \mathrm{odd}} 8/(n\pi)^2 = 1$; as
$t\to\infty$ it tends to the steady $gH/2$, which equals $H/2$ times the driving force, the
momentum balance of the steady channel. The frames change shape, so they are not scalar
multiples.

**Stokes's second problem** (a wall oscillating along $x$ at velocity $U\cos\omega t$ under a
deep fluid at rest) has the classical solution (checked):

$$
u(y,t) = U e^{-ky}\cos(\omega t - ky), \quad k = \sqrt{\omega/2\nu}, \qquad
\frac{\tau_w}{\rho} = \sqrt{2}\,\nu U k\,\sin(\omega t - \pi/4). \tag{3}
$$

The source usually given is Stokes (1851); it was not opened, and (3) is stated as derived and
checked here, not quoted. On a finite domain $0 \le y \le L_y$ the far boundary is declared
`neumann` and placed at $ky \ge 10$, where $e^{-ky} < 5\times10^{-5}$ (my arithmetic).

**What is known exactly:** $u$, $\tau_w(t)$, $u_\tau(t)$ and $C_f(t)$ at every frame; the
viscous wall unit $\nu/u_\tau$, so a resolution can be stated in $\Delta y^+$. **What it does
not give:** turbulence, and so no log law; a field that varies along $y$ only (uniform along
$x$). **Reader** (my design): one `ClosedFormTrajectory` subclass `wall_layers` with option
`flow: startup_poiseuille | stokes_oscillating`, grid periodic in $x$ and `neumann` in $y$,
field `velocity`; candidates by the existing `candidate` mechanism (a wrong $\nu$ or $g$ gives
a known error at every step). **Label:** "an analytic check: evidence that a wall diagnostic
recovers a known wall stress, and nothing about turbulence".

### 3.2 Option A2, simulated in kinet: the shipped `poiseuille/channel` case, from rest

kinet ships the case that realises (1): `simulations/poiseuille/channel.yaml` (read), weakly
compressible isothermal physics, BGK, D2Q9, periodic $x$, `type: wall` faces on $y$ (halfway
bounce-back, no-slip plane half a cell outside the first and last rows), a `constant` body force
$[3\times10^{-5}, 0]$, grid $8\times16$, 4500 steps, Mach 0.1, Re 10. The case header reports
the steady profile within 0.3% of the parabola and the first node 2.5% low. The same case at
a size the metrics can use (my choice, not run): `discretization.spatial.grid=[64,128]`,
viscosity $\nu \approx 0.1$ in lattice units (kinet sets $\nu = \mathrm{Ma}\,c_s N_x/\mathrm{Re}$,
so $\mathrm{Re} \approx 37$ at Ma 0.1), $g$ chosen for a peak velocity $gH^2/(8\nu) = 0.05$, so
$g \approx 2.4\times10^{-6}$, and 50 000 steps (about three times $H^2/(\pi^2\nu) \approx 1.7\times10^4$),
saved every 50th step (my arithmetic). Cost: $4.1\times10^8$ cell-steps, about 90 s at the
measured entropic rate (BUILD_ORDER, Phase 3 header), one debug job; storage about 0.2 GB
converted. Conversion: the existing `fmeval/data/convert_kinet.py`, with the dataset config
giving `reader.boundary: [periodic, neumann]` to `kinet_raw`. **Known answer:** (1) and (2) at
every saved step; the distance from them is the solver's discretisation error at that grid,
and a 32 × 64 rerun gives a refinement pair. **Label:** "a solver check against an exact
solution at a wall".

### 3.3 Option B, public data on disk: The Well `rayleigh_benard`

`/global/cfs/cdirs/m4790/Data/well/datasets/rayleigh_benard/data/test/`, 35 files of 1.05 GB,
one per (Rayleigh, Prandtl) pair, $\mathrm{Ra} \in \{10^6,\dots,10^{10}\}$,
$\mathrm{Pr} \in \{0.1, 0.2, 0.5, 1, 2, 5, 10\}$; five trajectories per file, 200 frames from
$t=0$ to 49.75, grid $512\times128$ on $[0,4]\times[0,1]$ (headers read). Fields
`t0_fields/buoyancy`, `t0_fields/pressure`, `t1_fields/velocity`. Boundary groups:
`x_periodic`, and `y_wall_dirichlet` with `bc_type: WALL`. The Well's page (read) gives the
equations solved with Dedalus (Burns et al. 2020), $\kappa = (\mathrm{Ra\,Pr})^{-1/2}$,
$\nu = (\mathrm{Ra/Pr})^{-1/2}$, $u=0$ on both walls, $b = 1$ at $y=0$ and $b=0$ at $y=1$, and
1750 trajectories in all. This is the only on-disk 2D set with no-slip walls and resolved
boundary layers, and it is 2D, so it needs no 3D support.

**Known answers** (no closed form for the fields). Two exact identities of stationary
Boussinesq convection between these walls (my derivation, from horizontally and time averaging
the buoyancy equation $\partial_t b + \mathbf u\cdot\nabla b = \kappa\nabla^2 b$ with $v=0$ at
the walls): the mean vertical flux $\langle v b\rangle - \kappa\,\partial_y\langle b\rangle$ is
the same at every height, and the mean scalar dissipation equals the wall flux,

$$
\kappa\,\langle|\nabla b|^2\rangle_V = -\kappa\,\partial_y\langle b\rangle\big|_{y=0}
\quad (\Delta b = H = 1), \tag{4}
$$

so both the wall gradient and the scalar dissipation of a candidate are checked against each
other without a reference. Wall stress and $u_\tau$ are measured directly. No log law is
expected at these Reynolds numbers (my reasoning; not checked against a source).

**What the reader needs** (Sect. 7): the Well boundary types `WALL` and `OPEN` mapped to
`neumann`; `buoyancy` mapped to `scalar`. **Two things to check at build time**, unverified:
(i) the Well page says the solver's $y$ points are Chebyshev nodes, but the stored $y$
coordinate is uniform (128 points, spacing $1/127$, endpoints 0 and 1 on the walls), and The
Well's paper states its data are on uniform grids (search snippet of Ohana et al. 2024, not
read in full); whether the stored rows were interpolated or merely labelled must be checked by
comparing the near-wall buoyancy gradient with the wall flux of (4). (ii) Every Well set read
here stores coordinates that include both endpoints (`x` from 0 to 4 in 512 points, spacing
$4/511$), so the reader's spacing $c_1 - c_0$ makes the periodic length $4\cdot512/511$, and
the wall rows are nodes on the walls, not cell centres half a cell inside. Whether the periodic
axes repeat their first column must be checked on one frame before the configs are trusted.
**Checked 2026-11-26 (step 27, first item), on the files.** (i) **The rows are not uniform:
they lie on the Gauss–Chebyshev nodes** $y_j = \tfrac12\big(1-\cos(\pi(j+\tfrac12)/128)\big)$,
interior points only, so neither wall is stored, although the `y` array reads 0 to 1 in equal
steps. The Well's page says so ("Sampled at Chebyshev nodes along the y axis") and lists a
separate `rayleigh_benard_uniform` set, resampled, which is not on disk. Two measurements
confirm it. Averaged over frames 150 to 199 of trajectory 1 at Ra $10^6$, Pr 1, the mean flux
$\langle vb\rangle - \kappa\,\partial_y\langle b\rangle$ of (4) is constant to 0.3% over the first
thirteen rows on those nodes, but varies by a factor of 13 on the stored uniform coordinate and
of 1.9 on Gauss–Lobatto nodes; at Ra $10^{10}$ it varies by 8% on the Gauss nodes and by a
factor of 28 on the uniform ones. The first row's mean buoyancy at Ra $10^8$, Pr 1 (trajectory
0, frames 120 to 196) is 0.9986, which is
$1 - (\text{wall gradient } 36.1)\times y_0$ with $y_0 = 3.8\times10^{-5}$, the first Gauss node;
on a uniform grid it would be the wall value 1. The repository's single spacing per axis cannot
hold this grid, so **no `rayleigh_benard` configuration is built**; it needs either the
`rayleigh_benard_uniform` files or a conversion that interpolates the Chebyshev rows onto a
uniform grid and records the interpolant (Sect. 2). A data-marked test
(`tests/test_loader_contract.py`) pins the signature. (ii) **The coordinates include both
endpoints and the periodic axes do not repeat a column**: in `rayleigh_benard` and
`turbulent_radiative_layer_2D` alike, the difference between the first and last periodic
columns is the size of a neighbour difference, so $N$ cells span the length $c_{N-1}-c_0$, and
the cell is $(c_{N-1}-c_0)/N$. In `turbulent_radiative_layer_2D` that gives square cells of
$1/128$ on both axes, against $1/127$ and $3/383$ from the step. The Well reader takes this as
the option `coordinates_span_domain` (default off, since the repository's own Well-format
file stores the step itself). The `buoyancy` field is not mapped: it is the nondimensional
temperature of a Boussinesq run ($b = 1$ on the hot wall, 0 on the cold one), so `temperature`
would be its existing vocabulary entry rather than a new `scalar`, a choice left until the
grid is resolved.
**Candidates:** the other four trajectories of the same file (unrelated realisations), the
neighbouring Ra or Pr file (a wrong parameter), and the degradation ladder. **Label:** "a public
reference with no-slip walls and an active scalar".

### 3.4 Option C, public data: the Johns Hopkins channel at $\mathrm{Re}_\tau \approx 1000$

The JHTDB channel README (full text read): DNS of channel flow, periodic in $x$ and $z$, no-slip
walls, domain $8\pi h\times2h\times3\pi h$, $2048\times512\times1536$ points stored, $\nu = 5\times10^{-5}$,
$dP/dx = 0.0025$, frames every $\delta t = 0.0065$ over $t\in[0, 25.9935]$ (4000 frames,
"approximately a single flow through time"), $u_\tau = 4.9968\times10^{-2}$,
$\mathrm{Re}_\tau = 999.35$, $\Delta x^+ = 12.26$, $\Delta z^+ = 6.13$, $\Delta y^+$ from
0.0165 at the first point to 6.155 at the centre. Velocity is stored in the wall frame as the
DNS velocity plus 0.45, and cutouts are on the moving grid $x = i\Delta x + 0.45\,m\,\delta t$
(README note 2). Its reference [1] is Kim, Moin & Moser (1987).

**The form that fits the framework** (my design): **wall-parallel planes** $y = $ const, full
$2048\times1536$ in $x$ and $z$, which are doubly periodic and so need no new boundary type and
none of the 13 periodic-only metrics is skipped. A plane at the first point off the wall
($y^+ = 0.0165$) is a wall-stress map, $\tau_w(x,z)/\rho \approx \nu\,u(y_1)/y_1$, whose mean
must equal $h\,dP/dx = 0.0025 = u_\tau^2$ (to the README's four digits:
$(4.9968\times10^{-2})^2 = 2.4968\times10^{-3}$, my arithmetic), an exact momentum balance for
a stationary channel. Planes at $y^+ \approx 15$ (streaks) and in the log layer give the mean
$U^+(y^+)$ at those heights, compared with the published Lee & Moser $\mathrm{Re}_\tau = 1000$
profile (data at the URL of Lee & Moser 2015; same group and code family). For the log law the
appropriate constants are flow-specific (the idea page); Lee & Moser (2015, Eq. 3.1, read via
ar5iv) fit $\kappa = 0.384\pm0.004$, $B = 4.27$ at $\mathrm{Re}_\tau \approx 5200$ for
$350 \le y^+ \le 0.16\,\mathrm{Re}_\tau$, a range they call "somewhat arbitrary"; at
$\mathrm{Re}_\tau = 1000$ the log region is short, so the comparison is with their tabulated
profile, not the fitted law. **Wall-normal ($x$–$y$) planes** would show the log law directly
but sit on the non-uniform $y$ grid and need interpolation onto a uniform grid (an interpolant
the metric definition must record); they come second.

**Fetch:** the `giverny` `getCutout` route that step 24 (spec 04, Option D) sets up, with a
JHTDB token; nothing new beyond the dataset name and plane indices. The out-of-plane velocity
$v$ has no slot in the 2D vocabulary, so a wall-parallel plane carries $(u, w)$ only and cannot
show $\langle u'v'\rangle$. **Cost** (my arithmetic): one plane of $(u, w)$ in float32 is
25 MB; three planes every 8th frame (500 frames, $\Delta t = 0.052$) are 38 GB, or 9.4 GB after
the existing remap coarsens them by 2. **Label:** "a public reference of wall turbulence".

### 3.5 Other simulated options, and why they come later

- **Schäfer & Turek 2D-2, a cylinder in a channel at Re 100** (FEATFLOW benchmark page, read):
  channel $[0,2.2]\times[0,0.41]$, cylinder of diameter 0.1 at $(0.2,0.2)$, parabolic inflow of
  peak 1.5 and mean 1.0, $\nu = 10^{-3}$, no-slip walls and cylinder, do-nothing outflow;
  FEATFLOW reference values $C_{D,\max} = 3.2200$, $C_{L,\max} = 0.9859$, Strouhal 0.30188. It
  gives skin friction and separation on a body with a periodic wake. **Not first**, because
  (i) kinet's LBM inlet takes a uniform velocity only (`InletFace`, `kinet/config/common/boundary_conditions.py`
  line 193; a parabolic profile would be a kinet addition, size not estimated), (ii) the solid
  cylinder sits inside the grid and the repository has no mask, so degradations smear velocity
  into the solid, and (iii) OpenFOAM can run it but its `cylinder2D` tutorial is a different
  configuration ($\nu = 1.558\times10^{-5}$, read in the v2406 image).
- **A turbulent channel in kinet** (Kim, Moin & Moser 1987; their paper could not be read, a
  scanned PDF): at $\mathrm{Re}_\tau = 180$ with a uniform lattice at $\Delta^+ = 2$ on a
  $2\pi h\times2h\times\pi h$ box the grid is $565\times180\times283 = 2.9\times10^7$ cells; with
  bulk velocity 0.05 and $u_\tau$ about one sixteenth of it (an assumption, not checked) an eddy
  turnover $h/u_\tau$ is about $2.9\times10^4$ steps, and 20 turnovers at the measured 2D rate
  of $4.6\times10^6$ cell-steps per second take about 40 GPU-days, before D3Q27's higher cost
  per cell (unmeasured). My arithmetic; **not feasible within the job budget**. The JHTDB
  channel replaces it.
- **OpenFOAM `planarPoiseuille`** (v2406 tutorial, read: `Stokes` and `Maxwell` setups with a
  `WatersKing` validation) is the start-up flow of (1) in an independent finite-volume code, a
  candidate of the "different solver" kind; its mesh and run length were not read.

### 3.6 The wall boundary and what `neumann` does to velocity

`neumann` extends a field evenly about the wall face (`BOUNDARIES` docstring, citing LeVeque
2002 Sect. 7.3.3). That is right for density, pressure, a scalar with zero wall flux and the
tangential velocity at a free-slip wall (The Well's Rayleigh–Taylor walls). At a **no-slip**
wall the velocity vanishes and is odd about the face, so the even extension is continuous but
has a kink, and any spectral smoothing then rounds it, putting a small slip velocity at the
wall (my reasoning). The extension is continuous, which is all `BOUNDARIES` requires, so the
framework accepts `neumann` as it is. **Recommendation (my judgement):** declare walls
`neumann` now, record on each dataset page that smoothing degradations create wall slip, and
only if a wall diagnostic proves sensitive to it add a per-field odd rule (velocity odd, other
fields even) in `GridSpec.extend`, which `fmeval/ladder.py` `_call` can select because it
already knows the field name (about 15 lines; a decision for Kareem, since it changes what a
boundary type means). Wall-stress estimators must use one-sided differences at the wall, since
the spectral vorticity refuses non-periodic grids (`fmeval/derived.py` line 84).

## 4. Regime (b): variable-density mixing (issue 090), without shocks

**What the metrics learn.** Whether a metric distinguishes fluids that are stirred from fluids
that are mixed (two fields with equal density RMSE and different $\Theta$); whether it tracks
the growth of a mixing layer; and the cost of a wall-bounded, strongly anisotropic layer.

### 4.1 Option A, analytic: the linear single-mode Rayleigh–Taylor interface

Two inviscid fluids, heavy $\rho_h$ over light $\rho_l$, Atwood number
$A = (\rho_h-\rho_l)/(\rho_h+\rho_l)$, gravity $g$, rigid lids at $z = \pm H$, periodic in $x$
with wavenumber $k$. The linearised problem (my derivation, standard method: potential flow in
each layer, kinematic and pressure continuity at the interface) gives the interface
$\eta(x,t) = a_0\cosh(\sigma t)\cos kx$ from rest, with

$$
\sigma^2 = A g k \tanh(kH), \tag{5}
$$

velocity potentials $\phi_{\pm} = \mp\frac{\dot a}{k}\frac{\cosh k(z\mp H)}{\sinh kH}\cos kx$
above and below (so $w = \dot a\cos kx$ at $z=0$ and $w=0$ at the lids), and the volume
fraction of heavy fluid $f = \tfrac12[1+\tanh((z-\eta)/\delta)]$ for an interface of chosen
thickness $\delta$ (a diffuse profile, not a solution of the inviscid equations; my design).
As $kH\to\infty$, (5) tends to $\sigma = \sqrt{Agk}$, the classical rate that Thévenin & Gréa
(2025, Sect. 3.2, read) quote. With viscosity $\nu$, diffusivity $\kappa$ and an initial
diffusive thickness $d$, Duff, Harlow & Hirt (1962; not opened) damp it; Thévenin & Gréa
(2025, Eq. 8, read from a text extraction) write that model, for $\nu = \kappa$, as
$\gamma^\star = R^{-4/3}\big(\sqrt{R^2/\psi + 1} - 2\big)$ in their units, with
$\psi = 1 + \sqrt{2/\pi}\,k_0 d$ at low Atwood number (the extraction of $\psi$ was garbled,
so this form must be checked against the paper before use).

**Known exactly:** the growth rate, $\eta(x,t)$, and the mixing width
$W = \int\langle f\rangle(1-\langle f\rangle)\,dz$ by quadrature at each frame; with
$\delta \to 0$ the molecular mixing fraction $\Theta$ of the idea page is exactly 0, and on a
grid it is set by the cells the interface cuts, which makes $\Theta$ a resolution test. **Valid
only** while $k a(t) \ll 1$ (my reasoning). **Reader** (my design): a `ClosedFormTrajectory`
subclass `rt_linear`, fields `scalar` ($f$), `density` ($\rho_l + (\rho_h-\rho_l)f$) and
`velocity`, grid periodic in $x$, `neumann` in $z$. Frames grow in amplitude and change shape,
so they are not scalar multiples. **Label:** "an analytic check of growth rate and mixing width".

### 4.2 Option B, public data on disk: The Well `rayleigh_taylor_instability`

Five Atwood numbers (files `..._At_0625`, `_125`, `_25`, `_50`, `_75`; train, valid and test
splits, test files 8.0 GB), $128^3$ on $[0,1]^3$, 119 frames, two trajectories per test file;
fields `t0_fields/density` and `t1_fields/velocity` only, stored contiguously (no chunking);
boundary groups `x_periodic`, `y_periodic`, `z_wall` (`bc_type: WALL`) (headers read). The
Well's page (read): code TurMix3D, miscible fluids with a common diffusivity $\kappa$, the
divergence constraint $\nabla\cdot\mathbf u = -\kappa\nabla\cdot(\nabla\rho/\rho)$, slip (not
no-slip) walls at top and bottom, 45 trajectories with log-normal initial spectra, Atwood
numbers $3/4, 1/2, 1/4, 1/8, 1/16$, reference Cabot & Cook (2006, not opened). The page does
not say whether density is linear in a volume fraction. If the model's mixing rule is the
ideal one, $1/\rho = Y_h/\rho_h + Y_l/\rho_l$ in the mass fractions $Y$, then the volume
fraction $f_h = \rho Y_h/\rho_h$ satisfies $f_h + f_l = 1$ and
$\rho = \rho_l + (\rho_h-\rho_l)f_h$ exactly (my derivation), so $f_h$ is a linear function of
the stored density; that the code uses this rule is an assumption to confirm in Cabot & Cook.

**Fit to the 2D framework** (my design): **vertical slices** $y = $ const are 2D fields periodic
in $x$ and slip-walled in $z$, so no 3D support is needed. The reader takes one slice per
trajectory (option `plane`, Sect. 7); several slice indices are separate dataset trajectories.
Plane averages over $x$ alone are noisier than over $x$ and $y$ (my reasoning). **Volume
fraction:** the repository never computes a constitutive quantity in a reader (the pressure
rule), so the slice carries `density` only and a mixing metric takes $\rho_h$ and $\rho_l$
from the dataset config; $\rho_h$, $\rho_l$ and the normalisation are read from frame 0 at build
time (the page does not state them). **Known answers:** the growth-rate coefficient
$\alpha_b \approx 0.025\pm0.003$ of 3D simulations against $0.057\pm0.008$ in experiments
(Dimonte et al. 2004, abstract via search snippet), and $\alpha_\infty \approx 0.02$ in
Thévenin & Gréa (2025, Fig. 2, Boussinesq); whether $128^3$ reaches self-similarity in these
runs was not checked. **Candidates:** the neighbouring Atwood number (a wrong parameter), the
other trajectories (other initial spectra), the ladder. **Label:** "a public reference of
Rayleigh–Taylor mixing, slices of a 3D run".

### 4.3 Option C, simulated in OpenFOAM: a 2D miscible Rayleigh–Taylor run with a stored volume fraction

kinet cannot run this: its weakly compressible physics holds pressure equal to
$\rho c_s^2$, so a heavy-over-light density jump is not in hydrostatic equilibrium, and no
multicomponent or passive-scalar physics exists (`kinet/physics/` lists none; a search for
species, mass fraction and passive scalar found only visualisation dye). OpenFOAM's
`twoLiquidMixingFoam` (v2406 image, tutorial `multiphase/twoLiquidMixingFoam/lockExchange`,
read) transports the volume fraction `alpha.sludge` with a diffusivity `Dab`, two Newtonian
phases (tutorial: $\rho$ = 1000 and 990, $\nu = 10^{-6}$, `Dab` $10^{-6}$), gravity, on a
$10\times2$ domain of $200\times40$ cells. **Standard configuration** (Guermond & Quartapelle
2000, not opened; as restated by Espinoza-Contreras et al. 2024, Sect. 6.2, read): domain
$(0, a/2)\times(-2a, 2a)$, $\rho_2 = 3\rho_1$ ($A = 1/2$), $\mathrm{Re} = a\sqrt{ag}/\nu = 1000$,
no-slip top and bottom, free slip on the sides, an interface displaced by a cosine of amplitude
about $0.1a$ and $\tanh$ thickness about $0.01a$ (my reading of a garbled text extraction;
check against Guermond & Quartapelle), mesh $100\times800$; the reference result is the
height of the rising bubble against time (their Fig. 5 compares with Guermond & Quartapelle).
The initial interface is set with `setExprFields` (an assumption that the v2406 image has it;
not checked). Cost: $8\times10^4$ cells, a few thousand steps, minutes on one CPU node (my
estimate, unmeasured). Storage: `alpha` as `scalar`, `rho` as `density`, `U` as `velocity`,
about 4 MB per frame, 0.8 GB for 200 frames. Candidates: half resolution, a larger `Dab`
(more molecular mixing at the same stirring: the $\Theta$ test), a different Atwood number.
**Label:** "an independent-solver run of Rayleigh–Taylor mixing with a stored volume fraction".

The Richtmyer–Meshkov case in kinet (`simulations/rmi_heavy_to_light`, PonD, $1200\times100$)
needs a shock and is excluded.

## 5. Regime (c): scalar and reacting mixing (issues 091, 058)

**What the metrics learn.** Whether a metric scores the small scales of a scalar correctly when
they lie below the velocity's (Schmidt or Prandtl number above 1), whether scalar dissipation
$\chi = 2D|\nabla Z|^2$ and conditional statistics on a mixture fraction $Z$ are recovered, and
whether boundedness ($0\le Z\le1$) survives a degradation.

### 5.1 Option A, analytic: the strained mixing layer, and the existing blobs

**The strained mixing layer** (my derivation, checked; Batchelor 1959 and Peters 1984 for the
physics, neither opened). A scalar $Z$ between two streams, $Z\to0$ and $Z\to1$, in the pure
strain $(u, v) = (a x, -a y)$ with strain rate $a>0$ and diffusivity $D$, depends on $y$ only
and obeys $\partial_t Z - a y\,\partial_y Z = D\,\partial_y^2 Z$. An error-function profile of
width $\delta(t)$ is an exact solution:

$$
Z = \tfrac12\Big[1+\mathrm{erf}\Big(\frac{y}{\sqrt2\,\delta}\Big)\Big], \qquad
\delta^2(t) = \frac{D}{a} + \Big(\delta_0^2 - \frac{D}{a}\Big)e^{-2at}, \tag{6}
$$

$$
\chi = 2D(\partial_y Z)^2 = \frac{D}{\pi\delta^2}\,e^{-y^2/\delta^2}
\;\xrightarrow{\,t\to\infty\,}\; \frac{a}{\pi}\exp\!\big(-2[\mathrm{erfc}^{-1}(2Z)]^2\big). \tag{7}
$$

The equilibrium width $\sqrt{D/a}$ is the Batchelor scale of strain rate $a$, and the limit of
(7) is the counterflow form of $\chi(Z)$ used in flamelet models (Peters 1984; the same form
appears in the ANSYS Fluent theory guide, a secondary source). Everything is known exactly:
the PDF of $Z$, $\chi(Z)$, the Batchelor scale and the approach to it. Frames change width,
so they are not scalar multiples. **Grid:** periodic in $x$ (the scalar is uniform along
$x$), `neumann` in $y$ (zero gradient far from the layer, exact to round-off beyond
$|y| > 8\delta$). The velocity is not stored, since $v = -ay$ is not periodic and the
equations need only $a$. **Reader** (my design): `strained_mixing_layer`, field `scalar`,
candidates a wrong $D$ or $a$. **Label:** "an analytic check of scalar dissipation and the
Batchelor scale".

**Already built:** `advecting_blobs` (`fmeval/data/analytic.py`) is an exact passive scalar
under advection and diffusion (its docstring), stored as `density`; with `diffusivity > 0`
its blobs spread as the heat kernel, so its $\chi$ is known in closed form today. It is a
harness fixture, not evidence (`docs/decisions.md`).

### 5.2 Option B, public data on disk

- **The Well `rayleigh_benard` buoyancy** (Sect. 3.3): an active scalar at Prandtl numbers 0.1
  to 10, so the sets at $\mathrm{Pr} = 2, 5, 10$ have thermal scales below the velocity's, and
  identity (4) ties the scalar dissipation to the wall flux exactly. It serves (a) and (c) with
  one reader change.
- **The Well `gray_scott_reaction_diffusion`**: six pattern regimes (bubbles, gliders, maze,
  spirals, spots, worms) with parameters $F$, $k$ in the file names; 20 trajectories of 1001
  frames at $128^2$, both axes `x_periodic`, `y_periodic`; fields `t0_fields/A` and `B` (headers
  read; the dataset page was not read). Reaction and diffusion with no flow: it tests
  boundedness and interface statistics of two reacting species, not mixing by a flow. The
  existing reader reads it once one species is mapped to `scalar`; low value.

### 5.3 Option C, simulated: OpenFOAM, a passive scalar in turbulence and a laminar counterflow flame

kinet has no scalar transport (Sect. 4.3); adding a second population for an advected scalar is
a substantial kinet change (not estimated) and is not recommended now.

- **A passive scalar riding on step 25.** Step 25 already runs the isotropic reference set's
  initial velocity in OpenFOAM with `cyclic` patches. Adding OpenFOAM's `scalarTransport`
  function object to that case (the solver itself is the shipped `scalarTransportFoam`,
  tutorial `basic/scalarTransportFoam/pitzDaily`, read) transports one or two scalars, for
  example at Schmidt numbers 1 and 8, with a large-scale initial blob or a mean gradient (my
  choice). Cost: that of step 25 plus one transport equation; storage one extra field. Known in
  advance: nothing exact, but the Batchelor-to-Kolmogorov ratio $\mathrm{Sc}^{-1/2}$ and the
  scalar-variance budget (the analogue of (4), $\frac{d}{dt}\langle Z'^2/2\rangle = -\langle\chi\rangle/2$
  for a periodic box; my derivation) check a candidate without a reference.
- **A laminar counterflow diffusion flame** (OpenFOAM v2406 tutorial
  `combustion/reactingFoam/laminar/counterFlowFlame2D`, read): a 20 mm × 20 mm box of
  $100\times40$ cells, fuel entering at $x=0$ at 0.1 m/s and air at $x = 20$ mm at −0.1 m/s,
  outlets at $y = \pm10$ mm, one-step methane chemistry
  ($\mathrm{CH_4} + 2\mathrm O_2 \to \mathrm{CO_2} + 2\mathrm{H_2O}$, Arrhenius $A = 5.2\times10^{16}$,
  $T_a = 14906$), species, temperature and pressure stored, end time 0.5 s with adaptive steps
  at Courant 0.4. It is the only option with species, a flame and a flame index. **Known in
  advance:** the strain rate is about $2\times0.1/0.02 = 10\ \mathrm{s^{-1}}$ (my estimate), and
  the mixture fraction across the stagnation line should follow (6) and (7) where density
  variations are small (they are not small through the flame, so this is approximate; my
  reasoning). The flow becomes steady, so only the approach to steady state is admissible, or
  the run is perturbed (a pulsed inlet velocity, my suggestion). Cost: minutes (unmeasured).
  The non-square cells (0.2 × 0.5 mm) are allowed by `GridSpec`. **Label:** "an
  independent-solver laminar flame".

## 6. Regime (d): line-of-sight projections (issue 087)

**What the metrics learn.** Whether a comparison made in an observation space recovers the
statistics of the underlying 3D fields, as velocity channel analysis claims, and whether a
metric is fooled by structure the projection creates (Lazarian & Pogosyan warn that velocity
alone makes small-scale structure in thin channels).

**The observation operator** (my design, to live in one function so reader and conversion
share it; the formula is the standard optically thin, position–position–velocity cube of
Lazarian & Pogosyan 2000): for a line of sight along $z$, column density
$N(x,y) = \sum_k \rho_{ijk}\,\Delta z$, and the cube

$$
I(x, y, v_c) = \sum_k \rho_{ijk}\,\Delta z\;\frac{1}{\sqrt{2\pi}\,v_T}
\exp\!\Big(-\frac{(v_c - u_{z,ijk})^2}{2v_T^2}\Big), \tag{8}
$$

with $N_v$ velocity channels $v_c$ of width $\Delta v$ and a thermal width $v_T$. **Fit to the
vocabulary:** $N$ is stored as `density` on the 2D sky grid (units mass per area, stated in the
notes), and the cube as a new primitive field `ppv` with $N_v$ channels, exactly as the
lattice populations are a 9-channel `distribution`. Then the existing degradations act per
channel on the sky axes, which is what a telescope beam (blur) and receiver noise (additive
noise) do, and the remap block-averages the sky axes only. The channel count is fixed in the
vocabulary entry ($N_v = 32$, my choice); a dataset with another count is refused.

### 6.1 Option A, analytic: projected Gaussian random fields

Spec 09's `random_field` reader draws Gaussian fields of prescribed spectrum on a periodic grid.
Drawn in 3D and projected by (8) (my design), it gives exact answers: the discrete
projection–slice identity $\widehat{N}(k_x,k_y) = \Delta z\,\widehat\rho(k_x,k_y,0)$ (checked to
$3\times10^{-14}$), so the column-density spectrum is the 3D spectrum on the $k_z=0$ plane, and
its slope equals the 3D slope for a power law; and, because Lazarian & Pogosyan assume Gaussian
velocities, their asymptotic channel slopes (2000, Table 1, read via ar5iv) apply: with density
spectrum $P(k)\propto k^n$ and velocity structure function $\propto r^m$, thin channels give
$K^{-3+m/2}$ for steep density ($n<-3$) and $K^{n+m/2}$ for shallow density; very thick
channels give $K^{n}$; for thick channels with steep density the paper's Table 1 and its
Eq. 43 disagree ($K^{-3-m}$ against $K^{-3-m/2}$), so only the thin and very thick limits are
used as known answers. "Thin" means $C|K|^{-m} \gg \delta V^2$, the velocity dispersion at the
scale compared with the squared channel width (their criterion). The density must stay positive
(spec 09's transforms handle that); density and velocity are drawn independently, as the paper
assumes. **Label:** "an analytic check of a projected observable".

### 6.2 Option B, public data on disk: The Well `MHD_64` (and `MHD_256`), subsonic members only

$64^3$, periodic on all axes, 100 frames ($\Delta t = 0.01$), fields `density`, `velocity`,
`magnetic_field` (headers read); isothermal ideal MHD without self-gravity, downsampled from
$256^3$ "after anti-aliasing with an ideal low-pass filter", sonic Mach $M_s \in \{0.5, 0.7,
1.5, 2, 7\}$ and Alfvénic $M_A \in \{0.7, 2\}$, ten initial conditions each (The Well's page,
read; source Burkhart et al. 2020, not opened). **Only $M_s = 0.5$ and $0.7$ are in scope.** The
interstellar medium is the setting velocity channel analysis was built for, so this is the
natural reference. **Route** (my design): a conversion that projects each 3D frame by (8) and
writes the 2D result (`density` = $N$, `ppv`) in the `kinet_raw` layout, recording the operator
($z$ axis, $N_v$, $\Delta v$, $v_T$) in the file's attributes; the existing `kinet_raw` reader
then reads it. Storage: $64^2\times33\times100\times8$ B = 0.11 GB per trajectory (my
arithmetic). Known answers: none exact (MHD velocities are not Gaussian), so it is evidence, not
a check. **Candidates:** the other $M_A$ at the same $M_s$ (a wrong parameter), other initial
conditions, a projection along $x$ instead of $z$ (an unrelated view; the field is anisotropic
when magnetised), and beam and noise degradations of the cube. **Label:** "a public reference
in observation space".

### 6.3 Option C, simulated in kinet

kinet runs 3D weakly compressible turbulence (`homogeneous_isotropic_turbulence/Re-1k_Ma-1en1_random_modes_forced_3d`,
$128^3$; spec 04, Option E). Projecting that run by (8) needs no new run. At Mach 0.1 the density
fluctuations are of order $\mathrm{Ma}^2$ (my reasoning), so $N$ is nearly uniform and the cube is
velocity-dominated: it tests only the thin-channel regime. Worth doing only once spec 04's run
exists.

## 7. Recommendation

**Ranking by value per unit of work** (my judgement):

1. **The shared reader change, then the Well `rayleigh_benard` set.** One change to the Well
   reader (map `WALL` and `OPEN` to `neumann`, map a named scalar to `scalar`) and one new
   vocabulary entry make a 2D, on-disk, 35-parameter dataset with no-slip walls and an active
   scalar readable, serving regimes (a) and (c) together, with the exact identity (4) as a
   reference-free check. It also makes `turbulent_radiative_layer_2D` readable (periodic $x$,
   zero-gradient $y$, which the Well page states; density, pressure, velocity), the
   catalog's first non-Sod run with a stored pressure. Do the two build-time checks of
   Sect. 3.3 first.
2. **The analytic readers `wall_layers` and `strained_mixing_layer`.** About 100 lines for exact
   wall stress, scalar dissipation and Batchelor scale, the known answers that the public data
   cannot give.
3. **kinet `poiseuille/channel` at $64\times128$**: one debug job, the existing converter, an
   exact answer for a solver at a wall.
4. **Variable-density mixing**: the Well Rayleigh–Taylor slices (the `plane` option) and then
   the 2D OpenFOAM run with a stored volume fraction (one converter, shared with step 25); the
   analytic `rt_linear` reader alongside, as the growth-rate check.
5. **The JHTDB channel planes**, once step 24's fetch route and token exist: the only option
   with turbulent wall data and a log law.
6. **Line-of-sight projections**: the `ppv` entry, the operator, the 3D option of spec 09's
   reader, then the MHD projections. Last, because only one planned idea (velocity channel
   analysis) uses it.
7. **The OpenFOAM counterflow flame**, for the flame-specific diagnostics (flame index, flame
   surface density), which no other option serves.

The Schäfer–Turek cylinder and the Chombo AMR vortex street in `treb_data/` (Sect. 8) wait
until the repository has a solid mask.

## 8. Data on disk that was checked and does not serve these regimes now

- `treb_data/karman_vortex_street/`: 1182 Chombo files (`VanillaAMRFileType`), three AMR levels,
  base $1024\times256$ at $\Delta x = 0.03125$, components velocity, pressure, pressure
  gradient, vorticity and embedded-boundary geometry (volume fraction, normals, distance);
  `read_data.py` assembles level 0 of one component. No input file, so the Reynolds number is
  unknown. It is the only on-disk data on more than one mesh (issue 053), but it needs a new
  AMR reader and a solid mask.
- `treb_data/3d_flat/`: one zarr snapshot at time 0, $2048\times1024\times1024$, embedded
  boundary; a single frame. `treb_data/2d_packed_flow/`: porous-medium runs (permeability
  outputs), not inspected further. `treb_data/double_shear_layer/`: doubly periodic, not a
  regime of this document.
- `kinet/flow_around_objects/weakly_compressible_isoT_fluids/Re-375e2_Ma-173en3/`: a 21 MB file
  that h5py refuses to open ("file is already open for write"), an unfinished run of an acoustic
  dipole beside a cylinder with absorbing layers; not wall data.
- `kinet/flow_around_objects/compressible_fluids/`: Mach 1.8, shocked, out of scope.
- `well/datasets/turbulent_radiative_layer_3D`, `MHD_256` training files and the supernova and
  merger sets: 3D, large, or supersonic; not needed for the four regimes.

## 9. What to store

- **Analytic readers:** nothing. Configs give grid, window, parameters and boundary
  (`[periodic, neumann]`).
- **kinet runs:** macroscopic observables only (`io.record_distributions=false
  io.record_equilibria=false`), converted to `kinet_raw` under
  `datasets/kinet/poiseuille/weakly_compressible_isoT_fluids/...`; density and velocity in
  float64 as kinet writes them; the weakly compressible gauge pressure is not carried over.
- **The Well sets:** nothing moved; configs point at the files in place. Precision float32 as
  stored, cast on read.
- **OpenFOAM runs** (RT, passive scalar, flame): fields written in ASCII at a fixed cadence,
  converted to `kinet_raw` (`density`, `velocity`, `scalar`, plus `pressure` where the solver's
  is absolute), with the OpenFOAM case directory archived beside the file as provenance.
- **JHTDB planes and MHD projections:** written to `kinet_raw` by their fetch or projection
  script, with the plane index and $y^+$, or the operator of (8), in the file attributes.
- **Boundary per axis** in every config, per `docs/recipes/add-a-dataset.md`.

## 10. Existing code reused and new code needed

| Piece | Existing file it extends | New lines (rough) |
|---|---|---|
| `scalar` vocabulary entry (primitive, one channel); its row in `TEST_DESCRIPTION.md` | `fmeval/data/base.py` `FIELDS` | 3 |
| Well boundary mapping: read each `boundary_conditions/*` group's `bc_type` and `associated_dims`; `PERIODIC` → `periodic`, `WALL` and `OPEN` → `neumann`; anything else refused as today | `fmeval/data/well.py` lines 99–106 (replaces the refusal) | 12 |
| Well option `scalar: str` naming the `t0_fields` dataset read as `scalar` (`buoyancy`, `A`) | `fmeval/data/well.py` `FIELD_MAP` handling | 6 |
| Well option `plane: {axis, index}` that reads one 2D slice of a 3D file, renaming the remaining axes `(x, y)` and keeping their two velocity components | `fmeval/data/well.py` constructor and `read_frame` | 15 |
| Fixtures and contract tests: a non-square Well file with a `WALL` group, a scalar, a 3D file sliced | `tests/fixtures_h5.py`, `tests/test_loader_contract.py` | 50 |
| `wall_layers` reader, Eqs. (1)–(3), with the series truncated at a stated tolerance | `fmeval/data/analytic.py` (`ClosedFormTrajectory`, `candidate`) | 50 |
| `strained_mixing_layer` reader, Eqs. (6)–(7) | `fmeval/data/analytic.py` | 30 |
| `rt_linear` reader, Eq. (5) with its potentials | `fmeval/data/analytic.py` | 45 |
| Tests of the three readers against independent statements (PDE residual by finite differences, Eq. (2) against the reader's wall gradient, $\chi(Z)$ against (7)) | `tests/test_analytic_datasets.py` | 80 |
| `scalar` and `ppv` in the flat layout's field map | `fmeval/data/kinet_raw.py` `FIELD_MAP` | 2 |
| The flat-layout writer split out of `convert_kinet_grouped`, so OpenFOAM, JHTDB and projection outputs share it (moved, not new) | `fmeval/data/convert_kinet.py` | 10 |
| OpenFOAM source: parse `internalField` of a single-block `blockMesh` case at each written time, reshape x-fastest, write through the shared writer | `fmeval/data/convert_kinet.py` (also serves step 25) | 45 |
| `ppv` vocabulary entry and the operator of Eq. (8), one function used by the reader and the projection script | `fmeval/data/base.py`; `fmeval/derived.py` | 25 |
| 3D draw plus `line_of_sight` option on spec 09's `random_field` | `fmeval/data/analytic.py` (spec 09's reader, once built) | 25 |
| Projection script for Well MHD files into `kinet_raw` | standalone, beside `convert_kinet.py`; reuses the Well reader to read and the shared writer to write | 30 |
| JHTDB channel planes | step 24's fetch script, with the channel dataset name and $y$ indices | 10 |
| Dataset configs (one fragment per set) and pages | `configs/dataset/`, `docs/datasets/` | 150 of config, 300 of prose |
| Evidence labels and properties | `configs/cards/default.yaml` | 25 |
| kinet: none for the Poiseuille run; a parabolic LBM inlet only if Schäfer–Turek is built later | — | 0 now |
| Optional, on decision: odd extension of velocity at a no-slip wall | `fmeval/data/base.py` `GridSpec.extend`, `fmeval/ladder.py` `_call` | 15 |

About 240 lines of production code (half of it the three analytic readers), 130 of tests,
plus configs and pages. No existing behaviour changes: the Well reader still refuses any
boundary type it does not map, and the defaults of every new option reproduce today's reads.

## 11. References

- Batchelor, G. K. (1959). Small-scale variation of convected quantities like temperature in
  turbulent fluid. Part 1. *J. Fluid Mech.* 5, 113–133. <https://doi.org/10.1017/S002211205900009X>
  — not opened; cited for the name of the scale only.
- Burkhart, B. et al. (2020). The Catalogue for Astrophysical Turbulence Simulations (CATS).
  *Astrophys. J.* 905, 14. — not opened; the source The Well cites for `MHD_64`.
- Burns, K. J., Vasil, G. M., Oishi, J. S., Lecoanet, D. & Brown, B. P. (2020). Dedalus: a
  flexible framework for numerical simulations with spectral methods. *Phys. Rev. Research* 2,
  023068. — not opened; cited by The Well for `rayleigh_benard`.
- Cabot, W. H. & Cook, A. W. (2006). Reynolds number effects on Rayleigh–Taylor instability
  with possible implications for type Ia supernovae. *Nature Physics* 2, 562–568. — not opened;
  cited by The Well for `rayleigh_taylor_instability`.
- Dimonte, G. et al. (2004). A comparative study of the turbulent Rayleigh–Taylor instability
  using high-resolution three-dimensional numerical simulations: the Alpha-Group collaboration.
  *Phys. Fluids* 16, 1668–1693. <https://doi.org/10.1063/1.1688328> — abstract, via a search
  snippet.
- Duff, R. E., Harlow, F. H. & Hirt, C. W. (1962). Effects of diffusion on interface instability
  between gases. *Phys. Fluids* 5, 417–425. — not opened; read through Thévenin & Gréa (2025).
- Espinoza-Contreras, N., Barrenechea, G. R., Castillo, E. & Pacheco, D. R. Q. (2024).
  Unconditionally stable, linearised IMEX schemes for incompressible flows with variable
  density. arXiv:2410.11510. — Sect. 6.2 read (text extraction).
- FEATFLOW group. DFG flow around cylinder benchmark 2D-2 (Re = 100), reference values.
  <https://wwwold.mathematik.tu-dortmund.de/~featflow/en/benchmarks/cfdbenchmarking/flow/dfg_benchmark2_re100.html>
  — read; its reference [1] is Schäfer, M. & Turek, S. (1996), *Notes on Numerical Fluid
  Mechanics* 52, 547–566 (not opened).
- Guermond, J.-L. & Quartapelle, L. (2000). A projection FEM for variable density incompressible
  flows. *J. Comput. Phys.* 165, 167–188. <https://doi.org/10.1006/jcph.2000.6609> — not opened;
  configuration via Espinoza-Contreras et al. (2024).
- Johns Hopkins Turbulence Databases. Turbulent channel flow dataset, README-CHANNEL (Graham,
  Lee, Malaya, Moser, Eyink, Meneveau; Kanov, Burns, Szalay).
  <https://turbulence.idies.jhu.edu/docs/channel/README-CHANNEL.pdf> — full text read.
- Kim, J., Moin, P. & Moser, R. (1987). Turbulence statistics in fully developed channel flow at
  low Reynolds number. *J. Fluid Mech.* 177, 133–166. — could not be read (scanned PDF); no
  number is taken from it.
- Lazarian, A. & Pogosyan, D. (2000). Velocity modification of H I power spectrum. *Astrophys.
  J.* 537, 720–748. <https://doi.org/10.1086/309040>; arXiv:astro-ph/9901241 — read via ar5iv
  (Table 1, Eqs. 18, 31, 42, 43, Sect. 4).
- Lee, M. & Moser, R. D. (2015). Direct numerical simulation of turbulent channel flow up to
  $\mathrm{Re}_\tau \approx 5200$. *J. Fluid Mech.* <https://doi.org/10.1017/jfm.2015.268>;
  arXiv:1410.7809 — read via ar5iv (Eq. 3.1, Table 1); data at <http://turbulence.ices.utexas.edu>.
- LeVeque, R. J. (2002). *Finite Volume Methods for Hyperbolic Problems*. Cambridge University
  Press. — not opened here; cited as the repository's `BOUNDARIES` docstring cites it.
- Ohana, R. et al. (2024). The Well: a large-scale collection of diverse physics simulations for
  machine learning. arXiv:2412.00568. — only a search snippet (uniform grids) was read. Dataset
  pages read: `rayleigh_taylor_instability`, `rayleigh_benard`, `turbulent_radiative_layer_2D`,
  `MHD_64` at <https://polymathic-ai.org/the_well/datasets/>.
- OpenCFD. OpenFOAM v2406, Shifter image `opencfd/openfoam-default:2406`, tutorials
  `multiphase/twoLiquidMixingFoam/lockExchange`, `combustion/reactingFoam/laminar/counterFlowFlame2D`,
  `basic/scalarTransportFoam/pitzDaily`, `incompressible/pimpleFoam/laminar/planarPoiseuille`
  and `cylinder2D` — case files read in the image, 2026-11-26.
- Peters, N. (1984). Laminar diffusion flamelet models in non-premixed turbulent combustion.
  *Prog. Energy Combust. Sci.* 10, 319–339. — not opened; the form of (7) was derived here and
  matched against the ANSYS Fluent theory guide (secondary).
- Stokes, G. G. (1851). On the effect of the internal friction of fluids on the motion of
  pendulums. *Trans. Camb. Phil. Soc.* 9, 8–106. — not opened; (3) derived and checked here.
- Thévenin, S. & Gréa, B.-J. (2025). Modeling late-time sensitivity to initial conditions in
  Boussinesq Rayleigh–Taylor turbulence. arXiv:2503.16244 (submitted to *Physica D*). — read
  (text extraction): Eqs. (2), (8), Sect. 3.2, Fig. 2.
- kinet (`/global/u2/k/khegazy/projects/pde/kinet`, branch `perf/cleanup`):
  `simulations/poiseuille/{channel,plates}.yaml`, `analytic.py`; `simulations/flow_around_objects/*.yaml`;
  `simulations/rmi_heavy_to_light/default.yaml`; `kinet/config/common/boundary_conditions.py` — read.

## 12. Confidence

**Sure of:** the HDF5 structure, shapes, boundary groups, coordinate ranges and storage of every
Well, treb and kinet file named (read from headers and coordinate arrays); the OpenFOAM tutorials
exist in the v2406 image with the parameters quoted; kinet's Poiseuille case and its inlet
limitation; the JHTDB channel numbers (README read in full); the closed forms (1)–(3), (6)–(7)
and the projection–slice identity (numerically checked); Lee & Moser's Eq. 3.1 constants and
Lazarian & Pogosyan's Table 1 slopes as read through ar5iv; the FEATFLOW reference values.

**Reasoning, my own:** (4) and the scalar-variance budget (derived, not checked numerically);
(5) and the RT potentials (derived; only its self-consistency was checked); the ideal-mixing
argument that density is linear in volume fraction; every cost and storage figure; the kinet
channel infeasibility estimate (it rests on an unchecked $u_\tau/U_b$ and an unmeasured D3Q27
rate); the claim that `neumann` creates wall slip under smoothing; the ranking.

**Not verified:** whether The Well's `rayleigh_benard` rows were interpolated from Chebyshev
nodes; whether Well periodic axes repeat their first column; Well RT's $\rho_h$, $\rho_l$ and
mixing rule; the Duff–Harlow–Hirt $\psi$ (garbled extraction); the Guermond–Quartapelle
interface formula (garbled extraction); that `setExprFields` is in the v2406 image; the
counterflow flame's run time; the JHTDB access terms and `getCutout` signature (as in spec 04);
whether OpenFOAM's `scalarTransport` function object runs alongside `pisoFoam` in v2406; and any
statement attributed to a source marked "not opened".

**Decisions for Kareem**, each with its consequence: (i) the per-field odd extension at no-slip
walls (Sect. 3.6): without it, smoothing degradations put a small slip velocity on the wall;
(ii) whether a mixing metric may turn density into a volume fraction with the dataset's
$\rho_h$, $\rho_l$ (Sect. 4.2), or only datasets that store a volume fraction (the OpenFOAM run)
count for $\Theta$; (iii) a fixed channel count for `ppv` (Sect. 6), which makes a cube with
another count unreadable.

## 13. Connections

- Issue 085 (rotating stratified data): The Well's `planetswe` (rotating shallow water on the
  sphere, equiangular grid, `theta_open`, fields `height` and `velocity`; headers read) is on
  disk, but its spherical grid does not fit `GridSpec`.
- Issue 053 (more than one mesh): the AMR vortex street of Sect. 8.
- Spec 02 (grid refinement against a known solution): Eqs. (1), (6) and the kinet Poiseuille run
  give refinement studies with walls, which spec 02 lacks.
- Spec 03 (shocks): `turbulent_radiative_layer_2D` becomes readable with the same boundary
  mapping and stores pressure.
- Step 25: the OpenFOAM converter and the passive scalar are additions to the same case.

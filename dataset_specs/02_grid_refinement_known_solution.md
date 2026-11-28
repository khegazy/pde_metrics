# Dataset 02: a grid-refinement sequence against a known solution

**Catalog clusters:** D5 (grid refinement against a known solution); B7 (the reader for the
512² reference run); H3 (one analysis grid per comparison, which this experiment must bypass).
**Metrics served:** the 10 pointwise and gradient norms (`mse`, `mae`, `rmse`,
`rmse_channel_mean`, `nrmse`, `vrmse`, `max_error`, `max_error_channel_mean`, `h1_seminorm`,
`h1_relative`) directly; `shock_set_distance` on the Sod form; every metric through the
reference's own discretisation error. **Ideas served:**
`docs/ideas/infrastructure/grid_convergence.md`; issue 126; the grid-convergence experiment proposal, deleted on 2026-11-27 once
built (`BUILD_ORDER.md`, steps 5, 16, 17 and 32).
**Date:** 2026-11-05. **Author:** research sub-agent (branch `update_metric_eval_principles`).

## 1. Purpose

The pointwise norms come from numerical analysis, where the first figure anyone draws is the
error against the grid spacing on logarithmic axes with the formal order of the scheme drawn
in as a slope (Roy 2005, Sect. 2.5, Fig. 3; read in full, see References). Nothing in the
repository refines a grid against a known answer. The coarsening degradations remove
resolution from a fixed reference, which is a damaged copy of a fine field and not a coarser solve;
the three forecast runs of `forecast_re5e4` are one trajectory at three resolutions with no
exact solution, their finest member's target is the reference itself, and their observed
order falls from 1.3 to 2.0 at the first step to 0.1 to 1.2 at the last as the chaotic flow
decorrelates (issue 126, table of evidence). A 512² and a 256² run of the reference shear
layer sit on disk from one deterministic initial condition and are a two-level solver
comparison with no exact answer (`FUTURE_EXPERIMENTS_CATALOG.md`, Sect. 1.3). The two
kinet Sod runs are one solver resolution each against an exact solution the repository
already computes (`docs/datasets/sod_shock_tube.md`).

This document specifies three kinds of dataset. Option A is a set of analytic ideals: flows
with closed-form solutions that the kinet lattice-Boltzmann solver, its finite-volume
(PonD) integrator, or any finite-volume code can run at 64², 128², 256² and 512². Option B
is the shear layer on disk read as a Richardson sequence with the finest run as the
reference. Option C is the kinet Sod runs against the exact Riemann solution, extended to
a sequence of resolutions.

## 2. What the dataset must provide

- **A sequence of grids refined by a constant ratio r = 2**, 64², 128², 256², 512² for a
  two-dimensional problem (Roy's worked example uses five grids, 129² down to 9², r = 2;
  his Table 1), and for the one-dimensional problems a sequence with the same ratio.
- **The same continuum problem on every grid.** The same domain length, the same physical
  parameters (viscosity, Mach number or its scaling rule, sound speed), the same initial
  condition sampled from one continuum function on each grid's own nodes, and the same
  physical output times. Lattice-unit parameters must be rescaled per level so that the
  physical ones are fixed (Sect. 4.0).
- **A known answer on each grid's own nodes.** The exact solution evaluated at the solver's
  node positions at every stored time, or (Option B) the finest solution at the coincident
  nodes of the coarser grids.
- **Fields.** Density and velocity for the weakly compressible lattice-Boltzmann problems;
  density, velocity and pressure for the compressible ones; vorticity recomputed, never
  stored for evaluation (`fmeval/data/base.py`).
- **Frames at several times**, because the observed order should be read at more than one
  time (Spiegel, Huynh and DeBonis 2015, Sect. IV.D, recommendation 3; read in full).
- **Double precision**, so that the finest grid's error is above round-off by a safe margin.
- **One realisation.** The problems are deterministic and the answer is a number per grid.

## 3. The known answer: the observed order of accuracy

Roy (2005, Sect. 2.3.2, p. 135; read in full) expands the discretisation error on grid level
k, of spacing h_k, as

```
DE_k = f_k - f_exact = g_p h_k^p + HOT,                                        (Roy Eq. 5)
```

where f_k is the numerical solution, g_p the coefficient of the leading term and p the
observed order. The "main assumption is that the higher-order terms (HOT) are negligible,
which is equivalent to saying the solutions are in the asymptotic range" (his words, p. 135).
He defines the asymptotic range as "the range of discretization sizes ... where the
lowest-order terms in the truncation error dominate" and lists what spoils the observed order:
"mistakes in the computer code, solutions which are not sufficiently smooth, defective
numerical algorithms, and numerical solutions which are not in the asymptotic grid
convergence range" (p. 135). With the exact solution known, the discrete norms on grid k are

```
Linf_k = max_n | f_{k,n} - f_exact,n |,
L2_k   = ( (1/N) sum_n | f_{k,n} - f_exact,n |^2 )^{1/2},                      (Roy Eq. 7)
```

summed over the N nodes of that grid, and the observed order between levels k and k + 1,
refined by the factor r, is

```
p = ln( L_{k+1} / L_k ) / ln r,                                                (Roy Eq. 8)
```

where L_k is either norm (p. 140). `max_error` is Linf_k, `rmse` is L2_k, `mse` is its
square, and `mae`, `nrmse`, `vrmse` and the channel means are rescalings of these that do not
change p. For a second-order scheme the figure of L against h shows a slope of two and p
settles at 2 as h shrinks (Roy's Figs. 3 and 4: the Premo code "clearly asymptotes to
second-order accuracy", the Wind code "slightly higher than two"). The expected outcome for
every metric here is therefore a number, 2 for the lattice-Boltzmann and finite-volume
schemes on smooth problems, and 1 or less on the non-smooth problems (Sect. 5.3).

Two rules follow from Eq. (5) and are repeated for every option below.

1. **Compare on each grid's own nodes.** Remapping a level onto a common analysis grid adds a
   remap error of its own order, which enters the measured p. Evaluate the exact solution at
   the solver's node positions and difference there (the catalog's D5 entry says the same).
   The repository's closed-form readers sample cell centres, (i + 1/2) h
   (`fmeval/data/analytic.py`, `ClosedFormTrajectory`). *Corrected on 2026-11-27:* kinet's
   Taylor–Green initializer places node i at (i + 1/2) · 2π/N, the same cell centres, not at
   i · 2π/N as first written here (the job agent's reading of `_build_coordinate_grid` in its
   comparison script, `docs/datasets/logs/kinet_runs/taylor_green_re50/_scripts/compare_tg.py`;
   measured: the converted runs' initial frames equal the exact solution at the cell centres to
   1e-14 on all eight grids, where half a cell's offset would leave an error of order h). So no
   node-offset option is needed, and `taylor_green_kinet` has none. Evaluating the exact
   solution half a cell off the solver's nodes would be a first-order error that caps the
   observed order at 1 (the author's reasoning).
2. **Read the order where it is steady.** Compute p per frame and per field from successive
   pairs of levels, and report the curve p(t); the asymptotic range is where p is steady
   across both the pairs (64, 128)→(128, 256) and (128, 256)→(256, 512) and across
   neighbouring times. With three or more grids the check of Roache's that the NPARC
   verification tutorial states as GCI_23 / (r^p GCI_12) ≈ 1 applies (Sect. 5.1).

The observed-order computation itself is harness work: `fmeval/analysis.py` from rows that
carry `param_resolution`, as issue 126 proposes, with the analysis-grid remap switched off by
setting `analysis_grid.resolution` to each level's own N.

## 4. Option A, the analytic ideals

### 4.0 Rules common to every ideal

- **Domain.** The periodic square [0, 2π)² unless stated (Taylor–Green, manufactured
  solution) or [0, 10]² (isentropic vortex). Both axes periodic, which every metric and
  degradation of the repository accepts.
- **Grid sequence.** N = 64, 128, 256, 512 nodes per axis, ratio 2, nodes at x_i = i L/N.
  (kinet's Taylor–Green runs place them at (i + 1/2) L/N, Sect. 3, rule 1; against an exact
  solution on each grid's own nodes the placement only has to be known, not nested.)
- **Scaling rule between levels (the trap that decides whether p can reach 2).** A
  lattice-Boltzmann solver has two small parameters, the lattice spacing and the Mach number,
  and its leading errors are O(h²) and O(Ma²). kinet fixes `mach` as a parameter and the
  reference runs keep Ma = 0.1 at every resolution ("step 2n of the 512² run is at the
  physical time of step n of the 256² run", catalog Sect. 1.3: that is acoustic scaling, with
  the lattice velocity fixed and the time step proportional to h). Under acoustic scaling the
  O(Ma²) error is the same on every level and floors the sequence at roughly 10⁻² relative,
  which a 128² Taylor–Green solve already reaches, so the observed order would fall toward
  zero for reasons that have nothing to do with the spatial scheme (the author's reasoning
  from the two error terms; not measured). The convergence studies in the lattice-Boltzmann
  literature use **diffusive scaling**, Ma ∝ 1/N: dos Santos and Siebert (2026, Sect. 3.2;
  read in full in the arXiv HTML version) set the lattice velocity U₀ = 2/L on L = 32 to 256
  with the relaxation time fixed at τ = 0.62, and Yu et al. (2023, Sect. III.2; read in a
  summary of the arXiv HTML version) fix Δx²/Δt. Therefore run the ideals with
  Ma_N = Ma_64 · 64/N (for instance Ma_64 = 0.08, so Ma_512 = 0.01) and the physical
  viscosity fixed, and run one second sequence at fixed Ma = 0.1 so that the floor is
  measured rather than assumed; the project's rule is to build every standard where fields
  disagree (`AGENTS.md` §1).
- **Initialisation.** A lattice-Boltzmann run started from equilibrium populations carries an
  initial layer; dos Santos and Siebert (2026, Sect. 4.2) report that equilibrium
  initialisation makes their Taylor–Green errors "two to about four and a half times larger"
  than initialising with the non-equilibrium part f_i^(1) built from the Navier–Stokes stress
  (their words as summarised; the numbers are theirs). Mei et al. (2006; abstract only) give
  an iterative procedure for the same purpose. Whether kinet's `initialization_policy:
  analytic` seeds f^neq from the analytic velocity gradient was not checked and must be,
  because an O(h) initial layer caps p at 1.
- **Comparison times.** At least three frames: a short time, a middle time and a time at which
  the solution has changed by order one (specified per ideal). The order read at a single
  time can be wrong (Spiegel et al. 2015, Sect. IV.D, recommendation 3).
- **Fields and norms.** Every stored field, both Roy norms (`max_error`, `rmse`) and the
  gradient seminorm, per frame and per level, on the level's own nodes.
- **Formal order.** Two for the D2Q9 BGK lattice-Boltzmann scheme in space under diffusive
  scaling (dos Santos and Siebert 2026, Sect. 4.2: "All three operators converge at second
  order: the error decreases by a factor of four at each refinement", with BGK one of the
  three; Yu et al. 2023: "spatial second-order convergence" of BGK, TRT, RLB and TRT-RLB on
  32² to 512²; Skordos 1993, abstract: the error "decreases quadratically with finer
  resolution both in space and in time"), and two for a second-order finite-volume scheme.

### 4.1 Ideal (i): the two-dimensional Taylor–Green vortex

**Equations.** Incompressible Navier–Stokes at unit density on [0, 2π)², periodic
(`docs/datasets/taylor_green_vortex.md`, Eq. 1).

**Solution.** Taylor (1923, p. 674, through the stream function ψ = A cos(πx/d) cos(πy/d)
exp(−2π²νt/d²); read by the repository's author, cited from the dataset page and from
kinet's `units/references.py`) gives, translated to the repository's convention
(`fmeval/data/analytic.py`, `TaylorGreen2D`),

```
u =  U0 sin(kx) cos(ky) exp(-2 nu k^2 t),
v = -U0 cos(kx) sin(ky) exp(-2 nu k^2 t),
p = p0 + (rho0 U0^2 / 4) (cos 2kx + cos 2ky) exp(-4 nu k^2 t),
omega = 2 k U0 sin(kx) sin(ky) exp(-2 nu k^2 t),
```

with k = 1 for the repository's and kinet's configurations. Taylor and Green (1937) is the
three-dimensional problem and was not opened; the two-dimensional closed form is Taylor's
(the search listings for the 1937 paper say the same). For a weakly compressible isothermal
lattice-Boltzmann solver the density is not constant: with p = c_s² ρ the exact solution's
pressure fluctuation is carried by the density, ρ = ρ0 + (p − p0)/c_s², which is of relative
size Ma² (the author's derivation; Yu et al. 2023, Eq. 66, write the same density perturbation
with the factor u₀²/(4 c_s²), as read in the summary of their arXiv HTML version; kinet's
initializer writes δp = ρ0 U0² (cos 2kx + cos 2ky)/4, `_pressure_perturbation_analytic`,
read in full). The exact solution is of the incompressible equations, so the compressible
solver's error against it contains the O(Ma²) term of Sect. 4.0.

**Parameters.** Re = U0 L/ν with L = 2π: Re = 50 as in dos Santos and Siebert (2026, Sect.
3.2, τ = 0.62, ν = 0.04 in lattice units at L = 32) or Re = 10 as in He and Chen (2026; only
their abstract and a search summary were read). Roy (2005, p. 137) advises Reynolds numbers
"near unity so that convective and diffusive terms are of the same order of magnitude" for
verification; the Taylor–Green flow is special in that the advective term is balanced exactly
by the pressure, so a low Reynolds number costs nothing here. The decay time of the velocity is
t_d = 1/(2 ν k²) (Yu et al. write t_d = 1/(8νπ²) for L = 1, which is the same with k = 2π).
Compare at t = t_d/4, t_d/2 and t_d, where the velocity has fallen to e^{−1}; the repository's
`taylor_green_2d` configuration ends at exactly that time (ν = 0.01, t = 50).

**What kinet has.** A Taylor–Green experiment, `experiments/taylor_green_vortex/Re-50k_Ma-1en1.yaml`
(read in full): D2Q9, entropic BGK, 512², Re = 5 × 10⁴, Ma = 0.1, periodic, k = 1,
`initialization_policy: analytic`; the data directory `kinet/taylor_green_vortex/` holds no
trajectory (listed on 2026-11-05). The sequence needs that configuration at 64, 128, 256 and
512 with `reynolds` lowered to 50 and `mach` scaled as Sect. 4.0 says.

**Known results.** dos Santos and Siebert (2026, Fig. 3, no table): second-order convergence
of the relative L₂ velocity error for BGK, RLBM and E-RLBM on 32² to 256² at Re = 50; the
only numbers in the text are the error differences at L = 256, about 1.1 × 10⁻⁶ (E-RLBM) and
1.4 × 10⁻⁵ (RLBM) relative to BGK. Yu et al. (2023, Fig. 3, no table): second order on 32² to
512². Krüger, Varnik and Raabe (2010; abstract only): the deviatoric stress is second-order
accurate in the bulk BGK method, shown on the decaying Taylor–Green vortex. No published
table of observed orders for plain D2Q9 BGK on this flow was found; the two papers that were
read give figures only.

**Limits.** A single Fourier mode: the sharp spectral degradations are degenerate on it
(`docs/datasets/taylor_green_vortex.md`, "What the evaluation sees"), the impostor is a
translation, and every frame is a scalar multiple of the first. None of that matters for the
order-of-accuracy figure, but it means this dataset is evidence about discretisation error
only.

### 4.2 Ideal (ii): the isentropic vortex convected on a periodic domain

**Equations.** The two-dimensional compressible Euler equations of a perfect gas, γ = 1.4.

**Solution.** Spiegel, Huynh and DeBonis (2015, Sect. IV.A.1, Eqs. 20 to 23; read in full)
build it as perturbations of velocity and temperature on a uniform mean flow, defined so that
the entropy p/ρ^γ is constant everywhere, from a Gaussian Ω = β e^{f},
f = −(1/2σ²)[(x/R)² + (y/R)²], with δv_x = −(y/R) Ω, δv_y = +(x/R) Ω,
δT = −(γ − 1) Ω²/2 (their Eq. 22, in their nondimensionalisation by ρ∞, a∞, T∞), and the
primitive variables ρ̃ = (1 + δT)^{1/(γ−1)}, p̃ = (1 + δT)^{γ/(γ−1)}/γ (their Eq. 23). The
version kinet implements (`kinet/reference/vortex.py`, read in full; its docstring cites
Shu, ICASE Report 98-32, Sect. 4.5, which could not be opened here: the NASA copy of Shu's
1997 report is a scan) is, with r the distance from the vortex centre in units of the core
radius R and a∞² = p∞/ρ∞,

```
theta = 1 - (gamma - 1) beta^2 / (8 gamma pi^2) exp(1 - r^2),
rho = rho_inf theta^(1/(gamma - 1)),      p = p_inf theta^(gamma/(gamma - 1)),
u = U_inf + (beta a_inf / 2 pi) exp((1 - r^2)/2) (-(y - y_c), x - x_c) / R,
```

and the exact solution at time t is this field with the centre at x_c + U∞ t, wrapped to
the periodic box: "the exact solution to the problem is just the translation of the initial
conditions based on propagation speed and simulation time" (Spiegel et al. 2015, Sect.
IV.B.1). The standard parameters, which kinet's `experiments/isentropic_vortex/default.yaml`
(read in full) uses, are β = 5, R = 1, ρ∞ = p∞ = 1, U∞ = (1, 1), γ = 1.4, domain [0, 10]²
periodic, vortex centred at (5, 5), so that at t = 10 the vortex has gone once round the box
and the exact solution is the initial state again. Spiegel et al. record that "the original
version of this problem used a computation domain of L = 5 and all boundaries were set to
periodic conditions" and was run for 10 periods (Sect. IV.A.2), and that the first version
is Shu's (Sect. IV.A); their Table 1 lists the parameter sets of Shu, Vincent, Hesthaven and
Warburton, and the high-order workshop. The attribution of this problem to Yee, Sandham and
Djomehri (1999) in the task statement could not be checked: the publisher page, the
Southampton eprint and two PDF copies of that paper could not be read here (one is a scan,
one is encrypted), so no equation number is quoted from it and the parameters above are
Spiegel's and kinet's.

**Parameters and times.** As above; store t = 2.5, 5 and 10 (a quarter, a half and one
period). The Gaussian tail at the box edge, five cores from the centre, is e^{−12} ≈ 6 × 10⁻⁶
in velocity and e^{−24} ≈ 4 × 10⁻¹¹ in θ (the author's arithmetic; kinet's docstring quotes
the second), so the periodic images are negligible for a second-order study; Spiegel et al.
warn (Sect. IV.D, recommendation 1) that a domain too small for the perturbation to vanish at
the boundary "create[s] an artificial shear layer that does not exist in the exact analytical
solution".

**Which code.** kinet runs this problem in its finite-volume PonD integrator (DUGKS, D2Q16,
100² cells on [0, 10]², dynamic viscosity 10⁻⁵; the three configurations read in full), not
in the lattice-Boltzmann path. Any finite-volume Euler code runs it. The vortex is smooth, so
the formal order of a second-order finite-volume scheme is 2 in both norms.

**Known results.** Spiegel et al. (2015, Fig. 2) show L₂ errors against the length scale for
polynomial orders P1 to P6 of a flux-reconstruction method after one period; they warn that
over- and under-resolution both spoil the computed order (Sect. IV.D, recommendation 2) and
that a second-order finite-volume scheme dissipates the vortex within a few periods
(Sect. IV.D, last paragraph), which is why the times above stop at one period. A
second-order MUSCL table on 64² to 512² was not found in an opened source; a search snippet
of a 2025 arXiv paper (2505.17753, not opened) reports L₂ density errors on 100² to 800²
with orders 2.7 to 2.9 for a k = 1/3 MUSCL reconstruction, which is not the second-order
case.

**Limits.** Inviscid, so it tests the convective discretisation and not the viscous one, and
the density and pressure carry only the vortex's O(β²) dip (about 0.5 at the centre for
β = 5, Spiegel's Fig. 1 contours run 0.5 to 0.98), so `h1_seminorm` on density sees one
smooth bump.

### 4.3 Ideal (iii): the Lamb–Oseen vortex

**Solution.** Gallay (2012, Sect. 3, Eqs. 3.1 and 3.2; read in full in the ar5iv rendering)
writes the Oseen vortex of circulation γ and viscosity ν as

```
omega(x, t) = (gamma / (nu t)) G(x / sqrt(nu t)),     G(xi) = exp(-|xi|^2 / 4) / (4 pi),
u(x, t) = (gamma / sqrt(nu t)) v^G(x / sqrt(nu t)),
v^G(xi) = (1 / 2 pi) (xi_perp / |xi|^2) (1 - exp(-|xi|^2 / 4)),
```

"a self-similar solution of (2.2) with Gaussian vorticity profile G" (his words), which in
polar form is the familiar u_θ = Γ/(2πr) (1 − e^{−r²/(4νt)}) and ω = Γ/(4πνt) e^{−r²/(4νt)}.
To start from a finite core of radius r_c, shift the time origin: t₀ = r_c²/(4ν).

**Why it ranks last here.** It is a solution on the whole plane with a far field u_θ ∝ 1/r
and non-zero net circulation, which no periodic box can hold; on a periodic box the
images strain the vortex and the solution is no longer exact (the author's reasoning; Gallay
treats the plane only). It needs velocity boundaries that impose the exact solution on all
four sides, which kinet's lattice-Boltzmann path does not advertise (the boundary package
lists periodic, Neumann and Robin types; not checked further), and the pressure of this
vortex is an integral of ρ u_θ²/r with no elementary closed form, so a compressible solver's
density has no simple target. Keep it as a candidate for a code with Dirichlet velocity
boundaries; its formal order is 2 for the same schemes.

### 4.4 Ideal (iv): the method of manufactured solutions

**Procedure.** Roy (2005, Sect. 2.5, pp. 136 to 137; read in full): "choose the solution a
priori, then operate the governing partial differential equations onto the chosen solution,
thereby generating analytical source terms. The chosen (manufactured) solution is then the
exact solution to the modified governing equations made up of the original equations plus the
analytical source terms." His six steps: (1) choose the governing equations, (2) choose the
manufactured solution, (3) derive the modified equations, (4) solve them on multiple meshes,
(5) evaluate the global discretisation error, (6) compare the observed with the formal order.
He adds that step 4 "may require code modifications to allow arbitrary source terms, initial
conditions, and boundary conditions", that "MMS requires the ability to include arbitrary
source terms" and "is thus code-intrusive" (p. 141), and that the solution "should be chosen
to be smooth, analytical functions with smooth derivatives", with "trigonometric and
exponential functions ... recommended", "no derivatives vanish, including cross-derivatives",
Reynolds numbers near unity, and realisable values (positive density and temperature)
(p. 137). Roache (2002) is the tutorial on the method; it was not opened, and its
bibliographic details are taken from the repository's proposal and kinet's
`units/references.py`.

**The source terms the isothermal weakly compressible equations then need.** For a chosen
density ρ̂(x, t) and velocity û(x, t), with p̂ = c_s² ρ̂ and the viscous stress τ̂ of the
Navier–Stokes model the solver implements,

```
S_rho = d_t rho_hat + div(rho_hat u_hat),
S_m   = d_t(rho_hat u_hat) + div(rho_hat u_hat u_hat) + grad p_hat - div tau_hat,
```

so that (ρ̂, û) solves the continuity and momentum equations with S_ρ and S_m added to their
right-hand sides (the author's statement of Roy's step 3 for these equations; Roy's own
example is the steady two-dimensional Euler system with sources f_m, f_x, f_y, his Sect. 2.5).
Both sources are evaluated symbolically or by automatic differentiation and sampled on each
grid's nodes at each time. A manufactured solution the author suggests, periodic on [0, 2π)²
and obeying Roy's rules: ρ̂ = ρ0 [1 + 0.1 sin(x + y) cos(t)],
û = U0 (sin(x) cos(2y) cos(t), cos(2x) sin(y) sin(t)) with U0 chosen so that Re ≈ 1 to 10; it
is not divergence-free and has no vanishing derivatives, which is the point.

**Can the kinet lattice-Boltzmann solver take a source term?** Partly, today. The solver has
a forcing registry with continuum source channels `mass`, `momentum` and `energy`
(`kinet/solver/common/forcing/sources.py`, read in full), a plugin decorator
`@register_forcing`, and a Guo, Zheng and Shi (2002) discrete force kernel
(`kinet/solver/lbm/physics/forcing/guo.py`, docstring read in full: the equilibrium uses the
half-force shifted velocity and the population source carries the prefactor 1 − 1/(2τ)). The
registered laws (`solver/common/forcing/laws/`, docstrings read) are a constant body force, a
linear (Lundgren) forcing, random low-mode forcing, uniform energy heating and the multipole
acoustic sources, which do carry a `mass` monopole and a `momentum` dipole as Gaussians
driven in time. No law evaluates an arbitrary analytic space–time field, so the manufactured
sources need one new law returning `{mass, momentum}` sampled on the lattice at the current
time; whether the weakly compressible scheme consumes a `mass` source outside the multipole
path was not verified. Guo et al. (2002; abstract only) show that "discrete lattice effects
must be considered in the introduction of a force into the lattice Boltzmann equation",
which is the known trap: the source discretisation must itself be second order or the
observed order falls to 1 regardless of the scheme. A mass source is less standard in the
lattice-Boltzmann literature than a body force, and the author did not open a paper that
verifies a second-order mass source; the Taylor–Green and vortex ideals need no source at all,
which is why they rank ahead of this one.

**Formal order.** Two, for the same schemes, provided the source discretisation is.

### 4.5 Ideal (v): one-dimensional viscous Burgers with the Cole–Hopf solution

**Equation.** ∂_t u + u ∂_x u = ν ∂_xx u on [0, 2π), periodic.

**Solution.** The Cole–Hopf transformation u = −2ν ψ_x/ψ maps Burgers' equation to the heat
equation ψ_t = ν ψ_xx (Gesztesy and Holden 1998, Eqs. 1.14 to 1.16 and Lemma 3.1 for the
viscous form; read in full in the ar5iv rendering; they cite Hopf 1950 and Cole 1951, which
were not opened). For the initial condition u(x, 0) = −sin x, ψ(x, 0) = exp(−cos x/(2ν)), and
expanding in the modified Bessel functions I_n through e^{z cos x} = I_0(z) + 2 Σ I_n(z) cos nx
with z = −1/(2ν) and I_n(−z) = (−1)^n I_n(z),

```
u(x, t) = 4 nu sum_{n>=1} (-1)^n n I_n(1/2nu) exp(-nu n^2 t) sin(nx)
          / [ I_0(1/2nu) + 2 sum_{n>=1} (-1)^n I_n(1/2nu) exp(-nu n^2 t) cos(nx) ],
```

the author's derivation (it reproduces u(x, 0) = −sin x, and the Bessel functions must be
evaluated in their exponentially scaled form, `scipy.special.ive`, because I_n(1/2ν) overflows
for small ν). The benchmark of Basdevant et al. (1986), u(x, 0) = −sin πx on (−1, 1) with
ν = 0.01/π and Dirichlet ends, is the standard one, known here only through Burkardt's code
pages (secondary source); it steepens into a layer of width about ν that a 64-cell grid cannot
resolve, so for a refinement study choose ν = 0.1 (Re = 10 on the 2π box), which keeps the 64-
cell grid in the asymptotic range (the author's choice, not sourced). Compare at t = 0.5, 1
and 2.

**Cost and code.** Fifty lines of NumPy for the exact solution and a few hundred for a
second-order finite-volume solver; kinet has a D1Q3 lattice (`experiments/sod/lbm_1d.yaml`)
but no Burgers scheme. Formal order 2 for a second-order scheme. This is the cheapest check
that the observed-order machinery in the harness works at all, and should be run first.

## 5. Options B and C: simulated data with the finest grid or the Riemann solution as reference

### 5.1 Option B: the kinet shear layer at 512², 256² and a 128² rerun (Richardson-style)

**What is on disk** (catalog Sect. 1.3 and the configs, read in full on 2026-11-05).
`kinet/doubly_periodic/weakly_compressible_isoT_fluids/sys_Re-5e4_Ma-1en1/D2Q9_shape-512-512_T-20000_H-56d32e.h5`
(1.43 TB) and `prev_256/D2Q9_shape-256-256_T-20000_H-131010.h5`, both D2Q9 entropic BGK,
Re = 5 × 10⁴, Ma = 0.1, periodic, density 1, the double shear layer with λ = 80 and
ε = 0.05, float64, 20 000 steps each; and `kinet_re5e4` itself (dc804f, 256², 10 000 steps).
The physical time unit is L/(Ma c_s): on 256 cells that is 256 √3/0.1 = 4434 steps, so 10 000
steps are 2.2553 time units, which is the end time the dataset page states (the author's
arithmetic, reproducing `docs/datasets/reynolds_ladder_2d.md`). The reviewer measured the
relative L₂ difference between the 2 × 2 block average of the 512² velocity and the 256² run
at 7 × 10⁻³ at steps 0, 500 and 2000, 2.4 × 10⁻² at 5000 and 3.9 × 10⁻² at 10 000 (256²
clock; catalog Sect. 1.3).

**A finding about the initial condition that must be checked before any order is read.**
kinet's current shear-layer initializer places its nodes at x_i = i/(N − 1), i = 0 … N − 1
(`kinet/initialization/shear_layer.py`, lines 48 to 49, read in full), so the field includes
both x = 0 and x = 1 and its period is stretched by N/(N − 1); the Taylor–Green initializer
in the same package documents this very convention as "the latent bug in the old
Taylor-Green vortex code" and uses x_i = i L/N instead. If the on-disk runs were initialised
this way (not verified: the runs may predate this code), the 256² and 512² initial fields are
not samples of one continuum function on nested grids but differ by a relative stretch of
256/255 versus 512/511, which moves the λ = 80 layers by about 4 % of their width and is an
O(1/N) discrepancy. That would explain the 7 × 10⁻³ difference at step 0 at least as well as
the catalog's remap explanation, and it caps the observed order at 1. The remedy is to rerun
all three levels, 128², 256² and 512², from t = 0 with nodes at i L/N, to 2 000 steps on the
256² clock (1 000 at 128², 4 000 at 512²), which is 0.45 time units and the range in which
the reviewer's differences were still at their floor; rerunning the 512² level that far costs
a fifth of the run on disk.

**Comparison rule.** With nodes at i L/N, node i of the 128² grid is node 2i of the 256² grid
and node 4i of the 512² grid, so the three levels are compared at coincident nodes with no
interpolation at all. Take the differences of successive levels, d_1 = ‖u_256 − u_512‖ and
d_2 = ‖u_128 − u_256‖ at the same physical time, in both norms and per field; then

```
p = ln(d_2 / d_1) / ln 2,
```

which is the three-grid observed order of the NPARC verification tutorial,
p = ln[(f_3 − f_2)/(f_2 − f_1)]/ln r, applied to norms of field differences (the tutorial was
read in full; it cites Roache 1994, which could not be opened). Richardson's estimate of the
continuum value is f_exact ≈ f_1 + (f_1 − f_2)/(r^p − 1), and the grid convergence index on
the fine grid is GCI_12 = F_s |(f_1 − f_2)/f_1| / (r^p − 1) with F_s = 3 for two grids and
1.25 for three or more (the tutorial's statement of Roache's recommendation; the repository's
`docs/ideas/infrastructure/grid_convergence.md` states the same formulas from Roache 1997 and
Celik et al. 2008, neither opened here). The asymptotic-range check is GCI_23/(r^p GCI_12) ≈ 1.

**The asymptotic-range caveat for a chaotic flow.** Roy (2005, Sect. 3.5.6, p. 154) says of
under-resolved simulations that "all methods for estimating the discretization error rely on
the solutions being asymptotic" and that outside that range the error estimate's "behavior ...
is possibly random due to the influence of the higher-order terms"; in Sect. 3.4.3 he calls
extrapolation "far outside the asymptotic range ... unpredictable and possibly" wrong. For
this flow the issue-126 table is the evidence: on the forecast runs the two-grid order was
1.3 to 2.0 at the first prediction step and 0.1 to 1.2 at the last, because the instantaneous
fields of a chaotic flow decorrelate and the difference between two resolutions saturates at
the size of the field. Read p only at short time, report p(t) and stop where it leaves its
plateau; past that point only statistics converge (the grid-convergence idea page's pitfall
list). The Reynolds number here, 5 × 10⁴ on 256 cells, is far from Roy's "near unity", and
Brown and Minion (1995; not opened, cited by kinet's docstring for the profile) is the paper
on exactly this flow under-resolved; the 128² level may well be outside the asymptotic range,
which the three-grid check will show rather than assume.

**Fields.** Density and velocity at the stored nodes; vorticity recomputed. **Formal order.**
Two for the spatial scheme under acoustic scaling at fixed Ma, until the O(Ma²) floor of
Sect. 4.0 is reached; since all three levels share Ma = 0.1 the compressibility error is
common to them and largely cancels in the differences (the author's reasoning).

### 5.2 Option C: the kinet Sod runs against the exact Riemann solution

**What is on disk** (`docs/datasets/sod_shock_tube.md`, the kinet configs
`kinet/sod/compressible_fluids/*/configs/*.yaml` and `experiments/sod/{subsonic,transonic}.yaml`,
read in full). Two lattice-Boltzmann Sod problems on 3001 × 5 nodes, D2Q9 with a lattice
shift of (0.4, 0), entropic BGK, Neumann walls on the tube axis, 1 000 frames, float64:
γ = 1.4, viscosity 10⁻⁴, Pr = 0.71, left (ρ, T) = (1, 0.2), right (0.125, 0.16), that is
(ρ, p) = (1, 0.2) and (0.125, 0.02); and γ = 2, viscosity 0.025, left (0.5, T = 0.2) and
right (2, 0.025), that is (ρ, p) = (0.5, 0.1) and (2, 0.05). Both have the higher pressure on
the left and both states at rest, so the repository's exact solver covers them with the
reader overrides the dataset page lists (`+dataset.reader.gamma`, `left`, `right`).

**The exact solution.** Toro (2009), Chapter 4: the star pressure from the pressure function
of Prop. 4.1, Eqs. 4.5 to 4.8, the star velocity Eq. 4.9, the star densities Eqs. 4.53 and
4.57, the wave speeds Eqs. 4.55 and 4.59, the fan state Eq. 4.56, and the region assignment
of Sect. 4.5, as the dataset page writes them out (its Eqs. 3 to 7). Toro was not opened by
this author; the equation numbers are the dataset page's and `fmeval/data/analytic.py`'s,
which say they were verified against the book.

**What a refinement sequence needs.** Three levels nested under the x_i = i/(N − 1)
convention are N = 751, 1501 and 3001 nodes (spacings 1/750, 1/1500, 1/3000; node j of 751
is node 2j of 1501 and node 4j of 3001), so one of the existing runs is the finest level and
two reruns complete the sequence; 376 does not nest and a fourth level would need 6001. Keep
the transverse 5 nodes and the lattice shift. The lattice viscosity must be rescaled per
level so that the physical viscosity in units of the tube length and sound speed is fixed:
ν_lat/(N c_s) is the dimensionless viscosity, so ν_lat = 10⁻⁴ (N − 1)/3000 (the author's
derivation from dx = dt = 1 and a fixed lattice sound speed). **Time.** In lattice units
the left sound speed of the γ = 1.4 run is a_L = √(1.4 × 0.2) = 0.529 nodes per step, the
exact solution is self-similar in (x − x₀)/t, and the pressure and density ratios are those
of Sod's problem, so every wave speed is √0.2 = 0.447 times the value in the dataset page's
table: the shock moves at 0.7836 nodes per step and reaches the wall, 1 500 nodes away, at
step 1 914, so the 1 000 stored frames are all valid; the dataset page's window t = 0.1 to 0.2
in tube units is steps 671 to 1 342 on 3001 nodes, of which steps 671 to 1 000 exist (the
author's arithmetic; the dataset page's "t = 200" for this run was not reconciled with it).
Compare at steps 700, 850 and 1 000 on 3001 nodes and at the same physical times on the
coarser levels (steps halved per level). **Fields.** Density, velocity, pressure, each on its
level's own nodes against the exact solution at the same nodes.

**What order to expect.** Not two. Roy (2005, p. 141): "Since MMS is predicated on having
smooth solutions, the analysis of non-smooth solutions (shock-waves, material interfaces,
etc.) is an open research issue" (confirmed verbatim); and p. 154, citing Carpenter and
Casper (1999): "for the Euler equations on sufficiently refined meshes, the simulation of
flows containing shock waves will reduce down to first-order accuracy, regardless of the
formal order of the numerical scheme employed". Banks, Aslam and Rider (2008; abstract read
on the Sandia page) sharpen this: shocks converge at first order in L₁, but linearly
degenerate discontinuities, the contact here, converge sub-linearly, at p/(p + 1) for a
scheme of order p, and "eventually dominate the global rate of convergence"; so a
second-order scheme's L₁ density error on Sod drifts from about 1 toward 2/3 as the grid
refines, and the velocity and pressure, which do not jump at the contact, stay nearer 1.
Ramani, Reisner and Shkoller (2018, introduction; read in the ar5iv rendering) report an L₁
order of about 0.95 for their artificial-viscosity method on Sod at 801 cells and "more
than twice" smaller for the bare WENO discretisation. `max_error` does not converge at a
jump at all (the error at the cell straddling the shock is of the order of the jump; the
author's statement), so on this option report L₁ (`mae`), L₂ and the shock position, and read
`shock_set_distance` against the smeared width, which should fall as h. The viscous
lattice-Boltzmann solution also differs from the inviscid exact one by a viscous shock
thickness of order ν/Δu, about 10⁻⁴ node for the γ = 1.4 run, which is far below the grid and
so invisible; for the γ = 2 run with viscosity 0.025 it is a few hundredths of a node and
still invisible.

**Cost.** Two reruns of at most 1 000 steps at 1501 × 5 and 751 × 5, minutes; a reader for
the layout (issue 046 for the wavenumber of a non-square domain, which this option does not
need because no spectral metric runs on Sod).

### 5.3 Not acceptable

The three `forecast_re5e4` runs as they stand (issue 126: provenance of the predictions
unknown, the finest member's target is the reference, order decays along the forecast); the
`homogeneous_isotropic_turbulence` runs at 128², 256² and 512², which start from different
random fields (catalog Sect. 1.3); any sequence in which the exact solution is remapped onto
a common analysis grid before differencing.

## 6. Recommendation

1. **Burgers with Cole–Hopf (4.5) first**, because it is a day's work with no solver and it
   proves the observed-order code path in `fmeval/analysis.py` and the node-offset reader
   before any solver time is spent.
2. **Taylor–Green on kinet (4.1) second**, at Re = 50 under diffusive scaling on 64² to 512²,
   with the fixed-Ma companion sequence; it is the lattice-Boltzmann community's own
   verification case, kinet already has the initializer, and it is the first run that gives
   the eight pointwise norms their log-log figure on a solver of the repository's family.
3. **The Sod sequence (5.2) third**, two short reruns, because it is the only non-smooth case
   and the shock metrics' resolution dependence has no other source.
4. **The shear-layer Richardson sequence (5.1) fourth**, after the initial-condition
   convention is settled, because it is the reference flow itself and gives the reference's
   discretisation error, which the grid-convergence idea asks for; but it has no exact answer
   and may not be asymptotic at 128².
5. **The isentropic vortex (4.2)** when the compressible metrics need a smooth two-dimensional
   case with pressure: kinet's PonD runs it today at 100²; the manufactured solution (4.4)
   when someone writes the forcing law; the Lamb–Oseen vortex (4.3) only on a code with
   velocity boundaries.

## 7. What to store

Following `docs/recipes/add-a-dataset.md`: one HDF5 file per level, read by a reader
registered in `fmeval/data/readers.py`, grouped by a dataset family whose configs state
`param_resolution`.

- **Fields.** `density`, `velocity` (and `pressure` for the compressible options; not for the
  isothermal lattice-Boltzmann runs, where it is density/3 and carries nothing), channel
  first with trailing `(x, y)`; vorticity recomputed, never stored for evaluation.
- **Precision.** float64 throughout; the finest level's error must sit well above round-off
  (the catalog's "round-off ranking" of the damage anchor measured where that floor lies).
- **Nodes.** The node convention (x_i = i L/N, or i/(N − 1) for the Sod runs) as a file
  attribute, so the reader evaluates the exact solution on the solver's nodes; the reader
  needs an offset option because `ClosedFormTrajectory` samples cell centres.
- **Cadence.** The comparison times of each option as frames, with the physical time of each
  in the `time` dataset; nothing is gained by storing every step.
- **Grid and boundaries.** `GridSpec` with the level's own N and `boundary = ("periodic",
  "periodic")`, or `("neumann", "periodic")` for the Sod strips.
- **Parameters.** Reynolds number, Mach number and its scaling rule, lattice relaxation time
  and lattice viscosity per level, γ, the initial condition's parameters, and the kinet git
  hash, in the file and in the config's `complexity` block.
- **The known answer.** For Option A and C the reader computes it from the stored
  parameters; for Option B the finest level is the reference, and the reader pairs each
  coarse frame with the fine frame at the same physical time at the coincident nodes.
- **Evaluation.** `analysis_grid.resolution` set to the level's own N on every run, so that
  the conservative remap is the identity and the comparison is on the level's own cells; the
  order computed afterwards from the per-level rows, never from remapped fields.

## 8. References

- Roy, C. J. (2005). Review of code and solution verification procedures for computational
  simulation. *Journal of Computational Physics* 205(1), 131–156,
  https://doi.org/10.1016/j.jcp.2004.10.036. **Read in full** (a PDF copy decoded locally;
  Sect. 2.3.2 p. 135, Sect. 2.5 pp. 136–141, Eqs. 5, 7 and 8, Table 1, Figs. 3–4, Sect. 3.4.3,
  Sect. 3.5.6 p. 154; the "open research issue" sentence is on p. 141).
- Roache, P. J. (2002). Code verification by the method of manufactured solutions. *Journal of
  Fluids Engineering* 124(1), 4–10, https://doi.org/10.1115/1.1436090. **Not opened**;
  bibliographic details from the repository's proposal and kinet's `units/references.py`.
- Roache, P. J. (1994). Perspective: a method for uniform reporting of grid refinement
  studies. *Journal of Fluids Engineering* 116(3), 405–413, https://doi.org/10.1115/1.2910291.
  **Not opened** (the publisher's page returned 403 and a mirror returned a bot-check page);
  bibliographic details from search listings; the GCI formulas are taken from the NPARC
  tutorial below, which cites it.
- NPARC Alliance Verification and Validation Archive, "Examining spatial (grid)
  convergence", https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html. **Read in
  full**: the three-grid order, Richardson's estimate, GCI with F_s = 3 (two grids) and 1.25
  (three or more), and the asymptotic check GCI_23/(r^p GCI_12) ≈ 1.
- Roache, P. J. (1997). Quantification of uncertainty in computational fluid dynamics. *Annual
  Review of Fluid Mechanics* 29, 123–160. **Not opened**; cited by the repository's
  grid-convergence idea page.
- Celik, I. B., Ghia, U., Roache, P. J., Freitas, C. J., Coleman, H. and Raad, P. E. (2008).
  Procedure for estimation and reporting of uncertainty due to discretization in CFD
  applications. *Journal of Fluids Engineering* 130, 078001. **Not opened**; cited by the
  repository's grid-convergence idea page.
- Spiegel, S. C., Huynh, H. T. and DeBonis, J. R. (2015). A survey of the isentropic Euler
  vortex problem using high-order methods. 22nd AIAA Computational Fluid Dynamics Conference;
  NASA NTRS document 20150018403,
  https://ntrs.nasa.gov/api/citations/20150018403/downloads/20150018403.pdf. **Read in full**
  (a PDF copy decoded locally; Sect. IV.A.1 Eqs. 20–23, Table 1, Sect. IV.A.2, IV.B.1, IV.D).
- Shu, C.-W. (1997). Essentially non-oscillatory and weighted essentially non-oscillatory
  schemes for hyperbolic conservation laws. ICASE Report 97-65, NASA/CR-97-206253 (published
  1998 in *Lecture Notes in Mathematics* 1697, Springer, which kinet cites as ICASE 98-32,
  Sect. 4.5). **Not readable**: both PDF copies found are scans or could not be decoded; the
  vortex parameters are taken from kinet's `reference/vortex.py` and Spiegel et al.'s Table 1.
- Yee, H. C., Sandham, N. D. and Djomehri, M. J. (1999). Low-dissipative high-order
  shock-capturing methods using characteristic-based filters. *Journal of Computational
  Physics* 150(1), 199–238, https://doi.org/10.1006/jcph.1998.6177. **Not opened** (publisher
  page 403; the Southampton eprint 403; the NASA report copy is a scan and a course copy is
  encrypted); no equation number or parameter is quoted from it.
- Taylor, G. I. (1923). On the decay of vortices in a viscous fluid. *Philosophical Magazine*
  (6) 46(274), 671–674, https://doi.org/10.1080/14786442308634295. **Secondary**: read through
  `docs/datasets/taylor_green_vortex.md` and `fmeval/data/analytic.py`, whose author read it.
- Taylor, G. I. and Green, A. E. (1937). Mechanism of the production of small eddies from
  large ones. *Proceedings of the Royal Society A* 158, 499–521,
  https://doi.org/10.1098/rspa.1937.0036. **Not opened**; three-dimensional, per the search
  listings and the dataset page.
- dos Santos, L. O. E. and Siebert, D. N. (2026). Extended-regularized lattice Boltzmann
  method. arXiv:2610.31072, https://arxiv.org/abs/2610.31072. **Read in full** (arXiv HTML;
  Sect. 3.2 setup with Eqs. 21, 22, 25, Sect. 4.2 and Fig. 3). A preprint, not peer reviewed.
- Yu, Y., Qin, Z., Chen, S., Shu, S. and Yuan, H. (2023). Two-relaxation-time regularized
  lattice Boltzmann model for Navier–Stokes equations. arXiv:2312.10318,
  https://arxiv.org/abs/2312.10318. **Read in a summary of the arXiv HTML** (Sect. III.2,
  Eqs. 62 and 66, Fig. 3); preprint.
- Yu, Y., Yu, Y., Zhou, Y., Chen, S., Yuan, H. and Shu, S. (2026). Purified two-relaxation-time
  lattice Boltzmann method. arXiv:2602.06686. **Read in a summary**; cited only for the grid
  sequence 32² to 512²; preprint.
- He, Z. and Chen, Z. (2026). Revisit the simplified lattice Boltzmann method: dissipation,
  dispersion and stability. arXiv:2605.29887. **Abstract and search summary only**; preprint.
- Krüger, T., Varnik, F. and Raabe, D. (2010). Second-order convergence of the deviatoric
  stress tensor in the standard Bhatnagar–Gross–Krook lattice Boltzmann method. *Physical
  Review E* 82, 025701, https://doi.org/10.1103/PhysRevE.82.025701. **Abstract only.**
- Mei, R., Luo, L.-S., Lallemand, P. and d'Humières, D. (2006). Consistent initial conditions
  for lattice Boltzmann simulations. *Computers & Fluids* 35(8–9), 855–862,
  https://doi.org/10.1016/j.compfluid.2005.08.008. **Abstract only.**
- Skordos, P. A. (1993). Initial and boundary conditions for the lattice Boltzmann method.
  *Physical Review E* 48, 4823, arXiv:comp-gas/9306002. **Abstract only.**
- Guo, Z., Zheng, C. and Shi, B. (2002). Discrete lattice effects on the forcing term in the
  lattice Boltzmann method. *Physical Review E* 65, 046308,
  https://doi.org/10.1103/PhysRevE.65.046308. **Abstract only** (APS page).
- Gallay, T. (2012). Stability and interaction of vortices in two-dimensional viscous flows.
  arXiv:1203.0846, https://arxiv.org/abs/1203.0846 (lecture notes). **Read in full** (ar5iv;
  Sect. 3, Eqs. 3.1–3.2).
- Gesztesy, F. and Holden, H. (1998). The Cole–Hopf and Miura transformations revisited.
  arXiv:solv-int/9812025. **Read in full** (ar5iv; Eqs. 1.14–1.16, 1.25–1.26, Lemma 3.1).
- Hopf, E. (1950). The partial differential equation u_t + u u_x = μ u_xx. *Communications on
  Pure and Applied Mathematics* 3, 201–230. Cole, J. D. (1951). On a quasi-linear parabolic
  equation occurring in aerodynamics. *Quarterly of Applied Mathematics* 9, 225–236. **Not
  opened**; cited through Gesztesy and Holden.
- Basdevant, C., Deville, M., Haldenwang, P., Lacroix, J., Ouazzani, J., Peyret, R., Orlandi,
  P. and Patera, A. (1986). Spectral and finite difference solutions of the Burgers equation.
  *Computers & Fluids* 14(1), 23–41. **Secondary** (Burkardt's code pages).
- Banks, J. W., Aslam, T. and Rider, W. J. (2008). On sub-linear convergence for linearly
  degenerate waves in capturing schemes. *Journal of Computational Physics* 227(14), 6985–7002,
  https://doi.org/10.1016/j.jcp.2008.04.002. **Abstract only** (Sandia publication page).
- Carpenter, M. H. and Casper, J. H. (1999). Accuracy of shock capturing in two spatial
  dimensions. *AIAA Journal* 37(9), 1072–1079. **Not opened**; cited through Roy (2005), p. 154.
- Ramani, R., Reisner, J. and Shkoller, S. (2018). A space-time smooth artificial viscosity
  method with wavelet noise indicator and shock collision scheme, Part 1: the 1-D case.
  arXiv:1806.08023. **Introduction only** (ar5iv); the convergence tables were not reached.
- Toro, E. F. (2009). *Riemann Solvers and Numerical Methods for Fluid Dynamics*, 3rd ed.,
  Springer, Chapter 4. **Not opened**; equation numbers from `docs/datasets/sod_shock_tube.md`.
- Brown, D. L. and Minion, M. L. (1995). Performance of under-resolved two-dimensional
  incompressible flow simulations. *Journal of Computational Physics* 122, 165–183. **Not
  opened**; cited by kinet's `shear_layer.py` docstring.
- Repository and solver sources read in full: `FUTURE_EXPERIMENTS_CATALOG.md` (At a glance,
  Sects. 1.3, 2.1 D5, 2.3 H3, 3.1); the grid-convergence proposal (since deleted);
  `issues/126`; `docs/ideas/infrastructure/grid_convergence.md`; `docs/datasets/sod_shock_tube.md`;
  `docs/datasets/taylor_green_vortex.md`; `docs/datasets/reynolds_ladder_2d.md` (the
  refinement section); `fmeval/data/analytic.py` (docstrings); `docs/recipes/add-a-dataset.md`;
  the kinet configs on disk (`56d32e.yaml`, `131010.yaml`, `d17baf.yaml`); kinet source
  `initialization/shear_layer.py`, `reference/vortex.py`, `initialization/vortex.py`,
  `experiments/taylor_green_vortex/{initialize.py,Re-50k_Ma-1en1.yaml}`,
  `experiments/isentropic_vortex/*.yaml`, `experiments/sod/*.yaml`,
  `solver/common/forcing/{__init__,sources}.py` and `laws/*` docstrings,
  `solver/lbm/physics/forcing/guo.py` docstring, `units/references.py`.

## 9. Confidence

**Sure of.** Roy's definitions, equation numbers, six steps, smoothness advice, Table 1, and
the two sentences on non-smooth solutions (pp. 141 and 154), all read from the decoded text.
Spiegel et al.'s problem definition, their statement that the exact solution is the translated
initial condition, their Table 1 and their five recommendations. The kinet vortex formula,
the kinet Taylor–Green, vortex and Sod configurations, the forcing registry and its source
channels, and the shear-layer node convention at lines 48 to 49. Gallay's Lamb–Oseen formulas
and Gesztesy–Holden's Cole–Hopf statement. The on-disk run configurations. dos Santos and
Siebert's second-order statement and setup.

**Reasoning, not sourced.** The acoustic-versus-diffusive scaling argument and the O(Ma²)
floor; the weakly compressible density of the Taylor–Green solution; the Fourier–Bessel form
of the Burgers solution; the nested-node arithmetic (751, 1501, 3001; i L/N); the lattice
viscosity rescaling; the Sod time conversion to solver steps and the wall-arrival step; the
claim that an i/(N − 1) initial condition caps the observed order at 1 and could account for
the 7 × 10⁻³ difference at step 0; the statement that `max_error` does not converge at a jump;
the expected drift of Sod's L₁ order toward 2/3; the manufactured solution of Sect. 4.4; every
comparison time; the ordering in Sect. 6.

**Not checked.** Whether the on-disk shear-layer runs used the current initializer's node
convention; whether kinet's `initialization_policy: analytic` seeds the non-equilibrium
populations; whether the weakly compressible scheme accepts a `mass` source outside the
multipole path; whether kinet's lattice-Boltzmann path has Dirichlet velocity boundaries; the
dataset page's "t = 200" for the Sod run against the step conversion here; Yee et al. (1999),
Shu (1997), Roache (1994, 1997, 2002), Celik et al. (2008), Toro (2009), Taylor (1923) and
Taylor and Green (1937) beyond the sources named; the He and Chen numbers; whether a published
table of observed orders for plain D2Q9 BGK on the Taylor–Green vortex exists (none was found
in an opened source; the two opened papers give figures).

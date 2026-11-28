# Dataset 03: two-dimensional shocks, from closed-form fronts to shocklet turbulence

**Catalog clusters:** D3 (two-dimensional shock dataset, three tiers), D8 (shock fronts with
known geometric errors), B4 (the build that produces them). **Metrics served:** the six
shock metrics that share one detector (`shock_mask_overlap`, `shock_set_distance`,
`shock_set_hausdorff`, `shock_set_hausdorff95`, `shock_set_masd`,
`shock_set_baddeley_delta`); `persistence_distance` (wants pressure with topology); the
compressible spectral flux and the Helmholtz split (judgement 003); the both-empty
convention of issue 120 and the empty-set conventions of issue 102. **Ideas served:**
`docs/ideas/shock_geometry/shock_turbulence_interaction.md` (shocklet census, corrugation
spectrum); the proposed fractions skill score and object-matched shock distance
(`proposals/MTR-shock_mask_overlap-fractions-skill-score.md`,
`proposals/MTR-shock_set_distance-object-matched-shock-distance.md`).
**Date:** 2026-11-05. **Author:** research sub-agent (branch `update_metric_eval_principles`).

## 1. Purpose

The six shock metrics read one stored pressure field, flag a cell as shocked when the
pressures of its two neighbours along *any* grid axis differ by at least the ratio across a
normal shock of Mach 1.3, and compare the two flagged sets (`metrics/shock_set_distance/card.md`,
Definition, Eq. 1; the pressure half of criterion (iii) of Schaal and Springel 2015,
Sect. 2.3.2, with their M_min = 1.3). Their only evidence is `sod_shock_tube`, the exact
one-dimensional Riemann solution, where a shock set is one or two cells on a line, so a
displacement, a size change and a rotation cannot be told apart, and the field's own
scores for thresholded fields are degenerate (the geometric and perturbed shock-case proposal,
deleted once built;
`FUTURE_EXPERIMENTS_CATALOG.md`, D3 and D8). Issue 002 accepted on 2026-08-07 that the
north-star case, many small shocks embedded in turbulence, has no dataset at all. The
detector's two untested choices are the ones a two-dimensional field exposes: it takes the
jump along each grid axis rather than along the shock normal, and it pools every flagged
cell of several shocks into one set without matching objects (card, Definition and
Limitations).

This document specifies (Option A) closed-form and self-similar shocked fields in two
dimensions, each with a known front position and so a known answer for every geometric
error, and (Options B to F) simulated systems from the literature that carry curved,
oblique, interacting and, at the top of the ladder, turbulence-embedded shocks. Every
option stores a thermodynamic pressure written by the generator or solver; none computes
pressure from density, by repository rule (`docs/recipes/add-a-dataset.md`, Sect. 1).

## 2. What the dataset must provide

The four needs, labelled as in the catalog, and which option meets each:

- **(a) Fronts curved and oblique to the grid.** Sedov–Taylor and Noh (closed circles),
  the oblique wedge shock and the tilted planar step (straight fronts at a chosen angle),
  the two-dimensional Riemann problems and the double Mach reflection (curved and
  interacting), the shock–vortex interaction (one front bent by one structure).
- **(b) Many shocks at once, the shocklet regime.** Decaying compressible turbulence at
  initial turbulent Mach number 0.6 (Option D) and forced two-dimensional compressible
  turbulence at Mach 0.3 to 0.6 (Option E). Nothing closed-form reaches this regime; the
  geometric cases with several closed fronts (A7) are the nearest known-answer stand-in.
- **(c) Known displacement, size and orientation errors.** Every Option A field: the front
  is a known curve, so a candidate built by shifting, scaling or rotating it, or by taking
  the self-similar solution at another time, has a known surface distance (Sect. 3.8).
- **(d) Frames where the reference holds no shock.** Any Option A field with the jump
  below the detector's ratio; Riemann Case 6, whose four waves are contacts (no pressure
  jump anywhere at t = 0); The Well's `turbulent_radiative_layer_2D`, a subsonic
  two-dimensional run that stores pressure; and, in the detector's sense, every shock
  weaker than Mach 1.3 (Sect. 2, next paragraph).

**The detector's threshold is the first constraint on every option.** With γ = 1.4 the
flag fires when max(p_{n-e_j}, p_{n+e_j}) ≥ 1.805 min(·) > 0 (card, Eq. 1; the ratio is
(2γM² − (γ − 1))/(γ + 1) at M = 1.3, my arithmetic 1.8050). Three consequences a data
preparer must respect:

1. **Both pressures must be positive.** A cell beside a zero or negative pressure is never
   flagged (issue 102). The Noh problem and the cold Sedov background are posed with zero
   pressure; the stored field must use the small positive value the solver used
   (Sect. 3.1, 3.4).
2. **The jump must be sharp.** The comparison spans two cells. A front smeared over k cells
   by a smoothed profile, a diffusive solver or a coarse remap carries a per-two-cell ratio
   of roughly (p₂/p₁)^{2/k}, so a Mach-2 shock (ratio 4.5) spread over 5 cells falls to
   1.8 and is lost (my estimate for a geometric ramp; the exact loss depends on the profile).
   Closed-form fields therefore use a step no wider than one cell, and solver output is
   stored on the solver's grid.
3. **Shocks below Mach 1.3 are invisible.** The standard shock–vortex cases of Inoue and
   Hattori (1999) are at shock Mach 1.2 and 1.29, whose pressure ratios are 1.513 and 1.775
   (my arithmetic from the normal-shock relation), both under 1.805: on those fields the
   reference set is empty although a shock is present. Option F therefore raises the shock
   Mach number (Sect. 4.6), and Mach 1.2 is kept only as a (d) case.

**Fields and shape.** `pressure` `(T, x, y)` always; `density` and `velocity` `(T, 2, x, y)`
from every solver run (the Helmholtz split and the shocklet census need them); nothing
derived stored for evaluation. **Boundaries** declared per axis from `BOUNDARIES`
(`fmeval/data/base.py`): the Riemann problems, the blast waves and the obstacle flow are
not periodic; the turbulence runs and the tilted stripe are. **Cadence.** Closed-form fields
are computed on demand at any time, as `sod_shock_tube` is (`fmeval/data/analytic.py`);
solver runs store every frame from a window in which the fronts are well separated.
**Known answers.** For each Option A field, the front curve at every time, hence the exact
surface distances of Sect. 3.8; for the simulated fields, a published reference figure or a
high-resolution run of the same code.

## 3. Option A, the analytic ideals

All Option A fields are ideal-gas Euler solutions or manufactured pressure fields with
γ = 1.4 (the detector's fixed value) unless stated. Each gives a pressure p(x, y, t) in closed
form or from a one-dimensional similarity profile, so a reader in the pattern of
`fmeval/data/analytic.py` evaluates it on any grid at any time.

### 3.1 The Sedov–Taylor blast wave in cylindrical (two-dimensional) geometry

**Problem.** Energy E is released at a point in a uniform gas of density ρ₀ at rest with
negligible pressure; the flow is self-similar (Taylor 1950, summary; Sedov 1959, as
reproduced by Kamm and Timmes 2007). In the geometry index j of Kamm and Timmes (j = 1, 2, 3
for planar, cylindrical, spherical; their Eqs. 1 to 3) the shock radius is their Eq. (12)
with ω = 0,

$$
r_2(t) = \left(\frac{E\,t^2}{\alpha\,\rho_0}\right)^{1/(j+2)}, \qquad
u_s = \frac{2}{j+2}\,\frac{r_2}{t}, \tag{A.1}
$$

(Eq. 13 for the shock speed), where α is the dimensionless energy integral, their Eq. (54),
depending only on j and γ. In two dimensions j = 2 and r_2 ∝ t^{1/2}. Taylor's own
spherical form is R = S(γ) t^{2/5} E^{1/5} ρ₀^{-1/5} (Taylor 1950, summary), and his Eq. (38)
gives t = 0.926 R^{5/2} ρ₀^{1/2} E^{-1/2} at γ = 1.4, so S(1.4) = 0.926^{-2/5} ≈ 1.031 (my
arithmetic).

**The constant in two dimensions.** Kamm and Timmes (2007, Sect. 4.1) define standard
verification problems with ρ₀ = 1, γ = 1.4 and E = 0.0673185, 0.311357 and 0.851072 in
planar, cylindrical and spherical geometry, "chosen so that the shock is at r = 0.5, 0.75,
and 1.0 cm" at t = 1. Inverting (A.1) with their cylindrical values gives
α_cyl(γ = 1.4) = 0.311357 / 0.75⁴ = 0.98404, so r_2 = 1.00403 (E t²/ρ₀)^{1/4} (my
derivation from their printed numbers; the spherical values give α = 0.851072 and a
prefactor 1.0328, consistent with Taylor's 1.031). Their public code generates the full
profiles ρ(r), u(r), p(r) behind the front for any j and γ; Sect. 3 of their report removes
the singularities of the energy integral.

**Post-shock state.** The strong-shock limit of the Rankine–Hugoniot relations, ρ₂/ρ₀ =
(γ + 1)/(γ − 1) = 6 and p₂ = 2ρ₀u_s²/(γ + 1) (Kamm and Timmes 2007, Sect. 2, "an infinitely
strong shock is assumed"; the same limit is Ramsey et al. 2012, Eqs. 9 to 11). With E = 1,
ρ₀ = 1 the front is at r_2 = 0.317 at t = 0.1 and p₂ = 2.10, at r_2 = 0.449 at t = 0.2 and
p₂ = 1.05 (my arithmetic). The background pressure p₀ must be positive for the detector; with
p₀ = 10⁻⁴ (Schaal and Springel 2015, Sect. 3.1, in three dimensions) the ratio p₂/p₀ exceeds
10⁴ throughout any practical window.

**What the field validates a finder on.** Schaal and Springel (2015, Sect. 3.1, Fig. 1) run
the three-dimensional problem on 25³ to 100³ cells with ρ₁ = 1, p = 10⁻⁴, γ = 5/3, E = 1 in one
cell, R(t) = β(Et²/ρ₁)^{1/5} with β = 1.152 for γ = 5/3 (their value from the Kamm and Timmes
code), and measure the detected shock zone and surface on a cross-section against the
analytic radius and the detected surface area against 4πR², finding "a small systematic
overestimation of ~5%" which they attribute to the simulated front running ahead at early
times, not to the surface estimate. The two-dimensional analogue is the detected set
against the circle r = r_2(t) and the flagged cell count against 2πr_2(t)/Δx (my
transfer).

**Serves.** (a): the front is oblique to the grid everywhere except on the axes, so the
axis-by-axis detector is tested at every angle in one frame. (c): the solution at t + δt is
a candidate whose front is displaced radially by r_2(t + δt) − r_2(t) at every point, a
physically consistent displacement; a blast with E' ≠ E is a pure size error. (d): a frame
before the front has grown past a few cells, or a p₀ raised until p₂/p₀ < 1.805, is a
no-shock frame. **Limits.** The detector flags only the front; the profile behind it is
smooth. The singular origin needs the solver's or the generator's care (Kamm and Timmes
2007, Sect. 3, extended precision near r = 0); a reader that evaluates the closed form
avoids it.

### 3.2 A steady oblique shock on a wedge

**Problem.** A uniform supersonic stream at Mach M₁ meets a wedge of half-angle θ; an
attached straight shock stands at angle β to the incoming flow. The θ–β–M relation, in the
form printed on the NASA Glenn page (read) with a = θ and s = β,

$$
\cot\theta = \tan\beta\left[\frac{(\gamma+1)M_1^2}{2\left(M_1^2\sin^2\beta - 1\right)} - 1\right], \tag{A.2}
$$

is the textbook relation (Anderson, *Modern Compressible Flow*, Chap. 4; Liepmann and
Roshko, *Elements of Gasdynamics*, Chap. 4; neither opened here). The jumps depend only on
the normal Mach number M_n = M₁ sin β (same page):

$$
\frac{p_2}{p_1} = \frac{2\gamma M_n^2 - (\gamma-1)}{\gamma+1}, \qquad
\frac{\rho_2}{\rho_1} = \frac{(\gamma+1)M_n^2}{(\gamma-1)M_n^2 + 2}. \tag{A.3}
$$

Worked case (my arithmetic from A.2 and A.3): M₁ = 2, β = 45° gives θ = 14.74°, M_n = 1.414,
p₂/p₁ = 2.167. **As a closed-form field:** two uniform states separated by the line through
the wedge tip at angle β, with p₁ = 1 and p₂ from (A.3); the velocity is uniform on each
side, so the field is a steady exact solution away from the wedge surface. It needs no
solver. **Serves.** (a) and (c): the front is straight at a chosen angle, so the detector's
behaviour against angle is read off directly, and the threshold has a closed form, M₁ sin β
≥ 1.3 (β ≥ 40.5° at M₁ = 2, β ≥ 25.7° at M₁ = 3; my arithmetic). A candidate with a wrong β
is a pure orientation error. **Limits.** One straight front; the wedge wall is a Neumann
boundary with the flow tangent to it; detached (bow) shocks are not closed-form.

### 3.3 A tilted planar Rankine–Hugoniot step on a periodic domain

**Field (my construction).** On a periodic square of N cells, a stripe of post-shock state
bounded by two parallel fronts at angle β to the x axis, with tan β = N_y'/N_x' for
integers so the stripe closes on itself. Front 1 is a normal shock of Mach M_s, p₂/p₁ from
(A.3) with M_n = M_s; front 2 returns to p₁ (an expansion step, not a physical shock, but
the detector's max/min test is symmetric so it flags both). The stripe moves along its
normal at the shock speed M_s a₁; the field at time t is the field at t = 0 shifted by
M_s a₁ t along the normal, evaluated with the step placed exactly on a cell face at t = 0 so
the jump occupies two cells. **Serves.** (a) and (c): one front at any rational angle, and
the pure displacement d = s sin β of a shift by s cells along x (my derivation: the
perpendicular distance between the two lines), so `shock_set_distance`'s Equation 3 for an
axis-aligned shift generalises to a known value at every angle. The periodic seam that
`metrics/shock_set_distance/code_notes.md` line 109 says no dataset has is produced by
placing the stripe across it. (d): M_s < 1.3. **Limits.** Not a solution of the Euler
equations across front 2; its purpose is the detector and the distances, not physics.

### 3.4 The Noh problem (cylindrical implosion)

**Problem.** Uniform gas of density 1 with velocity of magnitude 1 directed toward the
origin and zero pressure, γ = 5/3; an infinite-strength circular shock reflects from the
origin and moves out (Noh 1987; not opened; the statement and exact solution below are as
printed in Liska and Wendroff 2003, Sect. 4.5, and in Sutherland 2010, Table 9). Exact
solution in the plane:

$$
r < t/3:\ \rho = 16,\ u = 0,\ p = 16/3; \qquad
r > t/3:\ \rho = 1 + t/r,\ u_r = -1,\ p = 0;\qquad \text{shock speed } 1/3. \tag{A.4}
$$

The post-shock density is ρ₀((γ + 1)/(γ − 1))² = 16 (my arithmetic; the spherical value is 64,
Sutherland 2010, Table 19). Liska and Wendroff set the initial pressure to 10⁻⁶ "as many
schemes cannot deal with zero pressure", on (0, 1)² with 400² cells to t = 2; Sutherland
reports L1 errors of 0.74% (density) and 0.87% (pressure) at t = 2 (ar5iv copy, Table 10 and
Fig. 13). **Serves.** (a) and (c) as for Sedov, with the front at r = t/3 and a constant
post-shock state, so the pressure jump is the same at every time; the flagged band is
exactly one closed curve. The stored pre-shock pressure must be the solver's small positive
value, never zero (constraint 1 of Sect. 2). **Limits.** γ = 5/3, not the detector's 1.4; the
detector's ratio R is fixed at γ = 1.4 (card), so on this field the threshold corresponds
to a different Mach number but still fires, since p₂/p₁ = (16/3)/10⁻⁶. Known numerical
pathology at the origin ("wall heating", Liska and Wendroff 2003, Sect. 4.5) affects
density, not the front.

### 3.5 The Guderley converging shock

**Problem.** An infinitely strong cylindrical shock converging on an axis in a uniform gas
at rest with zero pressure (Ramsey, Kamm and Bolstad 2012, Eqs. 1 to 3, read in the LA-UR
copy). The solution is self-similar with trajectory R_s(t) ∝ (−t)^α for t < 0, and α is the
eigenvalue of a nonlinear ODE problem, not a closed form (their Sect. 3; the abstract calls
the complete solution "two coupled nonlinear eigenvalue problems"). Their Table 1 gives, for
cylindrical geometry, α = 0.835323192 at γ = 1.4 and 0.815624901 at γ = 5/3 (Lazarus's values
0.8353231919 and 0.8156249014 beside them); Table 2 gives the reflected-shock trajectory
multiplier B = 2.815610935 at γ = 1.4. The post-shock state is the strong-shock limit, their
Eqs. (9) to (11). **Usable?** Yes as a *semi-analytic* ideal: the front is a known circle at
every time once α is known, but the profiles need the ODE integration (Lazarus's method,
their Appendix B). **Serves.** (a) and (c) with a front that accelerates inward and then
reflects, giving a shock whose radius is known but whose strength changes in time, unlike
Noh. **Limits.** More work than Noh for the same geometry; recommended only if the
reflected phase (a second front crossing the first's wake) is wanted.

### 3.6 The exact one-dimensional Riemann solution at two times

Already on disk as `sod_shock_tube` (`docs/datasets/sod_shock_tube.md`, Eqs. 3 to 7 from
Toro 2009, Chap. 4). Scored at t against t + δt, each wave moves by its own speed times δt
with every jump exact; this is cluster D8(b) and works as a one-offset unit test in
`metrics/shock_set_distance/test_metric.py`. In two dimensions the same data extruded along
y, or the tilted stripe of Sect. 3.3 built from the Sod states, gives the Riemann waves at an
angle. Nothing new to prepare beyond a paired-time reader (catalog B6).

### 3.7 Geometric cases with known displacement, size and orientation errors

The spatial-verification intercomparison scored every method on idealised cases
(Ahijevych et al. 2009, Sect. 2a, Table 1, as read in full by the agent that wrote the
geometric and perturbed shock-case proposal, deleted on 2026-11-27 once built; the AMS copy
returned 403 to me and the table numbers are that proposal's): an ellipse on a 601 × 501 grid and
forecasts that are the same ellipse displaced by 50 or 200 points (geom001, geom002),
displaced by 125 points and enlarged (geom003), displaced with its aspect ratio changed
(geom004), and displaced and much larger so that it overlaps (geom005); the perturbed cases
(Sect. 3, Table 4) shift one real field by 3/5, 6/10, 12/20, 24/40 and 48/80 points
(pert001 to pert005) and combine the 12/20 shift with an intensity error (pert006,
pert007). Roberts and Lean (2008, Sect. 2d, Fig. 4) displace a one-cell band by 1, 3, 11 and
21 cells. **Transfer (my construction).** A manufactured pressure field

$$
p(\mathbf{x}) = p_1 + (p_2 - p_1)\,H\!\left(-d_C(\mathbf{x})\right), \tag{A.5}
$$

where d_C is the signed distance to a closed curve C (an ellipse with semi-axes a, b, centre
c, orientation φ) and H a step placed on cell faces, with p₁ = 1 and p₂ = 2.5 (a Mach-1.5
normal shock, ratio 2.458, my arithmetic from A.3), so the detector flags a closed band one
to two cells wide along C. Candidates: the ellipse displaced by s cells along x, along the
diagonal, and by the pert ladder scaled to the grid (on 512² my proposal is 2, 4, 8, 16, 32
cells, matching the repository's translation ladder); enlarged by a factor; rotated by
φ' − φ; and a second ellipse added (a spurious shock) or removed (a missed one). Several
ellipses at once are the known-answer stand-in for the shocklet regime (b). A frame with
no ellipse, or with p₂ = 1.5, is a no-shock frame (d). **Limits.** Not a flow; admitted as
evidence only by a decision like the one that admitted Sod (catalog, "Decisions only a
person can take", item 5).

### 3.8 The known answers for a geometric error (my derivations, to be pinned by tests)

Let A be the reference set and B the candidate set, both thin bands along curves C_A and
C_B, with every flagged cell a point (card, Definition). For a pure displacement of a
straight front by s cells along a grid axis the card's Equation 3 gives
ASSD = (s − ½)Δx and the Hausdorff distance sΔx. For a front at angle β to the axis of
shift, the perpendicular displacement is s sin β, and the nearest-cell distances cluster at
s sin β ± Δx (Sect. 3.3). For a circle of radius r displaced by s ≪ r, the point-to-set
distance varies with angle as s|cos ψ| and ASSD ≈ (2/π) s (the mean of |cos ψ| over the
circle), while the Hausdorff distance stays s. For a circle enlarged from r to r', every
distance is r' − r. For a rotation of an ellipse by δφ, the maximum displacement is of order
(a − b) sin δφ at the tips. Dice (`shock_mask_overlap`) falls to its floor as soon as the two
bands stop touching, at s of about two cells. These relations are what the geometric cases
measure; the (2/π)s value for a displaced circle in particular should be checked numerically
before it is written on a card.

## 4. Options B to F: simulated systems

Common to all: the two-dimensional Euler or Navier–Stokes equations of an ideal gas
(`docs/datasets/sod_shock_tube.md`, Eq. 1, with the y-momentum added), γ = 1.4 unless
stated, pressure written by the solver. Solver options available here: the kinet
compressible lattice-Boltzmann scheme (`compressible_fluids`, entropic BGK with an extended
F and Levermore G distribution), which already runs the Sod tube on 3001 × 5 cells with
γ = 1.4 and 2 and an obstacle flow at inlet Mach 1.8, γ = 1.4, Prandtl 0.71, Re 300 on 500 × 300
cells (`datasets/kinet/flow_around_objects/compressible_fluids/Pr-71en2_vuy-1.4_Re-3e2/configs/a92b16.yaml`,
read), and any finite-volume Euler code (Liska and Wendroff 2003 compare eight on exactly
these problems). Cost figures below are my estimates for a 512² explicit scheme at CFL 0.5;
no run was made.

### 4.1 Option B: two-dimensional Riemann problems

**Standard configuration** (Liska and Wendroff 2003, Sect. 4.3 and Table 4.3, read in full;
they take six cases "from the collection of 2D Riemann problems proposed by [Schulz-Rinne,
Collins and Glaz 1993] and used by [Lax and Liu 1998; Kurganov and Tadmor 2002]", numbered
as in Lax and Liu, "which are configurations 3, 4, B, F, G, K" of Schulz-Rinne et al.).
Domain (0, 1)², four constant states in the quadrants cut by x = ½ and y = ½, γ = 1.4, 400 × 400
cells, results shown at time T. The four one-dimensional Riemann problems between
neighbouring quadrants each produce exactly one wave: S shock, R rarefaction, J contact-slip,
listed from the left side clockwise. Initial states (p, ρ, u, v) per quadrant, as printed:

| Case | Upper-left | Upper-right | Lower-left | Lower-right | T | Waves |
|---|---|---|---|---|---|---|
| 3 | (0.3, 0.5323, 1.206, 0) | (1.5, 1.5, 0, 0) | (0.029, 0.138, 1.206, 1.206) | (0.3, 0.5323, 0, 1.206) | 0.3 | S,S,S,S |
| 4 | (0.35, 0.5065, 0.8939, 0) | (1.1, 1.1, 0, 0) | (1.1, 1.1, 0.8939, 0.8939) | (0.35, 0.5065, 0, 0.8939) | 0.25 | S,S,S,S |
| 6 | (1, 2, 0.75, 0.5) | (1, 1, 0.75, −0.5) | (1, 1, −0.75, 0.5) | (1, 3, −0.75, −0.5) | 0.3 | J,J,J,J |
| 12 | (1, 1, 0.7276, 0) | (0.4, 0.5313, 0, 0) | (1, 0.8, 0, 0) | (1, 1, 0, 0.7276) | 0.25 | J,S,S,J |
| 15 | (0.4, 0.5197, −0.6259, −0.3) | (1, 1, 0.1, −0.3) | (0.4, 0.8, 0.1, −0.3) | (0.4, 0.5313, 0.1, 0.4276) | 0.2 | J,R,S,J |
| 17 | (1, 2, 0, −0.3) | (1, 1, 0, −0.4) | (0.4, 1.0625, 0, 0.2145) | (0.4, 0.5197, 0, −1.1259) | 0.3 | S,J,R,J |

Lax and Liu (1998) is paywalled; its full set of 19 configurations and Kurganov and
Tadmor's reproduction (the CAM 00-34 preprint was opened but its text could not be
extracted) were not quoted. **What is known.** No exact solution ("exact solutions are not
known for these 2D Riemann problems", Sect. 4.4); the reference is a high-resolution run of
the same code, and Liska and Wendroff's Figs. 4.1 to 4.3 (Cases 3, 12, 15, pressure maps with
density contours) and Sutherland (2010, Sect. VI.1.3) are published pictures to compare
against. **Detector check.** The initial pressure ratios across the shocks are 5 (Case 3),
3.14 (Case 4) and 2.5 (Cases 12, 15, 17), all above 1.805, so every shock is flagged at
t = 0 (my arithmetic); Case 6 has p = 1 in all four quadrants and only slip lines, so it is a
no-shock reference (d) as long as the rolled-up vortex sheets keep the pressure ratio
across two cells below 1.805, which must be checked on the run. **Serves.** (a): the
Case-3 and Case-4 shocks curve and interact; (c): `translate` on the run, and the
same run at 200² or with another scheme, are candidates with a known or a measured
displacement. **Boundaries.** Declared `neumann` on both axes (the problems are run with
outflow; Liska and Wendroff state "natural" boundaries for the one-dimensional tests and
nothing more for these). **Cost.** About 10³ steps at 512²; seconds in a compiled code,
minutes in NumPy. **On disk.** Nothing.

### 4.2 Option C: the double Mach reflection

**Standard configuration** (Woodward and Colella 1984, Sect. IV, not opened; the setup
below is as printed by Kemm 2014, arXiv:1404.6510, read in full, who cites it as the
originator). Domain [0, 4] × [0, 1]; a Mach-10 shock meets the bottom wall at x₀ = 1/6 at 60°
to the wall (the wall is the 30° ramp unrolled). Pre-shock state in conserved variables
ρ = 1.4, ρu = ρv = 0, E = 2.5; post-shock ρ = 8, ρu = 57.1597, ρv = −33.0012, E = 563.544. In
primitive variables (my arithmetic, γ = 1.4) these are p₁ = 1 and (u, v, p)₂ = (7.145, −4.125,
116.5), a speed of 8.25 along the shock normal, and p₂/p₁ = 116.5 is the Mach-10 ratio of
(A.3). Final time t = 0.2; Kemm's default Δx = 1/480. Boundaries: reflecting wall for
x > 1/6 on the bottom and the post-shock state imposed for x < 1/6; inflow (post-shock) on
the left; outflow on the right; on the top the exact position of the moving shock, whose
foot at y = 1 is at x = 1/6 + (1 + 20t)/√3 (my derivation from shock speed 10 along the
normal), with the post-shock state to its left and the pre-shock state to its right. Kemm
tests an extrapolation alternative at the top and rejects it. **What is known.** The
reference picture is Woodward and Colella's density contour plot (reproduced by every
later paper): the incident shock, the reflected shock, the Mach stem, the two triple
points and the jet along the wall. **Serves.** (a): one straight oblique front at 60° plus
a curved reflected shock and a short normal stem, three fronts of different strength meeting
at a point; (c) through `translate` and resolution. **Limits.** Mach 10 is far above the
regime of the repository's other data; the pressure range (1 to several hundred) stresses the detector's
positivity, not its threshold. **Cost.** About 4 × 10³ steps on 1920 × 480; minutes in a
compiled code. **On disk.** Nothing.

### 4.3 Option D, one-dimensional companion: the Shu–Osher shock–entropy-wave problem

As printed by Liska and Wendroff (2003, Sect. 3.1; Shu and Osher 1989 not opened): on
x ∈ (−5, 5) with the discontinuity at x = −4, left state (ρ, u, p) = (3.857143, 2.629369,
10.33333), right state (1 + 0.2 sin 5x, 0, 1), final time 1.8, 400 cells; the left state is
the post-shock state of a Mach-3 shock into the unperturbed right state (my check from A.3
reproduces all three numbers to the printed digits; the density digit string in my text
extraction was partly garbled, so the preparer should confirm 3.857143 against the PDF).
**What is known.** No exact solution; the reference is a fine-grid run (2000 cells with a
seventh-order WENO scheme is the usual choice, a secondary statement). **Serves.** Many
small features behind one shock: the entropy waves steepen into a train of weak shocks
whose pressure ratios cross the detector's threshold one by one, so the detected set grows
in time and the (d)-to-(b) transition is watched on one field; extruded along y, or tilted
as in Sect. 3.3, it becomes two-dimensional. **Cost.** Seconds.

### 4.4 Option D: decaying compressible isotropic turbulence with eddy shocklets

**Regime.** Lee, Lele and Moin (1991, abstract read) establish in three dimensions that
shocklets form in decaying isotropic turbulence, with "all the characteristics of a typical
shock wave", that their occurrence rises with the initial turbulent Mach number M_t and the
Reynolds number, and that three-dimensional turbulence "needs a higher initial M_t for
shocklets to form" than two-dimensional. Samtaney, Pullin and Kosović (2001, abstract read)
run 128³ and 256³ at M_t ≈ 0.1 to 0.5 and Re_λ = O(50 to 100), extract shocklets with an
algorithm, and model the probability density of shocklet strength M_n − 1 with the most
probable strength scaling as M_t/Re_λ^{1/2} and thicknesses scaling on the Kolmogorov
length. In two dimensions, Passot and Pouquet (1987, abstract read) find on 256² that the
behaviour changes at r.m.s. Mach number 0.3 and that for initially supersonic flow "small
scales are dominated by shocks, and vortices form behind them".

**Standard three-dimensional setup** (Johnsen et al. 2010, Sect. 5, could not be opened;
the parameters below are as printed by Motheau and Wakefield 2021, Sect. 3.3, Eqs. 15 to 19,
read in full, who attribute the framework to Lee et al. and its use as a numerics test to
later work including, I infer from their reference list, Johnsen et al.): a solenoidal
velocity field with spectrum E(k) ∝ k⁴ exp(−2(k/k₀)²), k₀ = 4, scaled to M_t,0 =
√⟨u·u⟩/c₀ = 0.6 and Re_λ,0 = ρ₀ u_rms λ₀/μ₀ = 100 with λ₀ = 2/k₀ and u_rms = √(⟨u·u⟩/3);
constant viscosity from Re_λ,0, Pr = 0.71, uniform initial temperature and pressure; grids
64³ to 512³; run to t/τ = 4 with τ = λ₀/u_rms,0; shocklets are generated until t/τ ≈ 0.5 and
decay after t/τ ≈ 1. **What is known.** Curves of kinetic energy, enstrophy and dilatation
variance against t/τ from a converged reference run (Motheau and Wakefield Fig. 7; Johnsen
et al. Sect. 5 figures, not seen).

**Two-dimensional form (my proposal; no published two-dimensional standard with full
initial data was found).** Rerun the repository's own isotropic initial condition, the
random-mode field with k₀ = 4 of
`datasets/kinet/homogeneous_isotropic_turbulence/weakly_compressible_isoT_fluids/sys_Re-5e4_Ma-1en1/configs/b45da0.yaml`
(read: `density: 1.0`, `k0: 4`, `random_seed: 42`, `mach: 0.1`, 512²), with the kinet
`compressible_fluids` scheme at `mach` 0.6 to 1.0, γ = 1.4, Pr 0.71, periodic on both axes,
512² and 1024², storing density, velocity and pressure every step over the first two eddy
turnovers. Passot and Pouquet's threshold says Mach 0.3 is where shocks begin in two
dimensions, and Lee et al. say two dimensions needs less Mach than three, so 0.6 should be
in the shocklet regime; the acceptance test of issue 002 (a non-trivial detector mask) is
the check. The three independent realisations already on disk at Mach 0.1 (catalog
Sect. 1.3) give the anchor's "unrelated field" at the same parameters once rerun.
**Serves.** (b), the north-star case; the shocklet census and corrugation ideas; (d) in the
late decay once every shocklet has weakened below Mach 1.3. **Cost.** Two eddy turnovers at
1024² with a lattice-Boltzmann step: of order 10⁴ steps, hours on one GPU (my estimate;
kinet's step at Mach 0.1 on 256² is the only timing the repository has, and the catalog
asks for a wall-clock measurement first). **On disk.** The Mach 0.1 isothermal runs only,
which have no shocks and whose stored pressure is density/3 (issue 002).

### 4.5 Option E: forced two-dimensional compressible turbulence with shocks

**Standard configuration** (Falkovich and Kritsuk 2017, read in full via ar5iv, Table I and
Supplement Eqs. 2 to 4; Kritsuk 2019, read in full via ar5iv, Sect. 2 and Table 1). Euler
equations with an ideal gas at γ = 1.001 to mimic an isothermal fluid; periodic L × L box
with L = 1, ρ₀ = 1, sound speed c ≈ 1, starting from rest; solenoidal white-in-time random
force per unit mass at an intermediate scale λ_f = 2π/k_f with injection rate ε_f; no
bottom friction; implicit large-eddy simulation with the piecewise parabolic method (Enzo)
or an eighth-order central scheme with WENO dissipation. Runs: N = 512, λ_f = 0.047,
ε_f = 0.001 (case A); 2048, 0.023, 0.001 (B); 8192, 0.012, 0.001 (C); 4096, 0.012, 0.002 (D);
4096, 0.012, 0.008 (E); saturated r.m.s. Mach numbers 0.52 to 0.62 after (0.2 to 1.5) × 10³
sound-crossing times (2017, Table I). Kritsuk's 2019 case B, 16 384², λ_f = 0.006, sampled over
t ∈ [150, 180] with 600 snapshots at M ≈ 0.34, has no condensate and is treated as
stationary. **What is known.** Shocks form once the r.m.s. Mach number exceeds about 0.3;
long shocks connect the centres of the large-scale vortices and a single strong shock
(pressure jump above 2) can drop the total energy by several percent (2017, Fig. 1 and 4);
"shocklets" appear in the intermediate stage (2019, Sect. 2); the spectra of Kritsuk 2019
Figs. 1 to 6 (k⁻² velocity below k_f, Kraichnan enstrophy range above it, dilatational and
potential energy in equipartition at k ≳ k_f) are the published statistics. **Two
repository caveats (mine).** First, at γ = 1.001 the stored pressure is nearly ρc², so it
carries almost the information of the density, which the repository's isothermal readers
exclude as redundant (`REDUNDANT_FIELDS`, `fmeval/data/base.py`); the metric still reads a
solver-written pressure, which the rule allows, but a run at γ = 1.4 would give an
independent pressure at the cost of departing from the published flux-loop physics. Second,
whether kinet supports forcing is unchecked (catalog, "Decisions only a person can take",
item 1); two forced-3D folder names exist on disk with no data (catalog Sect. 1.3).
**Serves.** (b) in a statistically stationary form, which also serves cluster D4 (forced
turbulence with an inertial range); the shocks here are long and strong rather than small
and weak, a different shock population from Option D. **Cost.** Case A at 512² for 10³
crossing times is of order 10⁶ steps: a day on one GPU (my estimate). **On disk.** Nothing.

### 4.6 Option F: shock–vortex interaction

**Standard configuration** (Inoue and Hattori 1999, abstract read: two-dimensional
compressible Navier–Stokes, sixth-order compact scheme, sound generation tied to the
reflected shocks; their case C as reproduced by Zhao et al. 2019, arXiv:1901.00261, Sect. 4.8,
read in full, and by the adaptive-mesh discrete-velocity Boltzmann paper arXiv:2502.04820,
Sect. IV.2.2, Eqs. 62 to 65, read in full). A stationary normal shock of Mach M_s with the
Rankine–Hugoniot states on its two sides; an isentropic vortex of radius r_v = 1 centred
upstream, with (in the vortex frame, r the distance from its centre)

$$
u_\theta(r) = M_v\, r\, e^{(1-r^2)/2},\qquad
\rho(r) = \left[1 - \tfrac{\gamma-1}{2} M_v^2 e^{1-r^2}\right]^{1/(\gamma-1)},\qquad
p(r) = \tfrac{1}{\gamma}\left[1 - \tfrac{\gamma-1}{2} M_v^2 e^{1-r^2}\right]^{\gamma/(\gamma-1)}, \tag{F.1}
$$

with M_v = u_θ,max/a₁ the vortex Mach number, a₁ the upstream sound speed, Re = 800 on
post-shock quantities, γ = 1.4. Case C: M_s = 1.2, M_v = 0.25; case G: M_s = 1.29, M_v = 0.39.
Zhao et al. use the domain [−20, 8] × [−12, 12] with the shock at x = 0, the vortex at (1, 0),
supersonic inflow at x = 8, periodic y, non-reflecting at x = −20, 700 × 600 cells, and compare
the sound pressure Δp = (p − p_∞)/p_∞ at t = 6 (contours, Fig. 19; the radial profile at 135°
from the vortex centre, Fig. 20) against Inoue and Hattori's 1044 × 1170 solution. The
Boltzmann paper places the shock at x = 8 in [0, 28] × [0, 24] with the vortex at (6, 12)
and compares the profile at 45° at t* = 6, 8, 10 (Fig. 18). Zhang, Zhang and Shu (2006, read
in full) extend it to an oblique shock and a vortex pair at M_s = 1.05 and 1.2, M_v = 0.05 to
1.0 (their Table I), on 1280 × 960. Rault, Chiavassa and Donat (2003) study the same
interaction at higher shock Mach numbers (metadata only; not opened). **What is known.**
The sound-pressure field and its radial profiles in the papers above; the main shock's
deformation and the reflected shocks are the pictured fronts.

**The threshold problem.** Case C's main shock has p₂/p₁ = 1.513 and case G's 1.775 (my
arithmetic from A.3), both below the detector's 1.805, so on the standard cases the
reference shock set is empty: they are (d) cases in the detector's sense, and they exercise
issue 120's both-empty convention on a field that physically has a shock. For the (a) use,
one front bent by one structure, run the same setup at M_s = 1.5 or 2 (ratios 2.458 and 4.5;
my choice, which leaves the published pictures as qualitative guides only; Rault et al.'s
high-Mach cases, if their paper can be opened, would supply reference figures). The
reflected shocks and the sound waves are weak and will not be flagged at any M_s.
**Boundaries.** Inflow, outflow and periodic: the repository has no inflow type; declare
`neumann` on x and `periodic` on y and keep the fronts away from x boundaries within the
window. **Cost.** 10⁴ steps on 700 × 600: minutes in a compiled code. **On disk.** Nothing.

### 4.7 Already on disk without a reader (interim, no new simulation)

- **The kinet supersonic obstacle flow** (`.../Pr-71en2_vuy-1.4_Re-3e2/D2Q9_shape-500-300_T-1000_H-a92b16.h5`,
  12 GB): compressible scheme, inlet Mach 1.8, γ = 1.4, Pr 0.71, Re 300, a cylinder of radius
  20 at (166, 150) on 500 × 300 cells, 1000 frames, inlet on the left and Neumann elsewhere
  (config read). The bow shock has normal Mach 1.8 at the nose (ratio 3.61) weakening along
  the arc toward the detector's threshold, so the flagged set is a truncated arc whose
  length depends on the threshold: a real curved oblique front (a) and a direct test of
  constraint 3. Lattice-Boltzmann at Re 300 gives thick fronts; constraint 2 applies.
  Blocked on a reader for its layout and on issue 046 (wavenumber definition on a
  non-square domain) for the spectral metrics only.
- **The kinet Sod runs** (two configurations, 3001 × 5 cells): a solver's shock against the
  exact one; one-dimensional, so none of (a) to (d).
- **The Well's `turbulent_radiative_layer_2D`** (`datasets/well/datasets/turbulent_radiative_layer_2D/data/test/`,
  seven of the nine cooling times, 79 MB each; dataset card read): density, pressure and
  velocity on 384 × 128 (axis order to be checked in the HDF5), 101 frames every 1.597 time
  units, periodic in x and zero-gradient in y, Euler with a cooling sink −E/t_cool and
  γ = 5/3, a cold dense layer under a hot dilute one in relative motion "at highly subsonic
  velocities" (card; Fielding et al. 2020 not opened). The on-disk statistics show a
  pressure standard deviation of 0.061 about a mean of 0.94 (`stats.yaml`), so no cell pair
  should reach a ratio of 1.805: a two-dimensional pressure field with no reference shock
  (d), on which every false flag and the both-empty score are measured. Blocked on a
  boundary mapping in `fmeval/data/well.py`, which refuses non-periodic axes.

## 5. Recommendation

Prepare in this order; each step is cheap until the last.

1. **The closed-form reader with four fields** (Sects. 3.1, 3.3, 3.4, 3.7): Sedov–Taylor
   (cylindrical, with Kamm and Timmes' code or their standard case E = 0.311357), Noh, the
   tilted stripe, and the geometric ellipses, all evaluated on demand like `sod_shock_tube`.
   Seconds per run; every geometric error has a known answer (Sect. 3.8); the oblique wedge
   shock (Sect. 3.2) is a special case of the stripe with one front. This is cluster D8 and
   tier 1 of B4 in one reader, and it needs only the decision that a closed-form field is
   admitted as evidence.
2. **Riemann Cases 3, 4, 12 and 6** (Sect. 4.1) at 512² and 256² with any Euler code: curved
   interacting fronts with a resolution ladder, and Case 6 as the no-shock reference.
   Minutes.
3. **The obstacle-flow reader and the Well boundary mapping** (Sect. 4.7): two
   two-dimensional pressure fields already on disk, one with a real bow shock and one with
   none.
4. **Decaying compressible turbulence at Mach 0.6** (Sect. 4.4) with kinet's compressible
   scheme from the on-disk isotropic initial condition: the shocklet regime, issue 002's
   acceptance test, and the first field on which the pooled-average weakness of
   `shock_set_distance` is measurable. Hours; blocked on a wall-clock measurement.
5. **Forced compressible turbulence** (Sect. 4.5) only if kinet gains a forcing term; it
   then serves D4 as well.

The double Mach reflection (Sect. 4.2) and the shock–vortex interaction at raised Mach
number (Sect. 4.6) add specific front geometries (a straight-plus-curved triple point; one
front bent by one vortex) and are worth a run each once the reader exists, but neither is
needed first.

## 6. What to store

Following `docs/recipes/add-a-dataset.md`:

- **Fields** under canonical names: `pressure` `(T, x, y)` from every option, `density`
  `(T, x, y)` and `velocity` `(T, 2, x, y)` from every solver run and from every closed-form
  Euler solution (Sedov, Noh, the stripe), channel-first with trailing spatial axes. The
  geometric-case generator writes pressure only (and declares so). No vorticity stored.
  Pressure is never derived from density: for the isothermal forced runs, store the
  solver's own pressure and note its near-redundancy on the dataset page.
- **Precision.** float64 from the closed forms and from kinet; float32 copies acceptable.
- **Grid and boundaries.** `GridSpec.boundary` per axis: `("neumann", "neumann")` for Sedov,
  Noh, the Riemann problems, the double Mach reflection and the obstacle flow;
  `("periodic", "periodic")` for the stripe, the geometric cases and both turbulence
  options; `("neumann", "periodic")` for the shock–vortex box and `("periodic", "neumann")`
  for the Well layer. Resolution 512² for the closed forms (any grid on demand), 400² to
  1024² for solver runs, stored on the solver's grid.
- **Cadence and window.** Closed forms: a time window in which the front is at least ten
  cells from any boundary and from the origin (Sedov: 0.05 ≤ t ≤ 0.2 for E = 1, ρ₀ = 1 on
  the unit square centred at the origin, my choice from A.1). Riemann problems: every step
  to T of the table. Turbulence: every step for two eddy turnovers, then every tenth.
- **Provenance per file.** Solver config hash (kinet writes `configs/<hash>.yaml`), γ, the
  initial states or (E, ρ₀, p₀, α), the random seed, the front law r_2(t) or the curve
  parameters, and the detector threshold the preparer checked against (R = 1.805), as HDF5
  attributes, so the known answer travels with the data.
- **Configuration.** One `configs/dataset/<name>.yaml` per option with a shared
  `_`-fragment per family and a `complexity` block naming the family (`shock_analytic`,
  `riemann_2d`, `shocklet_turbulence_2d`, my names); the closed-form reader registered with
  `@register_reader` in `fmeval/data/analytic.py` beside `sod_shock_tube`.

## 7. References

Each entry says what was read.

- Ahijevych, D., Gilleland, E., Brown, B. G. and Ebert, E. E. (2009). Application of spatial
  verification methods to idealized and NWP-gridded precipitation forecasts. *Weather and
  Forecasting* 24(6), 1485–1497, https://doi.org/10.1175/2009WAF2222298.1. **Not opened by me
  (AMS returned 403); the case definitions are taken from the geometric and perturbed
  shock-case proposal, whose author read it in full (deleted once built; in git history).**
- Falkovich, G. and Kritsuk, A. G. (2017). How vortices and shocks provide for a flux loop in
  two-dimensional compressible turbulence. *Physical Review Fluids* 2, 092603(R),
  https://doi.org/10.1103/PhysRevFluids.2.092603; arXiv:1709.00814. **Read in full (ar5iv);
  Table I, Figs. 1, 4, 5, Supplement Eqs. 2 to 4.**
- Fielding, D. B., Ostriker, E. C., Bryan, G. L. and Jermyn, A. S. (2020). Multiphase gas and
  the fractal nature of radiative turbulent mixing layers. *Astrophysical Journal Letters*
  894(2), L24. **Not opened; cited by the Well dataset card.**
- Inoue, O. and Hattori, Y. (1999). Sound generation by shock–vortex interactions. *Journal
  of Fluid Mechanics* 380, 81–116, https://doi.org/10.1017/S0022112098003565. **Abstract
  only; the case-C setup is from the two secondary sources below.**
- Johnsen, E., Larsson, J., Bhagatwala, A. V., Cabot, W. H., Moin, P., Olson, B. J., Rawat,
  P. S., Shankar, S. K., Sjögreen, B., Yee, H. C., Zhong, X. and Lele, S. K. (2010).
  Assessment of high-resolution methods for numerical simulations of compressible turbulence
  with shock waves. *Journal of Computational Physics* 229(4), 1213–1237,
  https://doi.org/10.1016/j.jcp.2009.10.028. **Not opened (two repository copies returned
  403); Sect. 5 parameters are as reproduced by Motheau and Wakefield (2021).**
- Kamm, J. R. and Timmes, F. X. (2007). On efficient generation of numerically robust Sedov
  solutions. Los Alamos report LA-UR-07-2849,
  https://cococubed.com/papers/la-ur-07-2849.pdf. **Read in full; Eqs. 1 to 3, 12, 13, 54,
  Sect. 4.1 (standard problems), Appendix A.**
- Kemm, F. (2014). On the proper setup of the double Mach reflection as a test case for the
  resolution of gas dynamics codes. arXiv:1404.6510. **Read in full (ar5iv).**
- Kritsuk, A. G. (2019). Energy transfer and spectra in simulations of two-dimensional
  compressible turbulence. In *Turbulence Cascades II*, ERCOFTAC Series 26, 61–70, Springer;
  arXiv:1802.08228. **Read in full (ar5iv); Sect. 2, Table 1, Figs. 1 to 6.**
- Kurganov, A. and Tadmor, E. (2002). Solution of two-dimensional Riemann problems of gas
  dynamics without Riemann problem solvers. *Numerical Methods for Partial Differential
  Equations* 18(5), 584–608; UCLA CAM report 00-34. **The CAM preprint PDF was opened but its
  text could not be extracted; nothing is quoted from it.**
- Lax, P. D. and Liu, X.-D. (1998). Solution of two-dimensional Riemann problems of gas
  dynamics by positive schemes. *SIAM Journal on Scientific Computing* 19(2), 319–340,
  https://doi.org/10.1137/S1064827595291819. **Metadata only (paywalled); the case
  numbering is as Liska and Wendroff use it.**
- Lee, S., Lele, S. K. and Moin, P. (1991). Eddy shocklets in decaying compressible
  turbulence. *Physics of Fluids A* 3(4), 657–664, https://doi.org/10.1063/1.858071.
  **Abstract only (AIP page).**
- Liska, R. and Wendroff, B. (2003). Comparison of several difference schemes on 1D and 2D
  test problems for the Euler equations. *SIAM Journal on Scientific Computing* 25(3),
  995–1017, https://doi.org/10.1137/S1064827502402120. **Read in full (copy at
  math.umd.edu/~tadmor/centpack); Table 3.1, Sect. 3.1, Table 4.3, Sects. 4.3 to 4.8.**
- Motheau, E. and Wakefield, J. (2021). On the numerical accuracy in finite-volume methods
  to accurately capture turbulence in compressible flows. arXiv:2106.06585 (DOI
  10.1002/fld.5021 listed). **Read in full; Sect. 3.3, Eqs. 15 to 19, Figs. 7, 8.**
- NASA Glenn Research Center. Oblique shock waves,
  https://www.grc.nasa.gov/www/k-12/airplane/oblique.html. **Read in full.** Anderson, J. D.,
  *Modern Compressible Flow*, and Liepmann, H. W. and Roshko, A., *Elements of Gasdynamics*:
  **not opened**, named as the textbook sources of the same relations.
- Noh, W. F. (1987). Errors for calculations of strong shocks using an artificial viscosity
  and an artificial heat flux. *Journal of Computational Physics* 72(1), 78–120,
  https://doi.org/10.1016/0021-9991(87)90074-X. **Not opened; the exact solution is as
  printed by Liska and Wendroff (2003, Sect. 4.5) and Sutherland (2010, Table 9).**
- Passot, T. and Pouquet, A. (1987). Numerical simulation of compressible homogeneous flows
  in the turbulent regime. *Journal of Fluid Mechanics* 181, 441–466,
  https://doi.org/10.1017/S0022112087002167. **Abstract only.**
- Ramsey, S. D., Kamm, J. R. and Bolstad, J. H. (2012). The Guderley problem revisited.
  *International Journal of Computational Fluid Dynamics* 26(2), 79–99; Los Alamos report
  LA-UR-09-5853, https://www.osti.gov/servlets/purl/970025. **Read in full (OSTI copy);
  Eqs. 1 to 11, Tables 1 and 2.** Giron, I., Balberg, S. and Krief, M. (2021), Solutions of
  the imploding shock problem in a medium with varying density, arXiv:2106.04971:
  **abstract and introduction only.**
- Rault, A., Chiavassa, G. and Donat, R. (2003). Shock–vortex interactions at high Mach
  numbers. *Journal of Scientific Computing* 19, 347–371,
  https://doi.org/10.1023/A:1025316311633. **Metadata only; not opened.**
- Roberts, N. M. and Lean, H. W. (2008). Scale-selective verification of rainfall
  accumulations from high-resolution forecasts of convective events. *Monthly Weather
  Review* 136(1), 78–97, https://doi.org/10.1175/2007MWR2123.1. **Via the repository
  proposal, which read it in full.**
- Samtaney, R., Pullin, D. I. and Kosović, B. (2001). Direct numerical simulation of
  decaying compressible turbulence and shocklet statistics. *Physics of Fluids* 13(5),
  1415–1430, https://doi.org/10.1063/1.1355682. **Abstract only (AIP page).**
- Schaal, K. and Springel, V. (2015). Shock finding on a moving mesh — I. Shock statistics in
  non-radiative cosmological simulations. *Monthly Notices of the Royal Astronomical Society*
  446(4), 3992–4007, https://doi.org/10.1093/mnras/stu2386; arXiv:1407.4117. **Read in full
  (arXiv HTML v2); Sects. 2.3.2 and 3.1, Fig. 1.**
- Schulz-Rinne, C. W., Collins, J. P. and Glaz, H. M. (1993). Numerical solution of the
  Riemann problem for two-dimensional gas dynamics. *SIAM Journal on Scientific Computing*
  14(6), 1394–1414, https://doi.org/10.1137/0914082. **Not opened; configuration letters via
  Liska and Wendroff.**
- Sedov, L. I. (1959). *Similarity and Dimensional Methods in Mechanics*. Academic Press.
  **Not opened; its tables are reproduced and corrected by Kamm and Timmes (2007,
  Tables 1 to 3).**
- Shu, C.-W. and Osher, S. (1989). Efficient implementation of essentially non-oscillatory
  shock-capturing schemes, II. *Journal of Computational Physics* 83(1), 32–78,
  https://doi.org/10.1016/0021-9991(89)90222-2. **Not opened; data as printed by Liska and
  Wendroff (2003, Sect. 3.1).**
- Sutherland, R. S. (2010). A new computational fluid dynamics code I: Fyris Alpha.
  *Astrophysics and Space Science* 327, 173–206; arXiv:1003.0724. **Read in part (ar5iv):
  Sects. VI.1.3, VI.1.6, VII.3, Tables 9, 10, 19.**
- Taylor, G. I. (1950). The formation of a blast wave by a very intense explosion. I.
  Theoretical discussion. *Proceedings of the Royal Society A* 201(1065), 159–174,
  https://doi.org/10.1098/rspa.1950.0049. **Read in full (scanned copy at
  academicweb.nd.edu/~powers); summary and Eq. 38.**
- The Well, `turbulent_radiative_layer_2D` dataset card,
  https://huggingface.co/datasets/polymathic-ai/turbulent_radiative_layer_2D. **Read in
  full.**
- Toro, E. F. (2009). *Riemann Solvers and Numerical Methods for Fluid Dynamics*, 3rd ed.
  Springer. **Via `docs/datasets/sod_shock_tube.md`.**
- Woodward, P. and Colella, P. (1984). The numerical simulation of two-dimensional fluid
  flow with strong shocks. *Journal of Computational Physics* 54(1), 115–173,
  https://doi.org/10.1016/0021-9991(84)90142-6. **Metadata only (two copies returned 404 or
  403); the setup is as printed by Kemm (2014).**
- Zhang, S., Zhang, Y.-T. and Shu, C.-W. (2006). Interaction of an oblique shock wave with a
  pair of parallel vortices: shock dynamics and mechanism of sound generation. *Physics of
  Fluids* 18, 126101. **Read in full (PDF at academicweb.nd.edu/~yzhang10); Sect. II.A,
  Table I.**
- Zhao, F., Ji, X., Shyy, W. and Xu, K. (2019). Compact higher-order gas-kinetic schemes with
  spectral-like resolution for compressible flow simulations. arXiv:1901.00261. **Read in
  full (ar5iv); Sect. 4.8, Figs. 19, 20.** The adaptive-mesh discrete-velocity Boltzmann
  paper arXiv:2502.04820 (A fully conservative discrete velocity Boltzmann solver with
  parallel adaptive mesh refinement for compressible flows; authors not recorded): **read
  in full (arXiv HTML); Sect. IV.2.2, Eqs. 59 to 65, Figs. 17 to 19.**

## 8. Confidence

**Sure of** (read from a primary source or checked by arithmetic): the detector's rule and
ratio 1.805 (card, Eq. 1); the Sedov radius law and the standard-case energies of Kamm and
Timmes, and the cylindrical constant 0.98404 derived from them; Taylor's Eq. 38; Schaal and
Springel's three-dimensional test and its 5% overestimate; the Noh exact solution as printed
by Liska and Wendroff; the Guderley exponents of Ramsey et al. Table 1; the six Riemann
configurations of Liska and Wendroff Table 4.3 and their wave patterns; the double Mach
reflection states as printed by Kemm, which reproduce the Mach-10 ratios exactly; the
Shu–Osher data as a Mach-3 post-shock state; the Falkovich–Kritsuk and Kritsuk run tables;
the Inoue–Hattori case-C vortex profile and parameters as reproduced by two independent
papers, and the arithmetic showing that cases C and G lie below the detector's threshold;
the Well card and the on-disk kinet configurations.

**Reasoning, labelled as mine:** the loss of a smeared jump under the two-cell comparison
(constraint 2); every known-answer relation in Sect. 3.8, especially the (2/π)s value for a
displaced circle; the tilted-stripe construction and the oblique-shift distance s sin β; the
top-boundary shock foot formula for the double Mach reflection; the two-dimensional
decaying-turbulence setup, which is the repository's own choice since no published
two-dimensional standard with full initial data was found; the γ = 1.4 variant of the forced
run; the raised shock Mach number for Option F; all cost estimates; the claim that Riemann
Case 6 stays free of detector flags, which must be checked on a run.

**Not checked:** Ahijevych et al.'s tables (taken from the repository proposal); Lax and
Liu's own numbering beyond the six cases Liska and Wendroff carry; Johnsen et al.'s Sect. 5
beyond the secondary reproduction; Woodward and Colella's original text; Inoue and Hattori's
own domain and boundary conditions; Rault et al.'s Mach numbers; the exact wording of
Kurganov and Tadmor; whether kinet's compressible scheme accepts a random-mode initial
condition at Mach 0.6 and whether it supports forcing; the axis order of the Well files;
the one garbled density digit of the Shu–Osher state in my text extraction of Liska and
Wendroff (the value 3.857143 is confirmed by the Rankine–Hugoniot arithmetic, not by the
PDF).

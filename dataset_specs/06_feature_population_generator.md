# Dataset 06: the feature-population generator (vortices, fronts and bumps on a smooth background)

**Catalog clusters:** B5 (the build), merging D7 (known vortex population), D8(a) (shock fronts
with known geometric errors), D9(b) (the background-ratio sweep), with the per-feature forms of
G4 (add and remove a feature) and G10 (selective displacement of one feature).
**Metrics served:** every pairwise family except the ensemble metrics: the pointwise norms
(`mse`, `mae`, `rmse`, `max_error` and their siblings), `spectrum_l2`, the increment family
(`increment_w1`, `increment_flatness`, `tail_exceedance`), the topology pair
(`persistence_distance`, `persistence_wasserstein`), the six shock metrics, and the transport pair
(`wasserstein`, `h_minus_one`). **Ideas and issues served:** the vortex criteria (issue 060), the
eddy census (073), the pair correlation of features (082), the winding angle (086), the signed
vortex census (`proposals/MTR-persistence_distance-signed-vortex-census.md`), and catalog decision 4
("which vortex profile the generator uses, and its citation").
**Date:** 2026-11-26. **Author:** research sub-agent, branch `build_datasets`.
"My derivation", "my design" and "measured" mark the author's own work. Every "measured" number
was computed on 2026-11-26 with the repository's own metric functions in `.venv`; the scripts are
in the session scratchpad, not in the repository.

## 1. Purpose

Four groups of proposals ask for one thing: a field whose features are listed in advance, so that
a metric's answer is known before it runs. The persistence cards and four blocked ideas need a
known vortex population (catalog D7; `proposals/EXP-orchestrator-20261023-known-vortex-field.md`;
issues 060, 073, 082, 086, each of which says no current degradation "adds, removes or weakens
individual vortices by design"). The six shock metrics need fronts with a known displacement,
size and orientation error (D8(a); `proposals/EXP-shock_mask_overlap-geometric-and-perturbed-cases.md`).
`wasserstein` needs a translated bump on backgrounds of increasing size
(D9(b); `proposals/EXP-wasserstein-background-ratio-sweep.md`). The persistence cards need a
feature added or removed at a known depth (G4; `proposals/EXP-persistence_distance-spurious-feature-injection.md`,
`...-topological-simplification.md`). And the degradation cards' own limitations ask for the
displacement of one feature while the rest stay put (G10; `degradations/translate/card.md`
lines 80–83), which the catalog calls "the double-penalty case in its purest form, which the
global translations cannot produce".

The catalog's B5 merges these into one closed-form reader: a periodic field made of a smooth
random background plus a list of sharp features, each with its own kind, position, amplitude,
width, orientation and velocity. A candidate is the same list with one entry changed. Because
every feature is a closed form, every metric family has an answer known before the run
(Sect. 3.5). By Kareem's decision of 2026-11-26 (`BUILD_ORDER.md`, decision 9) it is an
evaluation dataset admitted to `evidence_datasets` with a claim label (Sect. 6), not a fixture.
Option B adds a kinet run seeded with a vortex population from the same reader, so the initial
population is known and the evolution (merger, core growth) is real.

**Following Kareem's instruction of 2026-11-26** (as much existing code and as little new code as
possible, no aliases, the design fitted to the framework), the reader is an extension of the
existing `advecting_blobs` reader, every candidate an existing degradation can make is left to
that degradation, and Section 5.1 lists each piece with the file it extends.

## 2. What the dataset must provide

- **Fields.** `density` (bumps on a positive background), `velocity` (from a vortex population),
  `vorticity` (the closed form, as a cross-check the harness replaces by its own recomputation
  from velocity, as for `taylor_green_2d`), `pressure` (positive fronts on a positive
  background). Pressure here is a manufactured field written by the generator, as in dataset 03,
  Sect. 3.7; it is never computed from density.
- **Grid and boundary.** The periodic unit square $[0,1)^2$ of `advecting_blobs`, both axes
  `periodic`, $N \times N$ cells of side $\Delta x = 1/N$, cell centres at $(i + \tfrac12)\Delta x$.
  256² for the evaluation configurations (Sect. 6); any grid on demand.
- **Time.** Static frames, or every feature carried at its own constant velocity, as
  `advecting_blobs` does now, so a time-dependent metric has a known curve.
- **Realisations.** Seeds draw the background and, when centres are not listed, the centres.
- **Known answers.** For each candidate edit and each metric family, a closed form, an exact
  discrete formula, or an exact bound (Sect. 3.5), each to be pinned by a test.

## 3. Option A, the analytic ideal: one closed-form reader

### 3.1 The design: `advecting_blobs` with options

The existing reader (`fmeval/data/analytic.py`, class `AdvectingBlobs`) already evaluates, on the
periodic unit square, a uniform level 1 plus a sum of Gaussians, each carried at its own constant
velocity, with centres drawn from `seed` and the periodic distance taken as the minimum image. The
generator keeps that loop and its defaults, so the existing `advecting_blobs` configuration and its
tests are unchanged, and adds options (Sect. 3.6): per-feature centres, amplitudes, widths,
aspect ratios and orientations; a `kinds` list that sends each feature to the field it lives in
(`bump` to density, `vortex` to vorticity and hence velocity, `front` to pressure); an optional
smooth background; and a `candidate` edit of the list. With the candidate set, the reader also
returns the candidate trajectory through a `predictions()` method, the interface
`ForecastPairs.predictions()` already gives `evaluate.py` (line 106), so the harness scores the
candidate against the reference frame by frame with no new pipeline code.

Every feature shares one geometry (my design): the elliptic radius about its centre
$\mathbf{c}_j + \mathbf{u}_j t$,

$$
\varrho_j(\mathbf{x}, t)^2 = \frac{x'^2}{w_j^2} + \frac{y'^2}{(\epsilon_j w_j)^2}, \qquad
\begin{pmatrix} x' \\ y' \end{pmatrix} = R(-\phi_j)\, \bigl[\mathbf{x} - \mathbf{c}_j - \mathbf{u}_j t\bigr]_{\mathrm{min.\,image}}, \tag{1}
$$

with width $w_j$, aspect ratio $\epsilon_j \le 1$ (1 is isotropic), orientation $\phi_j$ and
rotation matrix $R$. A bump or a vortex is a Gaussian in $\varrho_j$; a front is a smoothed jump
across a curve built from the same coordinates.

### 3.2 The background: a periodic random field of prescribed spectrum

On the $N^2$ grid, the background of one field is (my construction, reusing the
`gaussian_impostor` draw)

$$
b(\mathbf{x}) = \sum_{\mathbf{m} \ne 0} A(|\mathbf{m}|)\, e^{i\theta_\mathbf{m}}\, e^{2\pi i\, \mathbf{m}\cdot\mathbf{x}}, \qquad
A(|\mathbf{m}|)^2 = \frac{E_b(k)}{n_k}, \quad k = \mathrm{rint}(|\mathbf{m}|), \tag{2}
$$

where $\mathbf{m}$ is the integer wavevector, $E_b(k) \propto k^{-\beta}$ on
$k_{\min} \le k \le k_{\max}$ and zero elsewhere, $n_k$ the number of modes in shell $k$ (shells
from `radial_shells` of `metrics/spectrum_l2/metric.py`, so the binning is the metric's own), and
the whole scaled so the rms of $b$ is the parameter `background.rms` of that field. The phases
$\theta_\mathbf{m}$ are those of the Fourier transform of a real white-noise field, exactly as
`degradations/gaussian_impostor/degradation.py` takes them: that respects Hermitian symmetry,
$\theta_{-\mathbf{m}} = -\theta_\mathbf{m}$, including the self-conjugate modes ($\mathbf{m} = 0$,
the Nyquist row, column and corner), which a hand-drawn uniform phase breaks (the impostor's
docstring measured a flatness of 47.9 instead of 3 when drawn that way). The amplitudes are fixed
and only the phases are random, so the background's shell spectrum equals $E_b(k)$ exactly at
every seed (my derivation; it is the corollary of `05_..., Sect. 3.1`), and `spectrum_l2` between
two seeds of the background alone is zero to round-off. With random phases on many modes the
one-point distribution is close to Gaussian (central-limit reasoning, not exact). The random
stream is `fmeval.context.derive_rng(seed, "background", 0, field)`, the existing seeded-stream
helper, so each field's background is independent and reproducible. The time-resolved version of
this field is dataset 04's Option A3 and specification 09; both should call the same draw.

The background is static (not advected). Its size relative to the features is the
amplitude ratio $r_b = \texttt{background.rms}/\min_j |a_j|$, the knob of the background sweep.
The exact answers of Sect. 3.5 hold at $r_b = 0$; at $r_b > 0$ the pointwise answers stay exact and
the topological and increment answers become exact bounds (Sect. 3.5).

### 3.3 The feature types

**(i) Bumps (density).** $\rho = 1 + b_\rho + \sum_{j \in \mathrm{bumps}} a_j\, e^{-\varrho_j^2/2}$,
with $a_j > 0$, the existing profile of `advecting_blobs`. The reader refuses a field whose minimum
is not positive (needed by `wasserstein`, which is undefined on a non-positive cell).

**(ii) Vortices (vorticity, velocity).** The vorticity of vortex $j$ is the Gaussian
$\omega_j = a_j e^{-\varrho_j^2/2}$, with signed peak $a_j$ and, for $\epsilon_j = 1$, circulation
$\Gamma_j = 2\pi w_j^2 a_j$. This is the Lamb–Oseen (Oseen) vortex. Gallay and Wayne (2005),
Sect. 1, Eq. (7), with the viscosity set to 1, give
$\omega(x, t) = \frac{\alpha}{4\pi t} e^{-|x|^2/4t}$ and
$u(x,t) = \frac{\alpha}{2\pi}\frac{x^\perp}{|x|^2}\bigl(1 - e^{-|x|^2/4t}\bigr)$, with the profile
$G(\xi) = \frac{1}{4\pi}e^{-|\xi|^2/4}$ in their Eq. (8) and $\alpha$ the circulation. Restoring
the viscosity $\nu$ (replace $t$ by $\nu t$, my step) and writing $w^2 = 2\nu t$, the vorticity is
the Gaussian above and the free-space azimuthal velocity is

$$
u_\theta(r) = \frac{\Gamma}{2\pi r}\left(1 - e^{-r^2/2w^2}\right). \tag{3}
$$

So the "Gaussian vortex" and the "Lamb–Oseen vortex" are one profile: the Lamb–Oseen vortex is
the Gaussian whose core grows by diffusion, $w^2 = w_0^2 + 2\nu t$. Meunier, Le Dizès and Leweke
(2005), Sect. 2.1, state that each vortex of a viscous co-rotating pair "converges toward a
solution close to the Lamb–Oseen vortex". **Answer to catalog decision 4:** the Gaussian
(Lamb–Oseen) vorticity profile, cited to Gallay and Wayne (2005), Eqs. (7)–(8). Measured from (3):
the peak speed is $0.4513\,\Gamma/(2\pi w)$ at $r = 1.585\,w$.

*A torus holds no net circulation.* By Stokes' theorem the total vorticity in the periodic cell is
the circulation around its boundary, and periodicity makes the contributions of opposite edges
cancel, so $\int \omega\, dA = 0$ for every periodic velocity. A sum of Gaussians with
$\sum_j \Gamma_j \ne 0$ is therefore the vorticity of no periodic flow. The reader handles this in
two ways: the reference configurations pair the signs so that $\sum_j \Gamma_j = 0$ (measured mean
of such a sampled sum: $9 \times 10^{-19}$), and the stored vorticity is always
$\omega - \langle\omega\rangle$, the vorticity of the velocity it stores. A candidate that breaks
the balance (one vortex's sign flipped, one removed) then carries a uniform compensating vorticity
$-\Delta\Gamma/|\Omega|$, which enters its known answer explicitly (Sect. 3.5).

*Velocity from vorticity (periodic Biot–Savart).* With $\hat\omega_\mathbf{k}$ the discrete Fourier
transform of the sampled vorticity and $\mathbf{k} = 2\pi\,\mathrm{fftfreq}(N, \Delta x)$ from
`physical_wavenumber_grid` (`fmeval/external/kinet_spectral.py`, the repository's one definition),
the stream function solves $\nabla^2\psi = -\omega$ and $\mathbf{u} = (\partial_y\psi, -\partial_x\psi)$:

$$
\hat u_\mathbf{k} = \frac{i k_y \hat\omega_\mathbf{k}}{|\mathbf{k}|^2}, \qquad
\hat v_\mathbf{k} = \frac{-i k_x \hat\omega_\mathbf{k}}{|\mathbf{k}|^2}, \qquad \mathbf{k} \ne 0, \tag{4}
$$

with the $\mathbf{k} = 0$ mode set to zero, which is the mean subtraction above. A vorticity
background $b_\omega$ is added before the inversion. Measured: the harness's own recomputation
(`fmeval.derived.vorticity_from_velocity`) returns $\omega - \langle\omega\rangle$ to
$7.6 \times 10^{-15}$ of a peak of 7.07 on 128². Near a core, the periodic velocity differs from
(3) by the velocity the other vortices and the periodic images induce, 9.6% within $r < 0.5$ for
two opposite vortices about $2.3$ apart on a $2\pi$ box (measured), so the known velocity is (4),
not (3).

**(iii) Fronts (pressure).** $p = 1 + b_p + \sum_{j \in \mathrm{fronts}} a_j\, H_\delta(-\varphi_j)$,
with $H_\delta(s) = \tfrac12[1 + \tanh(s/\delta)]$, jump $a_j > 0$, thickness $\delta$, and $\varphi_j$
a level-set function negative inside the front (my design):

- *Closed curve (ellipse, circle when $\epsilon_j = 1$):* $\varphi_j = \sqrt{\epsilon_j}\, w_j(\varrho_j - 1)$,
  the signed distance for a circle of radius $w_j$, and a distance whose local scale varies along an
  ellipse by $\epsilon_j^{\pm 1/2}$.
- *Straight front (a stripe of two parallel fronts that closes on the torus):* for a direction
  $(p, q)$ of coprime integers the lines through $\mathbf{c}_j$ along $(p,q)$ and their periodic
  images are spaced $P = 1/\sqrt{p^2+q^2}$ apart along the unit normal $\mathbf{n}$, so with
  $d = \mathbf{n}\cdot(\mathbf{x} - \mathbf{c}_j)$, $\varphi_j = |((d + P/2) \bmod P) - P/2| - w_j$
  (my derivation). This is the geometry of dataset 03, Sect. 3.3, without its Rankine–Hugoniot
  states.

*Sized so the detector fires.* The shock metrics flag a cell when its two neighbours along an axis
have pressures in a ratio of at least $R = 1.805$ (dataset 03, Sect. 2; `metrics/shock_set_distance/card.md`,
Eq. 1). Both pressures are positive here by construction. Measured for an axis-aligned tanh front
over 201 sub-cell offsets of the front: with jump ratio $(1 + a)/1 = 2.458$ (a Mach-1.5 normal
shock, dataset 03, Sect. 3.7) the detector fires at every offset for $\delta \le 1.065$ cells; at
ratio 4.5, for $\delta \le 2.21$; at ratio 10, for $\delta \le 3.39$. For a front at 45° to the grid
the two axis neighbours span a normal distance of $\sqrt2$ cells instead of 2, so the limit falls
by about $1/\sqrt2$ (reasoning; the test of Sect. 5.1 pins it). The configurations use $a = 1.5$
(ratio 2.5) and $\delta = 0.25$ cell, which is nearly a step yet is evaluated in closed form at any
sub-cell position, so a sub-cell move of a front does not ring as a Fourier shift of a step does
(the need the catalog's "ladder housekeeping" records). Measured band thickness: a straight front
through cell centres flags one cell per row, a front on a cell face two; both, for an
axis-aligned front, at $\delta \le 0.75$. A front with $a$ below 0.805 is a no-shock frame for the
detector (dataset 03, need (d)). The detector does not wrap around the periodic seam
(`shock_set_distance` card, "Boundary handling"), so fronts are placed away from the seam.

**Isolation.** The exact answers need features that do not overlap. The reader refuses a list in
which two Gaussian features' centres come closer than $12\,w$ in any frame, for the larger $w$ of
the pair (my threshold: the Gaussian tail at half that distance is $e^{-18} = 1.5\times10^{-8}$ of
the peak), or a front curve comes closer than that to a Gaussian centre or than four cells to
another front. On a 256² grid, widths lie between 2 cells (so a cell-centre sum reproduces the
continuum integral: measured relative error $\le 10^{-14}$ at 2 cells, $10^{-8}$ at 1.5, $10^{-3}$
at 1) and $0.06$ (so the minimum image leaves a seam of round-off size, `advecting_blobs` docstring).

### 3.4 Candidates, and which existing code makes each

| Candidate | Made by | New code |
|---|---|---|
| Move every feature (and the background) by whole cells | `translate` | none |
| Move every feature by a sub-cell amount | `translate_subpixel` | none (rings beside a sharp front; use the reader's move for fronts) |
| Scale every amplitude (and the background) | `gain` | none |
| Offset the whole field | `bias` | none |
| Blur, filter, coarsen, add noise | the existing smoothing, spectral, coarsening and noise operators | none |
| Keep the spectrum, destroy the features | `gaussian_impostor` | none |
| A wrong speed of every feature | any ordinal operator with `per_unit_time: true` on a ladder entry (`docs/datasets/advecting_blobs.md`) | none |
| Move one feature; rescale one amplitude; change one width; flip one vortex's sign; rotate one feature; give one feature a wrong velocity | the reader's `candidate` override of one entry of the list | shared, Sect. 3.6 |
| Remove a feature (the weakest); add a spurious feature | the reader's `candidate` `remove` and `add` | shared, Sect. 3.6 |

A run with a `candidate` scores one candidate, because `evaluate.py` replaces the ladder by the
prediction (line 106 onward); a severity sweep of one edit is a Hydra multirun over the edit's
value. Every global edit stays on the ordinary degradation ladder of the reference, with no
candidate set.

### 3.5 The known answers, per metric family (my derivations unless cited; each to be pinned by a test)

Notation: domain area $|\Omega| = 1$; feature $j$ has peak $a_j$, width $w_j$ (isotropic unless
stated), centre on a cell centre unless stated; $s$ is a displacement; "flat" means
`background.rms` $= 0$. Measured checks were on 128² with widths of 2 to 4 cells.

**Pointwise norms** (`mse`, `rmse`, `mae`, `max_error`, ...). The background and every other
feature cancel in the difference, so these are exact at any background level and need only that
the edited feature does not wrap. For a Gaussian of covariance
$\Sigma = R(\phi)\,\mathrm{diag}(w_1^2, w_2^2)\,R(\phi)^{\mathsf T}$:

$$
\mathrm{MSE}_{\text{move}}(\mathbf{s}) = 2\pi w_1 w_2 a^2 \left(1 - e^{-\mathbf{s}^{\mathsf T}\Sigma^{-1}\mathbf{s}/4}\right), \qquad
\mathrm{MSE}_{\text{rotate}}(\delta\phi) = 2\pi w_1 w_2 a^2 - \frac{4\pi a^2}{\sqrt{\det(\Sigma^{-1} + \Sigma'^{-1})}}, \tag{5}
$$

with $\Sigma'$ the rotated covariance (the overlap integral of two Gaussians,
$\int G_\Sigma G_{\Sigma'} = 2\pi a^2/\sqrt{\det(\Sigma^{-1}+\Sigma'^{-1})}$). Measured agreement:
$10^{-14}$ to $10^{-16}$ relative at widths of 2 cells and more. For an isotropic feature,
$\mathrm{MSE} = 2\pi w^2 a^2(1 - e^{-s^2/4w^2})$, the same form as `tests/analytic_fields.py`.
**The double penalty in closed form:** removing the feature costs $\pi w^2 a^2$, so the moved
feature scores worse than no feature at all once $1 - e^{-s^2/4w^2} > \tfrac12$, that is for
$s > 2\sqrt{\ln 2}\, w = 1.665\, w$. The other edits:
rescale by $(1+g)$: $g^2 \pi w^2 a^2$; remove or add (height $h$): $\pi w^2 h^2$;
width $w \to w'$: $\pi a^2[w^2 + w'^2 - 4w^2w'^2/(w^2 + w'^2)]$;
flip a vortex's sign: $4\pi w^2 a^2 - 4\Gamma_j^2$ in vorticity, the second term from the
compensating offset $2\Gamma_j$ of Sect. 3.3 (since $\langle g_j\rangle = \Gamma_j$; it is
$4\pi w^2 = 5\times10^{-3}$ of the first at $w = 0.02$). `max_error`: $|g|a$, $h$, $2|a|$ for those
edits; for a move, the maximum of a one-dimensional function along $\mathbf{s}$, which tends to
$s\, a\, e^{-1/2}/w$ for $s \ll w$ (card Eq. 3 with $\max|\partial_x G| = a e^{-1/2}/w$) and to $a$
for $s \gg w$. `mae` for a small move: $2\sqrt{2\pi}\, a w s$ (as in `tests/analytic_fields.py`);
for a large one, $4\pi w^2 a$.

*Velocity of a vortex edit.* By Parseval and (4), the velocity error summed over both
components is

$$
\sum_{c} \langle (\Delta u_c)^2 \rangle = \sum_{\mathbf{k} \ne 0} \frac{|\Delta\hat\omega_\mathbf{k}|^2}{|\mathbf{k}|^2}, \qquad
\Delta\hat\omega_\mathbf{k} = \hat\omega_{j,\mathbf{k}}\,\bigl(e^{-i\mathbf{k}\cdot\mathbf{s}} - 1\bigr) \text{ for a move}, \tag{6}
$$

with $\hat\omega_{j,\mathbf{k}} = 2\pi w^2 a\, e^{-|\mathbf{k}|^2 w^2/2} e^{-i\mathbf{k}\cdot\mathbf{c}_j}$;
measured equal to the direct sum to 16 digits for a sign flip. `mse` pools the two channels into
its mean, so it reports half of (6).

**Spectrum** (`spectrum_l2`). The shell spectrum of the field is
$E(k) = \tfrac12\sum_{\mathrm{rint}|\mathbf{m}| = k}\bigl|\hat b_\mathbf{m} + \sum_j \hat g_{j,\mathbf{m}} e^{-i\mathbf{k}\cdot\mathbf{c}_j}\bigr|^2$,
so it is unchanged by a translation **only** when everything moves together. Measured: `translate`
gives $1.3 \times 10^{-16}$, and one isolated feature on a flat background moved alone gives
$2.6 \times 10^{-16}$; but moving one of two bumps (heights 1 and 0.6, width 3 cells) gives 0.017,
0.072 and 0.19 for moves of 1, 4 and 16 cells, because the cross terms between features (and
between a feature and the background) depend on their separation. So "the spectrum is blind to
position" holds for global translation and for a lone feature; for a population, moving one
feature changes the spectrum by a computable amount. A width change of every feature (no
background) multiplies each mode by $(w'/w)^4 e^{-|\mathbf{k}|^2(w'^2 - w^2)}$; `gain` by $(1+g)^2$.

**Increment distributions** (`increment_w1` and its siblings, one-cell increments). On a flat
background with isolated features:

- a whole-cell move of one feature permutes the increments, so $W_1 = 0$ exactly; `translate`
  gives 0 at any background;
- removing feature $j$ (or adding one of height $h$) gives, along $x$, the exact discrete value
  $W_1^{(x)} = \frac{2}{N^2}\sum_{\text{rows}} \max_x g_j$ (the total variation of a unimodal row is
  twice its peak above the floor, and all moved atoms go to zero), whose continuum limit is
  $2\sqrt{2\pi}\, a w\, \Delta x$; measured equal to $10^{-19}$ (continuum value 3% above it at
  $w = 2$ cells);
- flipping a vortex centred on a cell centre leaves the multiset of its increments unchanged, so
  $W_1 = 0$ (measured $3 \times 10^{-55}$): the increment family cannot see the sign of an isolated
  vortex. Off a cell centre the symmetry is broken and $W_1$ is small but not zero (measured
  $4 \times 10^{-5}$ against $3 \times 10^{-4}$ for removing the same vortex).

With a background, the identity coupling and the triangle inequality give
$|W_1 - W_1^{\text{flat}}| \le 2\langle|\delta b|\rangle$, an exact bound.

**Persistence diagrams** (`persistence_distance`, sublevel sets, T-construction, torus). On a flat
background at level $\ell$ with isolated features, the diagram is known point by point (measured
for four bumps of heights 1, 0.8, 0.6, 0.3 on $\ell = 1$: $D_1 = \{(1, 1.3), (1, 1.6), (1, 1.8)\}$ plus
two loops of the torus born at 1 that never die, and $D_2$ one class born at 2.0):

- each positive feature except the tallest is one finite point $(\ell, \ell + a_j)$ in $D_1$; the
  tallest gives the never-dying class of $D_2$, born at the global maximum;
- each negative feature except the deepest is one finite point $(\ell - |a_j|, \ell)$ in $D_0$; the
  deepest gives the never-dying class of $D_0$, born at the global minimum.

So on vorticity the clockwise cores are $D_0$ points and the counter-clockwise ones $D_1$ points,
as the card says. The bottleneck answers, each measured exactly with the metric (non-extreme
features): remove the weakest, $a_{\min}/2$ (measured 0.15 for $a_{\min} = 0.3$); add a spurious
feature of height $h$, $h/2$ (0.1 for $h = 0.2$); rescale one amplitude by $(1+g)$,
$\min(|g|a,\ \max(a, (1+g)a)/2)$ (0.06 for $a = 0.6$, $g = 0.1$), which equals `max_error` and
so makes the stability bound of the card's Eq. (5) tight; move one feature by whole cells, 0
(measured 0.0); move it by a sub-cell amount, the change of its sampled peak,
$a(1 - e^{-\delta^2/2w^2})$ for a move of $\delta$ off a cell centre (0.0138 for half a cell at
$w = 3$ cells); change one width with the centre on a cell centre, 0 (the peak and the floor do not
move): the topology is blind to width; flip one vortex, $|a|/2$ (measured 0.25 for $|a| = 0.5$),
because a $D_1$ point becomes a $D_0$ point, each matched to the diagonal, with the compensating
offset of Sect. 3.3 (0.0035 here) moving the never-dying classes by less. The signed census of
`MTR-persistence_distance-signed-vortex-census.md` then sees a flip as a change in both signs, a
weakening of one sign as a change in one. With a background, card Eq. (5) and the triangle
inequality give $|\mathrm{PD} - \mathrm{PD}^{\text{flat}}| \le 2\max|b|$, an exact bound.

**Shock sets** (the six shock metrics, on pressure fronts). For a straight front moved by $s$
whole cells along the axis normal to it, measured exactly: $\mathrm{ASSD} = s - \tfrac12$ cells
when the fronts lie on cell faces (two cells flagged per front per row, the card's Eq. 3) and
$s$ cells when they pass through cell centres (one cell flagged); the Hausdorff distance is $s$.
For a front at angle $\beta$ the perpendicular displacement is $s\sin\beta$ (dataset 03, Sect. 3.8).
For a circle of radius 20 cells moved by $s = 1, 2, 4, 8$ cells, the measured ASSD is 0.377,
0.940, 2.087 and 4.524 cells, below the continuum curve-to-curve mean $(2/\pi)s$ of dataset 03,
Sect. 3.8 (0.637, 1.27, 2.55, 5.09) by 0.26 to 0.57 cells: the bands are about 1.7 cells thick and
partly overlap. So that formula is the continuum limit, and the test pins the discrete value.
**The pooled-average weakness, exactly:** when one of several fronts moves, and the others lie
farther from it than twice the move, the
unmoved fronts contribute zero distances, so
$\mathrm{ASSD} = \mathrm{ASSD}_j\,(|A_j| + |B_j|)/(|A| + |B|)$ (measured: exactly half for one of
two equal circles), while the Hausdorff distance keeps the moved front's value.
For an ellipse with semi-axes $w$ and $\epsilon w$ rotated by $\delta\phi$, the first-order normal
displacement at parameter $t$ is
$\delta\phi\,(a^2 - b^2)\sin t\cos t/\sqrt{b^2\cos^2 t + a^2\sin^2 t}$ ($a = w$, $b = \epsilon w$),
whose maximum is exactly $(a - b)\,\delta\phi$, at $\tan^2 t = b/a$; measured Hausdorff distance
between the curves 0.998 against 1.0 at $a = 20$, $b = 10$ cells, $\delta\phi = 0.1$. Enlarging a
circle from $r$ to $r'$ moves every point by $r' - r$ (dataset 03, Sect. 3.8). `shock_mask_overlap`
reaches its floor once two bands stop touching, about two cells.

**Transport** (`wasserstein`, bumps on density). The metric divides each density by its mean
(card, Eq. 1), which is the linear normalisation of Engquist and Yang (2022), Eq. (2) (arXiv
numbering), $\tilde f = (f + c)/\langle f + c\rangle$, with their constant $c$ the background. For
one bump of mass $M = 2\pi w^2 a$ moved by $s$ on a uniform background $c$:

1. *Empty background.* "The W2 metric precisely captures the data shift s as the misfit is s^2
   independent of the profile of the signal" (Engquist and Yang 2022, Sect. 1, an illustration, not
   a theorem): $W_2 = |s|$ as $c \to 0$. The repository's metric cannot reach this limit: measured
   on 128² with $w = 4$ cells, it returns NaN (no convergence) at contrast $a/c \ge 33$ for
   $s \ge 8$ cells, converges at $a/c = 20$ for $s \le 8$, and at $a/c = 10$ for every $s \le 48$.
2. *Any background, exact upper bound.* Moving only the bump is an admissible transport plan, so
   $W_2^2 \le m s^2$ with $m = M/(M + c|\Omega|)$ the bump's share of the mass. Measured
   $W_2^2/(m s^2) = 0.62$ at $a/c = 10$, $s = 1$ cell.
3. *Large background, the linearised limit.* As $a/c \to 0$,

$$
W_2^2 \to \sum_{\mathbf{k} \ne 0} \frac{|\Delta\hat\rho_\mathbf{k}|^2}{|\mathbf{k}|^2\,\bar\rho^2}, \qquad
\Delta\hat\rho_\mathbf{k} = \hat g_\mathbf{k}\,\bigl(e^{-i\mathbf{k}\cdot\mathbf{s}} - 1\bigr), \tag{7}
$$

   the squared homogeneous $H^{-1}$ norm of the relative difference ($\bar\rho$ the mean). The
   relation of $W_2$ to this norm is what the proposal cites from Peyre (2018), Corollary 3 and
   Theorem 5, which I did not open. Measured ratio $W_2^2$ to (7): 0.75 at $a/c = 1$, 0.965 at
   $0.1$, 0.996 at $0.01$, for $s$ of 1 and 2 cells. In (7), $W_2^2$ grows as $s^2$ for $s \ll w$
   and much more slowly beyond: measured $7.7 \times 10^{-4}$, $2.6 \times 10^{-3}$ and
   $3.6 \times 10^{-3}$ at $s = 8$, 24 and 48 cells ($c = 10$). The $H^{-1}$ energy of a
   two-dimensional dipole grows like $\log(s/w)$ (my reasoning), whereas Engquist and Yang's
   Theorem 4.6 (Sect. 4.3) is one-dimensional: $W_2^2 = O(|s|^2)$ for $|s| \le 1/c + |\mathrm{supp} f|$
   and $O(|s|)$ otherwise. **So applying their theorem to the two-dimensional bumps, as the catalog
   notes is an extrapolation, predicts the wrong far regime;** the background sweep should be read
   against (7) and the bound of item 2, not against linear growth.

### 3.6 Time dependence, the reader's parameters, and its limits

**Time.** Feature $j$ is at $\mathbf{c}_j + \mathbf{u}_j t$ (mod 1), as in `advecting_blobs`. A
candidate giving feature $j$ the velocity $\mathbf{u}_j + \delta\mathbf{u}$ is a move by
$\mathbf{s}(t) = \delta\mathbf{u}\, t$, so every answer of Sect. 3.5 becomes a known curve; for
example $\mathrm{MSE}(t) = 2\pi w^2 a^2\bigl(1 - e^{-|\delta\mathbf{u}|^2 t^2/4w^2}\bigr)$, whose crossing
of a threshold $\theta$ is at $t^* = (2w/|\delta\mathbf{u}|)\sqrt{-\ln(1 - \theta/2\pi w^2 a^2)}$, a
known valid prediction time (issue 078), and periodic in $t$ only after a whole domain of drift.
The motion is prescribed, not dynamic: vortices do not move by mutual induction here. Option B
supplies the dynamics.

**Parameters** (constructor of `AdvectingBlobs`; "existing" ones keep their meaning and default):

| Parameter | Status | Meaning | Default |
|---|---|---|---|
| `grid`, `n_frames`, `t_start`, `t_end` | existing | as now | `(64, 64)`, 21, 0, 10 |
| `velocities` | existing | one $(u_x, u_y)$ per feature, domain lengths per unit time; its length is the number of features | three velocities |
| `width` | existing, extended | $w_j$ in domain lengths: a scalar for all or one per feature; for a front, the semi-major axis or the stripe half-width | 0.06 |
| `amplitude` | existing, extended | $a_j$, scalar or per feature: bump height, signed peak vorticity, or front pressure jump | 0.1 |
| `seed` | existing | draws centres when `centres` is absent, and the background | 0 |
| `centres` | new | explicit $\mathbf{c}_j$ | drawn from `seed` |
| `kinds` | new | per feature: `bump`, `vortex` or `front` | all `bump` |
| `aspect`, `orientation` | new | $\epsilon_j \in (0, 1]$ and $\phi_j$ in radians, per feature | 1, 0 |
| `front_direction` | new | per front: `null` for a closed curve, or coprime integers $(p, q)$ for a straight stripe | `null` |
| `front_thickness` | new | $\delta$, in cells, one value for all fronts | 0.25 |
| `background` | new | `{rms: {density, vorticity, pressure}, slope: β, k_min, k_max}`; absent means none | absent |
| `candidate` | new | `{feature: j, <parameter>: value, ...}` to override entries of feature $j$; `{remove: j}`; `{add: {kind, centre, amplitude, width, ...}}` | absent |

Fields produced: `density`, `velocity`, `vorticity`, `pressure`, as `(C, x, y)` float64. The
uniform levels are fixed at 1 for density and pressure, as `advecting_blobs` fixes density's now; a
background-ratio sweep varies `amplitude`, as the EXP proposal does. All parameters, the candidate
included, are recorded in `meta` through `ClosedFormTrajectory`, so the known answer travels with
the results.

**Limits.** No field here is a solution of the Euler or Navier–Stokes equations: the vortices
neither strain nor merge, the pressure is not in balance with the velocity, and the fronts carry no
Rankine–Hugoniot states. The answers are exact for the listed edits on a flat background and exact
bounds on a background; overlapping features have no closed form. The evidence it gives is that a
metric reports a known answer, nothing about turbulence.

## 4. Option B: a kinet run seeded with a known vortex population

**System.** Weakly compressible isothermal flow, D2Q9 lattice Boltzmann with entropic BGK, the
physics of `homogeneous_isotropic_turbulence/Re-50k_Ma-1en1` (`00_how_to_use_kinet.md`, Sect. 1):
256², Re 5e4 on the box side, Ma 0.1, so $\nu = 2.96\times10^{-4}$ in lattice units
(`00_...`, Sect. 4).

**What is known about the evolution.** Two equal co-rotating vortices of circulation $\Gamma$ a
distance $b$ apart rotate about each other at the point-vortex rate $\Omega = \Gamma/\pi b^2$
(Meunier et al. 2005, Sect. 2.1, their Eq. (1); the symbols of that equation did not survive my
text extraction, and the rate given is the standard point-vortex result). Each core spreads by
viscous diffusion (their Eq. (4); for a Lamb–Oseen vortex, $a^2 = a_0^2 + 4\nu t$ follows from
Gallay and Wayne's Eq. (7) with the viscosity restored), where Meunier et al. define the core size
$a$ by the vortex's angular momentum about its vorticity centroid, so $a = \sqrt2\, w$ for the
Gaussian of Sect. 3.3 (my arithmetic). Merging starts when $a/b$ exceeds a critical value, "the
critical two-dimensional value of 0.22" (Meunier et al. 2005, Sect. 3, comparing it with 0.19 in
three dimensions), after which the pair merges in a convective stage whose duration is nearly
independent of the Reynolds number (their Sect. 2.2).

**Population (my design).** All vortices with $w = 6$ cells ($a_0 = 8.49$ cells) and
$|\Gamma| = 3$ in lattice units, so the peak speed is $0.4513 \times 3/(2\pi\cdot 6) = 0.036$, a
local Mach number of 0.062. Pair A: two positive vortices $b = 36$ cells apart, $a/b = 0.236$,
above 0.22, so it merges convectively (rotation period $2\pi^2 b^2/\Gamma = 8\,530$ steps). Pair B:
two negative vortices $b = 64$ cells apart, $a/b = 0.133$; by $a^2 = a_0^2 + 4\nu t$ it reaches 0.22
after about $1.1 \times 10^5$ steps, so within the run it stays in the diffusive stage, with
constant separation and growing cores (period 26 950 steps). Net circulation zero, the pairs a
half-diagonal apart. The known outcome in a 20 000-step run: the census of positive extrema falls
from two to one, the negative stays at two; B's cores grow as above. Mutual advection of the two
pairs and their periodic images is not known in closed form.

**Route** (`00_how_to_use_kinet.md`, Sect. 6a, the Python `initial_state` route, verified there
unmodified): compose the case at 256², build the simulator, and paint with `macros(x, y)` returning
the generator's velocity at $t = 0$ (scaled by one factor to the target peak speed and moved to
`(X, Y, 2)`), the density $\rho = 1 + \delta p / c_s^2$ with $\delta p$ from kinet's own
`_pressure_poisson_solve` (the step `init_hit` uses, `simulations/homogeneous_isotropic_turbulence/initialize.py`;
starting at uniform density instead triggers the acoustic transient that function's comment
describes), and `temperature: 1/3`. Then step 20 000 times, saving every 10th step, with
`io.record_distributions=false io.record_equilibria=false`. Whether the case's population corrector
(`fneq_hit`) is applied on this route was not checked. Cost: one debug job; a 256² run of 10 000
steps takes about 2.5 minutes (`BUILD_ORDER.md`, "How jobs are run").

**Candidates.** The degraded solver runs of dataset 05, Option C, from the same painted state: 128²
and 64² (where $w$ is 3 and 1.5 cells, the second under-resolved), Re × 0.5 (faster diffusion, so
pair B nears merger sooner by a known factor in $\nu$), and plain BGK. The analytic population at
$t = 0$ is the reference for the persistence diagram's initial point count.

## 5. Recommendation

Build Option A first: an afternoon of code on an existing reader (Sect. 5.1), with every answer of
Sect. 3.5 pinned by a test before any run is cited. Three configurations cover the families: bumps
on density, vortices on velocity and vorticity, fronts on pressure (Sect. 6). Then run the
background sweep at $r_b = 0, 0.01, 0.1, 1$. Option B follows once kinet jobs are approved: it is
the only source here of a known topological change produced by real dynamics (one merger, one
non-merger). **Overlap with dataset 03:** its geometric ellipses (Sect. 3.7) and tilted stripe
(Sect. 3.3, the pressure field) are this reader's `front` features; building them once here would
leave step 7 of `BUILD_ORDER.md` with Sedov, Noh and Sod at a shifted time. That is a proposal for
the coordinating session, not a change made here.

### 5.1 Existing code reused and new code needed

| Piece | Existing code it extends or reuses | New code (rough) |
|---|---|---|
| Feature kinds, per-feature parameters, fronts, Biot–Savart (4), isolation check, `candidate` edits | `AdvectingBlobs` in `fmeval/data/analytic.py` (its Gaussian loop, minimum image, centre draw); `physical_wavenumber_grid` | 90–120 lines in that class |
| Background (2) | the phase draw of `gaussian_impostor`, moved into `fmeval/wavenumbers.py` as one function both call; `radial_shells`; `derive_rng` | about 15 lines, minus 4 in the impostor |
| Candidate scored against the reference | `ForecastPairs.predictions()` interface; `evaluate.py` line 106 | a default `predictions()` returning `None` on `Trajectory` (`fmeval/data/base.py`, 3 lines), line 106 calls it for every reader (1 line) |
| Global candidates | `translate`, `translate_subpixel`, `gain`, `bias`, smoothing, noise, `gaussian_impostor`, `per_unit_time` | none |
| Known-answer tests | `tests/test_analytic_datasets.py`; closed forms beside `expected_response` in `tests/analytic_fields.py` | about 150 lines |
| Configurations | `configs/dataset/advecting_blobs.yaml` pattern | one `_feature_population.yaml` fragment and three configurations, about 60 lines |
| Option B script | the `branch_from_frame.py` pattern of `00_...`, Sect. 6a; kinet's `_pressure_poisson_solve` | about 50 lines, kept with the kinet runs |

One duplication found on the way: `tests/analytic_fields.py` builds its own periodised Gaussian
bump (3 × 3 images) beside the reader's minimum-image one. Building the test's bump from the
reader would leave one definition; that is the builder's call. Tests that assert
`advecting_blobs` provides only `density` would need updating when `FIELDS` grows (not checked).

## 6. What to store

Option A stores nothing; Option B follows `BUILD_ORDER.md` and `docs/recipes/add-a-dataset.md`.

- **Configurations (Option A, my proposal), 256², periodic, static unless stated:**
  `feature_population_bumps` (density; six bumps of heights 1, 0.8, 0.6, 0.4, 0.3, 0.2, $w = 0.02$
  (5.1 cells), centres on a 3 × 2 lattice 0.33 and 0.5 apart, above the $12w = 0.24$ isolation
  distance); `feature_population_vortices` (velocity and vorticity; eight vortices of peaks
  $\pm 1, \pm 0.7, \pm 0.5, \pm 0.3$, $w = 0.02$, on a 4 × 2 lattice 0.25 and 0.5 apart, signs
  paired so $\sum\Gamma = 0$); `feature_population_fronts`
  (pressure; a circle of radius 0.08, an ellipse 0.1 by 0.05 at 30°, a circle of 0.04, and one
  stripe along $(1, 0)$, jump 1.5, $\delta = 0.25$ cell). A time-dependent variant of each sets
  distinct velocities over a window in which the isolation check passes. Each `fields:` lists only
  the fields its features populate.
- **Evidence entry.** In `configs/cards/default.yaml`, `evidence_datasets`: "a known-answer check:
  every feature and every difference between candidate and reference is set in closed form, so the
  evidence is whether the metric reports the answer known before the run, and nothing about
  turbulence"; `evidence_dataset_properties`: `{periodic: true, ensemble: false}`. A dataset page
  `docs/datasets/feature_population.md` with the formulas of Sect. 3.
- **Option B.** The reference in the `kinet_raw` layout (`density`, `velocity`, `vorticity`,
  `(1, C, T, X, Y)` float64, `time`, `discretization`), candidates in the `forecast` layout, under
  `datasets/kinet/vortex_population/...`; the weakly compressible gauge pressure is not carried
  over (issue 101). As HDF5 attributes: the generator's full parameter list and seed, $\nu$, and the
  predicted merger ratios. Size: 2 001 frames of 256² with four channels (density, two velocity
  components, vorticity) at 8 bytes, about 4.2 GB (my arithmetic).

## 7. References

- Gallay, T. and Wayne, C. E. (2005). Global stability of vortex solutions of the two-dimensional
  Navier–Stokes equation. *Commun. Math. Phys.* 255, 97–129, https://doi.org/10.1007/s00220-004-1254-9;
  arXiv:math/0402449. **Read:** Sect. 1, Eqs. (7)–(9), in the arXiv HTML rendering (the first
  100 000 characters); volume and pages from the Springer listing via a search result.
- Meunier, P., Le Dizès, S. and Leweke, T. (2005). Physics of vortex merging. *C. R. Physique*
  6(4–5), 431–450, https://doi.org/10.1016/j.crhy.2005.06.003. **Read:** the full text, extracted
  by me from the journal's open PDF; the prose survived, the mathematical symbols did not, so the
  statements used (Lamb–Oseen convergence and the angular-momentum core size in Sect. 2.1, the
  critical ratio 0.22 in Sect. 3, the convective stage in Sect. 2.2) are quoted from the prose, and
  the contents of their Eqs. (1), (4) and (5) were not read.
- Engquist, B. and Yang, Y. (2022). Optimal transport based seismic inversion: beyond cycle
  skipping. *Commun. Pure Appl. Math.* 75(10), 2201–2244, https://doi.org/10.1002/cpa.21990;
  arXiv:2002.00031. **Read:** Eq. (2), the Sect. 1 sentence quoted, and the statement of
  Theorem 4.6 (Sect. 4.3) in the arXiv HTML rendering (first 100 000 characters); the journal's
  numbering was not checked against the arXiv one.
- Peyre, R. (2018). Comparison between W₂ distance and Ḣ⁻¹ norm, and localization of Wasserstein
  distance. *ESAIM: COCV* 24(4), 1489–1501, https://doi.org/10.1051/cocv/2017050. **Not opened**;
  cited as `proposals/EXP-wasserstein-background-ratio-sweep.md` cites it.
- Repository sources read in full or in the cited sections: `fmeval/data/analytic.py`;
  `fmeval/derived.py`; `fmeval/external/kinet_spectral.py`; `fmeval/wavenumbers.py`;
  `evaluate.py` (field selection, prediction); `degradations/{translate,gain,bias,gaussian_impostor}/degradation.py`;
  `tests/analytic_fields.py`; the Definition sections of the cards of `persistence_distance`,
  `shock_set_distance`, `wasserstein`, `increment_w1`, `spectrum_l2`, `max_error`; dataset specs
  00, 03 (Sects. 1–3.8, 5–6), 04 (Sect. 3.3), 05 (Sect. 3); the catalog entries B5, D7, D8, D9, G4,
  G10; the five proposals and issues 060, 073, 082, 086; kinet's
  `simulations/homogeneous_isotropic_turbulence/initialize.py` (Poisson pressure and density steps).

## 8. Confidence

- **Sure (measured with the repository's metrics, or exact algebra checked numerically):** the
  pointwise closed forms (5) and (6); the persistence diagram structure and the five bottleneck
  answers; the increment answers (permutation, removal, sign flip at a cell centre); the spectrum
  results, including that moving one feature of a population changes the spectrum; the straight-front
  ASSD of $s - \tfrac12$ or $s$; the pooled dilution; the ellipse rotation maximum $(a-b)\delta\phi$;
  the Biot–Savart round trip; the detector-firing thicknesses; the `wasserstein` convergence range
  and its approach to (7). These were measured on 128², one or two seeds and a few widths, not
  swept exhaustively.
- **Reasoning, not measured:** the $1/\sqrt2$ reduction of the firing thickness at 45°; the
  $\log(s/w)$ growth of (7); the near-Gaussian one-point law of the background; the isolation
  threshold of $12w$; the exact bounds with a background (short proofs, not run).
- **Cited but only partly read:** the forms of Meunier et al.'s Eqs. (1), (4), (5); I used the
  point-vortex rate and the Lamb–Oseen growth law from Gallay and Wayne instead. The critical ratio
  0.22 is from their prose, and depends on their angular-momentum definition of $a$, which I mapped
  to $a = \sqrt2 w$ by my own arithmetic.
- **Not checked:** whether kinet's `initial_state` route applies the HIT population corrector;
  whether pair A in Option B merges within 20 000 steps (onset is above the critical ratio, the
  duration was not read); the mutual drift of the pairs on the torus; which existing tests pin
  `advecting_blobs`' field list; and whether Hydra's command line accepts the nested `candidate`
  dictionary as written.

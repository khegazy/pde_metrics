# Dataset 07: known-answer transport pairs

**What this dataset is.** Pairs of positive, periodic density fields whose quadratic Wasserstein
distance is known exactly before any transport metric is run, so that a metric's value can be
checked against the true distance rather than against another approximation. Most of it is
already within reach of existing code: one option on the existing `advecting_blobs` reader
produces two-dimensional pairs with an exact answer, the existing `translate`,
`translate_subpixel` and `mean_field` degradations produce the candidates for the other cases,
and an exact one-dimensional solver, moved out of an existing test, supplies the answer for
fields that vary along one axis or are products of one-axis profiles. Nothing is simulated and
nothing is stored. Nothing here trains or evaluates a machine-learning model.

**Catalog clusters:** D9(a) (known-answer transport problems) and the exact one-dimensional
counterpart of D9(b) (the background-ratio sweep), as merged into build B6 item 2
(`FUTURE_EXPERIMENTS_CATALOG.md`, Sects. 2.1 and 3.1). **Metrics served:** `wasserstein` and
`h_minus_one` (built); the planned sliced Wasserstein distance (issue 048), Sinkhorn
divergences (issue 067), and transport between signed fields (issues 047 and 066), clearly
marked as planned wherever they appear. **Proposals served:**
the known-answer transport proposal (deleted once built, step 13 of `BUILD_ORDER.md`),
`EXP-wasserstein-background-ratio-sweep`, and the
"How it could be tested" sections of `MTR-wasserstein-full-newton-gmres`,
`MTR-wasserstein-largest-displacement`, `MTR-wasserstein-softplus-normalisation` and
`MTR-wasserstein-discrete-coarsened`. **Date:** 2026-11-26. **Author:** research sub-agent for
`BUILD_ORDER.md` step 13. "My derivation" marks results I derived and checked numerically;
"measured" marks numbers from scratch scripts run with the repository's `.venv` on 2026-11-26
(listed in Sect. 8); "my design" marks choices.

## 1. Purpose

`wasserstein` solves the periodic Monge–Ampère equation for the optimal map between two
densities (Saumier, Agueh & Khouider 2015, Eq. 4). Its only check against an independent exact
answer today is one family: a profile varying along x, shifted by an eighth of the domain, at a
peak of at most 2.33 times the mean (`metrics/wasserstein/test_metric.py`). Its card records
that the solve fails at higher contrast, and its code notes say that near-empty regions are
untested (`metrics/wasserstein/code_notes.md`, "For the next agent"). Every planned transport
metric needs the same thing: issue 048 asks that the sliced distance be validated "against the
exact Wasserstein distance on small cases", and issue 067 needs a reference against which to
measure the entropic bias of a Sinkhorn divergence. The background-ratio proposal needs the
distance of a translated feature as its background goes from dominant to negligible, which on
the torus has an exact answer only in the cases given here.

The dataset therefore supplies pairs with an exact distance that reach genuinely
two-dimensional maps, contrasts up to and beyond 10³ (the ratio of the largest to the smallest
density value), near-empty regions and several modes, at any grid size. Admitted as evidence,
it lets each transport card state, with numbers, where its metric returns the true distance and
where it stops doing so.

## 2. What the dataset must provide

- **Fields.** `density` only, positive and absolute. Velocity and vorticity are not involved;
  signed fields enter only through the planned formulations of Sect. 3.7.
- **Grid and boundary.** The unit square, periodic on both axes, at the reader's default of
  64² cells and at 128² and 256² for grid convergence. Square grids are enough for the
  transport metrics; a non-square grid is a free option of the reader.
- **Frames.** Frames that differ from one another, so the dataset is not excluded by the rule
  against frames that are scalar multiples (`BUILD_ORDER.md`, "The task"). In the
  `advecting_blobs` option the blobs move from frame to frame, so the exact distance changes
  per frame.
- **Pairs.** Either a reference with a paired candidate (Sect. 3.1), or a reference whose
  candidates are existing degradations with an exact answer at each severity (Sects. 3.2–3.4).
- **Known answers.** For every pair, W₂ to a relative accuracy of 10⁻¹⁰ or better, computed
  without the Monge–Ampère solver; for `h_minus_one`, the identity or bound that relates it to
  W₂ on that pair.
- **Seeds.** The `advecting_blobs` seed fixes the blob centres; nothing else is random.

Throughout, for densities $\rho_r$ (reference) and $\rho_c$ (candidate) on the torus $\Omega$
of area $|\Omega|$, $f = \rho_r / \langle \rho_r \rangle$ and $g = \rho_c / \langle \rho_c
\rangle$ with $\langle \cdot \rangle$ the mean over the domain, and the distance is the one
`wasserstein` reports (its card, Eq. 2):

$$
W_2(f, g)^2 = \inf_{T_\# f = g} \frac{1}{|\Omega|} \int_\Omega d_\Omega\bigl(x, T(x)\bigr)^2
f(x)\, dx , \qquad d_\Omega(x, y)^2 = \sum_j \min_{n \in \mathbb{Z}} |x_j - y_j - n L_j|^2 , \tag{1}
$$

with $d_\Omega$ the flat-torus distance on a box of sides $L_j$, $T_\# f = g$ meaning that $T$
carries the mass of $f$ onto $g$.

## 3. Option A, the analytic ideal (computed on the fly)

### 3.1 A1: a manufactured Monge–Ampère map, as an option on `advecting_blobs`

**The construction** (Saumier et al. 2015, Sect. 5.1, which validates their solver this way).
Choose a periodic potential $u$ and a target density $g$, and define the source density by the
Monge–Ampère equation in their form (Eq. 4):

$$
f(x) = g\bigl(x + \nabla u(x)\bigr) \, \det\bigl(I + D^2 u(x)\bigr) . \tag{2}
$$

**When the map is optimal.** If $u$ is periodic and $\Psi = |x|^2/2 + u$ is convex
($I + D^2 u$ positive semidefinite everywhere), then $T(x) = x + \nabla u(x)$ is the optimal
map from $f$ to $g$ for the torus cost of Equation (1), and its displacement $\nabla u(x)$ is
the shortest one, so $d_\Omega(x, T(x)) = |\nabla u(x)|$. The argument (my derivation, from two
sources): McCann (2001, the theorem "Optimal Maps" of the 1999 preprint) shows that on a
compact Riemannian manifold, for a source absolutely continuous with respect to volume, a map
$t(x) = \exp_x(-\nabla\psi(x))$ with $\psi$ a $c$-concave function for $c = d^2/2$ minimises the
transport cost to its own image, and that any other minimiser coincides with it almost
everywhere. On the flat torus, writing the Legendre transform of the convex $\Psi$ as
$|y|^2/2 + v(y)$ with $v$ periodic gives $-u(x) = \inf_y [d_\Omega(x, y)^2/2 + v(y)]$, so
$\psi = -u$ is $c$-concave, and the infimum is attained at the nearest lift of
$x + \nabla u(x)$. Cordero-Erausquin (1999), as stated in Saumier et al. (2015, Theorem 2.1),
gives the same map: additive, $\nabla\Psi(x + p) = \nabla\Psi(x) + p$, unique and invertible.
The distance is then the source-weighted mean square displacement (Saumier et al., Eq. 3, with
$T = x + \nabla u$):

$$
W_2(f, g)^2 = \frac{\langle f\, |\nabla u|^2 \rangle}{\langle f \rangle} , \qquad
\langle f \rangle = \langle g \rangle . \tag{3}
$$

The equality of the means follows from the change of variables $y = T(x)$, which is a bijection
of the torus. Equation (3) is evaluated by quadrature on the cell centres. For smooth periodic
integrands the trapezoidal rule converges faster than any power of the cell size, and when $u$
is a trigonometric polynomial and $g = 1$ the integrand is itself a trigonometric polynomial,
which the rule integrates exactly once the grid exceeds four times the highest mode.

**Measured:** for Saumier's own example (below), the quadrature at 512², 1024² and 2048² agrees
to all 15 printed digits, and with $g = 1$ the values at 8², 16² and 64² agree to the last digit.

**The potentials.** A sum of Fourier modes,

$$
u(x) = -\sum_j \frac{a_j}{|k_j|^2} \cos(k_j \cdot x + \varphi_j), \qquad
k_j = 2\pi\bigl(m_{j,x}/L_x,\; m_{j,y}/L_y\bigr), \quad \sum_j |a_j| < 1 , \tag{4}
$$

with integer $m_j$ and phases $\varphi_j$. Then $D^2 u = \sum_j a_j \hat k_j \hat k_j^{\mathsf T}
\cos(k_j \cdot x + \varphi_j)$, whose operator norm is at most $\sum_j |a_j|$, so the condition
on the right of (4) makes $I + D^2 u$ positive definite (my derivation, a sufficient condition
the reader checks deterministically). For one mode it is also necessary: the eigenvalues of
$I + D^2 u$ are $1$ and $1 + a\cos(\cdot)$.

Two closed forms follow (my derivations, each checked numerically to $4 \times 10^{-16}$):

- **One mode against the uniform density.** With $g = 1$ and one mode,
  $f = 1 + a \cos(k \cdot x + \varphi)$ and $|\nabla u| = (a/|k|) |\sin(\cdot)|$, so

  $$
  W_2 = \frac{a}{\sqrt{2}\,|k|} = \mathrm{H}^{-1}(f, 1), \qquad 0 \le a < 1 , \tag{5}
  $$

  for every lattice wavevector, axis-aligned or oblique. The second equality is the
  `h_minus_one` value of the single mode $a\cos(k\cdot x)$ (its card, Eq. 3), so the two
  metrics agree exactly on this pair at every amplitude, not only to first order. The density
  ranges from $1 - a$ to $1 + a$, a contrast of $(1+a)/(1-a)$: 999 at $a = 0.998$. The
  one-dimensional case is the worked example already in `test_metric.py` ($a = 0.5$, four cells).
- **Saumier's example.** Their Sect. 5.1 uses $u = (1/k)\cos(2\pi\gamma x_1)\sin(2\pi\gamma x_2)$
  and $g = 1 + \alpha \cos(2\pi\rho x_1)\cos(2\pi\rho x_2)$ on the unit square; the arXiv v2 text
  gives no values of $k$, $\gamma$, $\rho$, $\alpha$. Writing $\kappa = 2\pi\gamma$ and
  $\lambda = \kappa^2/k$, the eigenvalues of $D^2 u$ are bounded below by $-\lambda$, so the map
  is convex exactly when $\lambda < 1$, and with $g = 1$

  $$
  W_2 = \frac{\lambda}{\sqrt 2\, \kappa} = \frac{\lambda L}{2\sqrt 2\, \pi \gamma} . \tag{6}
  $$

  **Measured:** with $\rho = \gamma$ (1 and 3) the distance does not depend on $\alpha$ at all
  (agreement to 15 digits); with $\rho = 2\gamma$ it does (0.0371 against 0.0338 at
  $\lambda = 0.3$, $\alpha = 0.9$). A builder who wants $g$ to matter chooses $\rho \ne \gamma$.
  Saumier's product is the sum of two oblique modes, each with $a_j = \lambda$ in the notation of
  (4), so the sufficient bound of (4) admits it only for $\lambda < 1/2$; Equation (6) is the reference for a direct test.

**The option on `advecting_blobs` (my design).** The target $g$ is the existing blob density,
$g = 1 + A \sum_b \exp(-|x - c_b - u_b t|^2/2w^2)$ (`fmeval/data/analytic.py`): multi-modal,
with a contrast set by the existing `amplitude` option and moving from frame to frame. Three new
options:

1. **`potential`**: a list of modes $[m_x, m_y, a, \varphi]$ defining $u$ by Equation (4);
   absent by default, which leaves the reader unchanged.
2. **`reverse`** (default false): which side of the pair is the reference.
3. **`amplitude`** relaxed from "positive" to "non-negative", so that $A = 0$ gives $g = 1$
   and Equation (5).

With a potential, each frame's reference is $f$ of Equation (2), evaluated at the cell centres
with $\nabla u$ and $D^2 u$ in closed form and $g$ evaluated exactly at the displaced points
$x + \nabla u$ (no interpolation). The reader's `predictions()` returns the plain blobs $g$ on
the same frames, as `ForecastPairs.predictions()` does. With `reverse`, the two sides swap.
A method `transport_distance(t)` returns Equation (3) for frame `t`, computed on the grid
refined four times per axis. The test, not the pipeline, compares it with the metric.

**Measured with this construction** (blob width 0.06, $A \in \{0.1, 1, 3\}$, one mode
$m = (1, 1)$, $a \in \{0.3, 0.8\}$, frames at $t = 0$ and 5): the quadrature at 128², 256² and
512² agrees to 12 digits, the exact W₂ changes from frame to frame (0.06128 to 0.06504 at
$A = 3$, $a = 0.8$), and `wasserstein` at 64² agrees with it to a relative $10^{-6}$ or better
at contrasts up to 35.

**What it tests.** That `wasserstein` returns the exact distance for a genuinely
two-dimensional map with off-diagonal Hessian, a multi-modal target and a contrast that the
user dials up (through $a$ and $A$) until the solve fails; and, with `reverse`, that the
answer does not depend on which side is the reference.

**Limits.** The source $f$ is a deformed blob field, not a field of independent features; the
known answer exists only for the pair $(f, g)$, not for degradations of either.

### 3.2 A2: one-dimensional profiles on the circle, the exact solver

A density that varies along x only has a one-dimensional optimal map: a plan acting along y
would only add cost. On a circle of length $L$, lift each cumulative distribution function to
the line with $F(x + L) = F(x) + 1$, and write $F^{-1}$ for its quantile function. Delon, Salomon
& Sobolevski (2010) show that every locally optimal plan couples mass level $v$ of the source
with mass level $v + \theta$ of the target (their Sect. 2 and the theorem of Sect. 4.2 on
shifts), that the average cost

$$
C(\theta) = \int_0^1 \bigl| F^{-1}(v) - G^{-1}(v + \theta) \bigr|^2 \, dv \tag{7}
$$

(their Eq. 14) is convex in $\theta$ (the lemma that opens their Sect. 5), and that its global
minimum is the transport cost on the circle (the theorem at the end of Sect. 5). So
$W_2^2 = \min_\theta C(\theta)$, with $C$ divided by $L^2$ only if lengths are measured in
periods. Rabin, Delon & Gousseau (2011, Eq. 9) state the same formula for any power cost.

**How to evaluate it exactly (my design, measured).** The test in `test_metric.py` evaluates
Equation (7) on a uniform grid of 10⁵ mass levels. That is accurate for densities bounded away
from zero, but it is wrong where a density is nearly zero, because then the quantile function
jumps and the wrap-around penalty at $v + \theta \approx 0$ falls between grid levels. Measured:
on a periodised Gaussian of width 0.03 shifted by 0.1, whose exact answer is 0.1 (Sect. 3.3),
the level grid returns 0.1000253 and moves $\theta$ off zero. The remedy: read each density as
constant on its cells, so both quantile functions are piecewise linear in $v$ with knots at the
cumulative cell masses; merge the knots of $F^{-1}(v)$ and $G^{-1}(v + \theta)$, and integrate
the squared difference exactly on each interval, where it is a quadratic. Minimise over
$\theta \in [-\tfrac12, \tfrac12]$ with a bounded scalar search. Measured: the same pair then
gives 0.1 to $8 \times 10^{-14}$; a cell-constant reading on $2^{14}$ and $2^{16}$ cells
converges as the square of the cell size ($5.6 \times 10^{-9}$ to $3.5 \times 10^{-10}$ change)
and takes 0.14 s and 0.64 s per pair. The exact answer for a smooth profile is therefore the
value on $2^{16}$ sub-cells (relative error about $10^{-10}$), or its Richardson extrapolation
from $2^{14}$ and $2^{16}$.

**Two-dimensional fields with an exact answer through the circle solver** (my derivations):

- **A profile constant along y**, of any shape: the "stripe". Its exact W₂ under any translation
  along x is the circle answer; under a translation along y it is exactly zero.
- **A product of two profiles**, $f(x, y) = p(x)\,q(y)$, against $p'(x)\,q'(y)$. Because the
  squared torus distance is the sum of the squared circle distances along each axis, any
  coupling of the products induces couplings of $(p, p')$ and $(q, q')$, which bound its cost
  below, and the product of the two optimal one-dimensional plans attains that bound:

  $$
  W_2^2\bigl(p \otimes q,\; p' \otimes q'\bigr) = W_2^2(p, p') + W_2^2(q, q') . \tag{8}
  $$

  **Measured:** `wasserstein` on products of periodised Gaussians with a background (contrast
  120 to 715, 128², a translation of 4 or 8 cells along x and a width change along y) agrees
  with Equation (8) to $2 \times 10^{-7}$ or better.

**Profiles that are already defined** and serve here: $1 + a\cos(2\pi m x/L)$ (Equation (5) is
its circle answer against the uniform one; it is the `mode` kind of `tests/analytic_fields.py`);
the two-mode and peaked profiles $\exp(\beta\cos 2\pi x/L)$ of `test_metric.py`, with contrast
$e^{2\beta}$ (10³ at $\beta = 3.45$); and a bump of height 1 on a background $c$, the stripe of
Sect. 3.4.

**Candidates.** Existing degradations only: `translate` and `translate_subpixel` along x, y or
both (`axis: diag`), and `mean_field`. Their exact values come from Equations (7) and (8)
applied to the profile translated analytically, or to the uniform density. `translate_subpixel`
shifts the trigonometric interpolant of the sampled profile; for a profile resolved by the grid
the difference from the analytic shift is the profile's aliasing error, which I did not measure.

### 3.3 A3: translations

Translations deserve their own statement, because the obvious answer, W₂ = |s| for a shift
$s$, is right on the plane and usually wrong on the torus.

- **On the plane**, every density is at distance exactly $|s|$ from its translate: the
  translation costs $|s|^2$, and no plan costs less because the difference of the means bounds
  W₂ below (Jensen's inequality; elementary, my statement).
- **On the torus, for a density positive almost everywhere, W₂ is strictly less than $|s|$**
  for every $s$ with $0 < |s_j| < L_j/2$ (my derivation). By McCann (2001), the optimal map is
  $\exp_x(-\nabla\psi(x))$ with $\psi$ a function on the torus, hence periodic and Lipschitz, so
  $\int_\Omega \nabla\psi \, dx = 0$: the volume-averaged displacement is zero. The translation
  has volume-averaged displacement $s$, so it is not that map, and the unique optimum is
  cheaper. This is the content of Saumier et al.'s remark after their Theorem 2.1 that $u$ is
  periodic, which `metrics/wasserstein/research_notes.md` lists as not verified. **Measured:**
  for the optimal circle map of a bump on a background of 0.01 or 1, the volume-averaged
  displacement is $3.6 \times 10^{-8}$ and $1.5 \times 10^{-10}$, while the mass-weighted mean
  displacement is 0.168 and 0.0017. The research notes' open question is thereby answered.
- **A sufficient condition for W₂ = |s| on the torus** (my derivation): if the density vanishes
  outside a box of sides $\ell_j$ with $\ell_j + |s_j| \le L_j/2$, both densities lie in a box
  of sides at most $L_j/2$, on which the torus and plane distances coincide, so the plane
  answer holds. **Measured** on the circle: a $\cos^2$ bump of width 0.2 keeps $W_2/s = 1$ to
  $10^{-12}$ up to $s = 0.31$ and drops to 0.99969 at $s = 0.35$, so the condition is
  sufficient, not sharp. Such densities have empty cells, so `wasserstein` returns NaN on them
  by design; they serve the planned metrics.
- **The background-ratio regime change.** Engquist & Yang (2022, Theorem 4.6, arXiv numbering)
  prove, for a compactly supported one-dimensional density on a bounded interval with a
  background $c$ added before normalising, that $W_2^2$ is $O(s^2)$ for
  $|s| \le 1/c + |\mathrm{supp} f|$ and $O(|s|)$ beyond. Their theorem is asymptotic and not
  periodic. The stripe gives the exact periodic counterpart. **Measured**, $W_2^2/s^2$ for a
  Gaussian stripe of height 1 and width 0.03 on background $c$, shifts 0.01, 0.02, 0.05, 0.1,
  0.2, 0.3:

  | $c$ | $W_2^2 / s^2$ at the six shifts |
  |---|---|
  | 0 | 1.0000, 1.0000, 1.0000, 1.0000, 1.0000, 1.0000 |
  | $10^{-4}$ | 0.9982, 0.9982, 0.9982, 0.9982, 0.9980, 0.9978 |
  | 0.01 | 0.8572, 0.8571, 0.8564, 0.8544, 0.8481, 0.8385 |
  | 0.1 | 0.3517, 0.3514, 0.3494, 0.3433, 0.3241, 0.2966 |
  | 1 | 0.0256, 0.0254, 0.0245, 0.0217, 0.0148, 0.0097 |
  | 10 | 0.0004, 0.0004, 0.0004, 0.0003, 0.0002, 0.0001 |

  A large background lowers the quadratic coefficient by orders of magnitude, and the fall of
  $W_2^2/s^2$ with $s$ at $c \ge 0.1$ is the start of the linear regime (my reading).
- **Radial bumps (spec 06) have no closed form**, but a certified bracket (my derivation): the
  map $x \mapsto x_j$ to one axis does not increase distances, so W₂² is at least the sum over
  axes of the circle W₂² of the one-axis marginals, and the translation plan bounds it above by
  $|s|^2$. For a radial bump translated along x the lower bound is the circle answer for the
  bump's x-marginal. Spec 06's generator makes those fields; this spec supplies only the bound.

### 3.4 A4: the background-ratio sweep, exactly

`EXP-wasserstein-background-ratio-sweep` asks for bumps translated over backgrounds from
dominant to negligible. Spec 06 (`06_feature_population_generator.md`, written in parallel)
generates translated bumps on a background, and this spec does not add a second generator. What
it adds is the exact answer, which needs the bump to be a stripe or a product of profiles
(Sect. 3.2). **Request to spec 06 (my design):** that its bump shape include `stripe` (varying
along x only) and that its background be allowed to reach zero; if spec 06 does not include
them, `stripe` is a `shape` option on `advecting_blobs` of about six lines, built with whichever
of steps 12 and 13 lands first. The `amplitude` option already sets the background ratio,
because a density $1 + A\,G$ normalises to the same field as $1/A + G$. **Measured with the
repository's solver** on a Gaussian stripe of width 0.06, 128² cells: agreement with the circle
answer to $10^{-7}$ to $10^{-9}$ wherever the solve converges; NaN at background 0.1 for a
quarter-domain shift (contrast 11) and at background 0.03 from a shift of 8 cells (contrast 34).

### 3.5 A5: Gaussians, for the planned metrics

- **Plane.** For Gaussians $\mathcal N(m_1, \Sigma_1)$ and $\mathcal N(m_2, \Sigma_2)$ (Peyré &
  Cuturi 2019, Remark 2.31, Eqs. 2.41–2.42; Dowson & Landau 1982; Givens & Shortt 1984):

  $$
  W_2^2 = |m_1 - m_2|^2 + \operatorname{tr}\Bigl(\Sigma_1 + \Sigma_2 - 2\bigl(\Sigma_1^{1/2}
  \Sigma_2 \Sigma_1^{1/2}\bigr)^{1/2}\Bigr) , \tag{9}
  $$

  which for diagonal covariances reduces to the sum over axes of $(\sigma_{1,j} - \sigma_{2,j})^2$
  plus the squared mean difference.
- **Torus, axis-aligned.** A periodised Gaussian with diagonal covariance, and the
  minimum-image Gaussian `advecting_blobs` draws, are products of one-axis profiles, so
  Equation (8) gives the exact torus answer through the circle solver (my derivation). This
  holds only on an empty background: $c + G(x)G(y)$ is not a product.
- **How close the plane formula is** (measured, exact circle answer against Equation (9), one
  axis, widths and shift in domain lengths): widths 0.03 and 0.05, shift 0.1: relative
  difference $4 \times 10^{-9}$; widths 0.05 and 0.08, shift 0.2: $-1.5 \times 10^{-3}$; widths
  0.1 and 0.15, shift 0.2: $-9.8 \times 10^{-2}$. The torus answer is always the smaller.
- **Entropic transport (for Sinkhorn divergences, issue 067).** Janati et al. (2020, Theorem 1,
  Eqs. 13–14) give the entropic cost between Gaussians on the plane in closed form, for their
  regularisation $2\sigma^2 \mathrm{KL}(\pi \,\|\, \alpha \otimes \beta)$ (their Eq. 7):
  $\mathrm{OT}_\sigma = |m_1 - m_2|^2 + \operatorname{tr}\Sigma_1 + \operatorname{tr}\Sigma_2 -
  \operatorname{tr} D_\sigma + d\sigma^2(1 - \log 2\sigma^2) + \sigma^2 \log\det(D_\sigma +
  \sigma^2 I)$ with $D_\sigma = (4\Sigma_1^{1/2}\Sigma_2\Sigma_1^{1/2} + \sigma^4 I)^{1/2}$, and
  the debiased divergence $S_\sigma(\alpha, \beta) = \mathrm{OT}_\sigma(\alpha, \beta) -
  \tfrac12[\mathrm{OT}_\sigma(\alpha, \alpha) + \mathrm{OT}_\sigma(\beta, \beta)]$. A planned
  Sinkhorn metric's bias is then its value minus Equation (9), on narrow Gaussians where the
  torus correction above is negligible. Not checked numerically here.
- **Sliced Wasserstein (issue 048), plane.** Each projection of a Gaussian onto a unit vector
  $\theta$ is $\mathcal N(\theta\cdot m, \theta^{\mathsf T}\Sigma\theta)$, so its one-dimensional
  W₂² is $(\theta \cdot \Delta m)^2 + (\sqrt{\theta^{\mathsf T}\Sigma_1\theta} -
  \sqrt{\theta^{\mathsf T}\Sigma_2\theta})^2$. Averaging over $\theta$ uniform on the circle (the
  definition of Peyré & Cuturi, Eq. 10.13, with a normalised measure, my convention) gives
  $|\Delta m|^2/2 + (\sigma_1 - \sigma_2)^2$ for isotropic widths in two dimensions (my
  derivation). On the torus, issue 048 has not decided what a projection is; for the two axis
  directions the sliced cost of a product density is Equation (8) halved.

### 3.6 A6: hard cases, with their exact answers

| Case | Contrast reached | Exact answer from | Measured behaviour of `wasserstein` |
|---|---|---|---|
| One mode, uniform candidate (Eq. 5) | 999 at $a = 0.998$ | Eq. (5) | Exact to $4 \times 10^{-16}$ at every $a$; one Laplacian step solves it, so it does not test the iteration |
| Uniform reference, one-mode candidate (`reverse`) | 66 at $a = 0.97$ | Eq. (5) | 64²: $1.4\times10^{-7}$ at $a = 0.1$ to $8 \times 10^{-4}$ at $a = 0.9$ along x, $9.5 \times 10^{-3}$ oblique; 128²: $8 \times 10^{-9}$ to $5 \times 10^{-5}$, $3.3 \times 10^{-4}$ oblique. NaN at $a \ge 0.97$ |
| Saumier's example, $\rho = \gamma = 1$, $\alpha = 0.5$ | 431 at $\lambda = 0.9$ | Eqs. (3), (6) | $10^{-12}$ to $10^{-14}$ up to $\lambda = 0.9$; NaN at $\lambda = 0.95$ (contrast 1739) |
| Saumier, $\rho = 2$, $\alpha = 0.9$ | 434 | Eq. (3) | $2 \times 10^{-8}$; NaN at contrast 4946; reverse direction converges where forward failed in two of three cases, to $4 \times 10^{-3}$ and $2 \times 10^{-4}$ |
| Blob target with one-mode potential | 35 | Eq. (3) | $\le 10^{-6}$ at 64² |
| Stripe on a near-empty background | 11 to 34 | Eq. (7) | Fails at a quarter-domain shift at contrast 11 |
| Product of profiles | 715 | Eq. (8) | $\le 2 \times 10^{-7}$ |

Two findings for the `wasserstein` card (measured, not yet on the card): failure follows a
near-empty *candidate* far more than a high-contrast *reference* (the reference reaches 431 while
a candidate of contrast 66 fails); and where the solve converges its error falls by a factor
of 16 to 30 from 64² to 128². Multi-modal targets are the blob densities of
Sect. 3.1 and products of multi-bump profiles. Near-empty regions are reached by the stripe with
$c \to 0$, by $a \to 1$, and by $\lambda \to 1$.

### 3.7 Signed fields (for planned metrics only)

Issue 047 leaves the signed-field formulation open; these are known answers for whichever is
chosen (my derivations unless cited).

- **Kantorovich–Rubinstein norm (W₁) of a zero-mean signed field.** W₁ is a norm that remains
  valid for signed measures of equal total mass (Peyré & Cuturi 2019, Eq. 6.1 and the text after
  it). On the circle, $W_1 = \min_\alpha \int_0^L |F - G - \alpha|\,dx$ (Rabin, Delon & Gousseau
  2011, Eq. 10), the minimiser being a median. For $d = a\cos(k\cdot x)$ on the torus, with
  any lattice $k$ and the probability normalisation of Equation (1),
  $W_1 = 2a/(\pi |k|)$, against $W_2 = a/(\sqrt2 |k|)$ for the positive $1 + d$. The same
  value holds in two dimensions because a test function and a flow both depending only on
  $\hat k \cdot x$ attain it. **Measured:** $3.546241406 \times 10^{-2}$ numerically against
  $3.546241427 \times 10^{-2}$ in closed form ($a = 0.7$, $m = 2$, $2^{15}$ cells).
- **Add a constant and renormalise** (the linear normalisation, Engquist & Yang 2022, Eq. 2):
  a signed one-mode field plus $c > a$ is the positive one mode with amplitude $a/c$, so
  Equation (5) gives $W_2 = a/(c\sqrt2|k|)$ against the uniform field.
- **Exponential, softplus, or positive and negative parts** (Engquist & Yang, Eqs. 3–4; issue
  047's split): each maps a signed one-axis profile to positive one-axis profiles, possibly with
  empty cells, which the knot-based circle solver of Sect. 3.2 handles exactly.

## 4. Options B to D: what simulation or other data could add

No solver simulation produces a transport distance with a known answer, so no kinet or
OpenFOAM run belongs in this dataset. Three non-analytic sources add something.

- **Option B, an exact discrete solver on a coarse grid.** For pairs with no closed form (spec
  06's radial bumps, rotated Gaussians), the network-simplex solution of the discrete problem
  (Peyré & Cuturi 2019, Eq. 2.17), in POT as `ot.emd2` (Flamary et al. 2021). POT is not
  installed; it would be a new dependency in `pyproject.toml` and `uv.lock`, which issue 067
  says cannot be added at present. Its known defect (`MTR-wasserstein-discrete-coarsened`): for
  displacements below a cell it measures the grid, so it is a reference only for features that
  move many cells on empty backgrounds, the regime of the planned metrics.
- **Option C, a kinet frame reduced to one axis.** Average a `kinet_re5e4` density frame along
  y and broadcast it back: a stripe with kinet's real spectrum and background, whose exact W₂
  under any translation is Equation (7). It needs no new code beyond a stripe option and the
  existing reader, but it is a derived field, not a solver output, and averaging removes most of
  the fluctuation.
- **Option D, a Gaussian random field profile** (spec 09, step 10): a one-axis random profile of
  prescribed spectrum, exact under translation by Equation (7). It adds a broadband profile to
  the smooth ones above.

## 5. Recommendation

1. **First, move and replace the circle solver** (Sect. 3.2): the knot-based solver into
   `tests/conftest.py`, the inline level-grid solver of `test_metric.py` deleted in favour of it,
   and the single-mode worked example parametrised over $a$, wavevector and direction. This
   pins the exact range of the existing solver with no reader change.
2. **Then the `potential` option on `advecting_blobs`** (Sect. 3.1) with the one-line pairing
   change in `evaluate.py`: the only two-dimensional, non-separable exact answer, and the one
   evidence dataset of this spec.
3. **Then the stripe and product shapes** from spec 06's generator, with their translation
   ladders, which give the exact background-ratio sweep.
4. Gaussians, signed fields and Option B wait for the planned metrics they serve.

### 5.1 Existing code reused and new code needed

| Piece | Existing code reused | New code | Rough new lines |
|---|---|---|---|
| Pairing of a reference with a candidate | `ForecastPairs.predictions()` and the `prediction=` path of `fmeval.pipeline.run` | `evaluate.py` line 106 tests `hasattr(trajectory, "predictions")` instead of `isinstance(..., ForecastPairs)`, and the reader's `predictions()` may return None. Shared with spec 05 Option A; built once | 2 |
| Manufactured pairs | `AdvectingBlobs` and `ClosedFormTrajectory` (`fmeval/data/analytic.py`), its grid, cell centres, time axis, validation and seed | Options `potential` and `reverse`; amplitude allowed to be zero; the blob density evaluated at arbitrary points (the present loop over blobs, given points instead of `self.centres`, now with two callers); $u$, $\nabla u$, $D^2u$ of Eq. (4); `predictions()`; `transport_distance(t)` | 60 |
| Circle solver | The quantile construction of `test_metric.py` | Rewritten with exact piecewise integration, moved to `tests/conftest.py`; the test's inline version deleted | 35 new, 20 deleted |
| Candidates for stripes and products | `translate`, `translate_subpixel`, `mean_field`; the ladder in `configs/degradation/default.yaml` | None | 0 |
| Stripe and product shapes | Spec 06's generator, or `advecting_blobs` | A `shape` option, only if spec 06 lacks it | 6 |
| Tests | `test_metric.py` of `wasserstein` and `h_minus_one`; `tests/test_analytic_datasets.py` | Eq. (5) parametrised in both directions; Eq. (3) against the metric on two frames; Eq. (7) and (8) against the metric on a stripe and a product; Eq. (6) against the quadrature | 60 |
| Dataset configs | `configs/dataset/advecting_blobs.yaml` | `transport_manufactured.yaml` (format `advecting_blobs`, one potential mode $m = (1,1)$, $a = 0.8$, amplitude 1) and `transport_manufactured_contrast.yaml` ($a = 0.95$, amplitude 3) | 30 |
| Evidence registration | `configs/cards/default.yaml` | Two entries in `evidence_datasets` and `evidence_dataset_properties` | 8 |
| Dataset page | `docs/datasets/` pattern | One page | 50 |

`tests/analytic_fields.py`, which catalog item B6 named as the home of these pairs, is not
extended: under the rule that every dataset built here is an evaluation dataset, the pairs live
in the reader, and that fixture keeps its present role as the oracle for the pointwise norms.

## 6. What to store

Nothing is stored; every field is computed when read (`fmeval/data/analytic.py`). Following
`docs/recipes/add-a-dataset.md`:

- **Fields:** `density` (positive, absolute). No pressure, velocity or vorticity.
- **Grid and boundaries:** unit square, `("periodic", "periodic")`, 64² by default, 128² and
  256² by override; non-square grids allowed.
- **Frames:** the reader's default 21 frames from $t = 0$ to 10, the blobs moving between them.
- **Seeds:** `seed` (default 0) fixes the blob centres; recorded in `meta` with the potential.
- **Known answers:** `transport_distance(t)` per frame (Equation (3) at four times the grid);
  the circle solver for stripes and products.
- **Evidence label (my wording):** "an analytic check: evidence that a transport metric returns
  the exact transport distance on a pair where it is known, and up to which contrast it does so;
  nothing about turbulence". `evidence_dataset_properties`: periodic true, ensemble false.
- **Window:** all frames; there is no developed-flow period to choose.

## 7. References

- Saumier, L.-P., Agueh, M. & Khouider, B. (2015). An efficient numerical algorithm for the L²
  optimal transport problem with periodic densities. *IMA J. Appl. Math.* 80(1), 135–157.
  doi:10.1093/imamat/hxt032; arXiv:1009.6039. **Full text of the arXiv v2 LaTeX source read**;
  numbering counted from it (Eqs. 1–6, Theorem 2.1 and the remark after it, Sect. 5.1), not
  checked against the journal.
- Cordero-Erausquin, D. (1999). Sur le transport de mesures périodiques. *C. R. Acad. Sci.
  Paris Sér. I Math.* 329, 199–202. **Not opened**; cited through Saumier et al., Theorem 2.1.
- McCann, R. J. (2001). Polar factorization of maps on Riemannian manifolds. *Geom. Funct.
  Anal.* 11(3), 589–608. doi:10.1007/PL00001679. **Read: the 1999 preprint** (MPI MiS Leipzig
  preprint 41/1999), as text extracted from its PDF in which theorem numbers were illegible; the
  two theorems titled "Optimal Maps" and the Introduction were read. The flat torus is not
  discussed in what I read; its application here is my derivation.
- Delon, J., Salomon, J. & Sobolevski, A. (2010). Fast transport optimization for Monge costs on
  the circle. *SIAM J. Appl. Math.* 70(7), 2239–2258. doi:10.1137/090772708; arXiv:0902.3527.
  **Full text of the arXiv LaTeX source read** (Sects. 2, 4.2 and 5; Eq. 14), not compiled, so
  lemma and theorem numbers are cited by section.
- Rabin, J., Delon, J. & Gousseau, Y. (2011). Transportation distances on the circle. *J. Math.
  Imaging Vis.* 41(1–2), 147–167. doi:10.1007/s10851-011-0284-0; arXiv:0906.5499. **Full text of
  the arXiv/HAL LaTeX source read**; Eqs. 9 and 10 counted from it. Volume, pages and DOI
  checked against the publisher record.
- Engquist, B. & Yang, Y. (2022). Optimal transport based seismic inversion: beyond cycle
  skipping. *Commun. Pure Appl. Math.* 75(10), 2201–2244. doi:10.1002/cpa.21990;
  arXiv:2002.00031. **Full text of the arXiv LaTeX source read**; Theorem 4.6 counted from it
  (Sect. 4: Assumption 4.1, Theorem 4.2, Remark 4.3, Corollary 4.4, Definition 4.5, Theorem
  4.6); Eqs. 2–4 as the repository's proposals number them.
- Peyré, R. (2018). Comparison between W₂ distance and Ḣ⁻¹ norm, and localization of Wasserstein
  distance. *ESAIM: COCV* 24(4), 1489–1501. doi:10.1051/cocv/2017050; arXiv:1104.4631. **Full
  text of the arXiv LaTeX source read** (Theorem 1, Lemma 2, Corollary 3, Theorem 5, the
  linearisation Eq. 5); numbering as in the `h_minus_one` card.
- Villani, C. (2003). *Topics in Optimal Transportation*. AMS, Graduate Studies in Mathematics
  58. **Not opened**; Sect. 7.6 is cited by Peyré (2018) for the linearisation.
- Peyré, G. & Cuturi, M. (2019). Computational optimal transport. *Found. Trends Mach. Learn.*
  11(5–6), 355–607. doi:10.1561/2200000073; arXiv:1803.00567. **Full text of the arXiv source
  read and compiled once** for the numbering: Eq. 2.17, Eq. 2.18, Prop. 2.3, Remark 2.30,
  Eq. 2.37, Remark 2.31, Eqs. 2.41–2.42, Eq. 6.1, Sect. 10.4 and Eq. 10.13.
- Dowson, D. C. & Landau, B. V. (1982). The Fréchet distance between multivariate normal
  distributions. *J. Multivariate Anal.* 12(3), 450–455. **Not opened**; bibliographic record
  checked.
- Givens, C. R. & Shortt, R. M. (1984). A class of Wasserstein metrics for probability
  distributions. *Michigan Math. J.* 31(2), 231–240. **Not opened**; named after the task's
  brief and the literature, details not checked.
- Janati, H., Muzellec, B., Peyré, G. & Cuturi, M. (2020). Entropic optimal transport between
  unbalanced Gaussian measures has a closed form. *Advances in Neural Information Processing
  Systems 33*. arXiv:2006.02572. **Full text of the arXiv source read and compiled** (Theorem 1,
  Eqs. 7, 13, 14; the Sinkhorn divergence of their Sect. 3).
- Flamary, R., Courty, N., et al. (2021). POT: Python Optimal Transport. *J. Mach. Learn. Res.*
  22(78), 1–8. **Abstract and record only.**
- Repository: `metrics/wasserstein/` (card, `metric.py`, `test_metric.py`, research and code
  notes), `metrics/h_minus_one/card.md`, `fmeval/data/analytic.py`, `fmeval/data/forecast.py`,
  `evaluate.py`, `degradations/translate*/`, `degradations/mean_field/`, issues 047, 048, 066,
  067 and 139, and the proposals named in the front matter.

## 8. Confidence

- **Sure** (derived and checked to round-off): Equation (5) for every wavevector and amplitude
  tested, in both metrics; Equation (6); the quadrature of Equation (3); Equation (8) on the
  products tested; the zero volume-averaged displacement on the circle; the exact-integration
  circle solver against translations of compactly supported bumps (to $10^{-12}$); the W₁
  single-mode value.
- **My derivations, argued but resting on sources I read only in part:** that convexity of
  $|x|^2/2 + u$ with periodic $u$ makes $x + \nabla u$ optimal on the torus, and that
  translation is never optimal for a positive density. Both rest on McCann's "Optimal Maps"
  theorems, read in a degraded text extraction; Cordero-Erausquin (1999) was not opened.
- **Measured, scratch scripts not kept in the repository** (in this session's scratchpad,
  `spec07/checks/`): every relative error and contrast in Sects. 3.1–3.6; they were run once and
  should be rerun by the builder's tests.
- **Not verified:** the journal numbering of every arXiv source; Givens & Shortt's details; the Janati et al. formula numerically; the aliasing error of
  `translate_subpixel` on a stripe; whether spec 06 will include a stripe shape.
- **Least sure of:** the reading of the background table as the start of the linear regime;
  Engquist & Yang's theorem is asymptotic on a bounded interval and gives no constant.

**Connections.** The manufactured map is the method of manufactured solutions applied to a
transport metric. The translation result on the torus is the periodic form of the seismic
cycle-skipping question that motivated Engquist & Yang. The single-mode identity W₂ = H⁻¹ is a
case in which Peyré's linearisation is exact at finite amplitude.

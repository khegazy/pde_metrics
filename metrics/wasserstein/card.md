---
name: wasserstein
kind: metric
---

## Definition

Let $\rho_r$ and $\rho_c$ be the reference and candidate densities on a periodic box
$\Omega$ of $N$ cells with spacing $h_j$ along axis $j$, and $\langle \cdot \rangle$ the mean
over cells. Each is divided by its own mean, the constant scaling that gives two fields equal
mass [@engquist2014] (Sect. 2.2):

$$
f = \frac{\rho_r}{\langle \rho_r \rangle}, \qquad g = \frac{\rho_c}{\langle \rho_c \rangle} \tag{1}
$$

so that $f\,dx/|\Omega|$ and $g\,dx/|\Omega|$ are probability measures on the torus. The
metric is their quadratic Wasserstein distance, the square root of the least mean squared
distance the mass of $f$ must travel to become $g$ ([@peyrecuturi2019], Eq. (2.18), a
distance between probability measures by their Prop. 2.3; [@engquist2014], Sect. 1, for
this form):

$$
W_2(f, g)^2 = \inf_{T_{\#} f = g} \; \frac{1}{|\Omega|} \int_\Omega
\bigl| x - T(x) \bigr|^2 f(x) \, dx \tag{2}
$$

where $T_{\#} f = g$ means that $T$ carries the mass of $f$ onto $g$, and distances are taken
on the torus. For densities bounded away from zero the optimal map is
$T(x) = x + \nabla u(x)$ with $u$ periodic. [@saumier2015] state in Theorem 2.1, after
Cordero-Erausquin, that the optimal map is additive, $\nabla\Psi(x + p) = \nabla\Psi(x) + p$, and
in the remark after it that this makes $\nabla\Psi - x$ the gradient of a periodic function.
The test against the exact circle transport below, at shifts where the optimal rotation is
not zero, would fail if a uniform displacement were missing. $u$ solves the Monge–Ampère
equation ([@saumier2015], Eq. (4))

$$
g\bigl(x + \nabla u(x)\bigr) \, \det\bigl(I + D^2 u(x)\bigr) = f(x) \tag{3}
$$

so that Equation (2) becomes the mean over cells of a transport cost density, which is the
companion map:

$$
W_2(f, g) = \bigl\langle f \, |\nabla u|^2 \bigr\rangle^{1/2} \tag{4}
$$

**How Equation (3) is solved.** By the periodic damped Newton method of [@saumier2015]
(Eq. (6)), from $u_0 = 0$:

1. **Evaluate.** $f_n = g(x + \nabla u_n) \det(I + D^2 u_n)$, then replace $f_n$ by
   $f_n - \langle f_n \rangle + 1$ so that the residual $f - f_n$ has zero mean
   ([@saumier2015], Eq. (14)).
2. **Stop** when the root mean square of $f - f_n$ is at most $10^{-12}$, a fraction of the
   mean density, and report Equation (4) with $u_n$.
3. **Step.** Solve $\Delta \theta_n = (f - f_n)/g(x + \nabla u_n)$, re-centred to zero
   mean, by FFT.
4. **Damp.** Set $u_{n+1} = u_n + \theta_n/\tau$ with the first of $\tau = 1, 2, 4, \dots$
   (at most $2^{30}$) that lowers the root mean square residual and keeps $I + D^2 u$
   positive definite.

Step 3 replaces their linearised operator ([@saumier2015], Eq. (5)) by its leading term,
$g\,\Delta$, with $g$ divided out cell by cell. That is mine: their Sect. 3.3 says only that a
simpler equation can *sometimes* replace the full one, and their $\tau = 1$ in Sect. 5.1 was
obtained with the full operator. Step 4 chooses their damping $\tau$ adaptively, also mine:
their proof needs $\tau$ large enough and $I + D^2 u_n$ positive definite at every step
(Sect. 3.3) and gives no value. In two dimensions the determinant of steps 1 and 4 is
$(1 + u_{xx})(1 + u_{yy}) - u_{xy}^2$, and positive definiteness is $1 + u_{xx} > 0$ with a
positive determinant (Sylvester's criterion), both from the three distinct second
derivatives; in any other dimension both come from the eigenvalues of $I + D^2 u$. The
answer is fixed by the residual of step 1, so these
choices change the number of iterations and not the value: over the 9499 values of the
kinet evidence run, the plain Laplacian step and this one differ by a relative
$5 \times 10^{-11}$ in the median and $1.4 \times 10^{-6}$ at worst, both far below the three
figures the tables report. Without step 3's division and step 4's damping the iteration overshoots, and
diverges, once the candidate density exceeds about twice its mean. Derivatives of $u$ are spectral, with the wavevectors
$k_j = 2\pi\,\mathrm{fftfreq}(N_j, h_j)$ that [h_minus_one](../../metrics/h_minus_one/card.md)
uses; [@saumier2015] also solve the linear step by FFT (Sect. 4.2). The candidate is
evaluated at the displaced points by a periodic cubic B-spline. That is my choice: they use
nearest-neighbour values and name linear interpolation as the common alternative (Sect. 4).
If the solve has not converged after 500 iterations, or no damping lowers the residual,
the value is NaN with a warning that says which. Kinet density needs 4 to 7 iterations.
Limitations gives the measured range in which the solve converges. A cell
that is not positive and finite in either field makes the value NaN: Equation (2) is
defined between measures, and any value given to a signed field would be one of the
signed-field formulations that `issues/047` leaves open.

`test_metric.py` checks the solve against an independent one. For a density that varies
along one axis only, the transport is one-dimensional, and on a circle its exact value is the
least, over a rotation of the mass levels, of the mean squared distance between the two
quantile functions ([@delon2010], Sect. 2). On two 256-cell profiles moved by an eighth of
the domain, one between 0.63 and 1.37 times its mean and one peaking at 2.33 times its mean
with a maximum ten times its minimum, the two agree to within the test's relative tolerance
of $2 \times 10^{-4}$.

**Why a continuous solve and not a transport between cells.** Treating each cell as a point
mass and solving the discrete problem exactly is the standard alternative, but on a density
whose displacements are smaller than a cell it measures the grid. Mass then moves a whole
cell or not at all, so the squared distance grows with the size of the change rather than
with its square. For a 1-D density $1 + \epsilon \cos(2\pi x)$ against the uniform one on
cells of size $h$, the discrete squared distance is about $h\epsilon/\pi^2$ against the
continuous $\epsilon^2/(8\pi^2)$, a ratio of $8h/\epsilon$, while the continuous displacement
$\epsilon/2\pi$ is below a cell. This derivation is mine. It is
also unaffordable here: one $256 \times 256$ pair is a $65\,536 \times 65\,536$ cost
matrix. Equation (3) has neither problem, because the displacement $\nabla u$ is a
continuous field.

**What it is close to on a near-uniform density.** For densities between $a$ and $b$ times
the volume measure, Theorem 5, Eq. (17) and Corollary 3 of [@peyre2018] bound it by the
$\dot H^{-1}$ seminorm $H$ of $f - g$, which `h_minus_one` computes as a root mean square:

$$
b^{-1/2} \, H \;\le\; W_2(f, g) \;\le\; 2\,a^{-1/2} \, H \tag{5}
$$

with the lower bound for the flat torus, where the Ricci curvature is zero. These bounds
alone are loose: on kinet density, whose normalised values lie between about 0.96 and 1.007,
they allow a ratio between about 1 and 2. What makes the two close is the linearisation:
as $f - g$ shrinks, $W_2$ equals the $\dot H^{-1}$ norm weighted by the reference density
([@peyre2018], Eq. (5)), and that weighted norm lies within $b^{-1/2}$ and $a^{-1/2}$ of $H$
([@peyre2018], Lemma 2), so to first order the factor 2 drops out. This step is my reading of
Peyre's results, not a theorem he states. `test_metric.py` checks Equation (5), which is a
consistency check and not a tight one. `h_minus_one` is not mass-normalised, so the two values
also differ by the factor $\langle\rho\rangle$, which is close to 1 on kinet density.

**Shift and background.** The property that recommends this distance for a displaced
feature is that $W_2^2$ of a signal moved by $s$ is $s^2$ whatever its profile
([@engquistyang2022], Sect. 1; [@engquist2014], Sect. 1). That holds for a signal on an empty
background. A density is a fluctuation on a large positive background. That is the "linear
normalisation" of [@yang2018] (section "Data normalization", Sect. 3.1 in the arXiv copy,
Eq. (27)), which they report makes the misfit non-convex in shifts. [@engquistyang2022]
(Theorem 4.6) show, for a compactly supported one-dimensional signal on a background $c$, that
$W_2^2$ is $O(s^2)$ only for shifts below about $1/c$ plus the width of the signal and $O(s)$
beyond. Their theorem does not cover a periodic field that fills the domain, as density does.
What applies here is the linearisation above. For a shift $s$ along $x$ small against the
density's scales, $f(x - s) - f \approx -s\,\partial_x f$, and the $\dot H^{-1}$ norm of
$\partial_x f$ is $(\sum_{\mathbf{k}} (k_x/|\mathbf{k}|)^2 |\hat f_{\mathbf{k}}|^2)^{1/2}$, at most the
root mean square of $f - 1$. So $W_2$ is about $s$ times a number no larger than the relative
fluctuation of the density, not $s$ itself (my derivation).

### Boundary handling

Periodic on every axis. The domain is the torus: the optimal map is $x$ plus the gradient of
a periodic function, derivatives are taken by FFT, and the candidate is interpolated with
wrap-around (`scipy.ndimage.map_coordinates`, `mode="grid-wrap"`), so mass leaving one side
enters the other. The metric therefore declares `requires_periodic`, and the harness does not
run it on a dataset with a non-periodic axis, such as the Sod shock tube.

### How its field reports it

Three communities use this distance, and each evaluates it differently.

- **Seismic inversion**, where $W_2^2$ is a misfit to be minimised. Its standard figure is the
  misfit against the shift of a signal, $L_2^2$ and $W_2^2$ between a wavelet and its shifted
  copy drawn against the shift $s$ ([@engquist2014], Fig. 1; reprinted as [@engquist2016],
  Fig. 1, with the convexity in $s$ stated as their Theorem 1); the same paper draws the misfit
  over the parameters of a layered model (Fig. 3) and repeats the shift test with noise
  (Fig. 4). The card's first figure is this comparison: the damage against the applied
  translation beside the pointwise errors, on log-log axes. It draws $W_2$, the registered
  number, where they draw its square; on log-log axes a square doubles the slope and changes no
  ordering. On density here the background makes the growth with the shift far weaker than
  theirs (Definition, "Shift and background").
- **Numerical optimal transport**, where a solver is validated against a known answer.
  [@saumier2015] (Sect. 5.1, Fig. 1) choose the potential and one density, compute the other
  from Equation (3), and report the error of the computed potential against Newton iterations
  on grids of $16^2$ to $256^2$, with the observed order of accuracy in the text.
  `test_metric.py` checks the solve against the exact transport on the circle (Definition); the
  manufactured two-dimensional problem is written up in
  [EXP-wasserstein-known-answer-transport](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-wasserstein-known-answer-transport.md).
- **Optimal-transport analysis** relates $W_2$ to the $\dot H^{-1}$ norm (Equation (5),
  [@peyre2018]); the check is the comparison with [h_minus_one](../../metrics/h_minus_one/card.md),
  computed on density in the same runs. A density whose fluctuation is not small against its
  mean, where the two separate, is written up in
  [EXP-wasserstein-background-ratio-sweep](https://github.com/khegazy/pde_metrics/blob/main/proposals/EXP-wasserstein-background-ratio-sweep.md).

**The transport map is not stored.** The displacement $\nabla u$ is drawn as arrows in a
seismic registration example ([@engquist2014], Fig. 2(d)) and for closed-form maps in a
textbook ([@peyrecuturi2019], Fig. 2.12), both as illustrations; [@saumier2015] draw none, and
no source read evaluates a distance by its map. On kinet density the displacements are far below
a cell, so an arrow plot would show little. The map would be a second, named field companion of
this metric; the cost density $f |\nabla u|^2$, the companion that is stored, already shows where
mass moves and how far.

**The experiments.** Misfit against shift: the translation axes of the degradation ladder on
`kinet_re5e4` (`translate_x`, `translate_subpixel`). The metric also runs on density on the
Reynolds ladder and on `forecast_re5e4`. It is not run on `synthetic_ensemble`, whose density is
a signed pattern (`card.yaml`).

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence wasserstein --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

![the metric against time: the clean field's own history in black and each strength of the operator applied at each time, or a real forecast's error against its lead time, one panel per start and one line per run](_generated/response_along_time__dataset-forecast_re5e4__field-density__along-lead.svg)

*As this metric's own field draws it, from run `comparison_1793811840`.* wasserstein on density against lead time, the physical time since the forecast started, one panel per start and one line per run, darker the finer the run's grid. Each point is one prediction step of one forecast.

![how the metric responded to each degradation, by field: rank correlation, separation of neighbouring strengths, damage per unit of field change, and the bound on its largest response](_generated/sensitivity_profile.svg)

Four measured statistics for wasserstein, one row per degradation grouped by family and one marker per field. From left: the rank correlation between the metric and the applied strength within a frame, with the line showing the resampling interval; the separation of neighbouring strengths as Cliff's delta, where 0 means the metric cannot tell one strength from the next and the faint ticks at 0.12, 0.28 and 0.42 are Vargha and Delaney's small, medium and large anchors, for scale and not as grades; the damage charged per unit of field change at the harshest strength; and the upper confidence bound on the largest damage, beside the fixed margin of 0.05. A hollow marker is a field and degradation on which that bound lies below the margin, so the response is provably small. A missing marker is a statistic the analysis withheld, as the rank correlation is on an axis the metric is invariant to.

![median damage against severity level, one panel per degradation family and field, on one shared scale](_generated/response_curves.svg)

Median damage over frames against severity level for wasserstein, one row per family of degradation and one column per field, on one shared scale. The solid grey line is damage 1, the anchor (by default the field's own mean); the dotted black line is the damage assigned to the fake prediction with the right spectrum, where the run included it. The hollow black ring marks the first level at which the metric has moved a tenth of the way to the anchor. Hollow grey markers are strengths excluded for repeating a milder one or for doing nothing. Degradations with three or fewer usable levels are drawn as markers only; points beyond 2 either side are drawn as triangles at the edge. Damage is negative where a degradation moves the metric away from the anchor, as noise raises a single-field quantity the field's mean sets to zero.

**Trend: does the response follow the degradation?**

| test family | field | degradations | rank correlation | fraction of frames in order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| Displacement | density | 3 | 1 | 1 | 0.943 to 0.96 |
| Cell-value distortion | density | 2 | 1 | 1 | 0.93 to 0.97 |
| Resolution loss | density | 3 | 1 | 1 | 0.865 to 1 |
| Smoothing | density | 5 | 1 | 1 | 0.963 to 0.974 |
| Spectral filtering | density | 5 | 1 | 1 | 0.548 to 0.968 |
| Noise | density | 2 | 1 | 1 | 1 |

**Reactivity: how far does it move?**

| test family | field | change from clean at the harshest strength | elasticity | first strength detected |
|---|---|---|---|---|
| Displacement | density | — | 0.999 to 1 | level 3 |
| Cell-value distortion | density | — | 1 | level 3 |
| Resolution loss | density | — | 1.4 to 2.14 | level 3 |
| Smoothing | density | — | 1.81 to 1.92 | level 3 |
| Spectral filtering | density | — | 1 to 6.71 | level 1 |
| Noise | density | — | 0.997 | level — |
| trap test: fake prediction, right spectrum | density | — | — | damage 1.33 |

**Consistency: how much does it vary from snapshot to snapshot?**

| test family | field | consistency, in the strength's units | snapshots per independent block |
|---|---|---|---|
| Displacement | density | 0.0531 to 0.316 | 1 to 16 |
| Cell-value distortion | density | 0.0137 to 0.0299 | 1 to 19 |
| Resolution loss | density | 0.388 to 1.72 | 1 to 20 |
| Smoothing | density | 0.00552 to 0.0139 | 17 to 19 |
| Spectral filtering | density | 0.0137 to 0.133 | 1 to 21 |
| Noise | density | 0.00993 | 1 to 19 |

One row per family of degradation and physical field; a cell gives the range over the degradations in that family. **Trend.** The rank correlation is the Spearman correlation between the strength and how far the metric has moved from its value on the undegraded field of the same frame, in the one direction it moves under that degradation, computed inside a single frame. A value of 1 means every strength moved it further than the last in every frame, whichever way it moves; a response that scatters to both sides scores near 0. The fraction of frames in order counts the frames with no exception. The weakest gap is the smallest Mann-Whitney overlap between two neighbouring strengths across frames: 1 means they never overlap, 0.5 that they cannot be told apart. **Reactivity.** The change from clean is the median, at the harshest strength, of the departure from the undegraded value of the same frame over the size of that value: 0.3 means 30%. It does not exist for this metric, whose undegraded value is exactly zero; the damage below is its relative reading. The elasticity is the percentage change of that departure per percentage change in strength over the mildest strengths. First strength detected is the mildest at which the metric has moved a tenth of the way to the anchor; **damage** reads that 0-to-1 scale as a number. A dash means the measurement is not defined there. A metric's reactivity scales with the power it is expressed in: mean squared error's elasticity is twice root-mean-square error's, though the two carry the same information, so compare magnitudes across metrics with that in mind. **Consistency** is how much the response varies from snapshot to snapshot relative to its size, in the strength's units; the snapshots of one trajectory are correlated, and the last column is how many consecutive snapshots one independent block spans.

These tables report what was measured and grade none of the measurements. What the numbers mean for this metric is written in the subsections below, beside the test that produced each number.

**Profile.**

| field | selectivity | charges most for | charges least for | response provably below 0.05 at 90% on | elasticity to a sub-pixel shift, against severity (distance) | compute cost (x cheapest in this run) |
|---|---|---|---|---|---|---|
| density | 0.592 | `band_attenuate` | `bias` | `additive_noise` `band_attenuate` `bias` `coarsen` `coarsen_bandlimited` | 1 | 1.09e+03 |

One row per physical field. **Selectivity** is how concentrated the metric's response is on a few degradations, measured per unit of field change: 0 means it charges every degradation the same, as mean squared error does by construction, and values toward 1 that one degradation carries most of it. **Charges most and least for** name the two ends of that profile. **Response provably below** lists degradations on which the upper confidence bound of the largest damage lies below the margin -- an equivalence test, so an entry says the response is provably small, not merely not significant; a dash means no degradation met the bound. **Elasticity** is the slope of log damage against log shift over the smallest shifts: 1 means damage grows in proportion to the shift, 2 with its square. **Compute cost** is wall-clock per evaluation over the cheapest metric and field in the same run.

<!-- END GENERATED performance -->

## Intuition

The metric treats each density as a pile of mass spread over the domain and asks how far,
on average, that mass would have to travel to turn one pile into the other, moving it as
cheaply as possible. A prediction that has the right structures in slightly the wrong places
needs only short moves and scores little. A prediction whose mass is spread quite
differently needs long moves and scores a lot. Each density is first divided by its own
average, so only the arrangement of mass counts, not how much there is.

It works by finding the cheapest way of moving the mass. That plan has a special form: every
small parcel moves in a straight line, along the slope of a single smooth function. The
metric solves for that function a few times over, each pass correcting where the moved
reference still differs from the candidate. It reports the root mean square distance moved,
in the grid's units of length.

Worked example: on a four-by-four grid, the reference's four columns hold 1.5, 1, 0.5 and 1
times the average density, and the candidate is uniform.

```
reference            candidate      result
1.5  1  0.5  1       1  1  1  1
1.5  1  0.5  1       1  1  1  1     0.225 cells
1.5  1  0.5  1       1  1  1  1
1.5  1  0.5  1       1  1  1  1
```

Mass slides sideways out of the
heavy column and into the light one. The parcels halfway between them travel furthest,
about a third of a cell, and the parcels at the centres of the heavy and light columns do
not move. The root mean square distance moved, weighted by mass, is 0.225 cells.

It ignores the total amount of mass, and it has no value where either field is zero or
negative, because neither is then a pile of mass.

## Reading the output

- **Range and units.** From zero up to at most half the domain's diagonal, in the grid's
  units of length: cells on kinet, whose spacing is 1.
- **Direction.** Lower is better. Zero means the two normalised densities are identical.
- **What is a good value.** A distance moved, so compare it with the scales of the flow: a
  value far below a cell means the prediction has the mass in nearly the right places. On a
  density whose fluctuation is a small fraction of its mean, the value is also small next
  to the spatial scales of the structures, for the reason under Limitations.
- **Valid comparisons.** Models on the same grid and domain, directly. Across grids with
  different spacing the number is in the same physical units and comparable, unless the
  coarser grid has averaged away structure. Across datasets it is not comparable: the size
  of the domain and the relative size of the fluctuation both set it.
- **The companion.** A per-cell map, $f\,|\nabla u|^2$ in length squared: the reference's
  normalised density times the squared distance its mass travels. Its mean is the square of
  the metric. It shows where mass has to move, not the error at each cell.

## Limitations

- **The total mass is invisible.** Both densities are divided by their own mean, so a
  prediction with the right arrangement and the wrong total scores zero (pinned in
  `test_metric.py`). Pair it with a metric that sees the mean or the amplitude.
- **On a density with a large mean it is close to `h_minus_one`.** To first order in the
  difference the two are within $b^{-1/2}$ and $a^{-1/2}$ of each other (Definition), and on a
  field like kinet's density, whose values lie within a few percent of its mean, those factors
  are close to 1. Read "Compared with the other metrics" before using both in one panel.
- **It does not measure the size of a shift.** The background makes the growth with a
  displacement far weaker than "distance squared": a large shift of the whole density costs
  only the transport needed to rearrange its small fluctuation, so the value is much smaller
  than the shift (Definition, "Shift and background"). Reading the
  number as "how far the features are displaced" is wrong here. That reading is also less
  clean in two dimensions than in one, because the optimal map can move different parts of
  the field in different directions.
- **A non-positive cell gives NaN, not a large value.** A surrogate that predicts a negative
  density anywhere is scored NaN, which an average over frames can hide. The harshest level of
  [multiplicative_noise](../../degradations/multiplicative_noise/card.md) makes density negative
  in some cells of every frame, so that level scores NaN here (`issues/139`).
- **At high contrast the solve can fail, and the value is then NaN.** [@saumier2015]
  (Sect. 3.3) note that the damping their convergence needs grows as the source density
  approaches zero or as either density becomes rough. Measured against the exact circle
  transport on 128-cell profiles moved by 1, 8 and 32 cells (my measurement, not a run of the
  harness): the solve converges and agrees to $10^{-4}$ for every shift when the density
  peaks at 2.33 times its mean, and for shifts up to 8 cells at 2.94 times; it fails at 2.94
  times its mean for a 32-cell shift and at 3.53 times for every shift, because no damping of
  its step then lowers the residual. A strong shock compresses density by more than that, so
  a shock-dominated field can score NaN with a warning. A full Newton step, solving their
  linearised operator (Eq. (5)) iteratively as their Sect. 4.2 does, would be the remedy.
- **It costs about thirty times `h_minus_one`.** Timed in one process on kinet density at step
  6000 against five candidates (mean field, a 16-cell shift, an eighth-cell shift, a blur and
  noise), interleaved over nine rounds with medians (my measurement,
  `.agent/scratch/interleaved_timing.py` in the build records): 74.7 ms per call against 2.71 ms
  for `h_minus_one`, a ratio of 28. Before the closed-form determinant the same measurement
  gave 196.0 ms, a ratio of 72. The pinned comparison run, which times both metrics in one
  run, gives 0.064 s against 0.0022 s on density, a ratio of 29. Costs recorded in
  different runs are not comparable (`issues/125`): the two fingerprints recorded before
  that run, on different login nodes, gave a ratio of about 90, and one call of
  `h_minus_one` took between 2.7 and 5.0 ms on one login node within minutes, at a load
  average above the node's core count.
- **Not exactly symmetric.** $W_2$ is symmetric, but solving from the other side gives a value
  that differs by the discretisation error, so the metric declares `symmetric=False`.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence wasserstein --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

Measured on `kinet_re5e4`, frames 2000 to 10000 (161 frames of developed flow), on the 256 analysis grid, seed 20260807, at commit `adbdc88e4950`. Run `comparison_1793829127`.

Every number in this section comes from that run, except in the subsections headed with another experiment and in a figure whose caption names another run, each of which names its own run. Regenerate with `python -m fmeval.cards evidence <name> --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`.

<!-- END GENERATED run -->

<!-- GENERATED experiments: written by `python -m fmeval.cards catalog`, do not edit -->

**Across the experiments.**

| experiment | what a run on it is evidence of | on this card |
|---|---|---|
| `kinet_re5e4` | developed flow | measured, run `comparison_1793829127`: the main results |
| `kinet_re1e6` | developed flow at Re = 1e6, twenty times the Reynolds number of kinet_re5e4, from the same initial condition | measured, run `comparison_1793829231`: under *On `kinet_re1e6`* |
| `synthetic_ensemble` | a calibrated null: evidence that the estimator computes what it claims to compute, and nothing about turbulence | not applicable: its density is a signed two-scale pattern plus noise, with cells below zero, where the distance is undefined: every value there is NaN (measured on all 168 rows) |
| `sod_shock_tube` | an analytic check: evidence that the metric locates and scores a known shock correctly, and nothing about turbulence | not applicable: needs a periodic domain, and this dataset is not periodic |
| `forecast_re5e4` | real predictions scored against their targets at each prediction step; who produced the predictions, a trained model or a coarser solver, is not recorded | measured, run `comparison_1793811840`: under *On `forecast_re5e4`* |

One row per dataset a card may cite (`configs/cards/default.yaml`). *Measured* names the run the card cites: the main results are `## Performance` and the subsections below, and every other run has its own subsection headed with its dataset. *Not applicable* gives the reason: one that follows from what the metric declares and what the dataset offers, or one a person wrote on the card (`not_run` in `card.yaml`) because the result would carry no information. *Not yet run* means the metric can run there and the card cites no run on it yet.

<!-- END GENERATED experiments -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[median_blur](../../degradations/median_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence wasserstein --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `box_blur` | density | 4 | 1 | 1 | 0.963 |
| `disk_blur` | density | 3 | 1 | 1 | 0.972 |
| `epanechnikov_blur` | density | 3 | 1 | 1 | 0.972 |
| `gaussian_blur` | density | 4 | 1 | 1 | 0.974 |
| `median_blur` | density | 3 | 1 | 1 | 0.971 |

<!-- END GENERATED results_smoothing -->

Every blur moves mass from the density's peaks into its troughs, and the distance follows the width on every frame, as pre-registered, with neighbouring widths almost never overlapping (weakest gap 0.963). The largest damage, 0.455 under `gaussian_blur`, is under half of what the spatial mean scores. The elasticity of 1.81 to 1.92 says the distance grows nearly as the square of the kernel width at the mildest widths. That is what a narrow blur does to a field carried by a few large-scale modes, each of which it damps by an amount proportional to the square of the width (my reading, not a source's).

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence wasserstein --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `band_attenuate` | density | 4 | 1 | 1 | 0.676 |
| `highpass_butterworth` | density | 4 | 1 | 1 | 0.576 |
| `highpass_ideal` | density | 3 | 1 | 1 | 0.548 |
| `lowpass_butterworth` | density | 4 | 1 | 1 | 0.848 |
| `lowpass_ideal` | density | 3 | 1 | 1 | 0.968 |

<!-- END GENERATED results_spectral -->

All five filters follow the fraction of energy removed on every frame. The high-pass pair separates neighbouring strengths least well (weakest gap 0.548 for `highpass_ideal`), because removing density's large-scale modes takes most of its fluctuation at once (my reading), and the harshest high-pass and low-pass strengths go slightly past the anchor (largest damage 1.08 for `lowpass_ideal`, `highpass_ideal` and `highpass_butterworth`). `band_attenuate` moves it very little (largest damage 0.000856) and is among the degradations whose response is provably below 0.05.

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence wasserstein --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `translate_subpixel` | density | 6 | 1 | 1 | 0.96 |
| `translate_x` | density | 5 | 1 | 1 | 0.959 |
| `translate_y` | density | 5 | 1 | 1 | 0.943 |

<!-- END GENERATED results_geometric -->

Both axes follow the shift on every frame, as pre-registered, and the elasticity of 0.999 to 1 says the distance is proportional to the shift over these ranges. That is not the property the idea was built for. The largest whole-domain shift on the ladder scores a damage of 0.468, and the anchor it is measured against is itself only 0.172 cells: moving the whole density by many cells costs a transport of a small fraction of a cell, because only its fluctuation, well under a percent of its mean in root mean square, has to be rearranged, not the whole mass. This is the background effect described in the Definition ("Shift and background"), measured; the run shows the size of the effect, not the non-convexity that the seismic papers describe.

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence wasserstein --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `coarsen` | density | 4 | 1 | 1 | 1 |
| `coarsen_bandlimited` | density | 4 | 1 | 1 | 0.865 |
| `subsample` | density | 4 | 1 | 1 | 0.962 |

<!-- END GENERATED results_resolution -->

All three operators follow the factor on every frame. The response of the two coarsenings is small: the profile table lists both among the degradations whose damage is provably below 0.05 (largest damage 0.0487 under `coarsen` and 0.0108 under `coarsen_bandlimited`). My reading: block averaging redistributes mass only within a block, and density's fluctuation sits in the largest scales, so little mass moves far. `subsample` costs more, with a largest damage of 0.308.

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence wasserstein --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `additive_noise` | density | 4 | 1 | 1 | 1 |
| `multiplicative_noise` | density | 5 | — | — | — |

<!-- END GENERATED results_stochastic -->

`additive_noise` is ordered perfectly, with no overlap between neighbouring amplitudes, and with an elasticity of 0.997, so the distance is proportional to the noise amplitude. The damage stays tiny (largest 0.0204): independent noise in each cell is evened out by moving mass over about a cell, which costs little next to the anchor (my reading). Only `bias`, `band_attenuate` and `coarsen_bandlimited` move it less.

`multiplicative_noise` has no ordering statistics, and the dashes do not mean the distance is blind to it. Its harshest level makes density negative in some cells of every frame, where the distance is undefined and the value is NaN (`issues/139`), and the run records no rank correlation, fraction in order or gap for the whole axis; that the NaN level is what removes them is my reading of `fmeval/analysis.py`. On the four milder levels the distance is defined, and its largest damage there is 0.639.

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence wasserstein --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

| field | damage assigned to the fake prediction | closest real degradation | damage of the reference moved far away | value on the anchor |
|---|---|---|---|---|
| density | 1.33 | `lowpass_ideal=1.4029` | 1.11 | 0.172 |

The fake prediction here has exactly the reference field's amplitude spectrum and completely scrambled structure. Damage 1 is what the anchor scores, by default the reference's own spatial mean, a prediction that knows the mean and nothing else. The damage column therefore says how close to useless this metric considers that fake prediction: a low number means the metric was fooled. The third column translates the same number into an ordinary degradation whose damage the fake prediction matches, which is easier to picture. The fourth is the reference moved by a large random offset, the right statistics in the wrong place; where a field's energy sits in its largest scales that copy stays partly correlated with the reference, so it is not the score of an unrelated field.

<!-- END GENERATED results_canaries -->

The fake prediction with the right spectrum scores a damage of 1.33, more than the spatial mean: the metric is not fooled by it, because the phases decide where the mass sits. The reference moved far away scores 1.11, close to the anchor.

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence wasserstein --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

| compared with | density |
|---|---|
| `h_minus_one` | 0.996 |
| `max_error` | 0.899 |
| `max_error_channel_mean` | 0.899 |
| `vrmse` | 0.887 |
| `mse` | 0.886 |
| `nrmse` | 0.886 |
| `rmse` | 0.886 |
| `rmse_channel_mean` | 0.886 |
| `mae` | 0.852 |
| `h1_relative` | 0.696 |
| `h1_seminorm` | 0.584 |
| `persistence_distance` | 0.242 |
| `spectrum_l2` | 0.239 |
| `increment_w1_by_separation` | 0.216 |
| `tail_exceedance` | 0.19 |
| `increment_w1` | 0.121 |
| `energy_distance` | 0.115 |
| `tail_index` | -0.0811 |
| `increment_flatness` | -0.111 |

Rank correlation over every degradation, computed separately for each physical field on the median value at each combination of degradation and strength, with the undegraded reference excluded. A dash marks a metric that does not run on that field. A metric with a target value enters by its distance from the target. Two metrics correlating near 1 put the degradations in the same order, but the two may still weight those degradations very differently. A correlation near 1 therefore means the two metrics are redundant for ranking models, not that the two are interchangeable as training losses.

<!-- END GENERATED results_summary -->

[h_minus_one](../../metrics/h_minus_one/card.md) orders the ladder almost exactly as this metric does on density, the highest correlation in the table, followed by `max_error` and the pointwise errors. On every axis but two, the largest damage and the elasticity of the two metrics, and both trap-test damages, agree to within about one percent (the two fingerprints). The exceptions are `bias`, which this metric orders and `h_minus_one` does not see, and `multiplicative_noise`, whose harshest level this metric cannot score. That agreement is the first-order relation in the Definition at work on a density this close to uniform; Equation (5) alone would allow a factor of two. On kinet density the two metrics carry nearly the same information, and this one costs 0.267 s per evaluation in this run, 1.09e+03 times the cheapest metric (Profile), many times what `h_minus_one` costs in the same run (its card's Profile); Limitations gives the ratio measured in one process.

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence wasserstein --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

![damage against applied strength for this metric beside the pointwise controls, log-log, one panel per displacement degradation and field](_generated/damage_beside_controls.svg)

Median damage over frames against the applied strength, log-log, for wasserstein (bold, in colour) and the pointwise controls mae, mse, rmse, vrmse (thin, grey), one column per displacement degradation and one row per field. The grey line is damage 1, the anchor (by default the field's own mean). Parallel lines charge in the same proportion at every strength; a steeper line charges relatively more for the larger shifts, which is what decides whether two metrics are interchangeable as training losses. These are the same numbers as the table beneath.

**Displacement, density, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `wasserstein` | 0.00347 | 0.00693 | 0.0139 | 0.0277 | 0.0554 | 0.111 |
| `mae` | 0.00383 | 0.00767 | 0.0153 | 0.0306 | 0.061 | 0.121 |
| `mse` | 2.17e-05 | 8.68e-05 | 0.000347 | 0.00138 | 0.00551 | 0.0219 |
| `rmse` | 0.00466 | 0.00931 | 0.0186 | 0.0372 | 0.0743 | 0.148 |
| `vrmse` | 0.00463 | 0.00926 | 0.0185 | 0.037 | 0.0738 | 0.147 |

**Displacement, density, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `wasserstein` | 0.0277 | 0.0554 | 0.111 | 0.221 | 0.434 |
| `mae` | 0.0306 | 0.061 | 0.121 | 0.24 | 0.469 |
| `mse` | 0.00138 | 0.00551 | 0.0219 | 0.0849 | 0.307 |
| `rmse` | 0.0372 | 0.0743 | 0.148 | 0.291 | 0.555 |
| `vrmse` | 0.037 | 0.0738 | 0.147 | 0.29 | 0.55 |

**Displacement, density, `translate_y`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `wasserstein` | 0.028 | 0.0559 | 0.112 | 0.222 | 0.438 |
| `mae` | 0.031 | 0.0616 | 0.122 | 0.244 | 0.476 |
| `mse` | 0.00142 | 0.00565 | 0.0224 | 0.0869 | 0.316 |
| `rmse` | 0.0377 | 0.0752 | 0.15 | 0.295 | 0.562 |
| `vrmse` | 0.0376 | 0.075 | 0.149 | 0.294 | 0.56 |

**Displacement, velocity, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `wasserstein` | — | — | — | — | — | — |
| `mae` | 0.00279 | 0.00559 | 0.0112 | 0.0223 | 0.0441 | 0.0859 |
| `mse` | 1.45e-05 | 5.81e-05 | 0.000232 | 0.000924 | 0.0036 | 0.0136 |
| `rmse` | 0.00381 | 0.00762 | 0.0152 | 0.0304 | 0.06 | 0.117 |
| `vrmse` | 0.00365 | 0.00729 | 0.0146 | 0.029 | 0.0574 | 0.111 |

**Displacement, velocity, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `wasserstein` | — | — | — | — | — |
| `mae` | 0.0223 | 0.0441 | 0.0859 | 0.163 | 0.31 |
| `mse` | 0.000924 | 0.0036 | 0.0136 | 0.0489 | 0.165 |
| `rmse` | 0.0304 | 0.06 | 0.117 | 0.221 | 0.406 |
| `vrmse` | 0.029 | 0.0574 | 0.111 | 0.209 | 0.383 |

**Displacement, velocity, `translate_y`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `wasserstein` | — | — | — | — | — |
| `mae` | 0.0223 | 0.0442 | 0.0856 | 0.16 | 0.295 |
| `mse` | 0.000935 | 0.00366 | 0.0138 | 0.0473 | 0.158 |
| `rmse` | 0.0306 | 0.0605 | 0.117 | 0.218 | 0.397 |
| `vrmse` | 0.0303 | 0.0599 | 0.115 | 0.212 | 0.384 |

**Displacement, vorticity, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `wasserstein` | — | — | — | — | — | — |
| `mae` | 0.0428 | 0.0854 | 0.169 | 0.328 | 0.582 | 0.86 |
| `mse` | 0.00112 | 0.00448 | 0.0176 | 0.066 | 0.21 | 0.44 |
| `rmse` | 0.0335 | 0.0669 | 0.133 | 0.257 | 0.458 | 0.663 |
| `vrmse` | 0.0329 | 0.0656 | 0.13 | 0.253 | 0.455 | 0.671 |

**Displacement, vorticity, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `wasserstein` | — | — | — | — | — |
| `mae` | 0.328 | 0.582 | 0.86 | 1.1 | 1.31 |
| `mse` | 0.066 | 0.21 | 0.44 | 0.679 | 1.1 |
| `rmse` | 0.257 | 0.458 | 0.663 | 0.824 | 1.05 |
| `vrmse` | 0.253 | 0.455 | 0.671 | 0.832 | 1.05 |

**Displacement, vorticity, `translate_y`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `wasserstein` | — | — | — | — | — |
| `mae` | 0.333 | 0.603 | 0.93 | 1.25 | 1.43 |
| `mse` | 0.0858 | 0.283 | 0.628 | 0.849 | 1.17 |
| `rmse` | 0.293 | 0.532 | 0.793 | 0.922 | 1.08 |
| `vrmse` | 0.268 | 0.495 | 0.793 | 0.927 | 1.08 |

Median damage over frames at every strength, this metric in the first row and the pointwise controls beneath it, all on the same 0-to-1 scale where 0 is the undegraded reference and 1 the anchor (by default the field's own mean); a dash means no damage scale on that field. The rank correlations under *Compared with the other metrics* say whether two metrics put the strengths in the same order; this table says how much each one charges for the same strength, which decides whether two metrics are interchangeable as training losses.

<!-- END GENERATED results_damage_by_level -->

This is the figure the transport-misfit literature draws, the misfit against an applied shift (`### How its field reports it`). On density this metric charges slightly less than `mae` and `rmse` at every shift, and its line is close to parallel to theirs: its damage is proportional to the shift over the whole range, and so, on density over this range, are theirs. *Displacement* above says why a shift costs this metric so little on this density. Velocity and vorticity carry no value because the metric reads density only.

### On `forecast_re5e4`

<!-- GENERATED results_on_forecast_re5e4: written by `python -m fmeval.cards evidence wasserstein --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

**Real predictions scored against their targets at each prediction step; who produced the predictions, a trained model or a coarser solver, is not recorded.**

Measured on `forecast_re5e4`, frames 0 to 59 (60 frames of real predictions scored against their targets at each prediction step; who produced the predictions, a trained model or a coarser solver, is not recorded), on the 64 analysis grid, seed 20260807, at commit `adbdc88e4950`. Run `comparison_1793811840`.

[mean_field](../../degradations/mean_field/card.md)

![the metric against time: the clean field's own history in black and each strength of the operator applied at each time, or a real forecast's error against its lead time, one panel per start and one line per run](_generated/response_along_time__dataset-forecast_re5e4__field-density__along-lead.svg)

wasserstein on density against lead time, the physical time since the forecast started, one panel per start and one line per run, darker the finer the run's grid. Each point is one prediction step of one forecast.

**density, wasserstein on the prediction, at each lead time.**

| lead time | 64², start 0 | 128², start 0 | 256², start 0 | 64², start 1.13 | 128², start 1.13 | 256², start 1.13 |
|---|---|---|---|---|---|---|
| 0.1128 | 0.00042 | 0.000141 | 8.7e-07 | 0.00422 | 0.00133 | 4.95e-06 |
| 0.2255 | 0.0014 | 0.000518 | 3.05e-06 | 0.00511 | 0.00184 | 8.17e-06 |
| 0.3383 | 0.00523 | 0.00217 | 1.39e-05 | 0.00805 | 0.00298 | 1.4e-05 |
| 0.4511 | 0.0149 | 0.00689 | 5.19e-05 | 0.0095 | 0.00366 | 1.72e-05 |
| 0.5638 | 0.036 | 0.0184 | 0.000197 | 0.0107 | 0.00431 | 2.19e-05 |
| 0.6766 | 0.0432 | 0.0154 | 0.000608 | 0.013 | 0.0049 | 2.39e-05 |
| 0.7893 | 0.0341 | 0.00962 | 0.00127 | 0.0151 | 0.00633 | 3.55e-05 |
| 0.9021 | 0.027 | 0.012 | 0.00206 | 0.0154 | 0.00603 | 2.91e-05 |
| 1.015 | 0.0272 | 0.0142 | 0.00325 | 0.0179 | 0.00732 | 4.3e-05 |
| 1.128 | 0.0274 | 0.0135 | 0.00525 | 0.0183 | 0.00794 | 4.26e-05 |

**density, wasserstein damage, at each lead time.**

| lead time | 64², start 0 | 128², start 0 | 256², start 0 | 64², start 1.13 | 128², start 1.13 | 256², start 1.13 |
|---|---|---|---|---|---|---|
| 0.1128 | 0.0229 | 0.00774 | 4.78e-05 | 0.0228 | 0.0072 | 2.68e-05 |
| 0.2255 | 0.107 | 0.039 | 0.000228 | 0.0298 | 0.0107 | 4.75e-05 |
| 0.3383 | 0.2 | 0.0835 | 0.000537 | 0.046 | 0.0171 | 7.99e-05 |
| 0.4511 | 0.259 | 0.119 | 0.000895 | 0.0527 | 0.0203 | 9.52e-05 |
| 0.5638 | 0.432 | 0.22 | 0.00236 | 0.0644 | 0.0259 | 0.000131 |
| 0.6766 | 0.32 | 0.114 | 0.0045 | 0.0712 | 0.0269 | 0.000132 |
| 0.7893 | 0.23 | 0.065 | 0.00856 | 0.0883 | 0.0369 | 0.000207 |
| 0.9021 | 0.164 | 0.0732 | 0.0125 | 0.0878 | 0.0345 | 0.000166 |
| 1.015 | 0.151 | 0.0789 | 0.0181 | 0.0983 | 0.0402 | 0.000236 |
| 1.128 | 0.163 | 0.08 | 0.0312 | 0.109 | 0.0472 | 0.000253 |

Every prediction of every forecast, nothing pooled: a cell is one prediction step of one forecast, a row the lead time (the physical time since the forecast started) and a column the forecast, named by its run's native grid and its starting time (`64², start 0` is `F-906861_64_Re_50k_from_256_to_64/forecast_t0-0`; `128², start 0` is `F-906861_64_Re_50k_from_256_to128/forecast_t0-0`; `256², start 0` is `F-906861_64/forecast_t0-0`; `64², start 1.13` is `F-906861_64_Re_50k_from_256_to_64/forecast_t0-1250`; `128², start 1.13` is `F-906861_64_Re_50k_from_256_to128/forecast_t0-2500`; `256², start 1.13` is `F-906861_64/forecast_t0-5000`). **Damage** is the prediction's departure from the target as a fraction of the anchor's in the same frame, by default the target's own spatial mean, so each step is scaled by its own target. A dash means no value there.

<!-- END GENERATED results_on_forecast_re5e4 -->

On real forecasts the distance behaves as [h_minus_one](../../metrics/h_minus_one/card.md)
does on the same forecasts, to two figures or better at every step, as the first-order relation
in the Definition gives for a density this close to uniform.

- **The coarser the forecast's grid, the larger the distance**, at almost every step: at the
  first lead time, 0.1128, the damage from start 0 is 0.0229, 0.00774 and 4.78e-05 on the 64²,
  128² and 256² forecasts.
- **The 64² forecast from start 0 peaks** at lead time 0.5638 (damage 0.432, distance 0.036)
  and then eases (0.163 at lead time 1.128).
- **From start 1.13 the 256² forecast stays close to its target** (damage at most 0.000253);
  from start 0 it grows at every step, to 0.0312 at lead time 1.128.

The damage is scaled by the anchor of each step, the distance from the target to its own mean,
whose median over the run is 0.168.

### On `kinet_re1e6`

<!-- GENERATED results_on_kinet_re1e6: written by `python -m fmeval.cards evidence wasserstein --results results/comparison_1793829127 --results results/comparison_1793811840 --results results/comparison_1793829231`, do not edit -->

**Developed flow at Re = 1e6, twenty times the Reynolds number of kinet_re5e4, from the same initial condition.**

Measured on `kinet_re1e6`, frames 2000 to 10000 (161 frames of developed flow at Re = 1e6, twenty times the Reynolds number of kinet_re5e4, from the same initial condition), on the 128 analysis grid, seed 20260807, at commit `adbdc88e4950`. Run `comparison_1793829231`.

[additive_noise](../../degradations/additive_noise/card.md) ·
[band_attenuate](../../degradations/band_attenuate/card.md) ·
[bias](../../degradations/bias/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md) ·
[disk_blur](../../degradations/disk_blur/card.md) ·
[epanechnikov_blur](../../degradations/epanechnikov_blur/card.md) ·
[gain](../../degradations/gain/card.md) ·
[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[mean_field](../../degradations/mean_field/card.md) ·
[median_blur](../../degradations/median_blur/card.md) ·
[multiplicative_noise](../../degradations/multiplicative_noise/card.md) ·
[subsample](../../degradations/subsample/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md) ·
[translate_x](../../degradations/translate/card.md) ·
[translate_y](../../degradations/translate/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

**Smoothing.**

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `box_blur` | density | 4 | 1 | 1 | 0.965 |
| `disk_blur` | density | 3 | 1 | 1 | 0.971 |
| `epanechnikov_blur` | density | 3 | 1 | 1 | 0.973 |
| `gaussian_blur` | density | 4 | 1 | 1 | 0.974 |
| `median_blur` | density | 3 | 1 | 1 | 0.975 |

**Spectral filtering.**

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `band_attenuate` | density | 4 | 1 | 1 | 0.688 |
| `highpass_butterworth` | density | 4 | 1 | 1 | 0.577 |
| `highpass_ideal` | density | 3 | 1 | 1 | 0.55 |
| `lowpass_butterworth` | density | 4 | 1 | 1 | 0.849 |
| `lowpass_ideal` | density | 3 | 1 | 1 | 0.976 |

**Displacement.**

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `translate_subpixel` | density | 6 | 1 | 1 | 0.961 |
| `translate_x` | density | 5 | 1 | 1 | 0.953 |
| `translate_y` | density | 5 | 1 | 1 | 0.94 |

**Resolution loss.**

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `coarsen` | density | 4 | 1 | 1 | 0.997 |
| `coarsen_bandlimited` | density | 4 | 1 | 1 | 1 |
| `subsample` | density | 4 | 1 | 1 | 0.967 |

**Noise.**

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `additive_noise` | density | 4 | 1 | 1 | 1 |
| `multiplicative_noise` | density | 5 | — | — | — |

**Cell-value distortion.**

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `bias` | density | 4 | 1 | 1 | 0.931 |
| `gain` | density | 4 | 1 | 1 | 0.97 |

**Trap tests.**

| field | damage assigned to the fake prediction | closest real degradation | damage of the reference moved far away | value on the anchor |
|---|---|---|---|---|
| density | 1.35 | `lowpass_ideal=1.41077` | 1.11 | 0.696 |

The fake prediction here has exactly the reference field's amplitude spectrum and completely scrambled structure. Damage 1 is what the anchor scores, by default the reference's own spatial mean, a prediction that knows the mean and nothing else. The damage column therefore says how close to useless this metric considers that fake prediction: a low number means the metric was fooled. The third column translates the same number into an ordinary degradation whose damage the fake prediction matches, which is easier to picture. The fourth is the reference moved by a large random offset, the right statistics in the wrong place; where a field's energy sits in its largest scales that copy stays partly correlated with the reference, so it is not the score of an unrelated field.

<!-- END GENERATED results_on_kinet_re1e6 -->

At twenty times the Reynolds number, on a 128² grid instead of 256², every axis that has an
ordering is in order on every frame, as on `kinet_re5e4`, including `bias` and `gain`
(rank correlation 1). `multiplicative_noise` again has none, for the same reason (`issues/139`).
The fake prediction again scores worse than the field's mean (damage 1.35) and the reference
moved far away about as much as the mean (1.11).

The anchor is 0.696 here against 0.172 on `kinet_re5e4`, so absolute values are not comparable
between the two runs; damages are. On that scale the shifts cost more here: the largest damage
is 0.893 under `translate_x` and 0.896 under `translate_y`, against 0.468 on `kinet_re5e4`, with
the elasticity to a sub-pixel shift still 1. The grid differs between the two runs as well as
the Reynolds number.

## References

\bibliography

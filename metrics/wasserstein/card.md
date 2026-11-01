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
$T(x) = x + \nabla u(x)$ with $u$ periodic ([@saumier2015], Theorem 2.1, after
Cordero-Erausquin), and $u$ solves the Monge–Ampère equation ([@saumier2015], Eq. (4))

$$
g\bigl(x + \nabla u(x)\bigr) \, \det\bigl(I + D^2 u(x)\bigr) = f(x) \tag{3}
$$

so that Equation (2) becomes the mean over cells of a transport cost density, which is the
companion map:

$$
W_2(f, g) = \bigl\langle f \, |\nabla u|^2 \bigr\rangle^{1/2} \tag{4}
$$

**How Equation (3) is solved.** By the periodic damped Newton method of [@saumier2015]
(Eq. (6)), from $u_0 = 0$, with step $1/\tau$ and $\tau = 1$, the value that converged in
their Sect. 5.1:

1. **Evaluate.** $f_n = g(x + \nabla u_n) \det(I + D^2 u_n)$, then replace $f_n$ by
   $f_n - \langle f_n \rangle + 1$ so that the residual $f - f_n$ has zero mean
   ([@saumier2015], Eq. (14)).
2. **Stop** when the root mean square of $f - f_n$ is at most $10^{-12}$, a fraction of the
   mean density, and report Equation (4) with $u_n$.
3. **Step.** Solve $\Delta \theta_n = f - f_n$ by FFT and set $u_{n+1} = u_n + \theta_n$.

Step 3 replaces their linearised operator ([@saumier2015], Eq. (5)) by the Laplacian, its
value at $u = 0$ and $g = 1$; their Sect. 3.3 notes that a simpler equation works in practice.
The answer is fixed by the residual of step 1, so this choice changes the number of
iterations and not the value. Derivatives of $u$ are spectral, with the wavevectors
$k_j = 2\pi\,\mathrm{fftfreq}(N_j, h_j)$ that [h_minus_one](../../metrics/h_minus_one/card.md)
uses; [@saumier2015] also solve the linear step by FFT (Sect. 4.2). The candidate is
evaluated at the displaced points by a periodic cubic B-spline. That is my choice: they use
nearest-neighbour values and name linear interpolation as the common alternative (Sect. 4).
If the solve has not converged after 100 iterations the value is NaN with a warning. On the
contract tests' field, whose density varies by a factor of four, it takes about 30. A cell
that is not positive and finite in either field makes the value NaN: Equation (2) is
defined between measures, and any value given to a signed field would be one of the
signed-field formulations that `issues/047` leaves open.

`test_metric.py` checks the solve against an independent one. For a density that varies
along one axis only, the transport is one-dimensional, and on a circle its exact value is the
least, over a rotation of the mass levels, of the mean squared distance between the two
quantile functions ([@delon2010], Sect. 2). On a 256-cell profile whose density lies between
0.63 and 1.37 times its mean, moved by an eighth of the domain, the two agree to within the
test's relative tolerance of $2 \times 10^{-4}$.

**Why a continuous solve and not a transport between cells.** Treating each cell as a point
mass and solving the discrete problem exactly is the standard alternative, but on a density
whose displacements are smaller than a cell it measures the grid. Mass then moves a whole
cell or not at all, so the squared distance grows with the size of the change rather than
with its square. For a 1-D density $1 + \epsilon \cos(2\pi x)$ against the uniform one on
cells of size $h$, the discrete squared distance is about $h\epsilon/\pi^2$ against the
continuous $\epsilon^2/(8\pi^2)$, a ratio of $8h/\epsilon$. This derivation is mine. It is
also unaffordable here: one $256 \times 256$ pair is a $65\,536 \times 65\,536$ cost
matrix. Equation (3) has neither problem, because the displacement $\nabla u$ is a
continuous field.

**What it is close to on a near-uniform density.** For densities between $a$ and $b$ times
the volume measure, Theorem 5, Eq. (17) and Corollary 3 of [@peyre2018] bound it by the
$\dot H^{-1}$ seminorm $H$ of $f - g$, which `h_minus_one` computes as a root mean square:

$$
b^{-1/2} \, H \;\le\; W_2(f, g) \;\le\; 2\,a^{-1/2} \, H \tag{5}
$$

with the lower bound for the flat torus, where the Ricci curvature is zero. As $f - g$ shrinks
the two agree to first order ([@peyre2018], Eq. (5)). `test_metric.py` checks Equation (5).
On a density whose fluctuation is a small fraction of its mean, $a$ and $b$ are both close
to 1. The two metrics then differ by the factor $\langle\rho\rangle$, since `h_minus_one` is
not mass-normalised, and by the narrow interval Equation (5) allows.

**Shift and background.** The property that recommends this distance for a displaced
feature is that $W_2^2$ of a signal moved by $s$ is $s^2$ whatever its profile
([@engquistyang2022], Sect. 1; [@engquist2014], Sect. 1). That holds for a signal on an empty
background. A density is a fluctuation on a large positive background. That is the "linear
normalisation" of [@yang2018] (Sect. 3.1, Eq. (27)), which they report makes the misfit
non-convex in shifts. [@engquistyang2022] (Theorem 4.6) show that, with a background $c$, it
grows as $s^2$ only for shifts below about $1/c$ plus the width of the signal, and as $s$
beyond.

### Boundary handling

Periodic on every axis. The domain is the torus: the optimal map is $x$ plus the gradient of
a periodic function, derivatives are taken by FFT, and the candidate is interpolated with
wrap-around (`scipy.ndimage.map_coordinates`, `mode="grid-wrap"`), so mass leaving one side
enters the other. The metric therefore declares `requires_periodic`, and the harness does not
run it on a dataset with a non-periodic axis, such as the Sod shock tube.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

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
- **On a density with a large mean it is close to `h_minus_one`.** Equation (5) holds the
  two within $b^{-1/2}$ and $2a^{-1/2}$ of each other, and on a field like kinet's density,
  which varies by a few percent, those factors are close to 1. Read "Compared with the other
  metrics" before using both in one panel.
- **It does not measure the size of a shift.** The background makes the growth with a
  displacement far weaker than "distance squared": a large shift of the whole density costs
  only the transport needed to rearrange its small fluctuation, so the value is much smaller
  than the shift ([@yang2018], Sect. 3.1; [@engquistyang2022], Theorem 4.6). Reading the
  number as "how far the features are displaced" is wrong here. That reading is also less
  clean in two dimensions than in one, because the optimal map can move different parts of
  the field in different directions.
- **A non-positive cell gives NaN, not a large value.** A surrogate that predicts a negative
  density anywhere is scored NaN, which an average over frames can hide.
- **Near vacuum the solve can fail.** [@saumier2015] (Sect. 3.3) note that the damping their
  convergence proof needs grows as the source density approaches zero. With $\tau = 1$ fixed,
  a density with near-empty regions may not converge in 100 iterations, and the value is
  then NaN with a warning.
- **Not exactly symmetric.** $W_2$ is symmetric, but solving from the other side gives a value
  that differs by the discretisation error, so the metric declares `symmetric=False`.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED run -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[median_blur](../../degradations/median_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_smoothing -->

Read once the evidence run exists.

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_spectral -->

Read once the evidence run exists.

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_geometric -->

Read once the evidence run exists.

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_resolution -->

Read once the evidence run exists.

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_stochastic -->

Read once the evidence run exists.

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_canaries -->

Read once the evidence run exists.

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_summary -->

Read once the evidence run exists.

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_damage_by_level -->

Read once the evidence run exists.

## References

\bibliography

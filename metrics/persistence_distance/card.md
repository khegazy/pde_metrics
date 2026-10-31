---
name: persistence_distance
kind: metric
---

## Definition

Let $f$ be a scalar field on a grid of $N$ cells $c$. Each cell is a closed top-dimensional
cube, and each lower-dimensional face of a cube takes the smallest value of the cubes it bounds:
the T-construction [@bleile2022], Definition 4.4, "Method 1" of [@skraba2020], Sect. 5.1, which
suits cell-averaged data and connects two cells that touch only at a corner. The sublevel set at threshold $t$ is the union of the
closed cells at or below it,

$$
K_t(f) = \bigcup \bigl\{ \bar c : f(c) \le t \bigr\} \tag{1}
$$

As $t$ rises, $K_t$ grows, and in each homology dimension $k$ (connected pieces for $k = 0$,
loops for $k = 1$, enclosed cavities for $k = 2$) a feature is born at some $b$ and dies at some
$d > b$, when it merges into an older feature or is filled in. The persistence diagram
$D_k(f)$ is the multiset of these points $(b, d)$; a feature of the whole domain never dies and
has $d = +\infty$ [@cohensteiner2005], Sect. 2. Points with $d = b$ are not recorded. The
Betti number of $K_t$ counts the points alive at $t$, by the $k$-Triangle Lemma of the same
section:

$$
\beta_k(t) = \#\bigl\{ (b, d) \in D_k(f) : b \le t < d \bigr\} \tag{2}
$$

and $\chi(t) = \sum_k (-1)^k \beta_k(t)$ is the Euler characteristic of $K_t$. Both are
computed from the diagram by `betti_curves` and `euler_characteristic_curve`, for a metric
built on those curves to import; this metric does not use them.

Two diagrams are compared with the bottleneck distance [@cohensteiner2005], Sect. 3.1: with the
diagonal $\Delta$ added to each at infinite multiplicity, so that a point may be matched to the
diagonal instead of to a point,

$$
d_B(X, Y) = \inf_{\gamma : X \cup \Delta \to Y \cup \Delta} \;
\sup_{x \in X \cup \Delta} \lVert x - \gamma(x) \rVert_\infty \tag{3}
$$

over bijections $\gamma$, with $\lVert (p_1, p_2) - (q_1, q_2) \rVert_\infty =
\max(\lvert p_1 - q_1 \rvert, \lvert p_2 - q_2 \rvert)$. A point matched to the diagonal costs
half its lifetime, $(d - b)/2$. The registered number is the bottleneck distance between the
diagrams of all homology dimensions $k = 0, \dots, n$ of an $n$-dimensional grid, each dimension
matched on its own [@skraba2020], Eq. 1:

$$
\mathrm{PD}(f, g) = \max_{0 \le k \le n} d_B\bigl(D_k(f), D_k(g)\bigr) \tag{4}
$$

It is the limit $p \to \infty$ of their total $p$-Wasserstein distance, which sums the $p$-th
powers over dimensions [@skraba2020], Definition 2.5. The Main Theorem of
[@cohensteiner2005], Sect. 3.1 (the journal version is [@cohensteiner2007]) bounds each term by
the largest pointwise difference, so

$$
\mathrm{PD}(f, g) \le \max_c \lvert f(c) - g(c) \rvert \tag{5}
$$

the value of [max_error](../../metrics/max_error/card.md). `test_metric.py` checks Equation (5)
on blurred, noisy and unrelated fields.

The diagrams come from `gudhi.PeriodicCubicalComplex` [@gudhicubical] over the coefficient field
$\mathbb{Z}/11$, gudhi's default, and Equation (3) from `gudhi.bottleneck_distance`
[@gudhibottleneck] at its default precision, an additive error of the smallest positive double
with the last two or three bits of the mantissa possibly wrong. When the two diagrams of a
dimension are equal as multisets, the term is set to exactly 0 without calling gudhi, which is
Equation (3) with the identity bijection and is the slowest case for gudhi. The classes that
never die are kept and matched among themselves; their number is fixed by the grid's topology
(on a doubly periodic grid one piece, two loops and one cavity, the torus), so both diagrams
always have the same number of them and their births, which include the global minimum and the
global maximum, enter Equation (3) like any other point, as points at infinity of the extended
plane [@cohensteiner2005], Sect. 2.

Only one-channel scalar fields are accepted: density, and vorticity on a two-dimensional grid.
A vector field, or a field holding a NaN or an infinite value, raises an error.

Four choices are this bundle's, not a source's. The bottleneck distance is registered rather
than a Wasserstein distance between diagrams, because it is the distance with the stability
theorem of Equation (5), which ties it to the pointwise maximum error; the Wasserstein distance
counts every feature and is the natural sibling. The filtration is by sublevel sets of the signed
field, not of its magnitude, so that on vorticity the cores of one sign are born as pieces and,
on the periodic grid, those of the other sign close loops, and both signs enter the diagram.
Pressure and other scalar fields are not declared, only because the evidence dataset has none to
test them on. The metric is declared not differentiable: Equation (4) has a gradient almost
everywhere, but it moves only the one pair of points that sets the value, and none is computed.

### Boundary handling

The complex wraps exactly the axes the grid declares periodic, read from the context: on a
doubly periodic grid the complex of the whole domain is a torus [@bleile2022], Sect. 4.2, and a
cell on the last row is a neighbour of the cell on the first. An axis with a wall is not wrapped,
so a domain with walls on every side is a box with one piece and no loops. Nothing is padded or
extended, so the metric does not assume periodicity and is not marked `requires_periodic`.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED performance -->

## Intuition

Imagine flooding a landscape whose height is the field. As the water rises, lakes appear in the
valleys, grow, and merge; islands of high ground shrink and finally go under. Each lake is born
at the height of its valley floor and dies at the height of the pass where it joins an older,
deeper lake. The list of these birth and death heights, for lakes and for the rings of water that
enclose islands, is the field's persistence diagram. A deep, wide valley lives long; a ripple of
noise is born and dies almost at once. The metric compares the two fields' lists: it pairs each
lake of one with a lake of the other, or with nothing, and reports the largest change of height
any pairing needs. A lake left unpaired counts as half its lifetime.

The list never records where a lake is. So a feature that is right in depth and shape but
sitting in the wrong place costs nothing, where a cell-by-cell error charges it twice, once
where it should be and once where it is.

A worked example on a four-by-four grid that wraps around at its edges. The reference is a
flat field of ones with a deep well of minus one in one corner and a shallow well of zero two
cells away diagonally. Its shallow well is a lake born at zero and dying at one, when everything
floods.

```
reference         moved well        filled well
-1  1  1  1       -1  1  1  1       -1  1  1  1
 1  1  1  1        1  1  1  1        1  1  1  1
 1  1  0  1        1  0  1  1        1  1  1  1
 1  1  1  1        1  1  1  1        1  1  1  1

persistence_distance:  0             0.5
max_error:             1             1
```

Moving the shallow well one cell leaves the list unchanged, so the metric scores 0, while the
largest cell-by-cell difference is 1. Filling the shallow well removes the lake born at zero and
dying at one; it has no partner, and pairing it with nothing costs half its lifetime, 0.5.

The metric ignores where features are, how large an area they cover and how their sizes are
distributed, and of all the differences between the two lists it reports only the largest.

## Reading the output

The value lies between 0 and the largest absolute cell-by-cell difference between the two
fields (Equation (5)), in the field's own units: density units for density, inverse time for
vorticity. Lower is better and 0 means the two diagrams are identical, which a field moved by
whole cells on a periodic grid attains exactly. The value is the size of the single worst
mismatch: a feature whose birth or death level is out by that much, or a feature of twice that
lifetime that one field has and the other lacks. Compare it with the field's own range or with
its fluctuation size, not across fields.

Values are comparable across models on the same grid. They are not comparable across
resolutions: a finer grid resolves smaller and sharper features and higher extremes, so the
diagram itself changes with the grid.

The companion is the persistence diagram of one field, stored as a point set with columns
`birth`, `death` (both in the field's units, `death` infinite for a class that never dies) and
`dimension` (0 for pieces, 1 for loops, 2 for cavities). It is computed for the candidate at
every strength, which on the clean level is the reference, and kept on the frames that
`report.error_map` names; the `companion_points` figure draws it.

## Limitations

- **Position is invisible.** Any rearrangement of the field that keeps its pattern of pieces and
  loops and their levels scores 0, including a translation by whole cells, a reflection or a
  rotation by a quarter turn on a square periodic grid. A prediction with every vortex in the
  wrong place but with the right strengths would score perfectly; this metric belongs beside a
  metric that sees position.
- **One feature sets the value.** Because Equation (3) is a largest displacement, a prediction
  that gets one strong vortex's peak wrong by some amount scores the same as one that gets every
  vortex wrong by that amount. Small noise features near the diagonal are absorbed cheaply, at
  half their lifetime each, so a field full of weak spurious features scores no worse than its
  single strongest one.
- **The extremes always count.** The classes that never die are born at the global minimum and,
  on a periodic grid, at the global maximum, so a single cell overshooting the reference's
  maximum by some amount makes the value at least that amount, even if the rest of the diagram
  matches.
- **Only scalar fields.** Velocity has no sublevel sets; a three-dimensional vorticity, with three
  channels, is refused.
- **No fluid-dynamics precedent for this exact use.** The published uses of persistence in fluids
  that this card's references cover built other objects: a filtration of the flow's trajectory
  in state space [@smith2024], a persistence-based template for locating a vortex core
  [@martinez2026], and threshold sweeps of connected regions in climate data that the authors
  call inspired by persistence [@muszynski2019]. None compared two fields by a diagram distance.
  The Topology ToolKit [@tierny2018] is an alternative implementation of the same diagrams.

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

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_spectral -->

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_geometric -->

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_resolution -->

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_stochastic -->

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_canaries -->

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_summary -->

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_damage_by_level -->

## References

\bibliography

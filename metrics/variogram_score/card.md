---
name: variogram_score
kind: metric
---

## Definition

For one channel of the reference with cell values $y_1 \dots y_d$, an ensemble of $M$ members
with values $x^{(k)}_i$, an order $p$ and weights $w_{ij} \ge 0$, the variogram score of order
$p$ is [@scheuererhamill2015]

$$
\mathrm{VS}_p = \sum_{i=1}^{d}\sum_{j=1}^{d} w_{ij}
\Bigl( |y_i - y_j|^p - \frac{1}{M}\sum_{k=1}^{M} \bigl|x^{(k)}_i - x^{(k)}_j\bigr|^p \Bigr)^2
\tag{1}
$$

which is Scheuerer and Hamill's Equation (3) with the forecast's expectation replaced by the
ensemble average of their Equation (4). The quantity $\tfrac{1}{2}\mathbb{E}|Y_i - Y_j|^p$ is
the variogram of order $p$ of geostatistics, so Equation (1) compares the reference's
variogram, estimated from one realization, with the ensemble's, pair by pair. It depends on
the means, variances and correlations of the cells together, which is why it is sensitive to
a wrong correlation structure where the energy score is not [@scheuererhamill2015]. Lower is
better.

The choices this bundle makes, each fixed and none tuned:

- **Order** $p = 0.5$, the order Scheuerer and Hamill find best at telling calibrated from
  miscalibrated ensembles among 0.5, 1 and 2, in every one of their experiments (Sections 3a
  to 3e) [@scheuererhamill2015].
- **Weights** $w_{ij} = 1/r_{ij}$, the inverse Euclidean distance between the centres of
  cells $i$ and $j$ in the grid's physical units, with $w_{ii} = 0$. Scheuerer and Hamill
  propose it as a pragmatic choice when correlations fall with distance (Section 2) and find
  it a good compromise when nothing more is known about them (Section 3e)
  [@scheuererhamill2015]. The score therefore carries an inverse length.
- **Every ordered pair** in the domain, as Equation (1) is written; no neighbourhood cut-off,
  which Scheuerer and Hamill reserve for prior knowledge of the correlations (Section 3e).
- **Channels separately, then summed.** For a vector field the pairs never mix two
  components; Scheuerer and Hamill call a score across variables of different kinds doubtful
  (Section 2), and a distance between one component at one cell and another component at
  another has no meaning. This is this bundle's choice.

The score is proper but not strictly proper: it sees the distribution only through the
$p$-th moments of pairwise differences, and every term depends only on differences, so a bias
common to every cell is invisible [@scheuererhamill2015]. Pacchiardi and colleagues use the
same score, their Equation (11), on spatial fields of a generative weather model
[@pacchiardi2024].

The ensemble average inside the square of Equation (1) makes the estimator depend on the
ensemble size. Squaring a mean of $M$ draws adds the draws' variance divided by $M$ to every
term in expectation (a derivation of this card's), so the same calibrated forecast scores
higher with fewer members; Scheuerer and Hamill observe the score improving with ensemble
size (Section 3a) [@scheuererhamill2015]. Pacchiardi and colleagues call this ensemble
estimate unbiased (Appendix C.1.3) [@pacchiardi2024]; for the reason just given it is not.

The per-cell map, the metric's companion, charges every ordered pair $(i, j)$ to cell $i$, so
cell $i$ holds $\sum_j w_{ij}(\dots)^2$ summed over channels and the map sums to the score.
The computation visits each displacement between cells once, which is $O(M d^2)$ for $d$
cells: under a second for a 64 by 64 field of sixteen members, and impractical on a 512 by
512 grid.

### Boundary handling

Pairs are formed only between cells inside the domain, and their distance is the straight
line between the cell centres. Nothing wraps: on a periodic domain two cells on opposite
edges, which are neighbours in the flow, count as far apart and get a small weight. No
stencil or transform is involved, so the metric needs no periodicity and runs on any grid.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED performance -->

## Intuition

This metric asks whether an ensemble gets the *differences* between places right. For every
pair of cells it looks at how different the true field is between the two, and at how
different each member is between the same two on average, and charges the squared mismatch.
Nearby pairs are weighted more than distant ones. An ensemble whose members are too rough or
too smooth from place to place, too strongly or too weakly tied between neighbouring cells,
gets the differences wrong and is charged for it, even when each cell on its own has the right
spread of values.

The differences are taken to the power one half before they are compared, which keeps a few
very large differences from dominating and steadies the score from one forecast to the next.

A worked example, with a row of three cells, unit spacing and two members:

```
reference        member 1        member 2        result
0, 4, 0          0, 1, 0         0, 0, 0         9
```

The reference's neighbouring cells differ by 4, whose square root is 2; its end cells do not
differ. Member one's neighbours differ by 1 and member two's by nothing, so the members
average a square root of 0.5 for each neighbouring pair. Each neighbouring pair, at distance
one, costs the square of 2 − 0.5, which is 2.25; the end pair matches and costs nothing. The
score counts every pair in both orders, so it is 2 × (2.25 + 2.25) = 9.

What it ignores is level: adding the same number to every member, or to the reference,
changes no difference and leaves the score exactly where it was.

## Reading the output

The score runs from zero upward, in the field's units per unit length, and lower is better.
Zero means every member's differences between every pair of cells matched the reference's.
There is no absolute threshold for a good value: the score is a sum over every pair of cells,
and on a two-dimensional grid each cell's inverse-distance weights add up to roughly the
domain's side length in cells, so with a similar mismatch everywhere the score grows about as
the number of cells to the power three halves (a derivation of this card's). It also depends
on the grid's spacing through the weights. Compare models only on the same analysis grid, field and ensemble
size; across ensemble sizes the comparison is biased toward the larger ensemble (Definition).

Because it is blind to a common offset, read it beside a score that sees one, such as `crps`
or `energy_score`. The per-cell map says where the mismatch in differences is concentrated: a
cell with a large value belongs to many pairs whose differences the ensemble gets wrong.

## Limitations

The score cannot see an error that shifts every cell by the same amount. An ensemble that is
right in every detail but uniformly too warm, too dense or too fast scores exactly as well as
the correct one; read alone it would rank them equal.

It is not strictly proper, so different errors can cancel: an ensemble whose cells are too
variable and too strongly correlated with their neighbours can produce the same pairwise
differences as the truth and score as well as a correct forecast. Scheuerer and Hamill show
such cancellation between a wrong trend and underdispersion and recommend checking the
cell-by-cell distributions first [@scheuererhamill2015].

The cost grows with the square of the number of cells. On a 512 by 512 analysis grid the score
would sum about seventy billion pairs per member, which is impractical; a neighbourhood
cut-off, which Scheuerer and Hamill describe for when the correlation range is known, would
change what the score sees and is not implemented.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED run -->

### Ensemble dispersion

[spread_inflate](../../degradations/spread_inflate/card.md) ·
[spread_deflate](../../degradations/spread_deflate/card.md)

<!-- GENERATED results_ensemble: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_ensemble -->

### Cell-value distortion

[bias](../../degradations/bias/card.md)

<!-- GENERATED results_pointwise: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED results_pointwise -->

## References

\bibliography

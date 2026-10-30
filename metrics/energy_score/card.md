---
name: energy_score
kind: metric
---

## Definition

Let the reference field be the vector $\mathbf{y}$ of all its values, every channel of every
cell, and let $\mathbf{X}$ and $\mathbf{X}'$ be independent draws from the forecast
distribution $F$ of that vector. With $\|\cdot\|$ the Euclidean norm, the energy score is

$$
\mathrm{ES}(F, \mathbf{y}) = \mathbb{E}\,\|\mathbf{X} - \mathbf{y}\|
- \tfrac{1}{2}\,\mathbb{E}\,\|\mathbf{X} - \mathbf{X}'\| \tag{1}
$$

which is Equation (22) of Gneiting and Raftery with the index $\beta = 1$ and the sign
reversed, so that lower is better [@gneitingraftery2007]. It is strictly proper for any
$\beta \in (0, 2)$: in expectation over the reference, the true distribution of the whole
field scores lower than any other forecast [@gneitingraftery2007]. With one value per field,
$\beta = 1$ turns Equation (1) into the kernel form of the continuous ranked probability score,
their Equation (21), and the score is the [crps](../crps/card.md).

From an ensemble $\mathbf{x}_1 \dots \mathbf{x}_M$ both expectations are estimated without
bias, the pair term over distinct members only [@pacchiardi2024]:

$$
\widehat{\mathrm{ES}} = \frac{1}{M}\sum_{i=1}^{M} \|\mathbf{x}_i - \mathbf{y}\|
- \frac{1}{2M(M-1)}\sum_{i=1}^{M}\sum_{j \ne i} \|\mathbf{x}_i - \mathbf{x}_j\| \tag{2}
$$

Pacchiardi and colleagues write the estimator, in their Appendix C.1.1, for twice the score of
their Equation (33); Equation (2) is half of it. Because its expectation over members drawn
independently from a distribution is that distribution's score, an ensemble drawn from the
truth's own distribution scores best on average at any ensemble size, which is what makes the
score *fair* in Ferro's sense [@ferro2014]. On a single cell Equation (2) is exactly the fair
estimator `crps` uses. The plug-in form, dividing the pair sum by $2M^2$, would reward
underdispersed ensembles and depend on $M$. At $M = 1$ the pair term is empty and the score is
$\|\mathbf{x}_1 - \mathbf{y}\|$.

The index $\beta = 1$ is the one at which the score reduces to the CRPS; it is fixed, not a
parameter. A vector field's components are pooled into one vector, so the norm of a velocity
error is the root of the summed squares of both components over all cells. The score has no
per-cell decomposition, because a norm is not a sum over cells, so the metric has no
companion map.

Equation (2) is never negative: by the triangle inequality
$\|\mathbf{x}_i - \mathbf{x}_j\| \le \|\mathbf{x}_i - \mathbf{y}\| + \|\mathbf{x}_j -
\mathbf{y}\|$, and summing over the $M(M-1)$ ordered pairs bounds the pair term by the first
term. It reaches zero for a perfect ensemble, every member equal to the reference, and also
whenever the reference lies on the straight segment between every pair of members.

### Boundary handling

None. Equation (2) uses only norms of whole-field differences; no stencil, transform or
neighbourhood is involved, so the domain edge is never consulted and periodicity is
irrelevant.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence <name>`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence <name>`.

<!-- END GENERATED performance -->

## Intuition

This metric scores a prediction that is a set of possible whole fields rather than one field.
Like the continuous ranked probability score it asks two things at once — were the
possibilities close to what happened, and was their range honest — but it asks them of the
whole field together instead of one cell at a time.

It takes each member as one long list of numbers, all the values of the field, and measures
how far each member lies from the reference as a single straight-line distance through all
of them. The average of those distances rewards members that land near the truth. From it
the score subtracts half the average distance between pairs of members, which pays back
spread: a collapsed ensemble, all members on one guess, gets no credit, while an ensemble whose
members differ as much as the truth differs from them gets exactly the right amount. The
balance is struck so that, on average, nothing scores better than an ensemble drawn from the
same process as the truth.

A worked example, with fields of two cells and two members:

```
reference        member 1        member 2        result
0, 0             3, 4            0, 4            3
```

Member 1 lies 5 from the reference and member 2 lies 4, an average of 4.5. The two members
lie 3 apart; the pair term counts that distance once in each order and divides by four, a
credit of 1.5. The score is 4.5 − 1.5 = 3. Scored cell by cell with the continuous ranked
probability score, the same ensemble averages 2: the first cell's members straddle the truth
and score zero there, and only the whole-field distance sees that the member which is right
in one cell is wrong in the other.

What it ignores is position: a feature drawn in the right shape one cell away counts as two
errors, exactly as a cell-by-cell metric counts it.

## Reading the output

The score is in the field's own units, runs from zero upward, and lower is better. Zero is
reached by a perfect ensemble and also by an imperfect one whose reference lies between its
members on a straight line, such as two members placed either side of it: with few members
the floor does not single out the perfect forecast, which is the price of an estimator that
is unbiased at every ensemble size.

There is no absolute threshold for a good value. For members and a reference drawn
independently from one Gaussian process with standard deviation $\sigma$ per value and $d$
values in the field, the expected score is $\sigma\,\Gamma\bigl(\tfrac{d+1}{2}\bigr) /
\Gamma\bigl(\tfrac{d}{2}\bigr)$, close to $\sigma\sqrt{d/2}$ (a derivation of this card's,
from the mean of a chi distribution, pinned at $d = 4$ by the bundle's test of the fair
estimator): the score grows with the square root of the number of values, so it rises with
resolution and with the number of channels. Compare models only
on the same analysis grid and field. Comparisons across ensemble sizes are valid because the
estimator is fair, which is why `n_members` is recorded on every row.

Read it beside `crps`. Both are proper and both reward accuracy and honest spread together;
`crps` averages the error cell by cell, and the energy score sees how errors in different
cells combine in one member. When the energy score moves and the mean CRPS does not, the
change is in how the members' values vary together across the field.

## Limitations

The energy score is weak at the one thing a whole-field score is wanted for: telling a
forecast with the right spatial correlation from one with the wrong correlation but the same
spread at each cell. Scheuerer and Hamill's simulations show it detecting a wrong mean well and
a wrong correlation strength hardly at all, with the calibrated and miscorrelated ensembles'
scores overlapping [@scheuererhamill2015]. An ensemble whose members carry independent noise
at every cell, where the truth has smooth correlated structure, can therefore score nearly as
well as a correctly correlated one. A low energy score does not certify the ensemble's spatial
structure.

On a large field the score is dominated by the bulk of the values, as every norm over the
whole field is: an ensemble excellent everywhere except a small region near a shock reads as
good, because the error in that region is a small part of the total distance.

It also cannot say which of accuracy or dispersion moved. An accurate overconfident ensemble
and an inaccurate honest one can score the same; `spread_skill` and `rank_histogram` say which
half changed.

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

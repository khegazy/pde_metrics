---
name: member_shape
kind: degradation
---

## Definition

At each cell, with $\bar{x}$ and $\hat{s}$ the members' sample mean and standard deviation and
$\Phi$ the standard normal distribution function,

$$
z_m = \frac{x_m - \bar{x}}{\hat{s}}, \qquad
u_m = Q\bigl(\Phi(z_m)\bigr), \qquad
x_m' = \bar{x} + \hat{s}\,\frac{u_m - \bar{u}}{\hat{s}_u}, \tag{1}
$$

where $\bar{u}$ and $\hat{s}_u$ are the sample mean and standard deviation of the $u_m$ over the
members. $Q$ is the quantile function of the Student-t with $\nu = 1/s$ degrees of freedom
(family `student_t`), or of the two-piece normal with scale $1 - s$ below its mode and $1 + s$
above it (family `two_piece`; Jordan, Krüger and Lerch [@jordan2019], Appendix A.2.7), with $s$
the severity (`dataset_specs/08_synthetic_ensemble_extensions.md`, Section 3.4). The map is
increasing, so every member keeps its rank, and the last step restores the cell's sample mean
and variance exactly, so the ensemble-mean error and the spread-to-skill ratio are unchanged.

As the ensemble grows, the members tend to draws from the family with the truth's mean and
variance, whose expected CRPS against a normal truth is the closed form of Jordan et al.
(Appendix A.2.5) integrated over the truth: 0.5646, 0.5666, 0.5726 and 0.5914 per unit noise
level at $\nu$ = 10, 5, 3.3 and 2.5, against 0.5642 for the normal.
`tests/test_synthetic_ensemble.py` checks the values at $\nu$ = 5 and 2.5 against the
repository's `crps`.

### Boundary handling

None. Equation (1) acts cell by cell across the members; no neighbourhood is consulted.

## Intuition

This stands in for a surrogate whose ensemble has the right centre and the right width but the
wrong shape: members that occasionally stray far from the consensus while the rest huddle near
it, or that lean to one side. Any check that reads only the average and the spread of the
members passes such an ensemble.

At a weak setting nothing visible changes. At a strong one, the members that were already
furthest from the consensus move further out, and the rest move in to keep the width the same;
with the skewed family, members above the consensus spread out and those below it bunch up.

One cell of five members, mapped onto a Student-t of two and a half degrees of freedom:

```
before                          after (severity 0.4)
-1.26, -0.63, 0, 0.63, 1.26      -1.29, -0.56, 0, 0.56, 1.29
```

The mean (0) and the sample variance (0.99) are the same before and after, and the order of the
members is kept; the outer members have moved out and the inner ones in.

What this leaves untouched is every cell's member mean, member variance and member order.

## Severity scale

Severity is absolute and dimensionless. For `student_t` it is one over the degrees of freedom,
so 0.1 is a Student-t of ten degrees of freedom, close to normal, and 0.4 one of two and a half,
whose fourth moment is infinite. For `two_piece` it is the split of the two scales, from 0
(normal) towards 1 (all of the spread on one side); it must stay below 1. Zero is a no-op in
both. The two families are separate ladder entries, `heavy_tails` and `skew` in
`configs/degradation/ensemble_miscalibration.yaml`.

## Limitations

The members are re-standardised, so a small ensemble cannot hold the tails of a heavy-tailed
family: with 16 members the CRPS rises by less than the closed form says at small $\nu$, and
only approaches it as the ensemble grows.

The vocabulary of preserved properties can say that the member mean is kept, but not that
every cell's variance and every member's rank are kept as well; a test in
`tests/test_degradation_contract.py` checks those.

The member mean is kept exactly, so the field change measured on it is round-off, and the
profile ratio of damage per unit change divides by it (issue 111), as for `spread_inflate`.

A cell whose members all agree has no shape to change; the operator refuses it.

## What the degradation looks like

### The picture

<!-- GENERATED exemplars: written by `python -m fmeval.cards exemplars member_shape`, do not edit -->

Not generated yet. Run `python -m fmeval.cards exemplars member_shape`.

<!-- END GENERATED exemplars -->

The panel, once drawn, shows one member of a synthetic ensemble around the canonical field.
The field row barely changes. The difference row is where to look: it is largest where the
member already sat far from the consensus, and the distribution row shows the tails of the
member's departures growing with severity.

## References

\bibliography

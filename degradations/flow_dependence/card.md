---
name: flow_dependence
kind: degradation
---

## Definition

With $\bar{x}$ the member mean and $\hat{s}$ the sample standard deviation of the members at
each cell, every member's departure from the mean is rescaled so that the cell's spread becomes
$k \hat{s}^{a}$:

$$
x_m' = \bar{x} + k\,\hat{s}^{\,a-1}\,(x_m - \bar{x}), \qquad
k^2 = \frac{\langle \hat{s}^2 \rangle}{\langle \hat{s}^{2a} \rangle}, \tag{1}
$$

where $\langle \cdot \rangle$ averages over every cell and channel of the field. The exponent is
$a = 1 - s$ for the direction `damp` and $a = 1 + s$ for `amplify`, with $s$ the severity
(`dataset_specs/08_synthetic_ensemble_extensions.md`, Equation 4). The mean is unchanged at
every cell, and $k$ keeps the field's mean sample variance, so the ensemble-mean error and the
spread-to-skill ratio are unchanged exactly. Damp 1 ($a = 0$) gives every cell the same spread;
damp 2 ($a = -1$) inverts the spread, so the most uncertain cells become the most confident;
amplify 1 ($a = 2$) squares it.

Because Equation (1) is monotone in $\hat{s}$ for $a > 0$ and leaves every error alone, the
binned spread-error diagram of Leutbecher and Palmer [@leutbecherpalmer2008] (Section 2.2,
Figure 4) keeps its bins, and its log-log slope becomes the calibrated slope divided by $a$; a
negative $a$ reverses the bins. `tests/test_synthetic_ensemble.py` checks this to 1%.

### Boundary handling

None. Equation (1) acts cell by cell across the members; only the scalar $k$ pools the cells.

## Intuition

This stands in for a surrogate whose ensemble has the right amount of spread overall but puts
it in the wrong places. An ensemble that knows where it is uncertain spreads widely there and
narrowly elsewhere; one that does not spreads evenly, or, worse, spreads most where it should
be sure. Damping makes the spread more uniform than the uncertainty, amplifying makes it more
extreme.

At a weak setting a picture of one member barely changes. At damp 1 the quiet cells become as
noisy as the noisy ones and the noisy cells calm down, so the noise in a member looks uniform.
At damp 2 the pattern of noise is turned inside out.

Two cells of three members each, with spreads 1 and 3, damped at severity 1, which makes
the spread uniform:

```
cell    before          after (damp, severity 1)
A       -1, 0, 1        -2.24, 0, 2.24
B       -3, 0, 3        -2.24, 0, 2.24
```

The average variance of the two cells is 5, so both end with a spread of the square root of 5,
about 2.24. The means (0 in both) and the average variance are unchanged; only where the
spread sits has moved.

What this leaves untouched is the member mean at every cell and the average spread of the
whole field.

## Severity scale

Severity is the change of the exponent $a$, dimensionless and absolute: zero is a no-op, and
damage rises with severity in each direction. The two directions are separate ladder entries,
`flow_dependence_damp` and `flow_dependence_amplify` in
`configs/degradation/ensemble_miscalibration.yaml`, because a signed severity would put the
mildest case in the middle of one axis. Nothing is calibrated against a measured spectrum: an
exponent of the spread means the same thing on every field.

## Limitations

The operator can only rearrange the spread the members already have. On an ensemble whose true
spread is the same everywhere, which is the default `synthetic_ensemble`, the per-cell sample
spread varies by sampling noise alone, so the damped axis mostly removes noise and the
amplified one exaggerates it; the reader option `sigma_ratio` gives a true spread that varies
across the domain, which is where the axis means what its name says.

The member mean is kept exactly, so the field change measured on the member mean is round-off,
and the profile ratio of damage per unit change divides by it (issue 111), as for
`spread_inflate` and `spread_deflate`.

A cell whose members all agree has no spread to raise to a power below one; the operator
refuses such an ensemble for damping rather than dividing by zero.

## What the degradation looks like

### The picture

<!-- GENERATED exemplars: written by `python -m fmeval.cards exemplars flow_dependence`, do not edit -->

Not generated yet. Run `python -m fmeval.cards exemplars flow_dependence`.

<!-- END GENERATED exemplars -->

The panel, once drawn, shows one member of a synthetic ensemble around the canonical field.
Look at the difference row: it shows each member's departure from the consensus, which damping
makes uniform in amplitude by the middle column and inverts by the last. The field row barely
changes, because the consensus does not move.

## References

\bibliography

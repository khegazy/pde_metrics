# Wasserstein distance between increment distributions at every separation

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The idea as first planned compares the distributions of velocity increments, or of
gradients, in the prediction and the reference with the 1-Wasserstein distance $W_1$, rather
than transporting the fields themselves. Most of the gradient part is built. The
[increment_w1](../../metrics/increment_w1.md) metric compares the distributions of one-cell
increments along each axis. On the common analysis grid, a forward-difference gradient is
that one-cell increment divided by the grid spacing, and $W_1$ scales in proportion to its
argument, so $W_1$ between forward-difference gradient distributions is `increment_w1`
divided by the grid spacing.

What remains is the same comparison at separations larger than one cell. With
$\delta_\ell u = u(\mathbf{x} + \boldsymbol{\ell}) - u(\mathbf{x})$ the increment at a
separation $\boldsymbol{\ell}$, collect the increments of the prediction and of the reference
into two one-dimensional distributions and compare them with $W_1$ separately at each
separation $\ell$. The result is a curve rather than one number, so the scale at which the
prediction's statistics depart from the reference is visible. Two smaller remainders are
gradients from another derivative stencil, such as the one used for the
[velocity-derivative skewness](../turbulence_statistics/derivative_skewness.md), and
reporting longitudinal increments (a velocity component along its own direction) separately
from transverse ones, which `increment_w1` averages together.

In one dimension $W_1$ has a quantile form. If $F^{-1}$ and $G^{-1}$ are the quantile functions
(inverse cumulative distribution functions) of the two distributions, then

$$
W_1 = \int_0^1 \bigl| F^{-1}(t) - G^{-1}(t) \bigr| \, dt , \tag{1}
$$

which on samples amounts to sorting both and averaging the differences in order. The
comparison is cheap. It has no positivity problem, because a probability distribution is
already the nonnegative, unit-total object that transport requires (contrast
[transport between signed fields](signed_field_transport.md)). It is also sensitive to heavy
tails, meaning extreme values that are far more probable than a Gaussian distribution would
allow. The Kolmogorov–Smirnov distance, the largest gap between the two cumulative
distribution functions, is a weaker alternative: the cumulative functions differ little in
the tails, so it is insensitive to exactly the extreme values that $W_1$ weighs.

## Precedent

Physics-based generative models of turbulence are built on exactly these criteria. A
multiscale generative adversarial network uses "the variance, skewness and flatness of the
increments of the generated field that retrieve respectively the turbulent energy
distribution, energy cascade and intermittency across scales" (Granero Belinchon and Cabeza
Gallucci 2024). Flatness is the normalised fourth moment, a measure of how heavy the tails
are; intermittency is the tendency of turbulence to concentrate its activity in rare, intense
events. The same paper reports that plain GAN and Wasserstein-GAN baselines do not generate
fields with turbulent velocity statistics, which gives a ready-made negative control.

## Pitfalls

- A single value pooled over separations hides which scale failed; the per-separation curve
  is what localises it.
- The tails that make $W_1$ useful are, by definition, sparsely sampled, so many samples are
  needed for a stable value.

## Rationale

*The team's judgement.* High priority: it is among the cheapest ideas that are provably
orthogonal to $L^2$, it needs no mathematical gap closed first, and it measures intermittency
directly, which is the first thing an over-smoothed surrogate destroys. It pairs naturally
with [tail-index estimators](../distributional/tail_index_estimators.md).

## References

- Granero Belinchon, C. & Cabeza Gallucci, M. (2024). A multiscale and multicriteria
  generative adversarial network to synthesize 1-dimensional turbulent fields. *Machine
  Learning: Science and Technology* 5(2), 025032. <https://doi.org/10.1088/2632-2153/ad43b3>

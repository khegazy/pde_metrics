# Wasserstein distance between gradient distributions

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The Wasserstein distance between the distributions of one-cell increments already exists as
[increment_w1](../../metrics/increment_w1.md). This idea is the remaining part of the same
comparison: rather than transporting the field itself, collect the gradients of the
prediction and of the reference into two probability distributions, and compare those
one-dimensional distributions with the 1-Wasserstein distance $W_1$. The idea is stated for
velocity increments $\delta_\ell u = u(\mathbf{x} + \boldsymbol{\ell}) - u(\mathbf{x})$ at a
separation $\boldsymbol{\ell}$, or for gradients, so increments at separations larger than one
cell are also part of what remains.

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
allow.

## Precedent

Physics-based generative models of turbulence are built on exactly these criteria. A
multiscale generative adversarial network uses "the variance, skewness and flatness of the
increments of the generated field that retrieve respectively the turbulent energy
distribution, energy cascade and intermittency across scales" (Granero-Belinchón and Cabeza
Gallucci 2024). Flatness is the normalised fourth moment, a measure of how heavy the tails
are; intermittency is the tendency of turbulence to concentrate its activity in rare, intense
events. The same paper reports that plain GAN and Wasserstein-GAN baselines do not generate
fields with turbulent velocity statistics, which gives a ready-made negative control.

## Rationale

*The team's judgement.* High priority: it is among the cheapest ideas that are provably
orthogonal to $L^2$, it needs no mathematical gap closed first, and it measures intermittency
directly, which is the first thing an over-smoothed surrogate destroys. It pairs naturally
with [tail-index estimators](../distributional/tail_index_estimators.md).

## References

- Granero-Belinchón, C. & Cabeza Gallucci, M. (2024). A multiscale and multicriteria
  generative adversarial network to synthesize 1-dimensional turbulent fields. *Machine
  Learning: Science and Technology* 5(2), 025032. <https://doi.org/10.1088/2632-2153/ad43b3>

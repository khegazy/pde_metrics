# Structure functions and scaling exponents

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The structure function of order $p$ is the $p$-th moment of the longitudinal velocity
increment $\delta_\ell u_\parallel$ (defined on
[the four-fifths law page](four_fifths_law.md)) at separation $\ell$:

$$
S_p(\ell) = \bigl\langle (\delta_\ell u_\parallel)^p \bigr\rangle
\propto \ell^{\zeta_p} . \tag{1}
$$

In the inertial range each $S_p$ follows a power law in $\ell$ with a *scaling exponent*
$\zeta_p$. The idea is to compare the predicted and reference curves $S_p(\ell)$ in log–log
space, order by order, and to compare the fitted exponents. The only exponent fixed exactly
by theory is $\zeta_3 = 1$, from the [four-fifths law](four_fifths_law.md). Kolmogorov's 1941
theory predicts $\zeta_p = p/3$ for all orders; above third order, measured exponents fall
increasingly below that line, a departure called *anomalous scaling* that is the signature
of intermittency, the concentration of activity in rare intense events (Frisch 1995).
Because the increments are computed in physical space, structure functions remain usable on
irregular grids where a Fourier transform is not available.

A widely used model of the anomalous exponents is the She–Lévêque formula (She and Lévêque
1994),

$$
\zeta_p = \frac{p}{9} + 2 \left[ 1 - \left( \frac{2}{3} \right)^{p/3} \right] , \tag{2}
$$

which gives $\zeta_3 = 1$, consistent with the four-fifths law.

At the moderate Reynolds numbers of most simulations the inertial range is too short to fit
exponents directly. *Extended self-similarity* replaces the separation by the third-order
structure function as the independent variable, plotting $S_p$ against $S_3$; the relative
scaling $S_p \propto S_3^{\zeta_p / \zeta_3}$ then holds over a much wider range of
separations than the inertial range itself, which makes the exponents measurable at finite
Reynolds number (Benzi et al. 1993).

A Gaussian field has no anomalous scaling. Its even moments obey
$S_{2n} = (2n - 1)!!\, S_2^{\,n}$ at every separation, so $\zeta_{2n} = n\, \zeta_2$ is linear
in the order, and its odd moments vanish in expectation (see
[the four-fifths law page](four_fifths_law.md)). The second-order function $S_2$ is a linear
function of the [two-point correlation](../basis_decompositions/two_point_correlation.md) and
so carries only spectral information; the orders above two carry what the spectrum does not.

The built [increment_flatness](../../metrics/increment_flatness.md) is the ratio
$S_4 / S_2^2$ at a single separation of one cell, and
[increment_w1](../../metrics/increment_w1.md) compares the whole one-cell increment
distribution. This idea extends both to every separation and to the exponents.

## Precedent

Structure functions and their exponents are the standard physical-space description of
inertial-range turbulence (Frisch 1995), and extended self-similarity is the standard way to
extract exponents at moderate Reynolds number (Benzi et al. 1993).

## Pitfalls

- High-order moments are dominated by rare events and converge slowly. Large samples and
  bootstrap confidence intervals are needed; see
  [uncertainty on every metric value](../infrastructure/metric_uncertainty.md).
- Fitting $\zeta_p$ needs an identified scaling range, and the fitted value depends on the
  range chosen, so the range must be fixed by the evaluator and declared.
- The longitudinal form assumes near-isotropy.

## Rationale

*From the field guide; the team has not yet set a priority.* Structure functions give a
scale-resolved check of fidelity in physical space, they generalise the built one-cell
increment statistics to every scale, and their exponents above second order measure the
intermittency that an over-smoothed or Gaussian-like prediction loses.

## Keywords

structure functions, scaling exponents, anomalous scaling, intermittency, extended
self-similarity, She–Lévêque model, K41.

## References

- Benzi, R. et al. (1993). Extended self-similarity in turbulent flows. *Physical Review E*
  48, R29–R32. <https://doi.org/10.1103/PhysRevE.48.R29>
- Frisch, U. (1995). Turbulence: The Legacy of A. N. Kolmogorov. *Cambridge University
  Press*. <https://doi.org/10.1017/CBO9781139170666>
- She, Z.-S. & Lévêque, E. (1994). Universal scaling laws in fully developed turbulence.
  *Physical Review Letters* 72, 336–339. <https://doi.org/10.1103/PhysRevLett.72.336>

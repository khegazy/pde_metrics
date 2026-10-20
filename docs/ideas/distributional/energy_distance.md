# Energy distance

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The energy distance is a distance between two probability distributions, built from the
average distances between samples drawn from them. It belongs to the kernel family of
distances: it is in fact the *maximum mean discrepancy* (a distance that compares two
distributions through the averages of a chosen kernel function over their samples) with a
particular kernel. It is cheap to compute.

For distributions $P$ and $Q$, a kernel $k$, and independent draws $X, X' \sim P$ and
$Y, Y' \sim Q$, the squared maximum mean discrepancy is

$$
\mathrm{MMD}^2(P, Q) = \mathbb{E}\, k(X, X') + \mathbb{E}\, k(Y, Y') - 2\, \mathbb{E}\, k(X, Y),
\tag{1}
$$

and its sample estimate is the statistic of the *kernel two-sample test*, a test of whether
two sets of samples come from the same distribution (Gretton et al. 2012). The comparison can
be made on whole fields or on physically meaningful features of them, such as increments,
gradients or energy fluxes.

The energy distance and the maximum mean discrepancy both belong to the *integral probability
metrics*, distances of the form

$$
d_{\mathcal{F}}(P, Q) = \sup_{f \in \mathcal{F}} \left| \int f \, dP - \int f \, dQ \right|,
\tag{2}
$$

the largest difference in expectation over a class $\mathcal{F}$ of test functions (Müller
1997). The Wasserstein distance and the Kolmogorov–Smirnov distance are members too, with
other classes $\mathcal{F}$. They differ in kind from the *f-divergences*, such as the
Kullback–Leibler and Jensen–Shannon divergences, which compare the ratio of the two
densities. An f-divergence is unstable when the two distributions have disjoint support, as
a prediction and a reference with slightly displaced sharp features can, whereas an integral
probability metric remains well behaved there. The two classes are not interchangeable.

## Pitfalls

- The energy distance does some averaging, and is therefore a poor tool for heavy tails,
  meaning extreme values that occur far more often than a Gaussian distribution would
  predict. This is exactly why a Wasserstein distance is preferred for comparing
  distributions here, as in [increment_w1](../../metrics/increment_w1.md) and the
  [Wasserstein distance between gradient distributions](../optimal_transport/gradient_pdf_w1.md).
- The maximum mean discrepancy depends on the choice of kernel and its bandwidth, which must
  be fixed once and declared.
- A single number for a whole field hides which physics failed. Computed on interpretable
  features such as increments, gradients or fluxes, it says more.

## Rationale

*The team's judgement.* Medium priority: it is worth keeping as a cheap baseline that shows
the difference between an averaging distance and a transport distance on heavy-tailed data,
but it is not expected to outperform the Wasserstein distance.

## Keywords

maximum mean discrepancy, kernel two-sample test, integral probability metric, f-divergence,
disjoint support.

## References

- Gretton, A., Borgwardt, K. M., Rasch, M. J., Schölkopf, B. & Smola, A. (2012). A kernel
  two-sample test. *Journal of Machine Learning Research* 13, 723–773.
  <https://jmlr.org/papers/v13/gretton12a.html>
- Müller, A. (1997). Integral probability metrics and their generating classes of functions.
  *Advances in Applied Probability* 29, 429–443. <https://doi.org/10.2307/1428011>

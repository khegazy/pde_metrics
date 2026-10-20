# Negative Sobolev norms of general order

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The homogeneous Sobolev norm of order $-1$, written $\dot H^{-1}$, is built already as
[h_minus_one](../../metrics/h_minus_one.md). This idea is the part that remains: Sobolev
norms $H^{-s}$ of general negative order $-s$, and dual norms. A Sobolev norm of order $s$
weights each Fourier coefficient of a field by $|\mathbf{k}|^{s}$, where $\mathbf{k}$ is the
wavevector, so a negative order suppresses fine scales instead of emphasising them. A dual
norm measures a field by the largest correlation it can have with any test function of unit
size in a chosen smooth norm; $H^{-s}$ is the dual of $H^{s}$ in this sense.

Negative-order norms are the opposite of the $H^1$ norm. They are *weaker* than $L^2$: they
metrize weak convergence, meaning that a sequence of fields converges in such a norm when its
averages against every smooth test function converge, even if the fields themselves keep
oscillating. They remain finite for rough and discontinuous fields. Most importantly, they
are quantitatively close to the [Wasserstein distance](../optimal_transport/wasserstein.md),
the cost of moving one field's mass onto the other's. On a periodic domain the $\dot H^{-1}$
norm is computed by dividing the Fourier coefficients by $|\mathbf{k}|$, so its cost is one
fast Fourier transform.

The relationship to the quadratic Wasserstein distance $W_2$ is a theorem rather than an
analogy. For an infinitesimal perturbation $d\mu$ of a probability measure $\mu$, the two
agree to first order:

$$
W_2(\mu, \mu + d\mu) = \| d\mu \|_{\dot H^{-1}(\mu)} + o(d\mu) \tag{1}
$$

where $\dot H^{-1}(\mu)$ is the $\dot H^{-1}$ norm weighted by $\mu$. Peyre integrates this
linearisation into a non-asymptotic two-sided bound. If $\mu$ and $\nu$ have densities $f$
and $g$ with $0 < a < f, g < b < \infty$, then

$$
b^{-1/2} \, \| f - g \|_{\dot H^{-1}(dx)} \le W_2(\mu, \nu) \le
a^{-1/2} \, \| f - g \|_{\dot H^{-1}(dx)} \tag{2}
$$

where $\dot H^{-1}(dx)$ is the unweighted norm (Peyre 2018). The two distances are therefore
equivalent up to constants set by the density bounds $a$ and $b$. The bound concerns order
$-1$ specifically.

## Pitfalls

- Equation (2) degrades as $a \to 0$, that is, when the field has near-vacuum regions. The
  equivalence is good when mass is spread out over the domain and poor when the
  distribution has regions of very high and very low density. This much is a direct reading
  of the bound's hypotheses.
- *The team's inference, not a result of the paper:* a density field with strong
  rarefactions may sit in the regime where $\dot H^{-1}$ is a weak proxy for $W_2$, whereas a
  well-mixed vorticity-magnitude field should sit comfortably inside the good regime. This is
  worth checking on real data across the degradation ladder rather than assuming.

## Rationale

*The team's judgement.* High priority: the family is nearly free to implement given a fast
Fourier transform, it is well defined for discontinuous fields where $H^1$ is not, and the
bound above makes precise the sense in which it approximates the transport distance that is
actually wanted. Among all the ideas, it offers the most value per line of code.

## Keywords

negative Sobolev norm, dual norm misfit, $\dot H^{-1}$ metric, weak convergence
metrization, Benamou–Brenier formula.

## References

- Peyre, R. (2018). Comparison between $W_2$ distance and $\dot H^{-1}$ norm, and localization
  of Wasserstein distance. *ESAIM: Control, Optimisation and Calculus of Variations* 24(4),
  1489–1501. <https://doi.org/10.1051/cocv/2017050>

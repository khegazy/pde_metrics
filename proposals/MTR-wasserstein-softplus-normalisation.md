---
type: MTR
kind: variant of docs/ideas/optimal_transport/signed_field_transport.md
related: ["docs/ideas/optimal_transport/signed_field_transport.md", "docs/ideas/optimal_transport/wasserstein_signed_fields.md", "wasserstein", "issues/047"]
seen_in: "Engquist & Yang 2022, Commun. Pure Appl. Math. 75(10), 2201-2244"
doi: "10.1002/cpa.21990"
found_by: "wasserstein, 2026-10-31"
---

# MTR: Wasserstein distance on signed fields through an exponential or softplus normalisation

## What it measures

The quadratic Wasserstein distance between two signed fields (velocity components, vorticity)
after each is mapped to a positive density by a smooth, one-to-one scaling function and
divided by its total. It measures the cost of rearranging the mapped mass, as `wasserstein`
does for density.

## Definition

Engquist & Yang (2022), Eqs. (3) and (4) (arXiv:2002.00031 numbering, compiled), give the
exponential and softplus normalisations

    f~ = exp(b f) / <exp(b f)>,      f~ = log(exp(b f) + 1) / <log(exp(b f) + 1)>,   b > 0,

and their Assumption 4.1, Eq. (19), the general class (sigma(f) + c) / integral of
(sigma(f) + c), with sigma smooth, positive and one-to-one and a buffer constant c >= 0.
Their Theorem 4.2 shows that W_2(P f, P g) is then a metric on signed functions. The
exponential form is attributed to Qiu et al. (2017). The distance itself would be computed by
the Monge-Ampere solver already in `metrics/wasserstein`, unchanged.

## Relation to existing work

`issues/047` lists four formulations for signed fields: split into positive and negative
parts, add a constant and renormalise, unbalanced transport, and graph-space transport. The
smooth one-to-one scalings are a fifth family, not on that list. The "add a constant" option
is the linear member of the family (sigma linear). The exponential and softplus members
differ: they amplify the positive part, so they are not symmetric in the sign of the field
(Engquist & Yang note one can add the same term applied to -f).

## How it could be tested

On kinet velocity and vorticity with the existing ladder, exactly as `wasserstein` is on
density. The background-ratio experiment (EXP-wasserstein-background-ratio-sweep) would show
how the hyperparameters b and c move the metric between the s^2 and s regimes.

## Why it is helpful

It gives issue 047 a documented option with a metric proof (their Theorem 4.2) and a
smoothness result for the optimal map. It also exposes the hyperparameters b and c, which
must be fixed once and never tuned per model, as the repository's rule on thresholds says.

## References

- Engquist, B. & Yang, Y. (2022). Optimal transport based seismic inversion: beyond cycle
  skipping. Commun. Pure Appl. Math. 75(10), 2201-2244. doi:10.1002/cpa.21990 (arXiv:2002.00031).
- Qiu, L. et al. (2017). Full-waveform inversion with an exponentially encoded optimal
  transport norm. SEG Technical Program Expanded Abstracts. Not opened; cited through
  Engquist & Yang (2022).

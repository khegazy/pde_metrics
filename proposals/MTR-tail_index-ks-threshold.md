---
type: "MTR"
kind: "variant of tail_index"
related: ["metrics/tail_index", "docs/ideas/distributional/tail_index_estimators.md"]
seen_in: "Clauset, Shalizi & Newman 2009, SIAM Rev. 51(4), 661-703"
doi: "10.1137/070710111"
found_by: "tail_index, 2026-10-30"
---

# MTR: Power-law exponent with a Kolmogorov-Smirnov threshold and a goodness-of-fit p-value

## What it measures

The power-law exponent of the largest absolute increments, with the threshold x_min above which
the power law is fitted chosen from the data, and, beside it, the p-value of the hypothesis that
the tail above x_min is a power law at all.

## Definition

Clauset, Shalizi and Newman (2009): the exponent is Eq. (3.1), alpha_hat = 1 + n [sum_i ln(x_i /
x_min)]^-1 over the n values at or above x_min (equivalent to Hill's estimator; the tail index is
alpha_hat - 1 for the survival function). x_min is the value minimising the Kolmogorov-Smirnov
distance D = max_{x >= x_min} |S(x) - P(x)| between the data's and the fitted model's
distribution functions, Eq. (3.9), Sect. 3.3. The goodness-of-fit p-value is the fraction of
synthetic power-law samples whose fitted D exceeds the data's, Sect. 4.1.

## Relation to existing work

`tail_index` fixes k = ceil(sqrt(n)) for every field and variant (Sect. 3.5 of the same paper
names that rule) and stores the Hill plot as its curve. This variant chooses k per sample. The
reason `tail_index` does not do so is that each variant would then be read at a different order,
which the repository's rule of fixing thresholds once argues against; the p-value, however, is
information `tail_index` cannot give and is the paper's main recommendation (Sects. 4 and 5).

## How it could be tested

On the ladder, `additive_noise` drives the increments toward a Gaussian, whose p-value for a power
law should fall to zero as the sample grows. The more useful test is a diagnostic one: the p-value
on the clean reference says whether `tail_index` can be read as an exponent at all on that field.

## Why it is helpful

It answers the question `tail_index`'s card can only warn about: whether the increments have a
power-law tail. A semi-parametric bootstrap per field and frame is expensive (Sect. 4.1 uses on the
order of a thousand synthetic samples), so it suits a one-off diagnostic of a dataset rather than
a per-row metric.

## References

- Clauset, A., Shalizi, C. R. & Newman, M. E. J. (2009). Power-law distributions in empirical
  data. *SIAM Review* 51(4), 661-703. doi:10.1137/070710111 (read in full, arXiv:0706.1062).

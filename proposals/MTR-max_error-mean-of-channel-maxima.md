---
type: "MTR"
kind: "variant of max_error"
related: ["metrics/max_error", "metrics/rmse", "metrics/nrmse"]
seen_in: "Takamoto et al. 2022, Advances in Neural Information Processing Systems 35 (Datasets and Benchmarks Track), 1596-1611"
doi: "10.52202/068431-0117"
found_by: "max_error, 2026-10-30"
---

# MTR: Maximum error averaged over channels (PDEBench's reduction)

## What it measures

The worst-cell error of each component of a vector field separately, averaged over the
components. It is the maximum error exactly as PDEBench's code computes it, so a number from
this repository could be set beside a PDEBench leaderboard entry.

## Definition

For $C$ channels and $N$ cells,

$$
\mathrm{MaxE}_{\text{PDEBench}}(f, g) = \frac{1}{C} \sum_{c=1}^{C} \max_{1 \le i \le N} \bigl| f_{c,i} - g_{c,i} \bigr| \tag{1}
$$

PDEBench's paper gives no equation for the maximum error (Sect. 3.3 names it, Appendix B says
it "measures the model's worst prediction"); Equation (1) is read off `metric_func` in
`pdebench/models/metrics.py`, which takes the maximum over space per channel and time step,
the maximum over the batch, and then the mean over channels and time steps when `if_mean` is
set. In this repository's harness one frame is scored at a time, so only the channel mean
remains.

## Relation to existing work

`max_error` registers the maximum over channels and cells pooled, $\max_c \max_i |f_{c,i} -
g_{c,i}|$, to match how `mae` and `mse` pool channels. The two agree on every one-channel field
(density, vorticity) and differ only on velocity, where Equation (1) is never larger than the
pooled maximum and at least half of it for two channels. The same split exists for RMSE:
PDEBench averages per-channel RMSEs, while `rmse` pools channels before the square root.

## How it could be tested

On the existing ladder, velocity only; every enabled axis that `max_error` follows applies.
A sibling bundle importing nothing new would be one line.

## Why it is helpful

Only for comparability with published PDEBench numbers; it carries no information the pooled
maximum lacks about where a prediction is worst.

## References

- Takamoto, M., Praditia, T., Leiteritz, R., MacKinlay, D., Alesiani, F., Pflüger, D. &
  Niepert, M. (2022). PDEBench: An Extensive Benchmark for Scientific Machine Learning.
  *Advances in Neural Information Processing Systems 35*, 1596–1611, Sect. 3.3 and
  Appendix B. doi:10.52202/068431-0117. Code:
  <https://github.com/pdebench/PDEBench/blob/main/pdebench/models/metrics.py>.

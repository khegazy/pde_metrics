# 010 — `nrmse` is PDEBench's nRMSE; the fluctuation-normalised error is `vrmse`, The Well's VRMSE

**Date:** 2026-11-04. **Made by:** the agent of task `metrics-pointwise` (branch from
`update_metric_eval_principles`), on the orchestrator's decision, which Kareem delegated
("This question is too detailed for me ... Determine this for yourself", 2026-11-03).
**Reverse with:** `git mv metrics/vrmse metrics/nrmse` after deleting the new
`metrics/nrmse/`, restore the old `nrmse` body (pooled RMSE over the pooled `fluctuation_rms`,
NaN on a uniform reference) from the commit before this one, put `nrmse` back in
`fmeval/analysis.py::DAMAGE_BLOCK_CONTROLS`, `configs/config.yaml` and the documents this commit
touched, delete this file and its row in `README.md`, and regenerate every card's evidence.

## The question that would have been asked

The bundle named `nrmse` divided the RMSE by the root mean square of the reference's
**fluctuation** about its spatial mean (`fmeval/context.py::fluctuation_rms`). PDEBench's nRMSE,
the metric a reader expects under that name, divides by the root mean square of the reference
itself, with no mean removed; the fluctuation-normalised error is The Well's VRMSE. Keep the name,
or rename the bundle to what it computes, and if so, which number does `nrmse` then report?

## The choice

**The bundle is renamed `vrmse` and computes The Well's VRMSE exactly; a new `nrmse` computes
PDEBench's nRMSE exactly.** Both reduce per channel and average over channels.

- **PDEBench** [Takamoto et al. 2022, NeurIPS 35 Datasets and Benchmarks, App. B, unnumbered
  equation; code `pdebench/models/metrics.py`, `metric_func`, `err_nRMSE`]: per sample, channel
  and time step, `sqrt(mean((pred - target)**2)) / sqrt(mean(target**2))` over space, no constant,
  then the mean over samples, channels and time steps. In this harness, one frame of one field, the
  mean over channels remains.
- **The Well** [Ohana et al. 2024, NeurIPS 37 Datasets and Benchmarks, App. E.3; code
  `the_well/benchmark/metrics/spatial.py`, `VRMSE` through `NMSE(norm_mode="std")`]: per field,
  `sqrt(mean((x - y)**2) / (torch.std(y)**2 + 1e-7))`. `torch.std` divides by the cell count less
  one; the constant is added to the variance, in the field's units squared. The library reports
  each field and the mean over fields (`the_well/benchmark/trainer/training.py`,
  `split_up_losses`, the `full` entry), and the paper's tables report that mean (Sect. 4, Table 2,
  "averaged over all physical fields"). One float per field here is therefore the mean of the
  per-channel values.

Both sources were read in their code on 2026-11-04 (GitHub `main` of PDEBench, `master` of The
Well) and in their arXiv sources (2210.07182, 2412.00568).

## What it changes

- Every number reported as `nrmse` before this change is now reported as `vrmse`, with three
  differences from the old definition: per channel then averaged, rather than pooled (velocity
  only); the variance divided by the cell count less one (a factor $\sqrt{(N-1)/N}$ on the value,
  $1 - 7.6 \times 10^{-6}$ on a $256^2$ grid); and $10^{-7}$ added to the variance. On a
  one-channel field the last two cancel from damage, so density and vorticity damage numbers are
  unchanged and the values move by the factor $\sqrt{s^2/(s^2 + 10^{-7})}$, 0.989 to 0.9989 on
  density over the evidence window (from `AGENTS.md` §4's fluctuation root mean square). On the
  development dataset, whose density fluctuation is about $10^{-8}$ of its mean, the constant is
  the whole denominator. A uniform reference now gives a finite value instead of NaN.
- The new `nrmse` is near zero on density for every degradation: density's mean is 1 and its
  fluctuation root mean square is $2.1 \times 10^{-3}$ to $6.7 \times 10^{-3}$ over the evidence
  window, so the denominator is the mean and the value is that factor below `vrmse`. That is
  PDEBench's definition behaving as The Well says it does on such fields (Sect. 4, Results), and
  the card says so.
- `vrmse` replaces `nrmse` among the pointwise controls of every card's damage table
  (`fmeval/analysis.py::DAMAGE_BLOCK_CONTROLS`) and in the default `metrics` of
  `configs/config.yaml`, so that both keep the fluctuation-normalised error they had.
- The old card's evidence was removed with the old definition; both cards are regenerated in the
  orchestrator's final evidence pass.

## Why not keep the name

A reader from PDEBench who opens a page called `nrmse` and finds a mean-removed denominator gets
a number that differs from theirs by two to three orders of magnitude on density; the repository's
rule is that a metric's page must match its field's standard (`AGENTS.md` §1, "How every metric is
evaluated"). Keeping only The Well's form under a new name would leave PDEBench's nRMSE unbuilt,
which the same rule's "several standards: build them all" forbids.

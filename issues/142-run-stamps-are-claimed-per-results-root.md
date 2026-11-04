# Run stamps are claimed per results root, but cards find runs by folder name in one place

**Category:** technical debt
**Priority:** low
**Status:** open.

## Context

`fmeval.io.claim_stamp` makes a run's `<name>_<stamp>` unique by creating
`<results_root>/.stamps/<stamp>` with `mkdir`, which is atomic across processes. The claim is
made under the run's own results root (`paths.results`). A card, though, finds every run it cites
by folder name under the one `results/` directory of the checkout (`fmeval.cards.catalog`,
`recorded_runs`), where runs kept elsewhere are linked in.

## Evidence

In the final evidence pass of `update_metric_eval_principles` (2026-11-04), three runs were started
in the same second under three results roots, `final_pass/sod_shock_tube`,
`final_pass/synthetic_ensemble` and `final_pass/forecast_re5e4`. Each claimed stamp 1793811840 in
its own root, so three folders named `comparison_1793811840` existed, which could not all be
linked into `results/`. Sod and the ensemble were re-run to get distinct stamps (logs and the
superseded Sod folder are kept in that effort's `agent_logs/.../final_pass/`).

## What would settle it

Claim stamps in one place shared by every results root (for example the checkout's
`results/.stamps`, or a fixed directory under the user's scratch), or make a run's identity
include its root. Either keeps `claim_stamp` the only source of a stamp.

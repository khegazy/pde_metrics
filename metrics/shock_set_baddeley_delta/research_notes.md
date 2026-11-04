# Research notes: shock_set_baddeley_delta

Built on 2026-11-04 by the agent of task `metrics-topology-shocks` on the branch
`update_metric_eval_principles`, from `proposals/MTR-shock_set_distance-other-surface-distance-summaries.md`
(narrowed in the same change to what is not built). The card is the source of truth; the task log
`agent_logs/2026-11-03-update_metric_eval_principles/task-metrics-topology-shocks.md` holds the
commands. The detector, the empty-set conventions and their sources are `shock_set_distance`'s:
read its notes first.

## Summary

The bundle registers Baddeley's Delta with p = 2 and no cutoff: the root mean square over every cell of the difference of the two sets' Euclidean distance maps, on the shock sets of `shock_set_distance`'s detector, with that
bundle's checks, cache, channel mean and empty-set conventions imported (`shock_set_score`,
`set_distance`). It is one of four siblings built together so that each standard summary the
medical-segmentation and spatial-verification fields report is its own bundle.

## Sources

| Source | How it was read | Locator | What it gave | Where it is used |
|---|---|---|---|---|
| spatstat.geom `deltametric` | Documentation (rdrr.io) and source `R/deltametric.R` (GitHub raw) through a summarising fetch tool | Details; source | The definition (mean over the window of |w(dA) - w(dB)|^p, ^(1/p), w = min(t, c)), defaults p = 2, c = Inf, the Hausdorff limit | `metric.py`, card |
| SpatialVx `locmeasures2d` / `LocMeasures.R` | Documentation and CRAN-mirror source through a summarising fetch tool | "bdelta"; `locmeasures2dPrep` | p = 2 default; bdconst set to Inf when NULL; computed by spatstat's deltametric | Card |
| Gilleland 2011, Weather Forecasting 26(3), 409-415, doi 10.1175/WAF-D-10-05061.1 | Abstract only (Crossref); the AMS page, the UCAR OpenSky PDF and scholar.archive.org refused automated fetches | Abstract | Delta as "a mathematical displacement metric" on the ICP test cases | Card |
| Baddeley 1992 | Not opened | — | Only the bibliographic data, as SpatialVx lists them | `refs.bib` |
| Schaal & Springel 2015, MNRAS 446, 3992 (arXiv HTML 1407.4117v2) | Through a summarising fetch tool, for the validation section | Sect. 3.1, Fig. 1; Sect. 3.2, Fig. 2, Table 1 | How shock detection validates a finder: Sedov-Taylor cross-section and surface area, shock-tube Mach histograms | `shock_set_distance`'s card, referenced here |

## Method choices

p and c are the implementation's defaults; Gilleland's own values could not be read (card, How its field reports it). The empty-set conventions are `shock_set_distance`'s, and the diagonal bounds Delta because |d(x, A) - d(x, B)| never exceeds the Hausdorff distance. Every flagged cell is a point of the set, as in `shock_set_distance` (the field's
code erodes masks to their border; a detected shock is one to three cells thick). The line-out
figure's companions are `shock_set_distance`'s `shock_positions` and `pressure_profile`,
registered for this metric by a call.

## Rejected formulations and negative results

None specific to this bundle; the scores not built (fractions skill score, critical success
index, equitable threat score) and why are on `shock_set_distance`'s card.

## Evidence runs

Smoke run on `sod_shock_tube` with the whole shock family (folder in the task log); the
orchestrator runs the evidence.

## Corrections to the rest of the repository

None specific to this bundle.

## Review round

Not yet reviewed.

## Open questions and follow-ups

- The empty-set conventions: `issues/102`. The blindness misreading of a flag-valued anchor:
  `issues/104`.
- Two-dimensional shock data: `issues/002`, `proposals/EXP-shock_set_distance-2d-shock-dataset.md`.

## For the next agent

- Code sources were read through a summarising fetch tool, which quotes short excerpts; the
  quoted lines are recorded in `refs.bib`.

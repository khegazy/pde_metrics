# Research notes: shock_set_masd

Built on 2026-11-04 by the agent of task `metrics-topology-shocks` on the branch
`update_metric_eval_principles`, from `proposals/MTR-shock_set_distance-other-surface-distance-summaries.md`
(narrowed in the same change to what is not built). The card is the source of truth; the task log
`agent_logs/2026-11-03-update_metric_eval_principles/task-metrics-topology-shocks.md` holds the
commands. The detector, the empty-set conventions and their sources are `shock_set_distance`'s:
read its notes first.

## Summary

The bundle registers the mean average surface distance, the mean of the two directed mean nearest-cell distances, on the shock sets of `shock_set_distance`'s detector, with that
bundle's checks, cache, channel mean and empty-set conventions imported (`shock_set_score`,
`set_distance`). It is one of four siblings built together so that each standard summary the
medical-segmentation and spatial-verification fields report is its own bundle.

## Sources

| Source | How it was read | Locator | What it gave | Where it is used |
|---|---|---|---|---|
| MetricsReloaded `metrics/pairwise_measures.py` | Raw source through a summarising fetch tool | `measured_masd` | 0.5 * (mean of one direction + mean of the other) | `metric.py`, card |
| Maier-Hein et al. 2024, Nature Methods 21, 195-212 | Not re-read; the recommendation is as `shock_set_distance`'s notes record it (Suppl. Note 2.3) | Suppl. Note 2.3 | MASD recommended over ASSD when errors are penalised by distance | Card |
| SpatialVx `locmeasures2d` | Documentation through a summarising fetch tool | measure "med" | Directed mean error distances reported per field | Card |
| Schaal & Springel 2015, MNRAS 446, 3992 (arXiv HTML 1407.4117v2) | Through a summarising fetch tool, for the validation section | Sect. 3.1, Fig. 1; Sect. 3.2, Fig. 2, Table 1 | How shock detection validates a finder: Sedov-Taylor cross-section and surface area, shock-tube Mach histograms | `shock_set_distance`'s card, referenced here |

## Method choices

The formula is taken from the consortium's code; whether the paper's cheat sheet states the same formula was not checked (no agent could read it); Beneš & Zitová 2015, the origin per Metrics Reloaded, was not opened. Every flagged cell is a point of the set, as in `shock_set_distance` (the field's
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

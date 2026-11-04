# Research notes: persistence_wasserstein

Built on 2026-11-04 by the agent of task `metrics-topology-shocks` on the branch
`update_metric_eval_principles`, from `proposals/MTR-persistence_distance-wasserstein-diagram-distance.md`
(narrowed to p = 2 in the same change). The card is the source of truth; the task log
`agent_logs/2026-11-03-update_metric_eval_principles/task-metrics-topology-shocks.md` holds the
commands. The diagrams, and everything read about them, are `persistence_distance`'s: read its
notes first.

## Summary

The bundle registers the 1-Wasserstein distance with the L-infinity ground norm between the two
fields' sublevel-set persistence diagrams, summed over homology dimensions, on the diagrams
`persistence_distance` computes. It is the field's other standard distance between diagrams, the
sum where the bottleneck distance takes the maximum. It is computed by Hera at a relative error of
1e-6, on the finite points and the points at infinity separately, because Hera crashes the process
on one mixed case.

## Sources

| Source | How it was read | Locator | What it gave | Where it is used |
|---|---|---|---|---|
| Cohen-Steiner, Edelsbrunner, Harer & Mileyko 2010, Found. Comput. Math. 10(2), 127-139 | Full text: the authors' copy (pub.ista.ac.at/~edels/Papers/2010-01-LpStablePersistence.pdf), text extracted with Ghostscript (`gs -sDEVICE=txtwrite`) | Sect. 3, paragraph "Wasserstein distance"; Sect. 3, Wasserstein Stability Theorem; Sect. 4 | The degree-p Wasserstein distance, the p-th root of the sum over all dimensions and matched points of the p-th power of the L-infinity distance; stability for tame Lipschitz functions; "we suggest using W_2" for gene-expression clustering | Card Equations (1)-(2), `metric.py`, `refs.bib`, judgement 018 |
| Skraba & Turner 2020, arXiv:2006.16824v7 | arXiv HTML through a summarising fetch tool (two passes) | Definitions 2.4, 2.5; Remark 2.6; Theorems 4.6, 5.1 | Points at infinity matched only among themselves; the total p-Wasserstein distance over dimensions; the literature's (p, q) discrepancy and their p = q choice; the cellular stability bound used in `test_metric.py` | Card, `metric.py`, tests |
| GUDHI 3.13.0, `gudhi.wasserstein.wasserstein_distance` and `gudhi.hera.wasserstein_distance` | Installed docstrings and signatures | — | Defaults `order=1.0`, `internal_p=inf`; Hera's "Relative error 1+delta", points at infinity supported | `metric.py`, card |
| giotto-tda 0.4.0, `gtda/diagrams/distance.py` | Module source page through a summarising fetch tool | `PairwiseDistance` docstring | `p` default 2., `delta` default 0.01, "an exact algorithm is not available", dimensions combined by a p-norm of order 2 | Card, judgement 018 |
| R package TDA, `wasserstein` | rdrr.io documentation | Usage | `p = 1` default, one dimension per call | Card |
| GUDHI 3.13 manual, "Persistence graphical tools" reference | Web page through a summarising fetch tool | `plot_persistence_diagram` | Infinite deaths placed above the largest death; colour by dimension; the grey lower half-plane | Card, "How its field reports it" |

## Method choices

- **p = 1 and the L-infinity ground norm**, GUDHI's defaults; p = 2 left as a proposal for
  evaluation cost (judgement 018).
- **Sum over dimensions** (Skraba & Turner, Definition 2.5, at p = 1; Cohen-Steiner et al. 2010).
  giotto-tda combines by a 2-norm; not registered.
- **Hera at delta = 1e-6.** The exact optimal-transport route builds a dense matrix of about
  15000 by 15000 points on a 256 x 256 vorticity field. On that field the value at 1e-6 differed
  from 0.01 by 2.3e-4 relative, at 1.5 times the cost (task log, Runs). On the 16 x 8 test field
  Hera at 1e-6 equals GUDHI's exact solver (`test_metric.py`).
- **Finite and infinite parts computed separately.** See code_notes.md, Bugs and fixes.
- **Not run on `sod_shock_tube` or `synthetic_ensemble`** (`card.yaml`, `not_run`): Sod's exact
  density is non-increasing along the tube at every frame, so its diagram is the single point
  (0.125, inf) (measured on all ten frames); the ensemble's axes either leave the member mean
  unchanged or add a uniform offset.

## Rejected formulations and negative results

- **The exact POT route** for the registered number: too slow and too large on real fields.
- **p = 2**: see judgement 018.

## Evidence runs

Smoke runs only (the orchestrator runs the evidence): `kinet_re5e4_dev` and `forecast_re5e4` at
`analysis_grid.resolution=64`, folders and outcomes in the task log.

## Corrections to the rest of the repository

None beyond the narrowed proposal.

## Review round

Not yet reviewed.

## Open questions and follow-ups

- p = 2: `proposals/MTR-persistence_distance-wasserstein-diagram-distance.md`.
- The cost of a full 256 x 256 ladder (judgement 018, estimate of days) means the evidence run may
  need the 128 grid or a sparser time window; that is the orchestrator's call.

## For the next agent

- The cellular stability bound of `test_metric.py` uses GUDHI's own filtration of every cell; that
  Skraba & Turner's Theorem 4.6 covers this complex is the bundle's reading, as on
  `persistence_distance`.
- The Hera crash (code_notes.md) was found by probing; other mixed cases were not searched
  exhaustively.

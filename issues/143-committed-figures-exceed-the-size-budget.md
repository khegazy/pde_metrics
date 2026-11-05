# The committed generated files exceed the 40 MB budget and the 50 MB line for Git LFS

**Category:** data / repository
**Priority:** high — `tests/test_cards.py::test_committed_figures_fit_the_size_budget` fails
**Status:** open. Needs Kareem's decision (`docs/decisions.md`, "Known risks": past roughly 50 MB
the fallback is Git LFS — raise the question, do not delete panels or figures).

## Context

`update_metric_eval_principles` runs every metric on every experiment where it makes sense
(`AGENTS.md` §1) and builds every field's standard as its own bundle. The repository now has 39
metric cards, most citing three to five runs (kinet_re5e4, sod_shock_tube, synthetic_ensemble,
forecast_re5e4, kinet_re1e6), each further run with its own tables and figures, and each card
leading with its field's standard figure. The generated files grew accordingly.

## Evidence

Measured after the first regeneration of 2026-11-04 from the final-pass runs, before the dense
curves were thinned, with every committed generated file the size test
counts:

| What | Size |
|---|---|
| total | 107.3 MB |
| `tail_index`'s classical Hill plot JSON (three fields, every order k = 1 to 6553) | 32.4 MB |
| everything else | 74.4 MB |

of which, by figure type: `companion_points.json` 13.7 MB (six shock cards draw the same
2048-cell line-outs, 1.7 MB each; persistence diagrams 3.4 MB), `fingerprint.json` 11.4 MB,
degradation `exemplars.png` 7.3 MB, `response_curves.svg` 7.0 MB, `sensitivity_profile.svg` 5.9 MB,
`response_curves.json` 4.8 MB, `damage_beside_controls.svg` 4.5 MB, `companion_curves.svg` 4.3 MB,
`response_along_time.svg` 3.8 MB, and smaller ones.

The dense curves are now drawn at most at 256 evenly spaced coordinates plus the analysed ones
(`fmeval/report/plots.py::_DENSE_DRAWN`). After the final regeneration of 2026-11-04 (20:01), with
that thinning and no figure dropped, the test measured **76.8 MB**, and **79.3 MB** once the
overview figures were redrawn from `comparison_1793846511` and the readings written. The largest files are
`persistence_distance/companion_points__field-vorticity.json` (3.3 MB) and the shock cards' shared
pressure line-outs (`companion_points__field-pressure.json`, 1.6 MB each). This is the evidence
itself, past the 50 MB line.

## Options

1. Move the generated files to Git LFS, as `docs/decisions.md` names.
2. Raise the cap (it was raised from 25 to 40 MB on 2026-11-02, #34).
3. Write figure JSON column by column instead of row by row (lossless; repeated keys dominate
   files such as the shock line-outs), and draw a figure shared by several sibling cards once.
   Measured savings not yet known; unlikely alone to reach 40 MB.

# A metric cannot declare that it needs an absolute, positive field

**Category:** technical debt
**Priority:** low
**Status:** open. No harness change made; `shock_set_distance` documents the limit on its card.

## Context

`shock_set_distance` detects shocks from the ratio of neighbouring pressures, which is defined
only for an absolute, positive (thermodynamic) pressure. The metric declares
`fields=("pressure",)`, and the harness runs it on every dataset that stores a field called
pressure. One of them, `taylor_green_2d`, stores the pressure of an incompressible flow: a gauge
field, defined only up to an added constant, with zero mean and both signs
(`p = (cos 2x + cos 2y)/4`, `fmeval/data/analytic.py`). There the metric's value means nothing:
adding a constant, which changes nothing physical, changes which cells are flagged.

**Measured** in the adversarial review of 2026-10-31 (builder's records,
`.agent/adversary/probe2.py` and the smoke run
`python evaluate.py metrics=[shock_set_distance] dataset=taylor_green_2d degradation=quick paths.data_url=null`):
before the non-positive convention changed (issue 102), 73% of the Taylor-Green reference's cells
were flagged, the reference against itself plus 1 scored the worst value, and the `mean_field`
anchor scored 0.10 of the diagonal instead of 1. After the change, measured on the 64x64
Taylor-Green pressure at t = 0 by calling the metric directly: 17% of the cells are still
flagged, where a small positive pressure sits beside a larger one, and the same field plus 1, a
physically identical pressure, scores the worst value, the diagonal 8.886. The flags still depend
on the arbitrary constant.

`taylor_green_2d` is a harness fixture, not an evidence dataset (`docs/decisions.md`), so no
card's evidence is affected today. The gap is that nothing stops a future evidence run on an
incompressible dataset with pressure.

## The choice to be made

The decorator has `requires_periodic` to keep a metric off a dataset whose boundary it cannot
handle, and nothing equivalent for the field's meaning. Options:

1. A metric declaration such as `requires_absolute=True` (the field must be an absolute
   thermodynamic quantity, positive), with a per-dataset statement of which of its fields are
   gauge fields; the pipeline then skips the metric there and says why, as it does for
   `requires_periodic`.
2. Distinct canonical field names for a gauge pressure and a thermodynamic pressure, so that
   `fields=("pressure",)` cannot match the gauge one.
3. Leave it to each card, as now.

Option 2 changes the field vocabulary every reader and metric uses; option 1 is local to the
decorator, the dataset configs and one check in `fmeval/pipeline.py`.

## What would unblock it

A decision for one option, made with the first incompressible evidence dataset that stores
pressure, or with the second metric that needs a positive field (an entropy or a log-density
metric would).

## Related

Found by the adversarial review of `shock_set_distance` (pull request #22), 2026-10-31. Issue
102 records the non-positive convention; issue 096 the related question of handing a metric
several fields.

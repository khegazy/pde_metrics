# Increment flatness is not monotone under smoothing, on real data, on every field

**Category:** acceptance criteria
**Priority:** medium — needs a decision, not a fix
**Status:** open

## Context

`CLAUDE.md` states the acceptance rule plainly: "a metric joins the panel only if it is
monotone in degradation with high Spearman rank correlation. Non-monotone metrics are
dangerous for model selection." `metrics/increment_flatness` fails that rule on the
smoothing axis. It is implemented, tested and documented anyway, because what it measures —
intermittency, the first property an over-smoothed surrogate destroys — is on the
first-wave priority list and nothing else in the panel measures it. The open question is
what a panel is supposed to do with a metric like this, and that is a person's call.

## Evidence

Measured directly, not inferred. Frame 5000 of `kinet_re5e4` (the canonical exemplar
frame), derived fields recomputed, blurred with `scipy.ndimage.gaussian_filter(mode="wrap")`
at sigma = 0, 0.5, 1, 2, 4:

| field | sigma=0 | 0.5 | 1 | 2 | 4 | monotone? |
|---|---|---|---|---|---|---|
| density | 16.4684 | 16.5496 | 16.3802 | 15.5289 | 12.9909 | no — rises first |
| velocity | 8.3400 | 8.2108 | 8.1013 | 8.4812 | 8.3551 | no — wanders |
| vorticity | 12.7123 | 12.3369 | 10.1410 | 7.5878 | 16.1508 | no — falls, then doubles |

The vorticity row is the sharpest case: flatness falls by 40% out to sigma = 2, then more
than doubles at sigma = 4. A model-selection procedure ranking candidates by closeness to
the reference's flatness would prefer the sigma = 4 field over the sigma = 2 one on
vorticity, which is the wrong ordering by any other measure in the repository.

The same non-monotonicity appears on the synthetic fixture in `tests/conftest.py`, so this
is not an artifact of the real data either: the two-scale sine gives 2.437 / 2.581 / 2.366 /
2.253 / 2.250 across the same sigmas.

## Why this is a property, not a defect

Flatness is a normalised fourth moment — a statistic of the *shape* of the increment
distribution, scale-free by construction. Smoothing changes both the numerator and the
denominator, and nothing forces the ratio to move one way. At heavy blur the field retains
only a few large-scale structures, so the largest increments become *rarer* relative to a
now much smaller typical increment, and the ratio climbs again. Enstrophy and kinetic
energy are monotone under blur because they are energy-like, not because single-field
quantities generally are.

The fix that would make it monotone — reporting the absolute difference from the
reference's flatness as a pairwise error — is the one `AGENTS.md` forbids: "do not
transform the metric into a monotone error to make it fit, because then the number in the
table is no longer the number the name promises." So the metric reports flatness.

## What was done in the meantime

`metrics/registry.py` gained a declared `monotone_under_smoothing` flag, defaulting to
True so no existing metric changes. `tests/test_metric_contract.py` checks the declaration
**in both directions**: a metric declaring False must actually fail to rank the blur ladder,
so the flag cannot be used to slip a metric past a gate it would otherwise have passed. That
follows the pattern `severity_direction` already uses on the degradation side, where the
declaration is verified by measurement rather than trusted.

This keeps the finding visible rather than hiding it, but it does not answer the question.

## What would settle it

A decision on one of these, which only a person should make:

1. **Exclude it from the panel** and keep it as a reported diagnostic only, in the way
   `enstrophy` is described as a tripwire. This is the conservative reading of `CLAUDE.md`.
2. **Accept non-monotone metrics on axes where non-monotonicity is itself informative**,
   and say so in the protocol. Flatness returning to the reference value under heavy blur is
   not noise; it is a real and nameable failure mode of the statistic, and a panel that
   reports it alongside a monotone metric loses nothing.
3. **Replace the single-cell separation with a curve over separations** (`increment_w1`'s
   increment-PDF comparison is the neighbouring item) and judge the curve rather than one
   point. This is more work and changes what the metric returns from a scalar to a vector,
   which the registry already supports via `returns="vector"`.

Option 3 is the one that most directly addresses the underlying problem, since
intermittency is a statement about how flatness varies *across* scales and a single
separation cannot express it. It is not obviously worth the cost until option 1 or 2 has
been ruled out.

## Related

- `issues/014-gradient-signal-criterion.md` — the other place a single-field statistic's
  acceptance is at issue.
- `metrics/increment_flatness/card.md`, Limitations, states the user-facing consequence.

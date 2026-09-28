# A position-blind metric scores the unrelated-field anchor at zero, so it has no damage scale

**Category:** protocol
**Priority:** high — it blocks the normalised reading of a whole family of candidate metrics
**Status:** open

## Context

The normalised damage scale runs from the undegraded reference at 0 to an unrelated field at
1, and the unrelated field is produced by `random_large_translation`: a shift far enough that
the result is statistically a twin of the reference but positionally unrelated. `AGENTS.md`
records why it must be measured rather than scavenged from a ladder severity.

That anchor is built out of a translation. Any metric that is *invariant* to translation
therefore scores it exactly zero, the span between the two anchors is zero, and no damage
number exists — not a small one, not a noisy one, none.

This is not a corner case for this project. Position tolerance is the property nearly every
candidate in the tracker is being added for. The mollification split, the optimal-transport
family, the increment-PDF metrics and the shock-set distances are all in the repository
precisely because they do not care where a feature is in the way that a pointwise norm does,
and the more completely a metric achieves that, the more completely it loses its damage
scale.

## Evidence

`metrics/increment_w1` is exactly translation-invariant by construction: rolling a field
permutes its increments without changing the multiset. Measured on `comparison_1789629226`
(`kinet_re5e4`, start 2000, reduction 50, 161 frames), median value on vorticity:

| degradation | level | increment_w1 |
|---|---|---|
| `identity` | 0 | 0.000000 |
| `translate_x` | 1–5 | 0.000000 at every level |
| `uncorrelated` (the anchor) | 1–6 | 0.000000 at every level |
| `gaussian_impostor` | 1 | 0.000294 |

Consequences visible in that metric's own card, all of them correct behaviour by the
harness rather than defects in it:

- Every `first strength detected` column reads `—`, on every family and every field,
  because the fraction-of-the-way-to-unrelated quantity it reports divides by zero.
- The trap-test table reports `damage —` and `value on an unrelated field 0` for all three
  fields, so the Gaussian impostor cannot be scored even though the metric does respond to
  it: the raw value 0.000294 is small but not zero, and there is simply no scale to put it on.
- `translate_x` rank correlation is withheld as `—`, which is the round-off guard working
  as designed.

The metric is otherwise well behaved: rank correlation 1 on smoothing, spectral filtering,
noise and coarsening, on all three fields. It is only the *normalisation* that is unavailable,
and normalisation is what makes values comparable across metrics and fields.

`metrics/increment_flatness` has the same problem for the separate reason that it is a
single-field quantity, which `AGENTS.md` already documents as "no dynamic range"; its
unrelated-field values are 15.2 / 9.23 / 9.34 against reference values of the same order.
The two causes are different but the missing scale is the same.

### The canary's own target: `spectrum_l2`

`metrics/spectrum_l2` was added as the kind of quantity the Gaussian impostor exists to
catch — a function of the Fourier amplitudes alone. Measured on `comparison_1789632054`
(`kinet_re5e4`, start 2000, reduction 50, 161 frames, grid 256), median values:

| degradation | density | velocity | vorticity |
|---|---|---|---|
| `identity` | 0 | 0 | 0 |
| `translate_x`, every level | 1.5e-16 to 1.9e-16 | 2.1e-17 to 2.2e-17 | 1.3e-16 |
| `uncorrelated` (the anchor) | 1.3e-16 to 1.9e-16 | 1.6e-16 | 1.6e-16 to 1.7e-16 |
| `gaussian_impostor` | 2.8e-15 | 1.6e-16 | 2.2e-16 |
| `gaussian_blur`, strongest | 0.62 | 0.58 | 0.15 |

So the canary does catch it: the impostor scores as the reference does, fifteen orders of
magnitude below the metric's response to a blur. But the trap-test row reports
`damage —`, because the damage score divides by the anchor's round-off. The one metric that
makes the IN-4 check discriminate is exactly the one whose IN-4 result cannot be printed on the
normalised scale. The same holds for `palinstrophy`, as for every single-field quantity.

A second consequence was a defect rather than a protocol gap, and is fixed: with every value
on `translate_x` at round-off, the rank-correlation guard compared the axis's spread against
the axis's own largest value — also round-off — and reported `rho` of 0.0 / 0.10 / −0.1, and
−0.6 to −0.71 on `translate_subpixel`. `analysis.summarise_axes` now judges round-off against
the metric's largest value in the same frame across every axis, and those correlations are
withheld (`tests/test_robustness.py::test_rank_correlation_is_withheld_when_every_value_on_the_axis_is_round_off`).

An interim option, not implemented because it is a reporting decision: the probe summary could
report the impostor's raw value as a fraction of the metric's largest ladder response when the
anchor is degenerate. For `spectrum_l2` that fraction is about 1e-15, which says "phase-blind"
without needing the anchor.

## Why the obvious fixes do not work

**Use a different translation.** No translation helps; the invariance is exact.

**Use the Gaussian impostor as the anchor.** It is a probe, not a bound, and `AGENTS.md`
warns that it is aimed at amplitude-spectrum metrics; anchoring on it would make every
metric's scale depend on how that particular fake is built.

**Use a distant frame.** `AGENTS.md` records this one as already tried and wrong: the flow
decays, so a frame 4000 steps away has 0.70 of the variance and a different flatness, and
scores *closer* than a true twin.

## What would settle it

An anchor that is statistically a twin of the reference but *independent* of it, rather than
a rearrangement of it. That is exactly `issues/004-independent-realizations.md` — a second
seed of the same configuration. A second realisation differs from the reference in position
and in phase while sharing every statistic, so a position-blind metric would score it at its
genuine "unrelated" level rather than at zero.

Until such data exists, the honest options are to report these metrics unnormalised and say
so, which is what their cards now do, or to define a per-metric anchor and accept that the
number is no longer comparable across metrics.

## Related

- `issues/004-independent-realizations.md` — the data that would fix this.
- `issues/035-no-generated-block-for-cross-metric-damage.md` — the other place the
  normalisation layer does not carry what a reader needs.

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

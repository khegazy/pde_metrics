# Only one seed per configuration

**Category:** data generation
**Priority:** medium
**Status:** open

## Context

The damage anchor is the field's spatial mean (`judgements/001`), the climatological reference.
What the data cannot provide is the other classical reference, an *independent realisation*: a
field with every statistic of the reference and none of its positions or phases. The suite
stands in for it with a probe that translates the reference by a large random offset
(`uncorrelated`), and that stand-in is measured not to be one: a translation multiplies each
mode by a phase, which a field whose energy sits in a few large-scale modes does not average
away. On `kinet_re5e4` the probe's median `energy_changed`, which is 2 for an unrelated field of
the same variance, is 1.64 on density, 3.05 on velocity and 2.25 on vorticity, and a
translation-invariant metric scores it at exactly the clean value.

An independent realisation at the same physical parameters would separate "wrong phase" from
"wrong realisation", which translation cannot, and would give every metric — position-blind
ones included — its genuine score for an unrelated field. Every run in
`kinet/doubly_periodic/old/` carries `R0-1`, so there is one seed per configuration.

## What is needed

Two or more runs at identical physical parameters with different initial-condition seeds.

## Acceptance criteria

A second realisation is available, a ladder entry scores each metric against it, and its
`energy_changed` against the reference is 2 to within the spread across frames.

## Related

`degradations/random_large_translation`; `uncorrelated_value` in TEST_DESCRIPTION.md; `judgements/001`.

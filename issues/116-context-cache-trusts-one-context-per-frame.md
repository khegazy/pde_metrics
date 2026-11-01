# The context cache trusts, without checking, that each context holds one reference

**Category:** technical debt
**Priority:** low — the pipeline honours the contract today; nothing else calls a metric with a context
**Status:** open.

## Context

`FieldContext.cache` (`fmeval/context.py`) lives across the whole ladder of one frame and field,
and its documented contract is one context per (frame, field, metric). Four merged bundles cache a
quantity of the reference in it under a fixed key, computed on first use:
`persistence_distance`, `spectral_energy_flux` and `increment_w1_by_separation` (each one's
reference curve or diagram) and `shock_set_distance` (the reference's shock mask). Those three
and `tail_index` also read the pipeline's `COMPANION_KEY` entry whenever it is present.

A context reused for a second reference therefore returns the answer for the first, silently.
Nothing records which reference a cached entry was computed from.

Found by the agent that built `persistence_distance` (finding 024, adversarial review
2026-10-31). The orchestrator added `shock_set_distance`, which the finding did not list.
`tail_exceedance` (pull request #31) caches its reference thresholds the same way; its
adversarial review reproduced the failure there, 21.6 instead of 1 on a reused context, with
no error even for a reference of a different shape (finding 027).

## Evidence

The agent's script `reused_ctx.py` (kept in its log archive) scores `persistence_distance(b, a)`
at 0.0 on a context first used with reference `b` against itself, and 0.1148 on a fresh context.
Today the pipeline is the only code that passes a context to a metric
(`fmeval/cards/exemplars.py` builds contexts for degradations only), so no recorded number is
affected.

## Options

1. Key the cache in the harness by the identity of the reference array (or a cheap digest of
   it), so a different reference misses rather than reads a stale entry.
2. Have the pipeline check, in debug runs, that a context never sees two references.

A guard inside one bundle would protect none of the others.

---
type: EXP
kind: degradation
related: ["metrics/persistence_distance", "proposals/EXP-orchestrator-20261023-known-vortex-field.md"]
seen_in: "agent's own"
doi: "none"
found_by: "persistence_distance, 2026-10-31"
---

# EXP: Injecting isolated spurious features of known depth

## What the experiment is

A degradation that adds a fixed number of small, isolated Gaussian wells (or bumps) of depth h, the
severity, in units of the field's fluctuation RMS about its mean, at random positions drawn from
the run's generator. The well width is fixed in cells and small against the characteristic scale.

## What it tests

It creates new features of known depth while leaving the rest of the field almost untouched: the
artefact a surrogate makes when it invents a spurious vortex or shocklet. For a well placed where
the field is locally flat, the diagram gains one point of lifetime about h, so the bottleneck
distance should rise as about h/2 and the pointwise maximum error as h. That prediction is my
reasoning, and it fails where a well lands on a slope or near an existing extremum, which is what
a run would measure.

## Metrics it would test

`persistence_distance` and its proposed variants (Wasserstein, Betti curves, signed census), the
eddy census (issue 073), `max_error`, and the pointwise controls, which dilute a few spurious cells
in their mean.

## Why it is helpful

No current degradation adds a few strong spurious features: `additive_noise` adds many weak ones
everywhere. Topological and feature-based metrics are built to detect exactly this.

## Cost and requirements

One stochastic degradation bundle, a few lines on the periodic grid; uncalibrated (absolute depth
in RMS units). It preserves nothing in `PRESERVED` exactly.

## References

None; the proposal is my own.

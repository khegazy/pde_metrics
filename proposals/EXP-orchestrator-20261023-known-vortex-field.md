---
type: EXP
kind: benchmark suite or dataset
related: ["issues/060", "issues/073", "issues/082", "issues/086"]
seen_in: "orchestrator's own"
doi: "none"
found_by: "orchestrator, 2026-10-23"
---

# EXP: A field with a known vortex population

## What the experiment is

Either of two forms:

1. **A dataset** computed from a closed form (the `ClosedFormTrajectory` pattern of
   `fmeval/data/analytic.py`): a periodic superposition of a known number of isolated vortices of
   known radii, circulations and positions, so that the number, sizes and pair distances of the
   vortices are known exactly.
2. **A degradation** applied to `kinet_re5e4` that removes or weakens a known fraction of the
   vortices identified in the reference, for example by attenuating the vorticity inside a chosen
   set of closed vorticity contours and recomputing the velocity.

## What it tests

It changes the vortex population (count, sizes, positions, strengths) in a controlled and known way.
No current degradation does: smoothing and spectral filters change amplitudes, translations move
every vortex together, and noise creates spurious structure only incidentally.

## Metrics it would test

The winding angle (issue 086), any comparison built on the vortex criteria (060), the eddy census
(073) and the pair-correlation function of features (082).

## Why it is helpful

Every feature-based idea is blocked on it, including the winding angle, which the team ranks high.

## Cost and requirements

The dataset form is a new reader, admitted as evidence only by a decision like the one that admitted
`sod_shock_tube`; the degradation form needs a vortex detector, which is the thing being tested, so
the dataset form is the cleaner experiment. The vortex profile (for example a Lamb–Oseen or a
Gaussian vortex) must be chosen and cited: TODO(cite).

## References

TODO(cite): a standard reference for the chosen vortex profile.

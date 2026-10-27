# Bispectrum and bicoherence: the distance between maps is not fixed

**Category:** method
**Priority:** unset — the team has not set a priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Bispectrum and bicoherence](../docs/ideas/basis_decompositions/bispectrum.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

The page: "The metric compares the predicted bicoherence map with the reference's. The guide does not fix which distance between the two maps to use." It also says reducing the two-wavevector bispectrum, for example to wavevector magnitudes, "is a choice that must be declared".

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. The metric would be testable: the `gaussian_impostor` keeps every amplitude and draws new uniform phases, so its expected bicoherence is zero. What is missing is the definition of the number.

## What would unblock it

Decisions on the reduction of the wavevector pair and on the distance between the two bicoherence maps.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).

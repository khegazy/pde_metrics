# EXP: Scaling the dilatational part of the velocity

Found by: the orchestrator screening `docs/ideas/`, 2026-10-23. Seen in: the orchestrator's own
proposal.

## What the experiment is

A whole-frame degradation on a periodic domain: split the velocity into solenoidal and dilatational
parts by the Fourier projection, multiply the dilatational part by `1 + s` (the severity `s` may be
negative, down to −1, which removes it), recombine, and recompute vorticity (which is unchanged,
since the dilatational part is curl-free).

## What it tests

It changes the partition of kinetic energy between rotation and compression by a known factor
while leaving the rotational part exactly unchanged. No current degradation does this: the
smoothing and spectral operators are isotropic and linear and damp both parts equally at each
wavenumber.

## Metrics it would test

The Helmholtz split (issue 057), and any later compressibility diagnostic, such as the inferred
driving parameter on the log-density page (088).

## Why it is helpful

It turns the Helmholtz split, ranked high by the team, from untestable into testable, and it is a
clean blind-axis test for every curl-based metric (enstrophy and palinstrophy must be invariant to
it).

## Cost and requirements

One degradation bundle with `whole_frame=True` acting on velocity, periodic domains only. It
overlaps with the solenoidal projection of issue 024, whose projection operator it would share.

## References

None; the proposal is the orchestrator's own.

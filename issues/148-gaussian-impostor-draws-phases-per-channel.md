# The Gaussian impostor draws its phases per channel, so a divergence-free velocity comes out about a quarter divergent

**Category:** method
**Priority:** medium. The impostor is the canary every metric is read against, and the planned
graded phase randomisation (`FUTURE_EXPERIMENTS_CATALOG.md`, G3) would reuse its phase draw.
**Status:** open; measured, not fixed (2026-11-27).

## Context

`degradations/gaussian_impostor/degradation.py` keeps each channel's Fourier amplitudes and
replaces its phases with those of a white Gaussian field. It does this in a loop over channels,
drawing a new noise field for each, so the two components of a velocity receive unrelated
phases. A divergence-free (solenoidal) velocity has its Fourier coefficient perpendicular to its
wavevector at every mode, and that is a relation *between* the components' phases. Independent
phases destroy it.

The impostor is meant to differ from the reference in one way only: it has the same spectrum
and no phase coupling between scales. On a velocity it differs in a second way that nobody
asked for, its split between the divergence-free and the curl-free (dilatational) part.

## Evidence

- **Expected value.** For a solenoidal input, the dilatational fraction of the impostor's
  energy at a wavevector at angle $\theta$ to the x axis is $\tfrac12\sin^2 2\theta$, which
  averages to 1/4 over angles (derivation in `dataset_specs/10_acoustic_and_helmholtz_fields.md`,
  the list of what each degradation does to the split; it is the specification author's
  derivation, not a cited result).
- **Measured, 2026-11-27.** A broadband, exactly solenoidal two-component velocity on a 128²
  periodic grid (white noise with amplitude roll-off $1/(1+|k|^2/16)$, Nyquist modes removed,
  projected with `fmeval.derived.helmholtz_split`; residual dilatational fraction below 1e-24)
  was passed through `gaussian_impostor`, and the output split with the same function. Over
  ten seeds the dilatational fraction of the fluctuation energy was 0.18 to 0.28, mean 0.24.
- **Earlier measurements agree.** 0.228 on another solenoidal field
  (`FUTURE_EXPERIMENTS_CATALOG.md`, G3, point 2) and 0.22 to 0.29 over five seeds
  (`dataset_specs/10_acoustic_and_helmholtz_fields.md`). On Taylor–Green, whose four modes all
  sit at 45°, the expected fraction is 1/2 and single draws ranged from 0.10 to 0.91.
- **For scale.** `kinet_re5e4` holds 1e-6 to 1e-5 of its fluctuation kinetic energy in the
  dilatational part (`dataset_specs/10_acoustic_and_helmholtz_fields.md`, Section 1), so on that
  data the impostor's velocity is four to five orders of magnitude more compressible than the
  flow it imitates.

## Consequences

- Any metric that reads the divergence of velocity or the dilatational part scores the
  impostor as badly wrong for a reason that has nothing to do with phase coupling between
  scales, so its canary reading on velocity does not say whether it is phase-blind.
- The impostor's card and its `preserves` tuple (`amplitude_spectrum`, `spatial_mean`) are
  correct per channel and silent about the relation between channels.
- A graded phase randomisation built on the same draw would inherit the defect at every
  severity above zero.

## What would settle it

1. Rotate every component of a vector field by **one** random phase per wavevector, in place of
   replacing each component's phases separately: $\hat u_j(\mathbf k) \to \hat u_j(\mathbf k)\,
   e^{i\varphi(\mathbf k)}$ with $\varphi$ the phase of one real white-noise field. This keeps
   each component's amplitudes, keeps $\mathbf k\cdot\hat{\mathbf u}$ (so a solenoidal field
   stays solenoidal), and keeps the cross-spectrum between components. For a single-channel
   field it has the same distribution as today's draw.
2. A test that pins it: a solenoidal input stays solenoidal to round-off, and the existing
   amplitude-spectrum and flatness checks still pass.
3. A decision by the team, because the change alters every recorded canary number on velocity:
   the evidence would have to be rerun, and the card should say which convention a recorded
   number used.

## Not checked

- Whether the vorticity the ladder scores under the impostor is recomputed from the impostor's
  velocity or drawn as a scalar field of its own. If it is recomputed, the vorticity readings
  carry the defect too; if it is drawn on its own, they do not.
- Which registered metrics' canary readings change materially under the fix. No metric was
  rerun for this issue.

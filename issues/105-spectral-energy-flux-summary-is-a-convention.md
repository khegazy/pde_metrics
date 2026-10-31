# The number `spectral_energy_flux` registers, and the octaves it samples, are conventions with no source

**Category:** method
**Priority:** unset
**Status:** open. The metric is built with both conventions labelled; what would replace them is
open.

## Context

`spectral_energy_flux` compares the spectral energy flux $\Pi(K)$ of a prediction's velocity
with the reference's, $\Pi(K) = \langle \mathbf{u}^{<K} \cdot (\mathbf{u}\cdot\nabla)\mathbf{u}
\rangle$ (Alexakis & Biferale 2018, *Physics Reports* 767–769, 1–101, Eq. 18 of
arXiv:1808.06186). The idea page asked for "the error of the curve $\Pi(k)$ across the inertial
range". Two things in the built metric come from no source:

1. **The coordinates.** The curve is stored at the octave wavenumbers $K = 1, 2, 4, \dots$ up to
   half the smallest side of the grid (eight on $256^2$), not at every unit shell (182 on
   $256^2$). Because $\Pi$ is cumulative, each sampled value still counts every mode inside it;
   the sampling decides how often each range of scales is counted. The shells beyond $N/2$
   exist only in the corners of a square grid, and they enter only through the flux out of the
   last octave.
   One column per shell would also make the card's per-coordinate table 182 columns wide.

   That table is the reason for sampling at all. A curve companion is stored at every
   coordinate it returns. `fmeval/cards/evidence.py::companion_block` renders one table column
   per coordinate, and `fmeval/analysis.py` analyses each coordinate as a metric of its own
   (`metric[coordinate]`). On unit shells `rint(|k|)` a $256^2$ grid has 182 coordinates, so a
   spectral curve companion needs a sampled coordinate set to stay readable and to keep the
   analysis cost bounded. Any later spectral curve, such as a coherence spectrum or
   `spectrum_l2`'s own curve, meets the same limit.
2. **The summary.** The number is $\lVert \Pi_{\text{cand}} - \Pi_{\text{ref}} \rVert_2 /
   \lVert \Pi_{\text{ref}} \rVert_2$ over those octaves, the form `spectrum_l2` uses for the
   energy spectrum. The idea page's "inertial range" does not exist on `kinet_re5e4`, which is
   two-dimensional, unforced and decaying, so every octave is used.

## What is measured about it

**Measured** on the evidence run `spectral_energy_flux_1793391588` (`kinet_re5e4`, 161 frames
from 2000, velocity, with the conserving flux of the adversarial review). The dominance fraction
is the share of frames in which the harsher of the weakest pair of neighbouring strengths has
moved the curve at least as far at every octave. It is low on every degradation, 0 to 0.168 (the
metric's card, "The curve behind the number"). By that test the summary, not the curve, decides
the order of those strengths in most frames. On `increment_w1_by_separation` the same fraction is
at least 0.92 on every degradation of density and velocity (`issues/098`). Several octaves
reverse the direction of the trend that the number shows, for example `box_blur` and
`gaussian_blur` at octave 8. The number itself ranks every pre-registered axis in the typical
frame, with rank correlation 1 except `lowpass_butterworth` at 0.5, and between 0.46 and 1 of
frames fully in order.

The reference's own flux changes sign along this decaying trajectory. In that run it is negative
at octaves 1 to 8 in 67% to 80% of frames, and positive at octaves 32 to 128 in at least 90%
(the clean rows of `companions.csv`). So no fixed sign convention could replace the comparison
either.

## What would settle it

A published reduction of a flux-curve comparison to one number, or a decision to register a
different summary for a stated purpose: the largest normalised gap (worst octave), the
direction-of-transfer disagreement (a proposal drafted with this metric), or a sum over all unit
shells. Each is a sibling bundle importing the same curve, not a change to this one.

## Related

Written with `spectral_energy_flux` (branch `metric/spectral_energy_flux`), 2026-10-30. Modelled on
`issues/098`, the same question for `increment_w1_by_separation`.

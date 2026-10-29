# The number `increment_w1_by_separation` registers is a convention with no source

**Category:** method
**Priority:** unset
**Status:** open. The metric is built with the convention labelled; what would replace it is open.

## Context

`increment_w1_by_separation` compares the increment distributions of a prediction and the
reference at every octave of separation, 1, 2, 4, ... cells, with the 1-Wasserstein distance
$W_1(\ell)$. Its companion stores that curve on every row, untransformed, in the field's units.
The idea page (`docs/ideas/optimal_transport/gradient_pdf_w1.md`) and its reference (Granero
Belinchon and Cabeza Gallucci 2024, *Mach. Learn.: Sci. Technol.* 5(2), 025032) compare
increment statistics across scales, but neither reduces the curve to one number. The panel
needs one number per comparison, so the metric registers

$$
\frac{1}{L}\sum_{\ell} \frac{W_1(\ell)}{\langle \lvert \delta_\ell u_{\text{ref}} \rvert \rangle},
$$

the mean over separations of each distance divided by the reference's mean absolute increment
at that separation. That choice is the repository's, by Kareem's decision of 2026-10-28:
build the number, label it a convention, and record it here.

## Why this convention and not a plain mean

The increments grow with separation, so $W_1(\ell)$ does too, and a plain mean is carried by the
largest separations. **Measured** on the evidence run `comparison_1793262246` (`kinet_re5e4`,
density, frame 2000, the second `gaussian_blur` level, $\sigma = 6.94$ cells): $W_1(\ell)$ grows
17.1 times from $\ell = 1$ to 128, so a plain mean is carried 45% by the two largest separations
and 9% by the three smallest; divided by the reference's mean absolute increment at each
separation, the shares become 11% and 51%. The reference rebuilt for this measurement reproduces
the registered value of that row exactly. On vorticity ($\sigma = 1.63$) the same shares are 36%
and 18% plain, 18% and 50% normalised; there the rebuilt reference reproduces the registered
value only to 1.8%, so those four numbers are approximate. The normalisation weighs every
separation alike; it does not say which separations matter more.

## What is measured about it

The dominance fraction asks whether the summary can change the ordering of neighbouring
strengths. If, in every frame, the harsher strength's curve lies at or above the milder one's at
every separation, every summary that grows with each separation's departure orders that pair
the same way, this one included. **Measured** on the same run, the weakest pair's dominance
fraction is at least 0.92 on every degradation of density and velocity. On vorticity it falls to
0.47 under `lowpass_ideal` and 0.58 under `lowpass_butterworth`: there the summary decides the
ordering of that pair in about half the frames. The values per degradation are on the metric's
card, under "The curve behind the number".

## What would settle it

A published reduction of a scale-by-scale increment comparison to one number, or a decision to
register a different summary for a stated purpose (for example the largest normalised distance,
if the use is detecting the worst scale). Either is a sibling bundle importing the same curve, not
a change to this one.

## Related

Written with the first curve metric (pull request #19), 2026-10-28.

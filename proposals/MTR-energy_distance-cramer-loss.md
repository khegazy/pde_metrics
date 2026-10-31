---
type: MTR
kind: variant of energy_distance
related: ["energy_distance", "increment_w1", "docs/ideas/evaluation_design.md"]
seen_in: "Bellemare et al. 2017, arXiv:1705.10743"
doi: "10.48550/arXiv.1705.10743"
found_by: "energy_distance, 2026-10-30"
---

# MTR: Squared energy (Cramér) distance of increments as a training loss

## What it measures

The same quantity as energy_distance, the gap between the reference's and the prediction's
one-cell increment distributions, but reported in the squared form and intended as a
distributional training loss rather than as a diagnostic.

## Definition

Per channel and axis, the Cramér distance l_2^2 = integral of (F_n - G_n)^2 dx, which is half the
squared energy distance on the line (Székely & Rizzo 2013, J. Stat. Plann. Inference 143(8),
1249-1272, the display immediately before Eq. (2.3)); averaged over channels and axes as
energy_distance does. scipy.stats.energy_distance(u, v)**2 / 2 computes it.

## Relation to existing work

energy_distance registers the square root form as a diagnostic. increment_w1 is the transport
counterpart. The abstract of Bellemare et al. (2017) states that the Wasserstein metric lacks
unbiased sample gradients while the Cramér distance has them, which matters when the loss is
estimated on minibatches of samples rather than on whole fields. Only the abstract was read, so
the claim is not verified here. docs/ideas/evaluation_design.md collects training counterparts of
evaluation metrics and does not list this one.

## How it could be tested

As a diagnostic it ranks the ladder exactly as energy_distance does (a monotone transform), so
the ladder adds nothing. As a loss it needs a training experiment, which the repository does not
have; the testable claim is the gradient-bias one, on synthetic samples: compare the mean of
minibatch gradients against the full-sample gradient for both this loss and increment_w1.

## Why it is helpful

The project's stated aim includes using validated metrics as training losses, and CLAUDE.md
keeps diagnostics and losses separate. If the abstract's claim holds, this is the distributional
loss on increments with the better-behaved gradients of the two the repository can already
compute.

## References

- Bellemare, M. G., Danihelka, I., Dabney, W., Mohamed, S., Lakshminarayanan, B., Hoyer, S. &
  Munos, R. (2017). The Cramer distance as a solution to biased Wasserstein gradients.
  arXiv:1705.10743. Abstract read only.
- Székely, G. J. & Rizzo, M. L. (2013). Energy statistics: A class of statistics based on
  distances. J. Stat. Plann. Inference 143(8), 1249-1272. doi:10.1016/j.jspi.2013.03.018.

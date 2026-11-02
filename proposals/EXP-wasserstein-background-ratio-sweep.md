---
type: EXP
kind: protocol
related: ["wasserstein", "h_minus_one", "docs/ideas/optimal_transport/wasserstein_signed_fields.md", "docs/ideas/optimal_transport/signed_field_transport.md"]
seen_in: "Engquist & Yang 2022, Commun. Pure Appl. Math. 75(10), 2201-2244"
doi: "10.1002/cpa.21990"
found_by: "wasserstein, 2026-10-31"
---

# EXP: Translate a positive feature over backgrounds of increasing size

## What the experiment is

Use the existing `advecting_blobs` reader, which draws Gaussian bumps of height `a` on a
uniform background of 1. Sweep the bump height over several decades, for example a = 0.1, 1,
10 and 100, so that the background ranges from dominant to negligible. On each, run the
`translate_x` and `translate_subpixel` axes with `wasserstein`, `h_minus_one` and `mse`.

## What it tests

It tests the known dependence of the Wasserstein distance's growth with a shift on the size of
the background. On an empty background, W_2^2 of a feature moved by s is s^2 whatever its
profile (Engquist & Yang 2022, Sect. 1; Engquist & Froese 2014, Sect. 1). With a background
c added before normalising, Engquist & Yang (2022), Theorem 4.6 (arXiv numbering), show the
growth is O(s^2) only up to a shift of about 1/c plus the feature's width, and O(s) beyond.
On kinet density, the background is two to three orders of magnitude larger than the
fluctuation, and `wasserstein` behaves like `h_minus_one`. The sweep would show the transition
between the two regimes in this repository's own pipeline, with a known answer at each end.

## Metrics it would test

`wasserstein` directly. `h_minus_one`, whose relation to W_2 depends on the same density
bounds (Peyre 2018, Corollary 3 and Theorem 5). Any future transport metric for signed
fields, whose normalisation choice (issue 047) adds a background of its own.

## Why it is helpful

The evidence dataset cannot show what the idea page promises, because its density has a
large background. This experiment can show it, and it says how large a background a signed-field
formulation can add before the shift property is lost. That bears directly on issue 047.

## Cost and requirements

No new code: the bump height is already a reader option (`+dataset.reader.height=...`). Each
run is a 64^2, 21-frame dataset and costs a few minutes with `wasserstein`. `advecting_blobs`
is not an evidence dataset (`docs/decisions.md`), so this is a capability check, not card
evidence. Bumps much taller than the background make the density nearly vanish elsewhere, and
the Monge-Ampere solve may then need damping (Saumier et al. 2015, Sect. 3.3).

## References

- Engquist, B. & Yang, Y. (2022). Commun. Pure Appl. Math. 75(10), 2201-2244. doi:10.1002/cpa.21990.
- Engquist, B. & Froese, B. D. (2014). Commun. Math. Sci. 12(5), 979-988. doi:10.4310/CMS.2014.v12.n5.a7.
- Peyre, R. (2018). ESAIM: COCV 24(4), 1489-1501. doi:10.1051/cocv/2017050.
- Saumier, L.-P., Agueh, M. & Khouider, B. (2015). IMA J. Appl. Math. 80(1), 135-157. doi:10.1093/imamat/hxt032.

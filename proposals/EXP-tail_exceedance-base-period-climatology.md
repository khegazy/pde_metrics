---
type: "EXP"
kind: "protocol"
related: ["tail_exceedance", "tail_index", "proposals/MTR-tail_exceedance-sigma-threshold.md", "proposals/EXP-spectral_energy_flux-forced-2d-compressible-flux-loop.md", "proposals/EXP-increment_flatness-isotropic-3d-turbulence-cutouts.md", "issues/118"]
seen_in: "ETCCDI, Definitions of the 27 core indices (web page), item 13 (TX90p); Zhang, Hegerl, Zwiers & Kenyon 2005, J. Climate 18(11), 1641-1651"
doi: "10.1175/JCLI3366.1"
found_by: "update_metric_eval_principles, 2026-11-03"
---

# EXP: Exceedance thresholds from a separate base period of a long stationary reference

## What the experiment is

The protocol of the percentile-based climate-extremes indices that `tail_exceedance` takes its
construction from. A threshold is a high percentile of the reference over a fixed **base
period**, and the index is the frequency with which other periods exceed it. The ETCCDI
definition of TX90p is the percentage of days on which the daily maximum temperature exceeds
the calendar-day 90th percentile "centred on a 5-day window for the base period 1961-1990"
(ETCCDI page, item 13). Thresholds estimated from a sample are exceeded less often inside that
sample than outside it, because of their sampling error, so out-of-base rates are
overestimated; Zhang et al. (2005, abstract) correct this with a bootstrap over the base
period, which ETCCDI requires for the in-base computation.

Transferred here: take a long, statistically stationary reference record, set the increment
threshold from the frames of a base period, and count exceedances of the reference and of the
candidate on frames outside it. The candidate's frequency bias is then measured against a
climatology, not against the same frame's order statistic, and the reference's own
out-of-base rate measures how stationary the record is.

## What it tests

It separates two things the current construction ties together: the threshold and the frame
being scored. Today the threshold is the reference's ceil(sqrt(n))-th largest one-cell
increment in the same frame (`tail_exceedance` card, Definition), which fixes the reference's
event rate at k/n by construction and leaves only the candidate's count free. With a base
period, both counts are free, so the experiment shows whether a candidate produces extreme
increments at the climatological rate, which is the question the field asks, and whether a
frame-by-frame threshold and a climatological one rank degradations the same way.

## Metrics it would test

`tail_exceedance` (directly), its proposed fixed-multiple-of-rms threshold variant, and
`tail_index` if its tail sample is taken above a base-period threshold rather than as the
frame's own top ceil(sqrt(n)).

## Why it is helpful

`kinet_re5e4` cannot serve: its flow decays (`docs/datasets/reynolds_ladder_2d.md`, "The flow
decays"), so a threshold from early frames is exceeded less and less often later for reasons
that have nothing to do with a candidate. A forced, statistically steady record is needed:
the forced two-dimensional compressible run of `EXP-spectral_energy_flux-forced-2d-compressible-flux-loop.md`,
or the forced isotropic cutouts of `EXP-increment_flatness-isotropic-3d-turbulence-cutouts.md`
(whose 1024 frames span about one large-eddy turnover, Li et al. 2008, Table 1, which may be
too short for a base period and a separate evaluation period; the agent's reasoning). Until one
exists, the card can describe the field's protocol but not run it.

## Cost and requirements

A stationary record long enough to hold a base period and a disjoint evaluation period of
several correlation times each; a series-level procedure, since the threshold pools many
frames (issue 095 asks for the contract of exactly such a procedure); the in-base bootstrap of
Zhang et al. if in-base frames are ever scored.

## References

- ETCCDI (CCl/CLIVAR Expert Team on Climate Change Detection and Indices). Climate Change
  Indices: Definitions of the 27 core indices. <https://etccdi.pacificclimate.org/list_27_indices.shtml>
  (read 2026-11-04; item 13, TX90p, and the bootstrap note).
- Zhang, X., Hegerl, G., Zwiers, F. W. & Kenyon, J. (2005). Avoiding inhomogeneity in
  percentile-based indices of temperature extremes. *Journal of Climate* 18(11), 1641-1651.
  <https://doi.org/10.1175/JCLI3366.1> (abstract only; the journal's section numbers were not
  readable).
- Li, Y., et al. (2008). *Journal of Turbulence* 9, N31. <https://doi.org/10.1080/14685240802376389>
  (Table 1).

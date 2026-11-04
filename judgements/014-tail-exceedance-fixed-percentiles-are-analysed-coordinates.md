# 014 — `tail_exceedance` registers no fixed-percentile sibling; the field's percentiles are analysed coordinates

**Date:** 2026-11-04. **Made by:** the agent of task `metrics-tails` (branch from
`update_metric_eval_principles`).
**Reverse with:** add a sibling bundle, for example `tail_exceedance_p99`, whose metric returns
`tail_exceedance_percentile(...)` at the chosen percentile (import it; do not copy it), with its
own card and evidence; nothing in `tail_exceedance` changes. Then delete this file.

## The question that would have been asked

Kareem's rule is that where fields report a metric differently, each standard is built as its own
bundle. `tail_exceedance` registers the frequency bias at the reference's sqrt(n)-th largest
increment, a convention (`issues/118`). Does the field report a frequency bias at one fixed
climatological percentile, the 90th, 95th or 99th of the ETCCDI indices, as a standard number,
so that it should be a sibling bundle registered on the panel?

## The choice

**No sibling.** The frequency bias against the reference percentile, from 90 to 99.99, is the
companion `tail_exceedance.percentile`, analysed at 90, 95 and 99, so those three values are in
the per-coordinate tables of every run, and the whole curve is the card's figure.

## The evidence

Read for this task (2026-11-04); the report of the reading is in the task log.

- **The verification recommendations draw the bias against threshold, not at one.** WWRP/WGNE
  Joint Working Group on Verification, "Recommendations for the verification and intercomparison
  of QPFs from operational NWP models" (December 2004), read in full: BIAS is "highly
  recommended" (Section 4), the verification is stratified by fixed rain amounts (1, 2, 5, 10, 20,
  50 mm per day, Section 2), and the display asked for is the score "as a function of rain
  threshold" (Section 5(c)).
- **The JWGFVR page** (https://jwgfvr.github.io/forecastverification, read in full) defines the
  frequency bias with no threshold attached and, for rare events, says it should be presented
  beside a dependence score.
- **The ETCCDI indices are not frequency biases.** Items 10 to 13 count the percentage of days
  beyond the 10th or 90th percentile of a 1961-1990 base period; items 25 and 26 are
  precipitation totals above the 95th and 99th wet-day percentiles; each dataset is counted
  against its own base period, so none compares one dataset's count with another's. Sillmann et
  al. (2013, J. Geophys. Res. Atmos. 118, read in full in a repository copy) evaluate models on
  these indices by the RMSE of their climatologies, not by a ratio of counts (Eqs. (1) to (3)).
- **The fixed-percentile frequency biases found are research choices.** Magnusson, Haiden and
  Richardson (2014), ECMWF Technical Memorandum 731, read in full, draw the frequency bias at the
  98th percentile over 2002 to 2013 (Section 5, Figure 8). ECMWF's current headline scores for
  severe weather (Haiden et al. 2025, Technical Memorandum 931, Section 5.1, read in full) define an
  extreme as beyond the 95th percentile of the station climate but score it by the area under a
  ROC curve, not by a frequency bias.
- **Not read:** Ferro and Stephenson (2011), the SEDI paper (publisher and repository refused);
  its recommendation to calibrate the bias to 1 before computing SEDI is known through
  Technical Memorandum 731, Section 2.

So there is no single fixed percentile a reader from either field would expect; there are three
percentiles of the climate indices (90, 95, 99), a 98th in one memorandum, and a recommended
figure across thresholds. The figure is built, and the three index percentiles are tabulated.

## What it changes

Nothing registered: no new panel number, and `tail_exceedance`'s number is unchanged. The
percentile companion adds three analysed coordinates per field and a dense curve on the
`report.error_map` frames.

## Why not the alternatives

- **A sibling at the 99th percentile.** Critique finding 7 measured on `comparison_1793657627`
  that the 99th percentile (theta about 0.585 on 256 by 256) saturates under blur almost exactly
  as the registered theta = 1/2 does; registering it would add a panel member with the same
  failure and no source that singles it out.
- **Three siblings at 90, 95 and 99.** Three panel numbers from one curve, each a convention for
  the ratio-of-counts use here, where the analysed coordinates already report them.

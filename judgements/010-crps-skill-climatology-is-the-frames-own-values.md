# 010 — The CRPS skill score's climatology is the reference's own values over the same frame

**Date:** 2026-11-04. **Made by:** the agent of task `metrics-ensemble` (branch from
`update_metric_eval_principles`), adding `crps_skill_score`.
**Reverse with:** replace the `uncertainty` line of `metrics/crps_skill_score/metric.py` by the
climatology chosen instead, update the card's Definition and this bundle's tests, re-run its
evidence, then delete this file.

## The question that would have been asked

The CRPS skill score compares an ensemble's mean CRPS with that of a reference forecast,
"typically a climatological forecast, that is, an estimate of the marginal distribution of the
predictand" (Gneiting & Raftery 2007, JASA 102(477), Sect. 2.3, around Eq. 8). The CRPS
decompositions fix that reference as the empirical distribution of the observations in the
verification set; its mean score is their uncertainty term `UNC_0` (Arnold, Walz, Ziegel &
Gneiting 2024, Electron. J. Stat. 18(2), 4992–5044, Eq. 10 of the published version, Eq. 11 of
arXiv:2311.14122v1). The verification set of a weather study is many cases at one station or
grid point. Here there is one frame of one field per row, scored cell by cell. Which values
make the climatology?

## The choice

**The reference's own values over the whole domain of the same frame, per channel.** At every
cell the climatological forecast is the empirical distribution of all `n` values of that
channel of the reference in that frame, and its mean CRPS over those values is
`UNC_c = (1/(2 n^2)) sum_ij |y_i - y_j|`, computed exactly. The skill score is
`1 - mean CRPS / mean_c UNC_c`.

Reasons:

- **It is the field's definition applied to the cases this repository scores.** Every
  ensemble metric here treats the cells of one frame as the cases (`crps` averages over them,
  `rank_histogram` histograms them), so the verification set is those cells and its empirical
  distribution of observations is the frame's values. That makes the denominator exactly
  Arnold et al.'s `UNC_0` for the same set of cases as the numerator.
- **It needs no data the row does not have.** A climatology over the trajectory or a base
  period would need other frames' values inside a per-row metric, which the harness does not
  hand a metric; and on a decaying flow (`kinet_re5e4`, if it ever has an ensemble) a pooled
  climatology would mix frames whose variance differs by a factor of about 0.7 per 4000 steps
  (`AGENTS.md` §9), so the skill would drift with the frame for reasons that are not skill.
- **Per channel.** The two components of a velocity are different variables; pooling them into
  one distribution would widen the climatology and inflate the skill. Gneiting & Raftery's
  "marginal distribution of the predictand" is per predictand.

What the choice means for reading the number: this climatology knows the distribution of the
field's values but not where each value sits. A forecast that places the field's structure
correctly earns skill against it even with no knowledge of the noise. On `synthetic_ensemble`,
whose reference is a deterministic two-scale pattern plus noise of standard deviation 0.15, the
smoke run `crps_skill_score_1793789135` reads 0.761 at the clean level (median over 12
frames): most of the skill is knowing the pattern.

## Alternatives considered

- **The trajectory's climatology** (every frame's values pooled): needs cross-frame data in a
  per-row metric, and on a decaying flow mixes different flows (above).
- **A sample-mean point forecast**, the deterministic forecast of the field's spatial mean: this
  is what the plan first proposed, and it is not climatology; the review (critique finding 10)
  rejected it, because the reference must be a distribution, the observations' marginal one.
- **The fair (sample) form of `UNC`**, dividing the pair sum by `2n(n-1)`: rejected, because the
  climatological forecast *is* the empirical distribution, not a sample from one; Arnold et al.'s
  `UNC_0` is the mean score of that distribution itself. One consequence is stated on the card
  and pinned by a test: an ensemble whose members are exactly the `n` climatological values
  scores `1/(n-1)`, not 0, because the fair CRPS treats its members as a sample of a wider
  distribution.

## What it changes

Only `crps_skill_score`, which is new. No other number.

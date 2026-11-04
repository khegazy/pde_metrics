# 016 — No log-spectral sibling of `spectrum_l2` until an empty shell has a stated value

**Date:** 2026-11-04. **Made by:** the agent of task `metrics-spectral` (branch from
`update_metric_eval_principles`). Kareem's rule: "several standards: build them all"; the
orchestrator's instruction for this task: build a log-spectral sibling only if a field source
reports one as a standard number for spectra.
**Reverse with:** build the sibling bundle (scaffold with `python -m fmeval.cards new`), importing
`metrics.spectrum_l2.metric.energy_spectrum`, with the shell range and floor `issues/137` asks
for; delete this file and its row in `README.md`, and narrow `issues/137` and `issues/136`.

## The question that would have been asked

Two machine-learning papers compare spectra on their logarithm: Stachenfeld et al. (2022, ICLR,
arXiv:2112.15275, Sect. 5, Fig. 2c–d), the RMSE of the log spectrum, and Lienen et al. (2024,
ICLR, arXiv:2306.01776, Sect. 6.3, Eq. (7)), the L2 distance between log spectra as the ground
distance of a Wasserstein distance. Do these make a log-spectral distance a standard that must
be built now as a sibling of `spectrum_l2`?

## The choice

**Not built now; written up as `issues/137`.** The sources exist, so the standard is recorded on
`spectrum_l2`'s card under "How its field reports it". But neither source states what a shell
holding no energy contributes, and on this repository's ladder the answer decides the number:

- the anchor, the field's spatial mean, has $E = 0$ in every shell, so its log distance is
  infinite and the damage scale of the whole bundle undefined;
- on `kinet_re5e4` frame 6000, velocity, a sharp low-pass at shell 32 leaves round-off in the
  149 shells above it ($10^{-29}$ to $10^{-16}$ of the reference's energy there), and the RMSE
  of $\log_{10} E$ is 22.5 decades over every shell, $3 \times 10^{-16}$ over shells 1–32, and
  16.8 with the emptied shells floored at $10^{-30}$ (`issues/137` has the measurement).

A floor or a shell cut chosen here would be a tuned threshold the sources do not give, and the
memory rule "untestable metrics become issues" sends a metric whose maths is unclear to an issue.

## What it changes

Nothing registered. `spectrum_l2` keeps its linear number (`issues/136`); its curve companion is
the spectrum any log-spectral sibling would read, so building one later moves no existing
number.

## Sources

Stachenfeld et al. 2022 and Lienen et al. 2024, both read in their arXiv TeX sources for this
task by a research sub-agent, which also read Kochkov et al. 2021 (a linear error of the
$k^5$-scaled spectrum, no formula) and The Well's binned spectral error (phase-sensitive, not a
spectrum comparison). All four are cited with locators in `metrics/spectrum_l2/refs.bib`.

# Open items

One file per item, so future work is written down where a colleague will find it rather than
living in a plan document or in someone's memory. Each file states the evidence, not just the
intent: six months from now "we need a lower-Reynolds reference" is useless without the
measurement that showed why.

Write an issue while the evidence is in front of you. One written from memory later is worth
much less.

**Delete an issue once it is fully resolved.** This folder holds only what is open, so there is
no resolved list: remove the file and its row below, say in the resolving commit's message what
was done and on what evidence, and rewrite every reference to the issue so it states the reason
itself where the code or document needs it. `git log --diff-filter=D --stat -- issues/` lists
the closed issues and the commits that closed them. An issue resolved only in part stays, and
its status says first what is still open.

## Data generation required

These block criteria that are designed and implemented but cannot be exercised.

| ID | Title | Priority |
|---|---|---|
| [001](001-low-reynolds-reference.md) | The protocol specifies Re ~ 500; no such dataset exists | medium |
| [002](002-shocklet-dataset.md) | No shocklet-populated compressible turbulence | accepted, scheduled |
| [003](003-ensemble-data.md) | CRPS and spread-to-skill need ensembles — estimators built and validated on a synthetic ensemble; physical data is [004](004-independent-realizations.md) | low |
| [004](004-independent-realizations.md) | Only one seed per configuration | medium |
| [037](037-position-blind-metrics-have-no-damage-anchor.md) | A translation-invariant metric scores the unrelated-field anchor at zero, so a whole family of candidates has no damage scale until [004](004-independent-realizations.md) lands | high |
| [005](005-3d-and-cost-extrapolation.md) | All data is two-dimensional | low |
| [034](034-the-well-format-copy-is-not-published.md) | The Well-format copy is not published, so that reader's HTTP path is only covered by a fixture | low |

## Deferred functionality

Designed, hooks in place, not built.

| ID | Title | Priority |
|---|---|---|
| [010](010-forecast-pair-reader.md) | Read the real prediction/target pairs | **high** |
| [011](011-cross-dataset-comparison.md) | Compare metrics across a Reynolds ladder | medium |
| [012](012-vector-valued-metrics.md) | Metrics returning spectra or PDFs | medium |
| [013](013-remaining-intuition-figures.md) | Outlier, invariance, triangle-inequality figures | low |
| [014](014-gradient-signal-criterion.md) | Gradient quality where L2 goes flat | medium |
| [015](015-rotation-degradation.md) | Rotation, which must rotate vector components | low |
| [016](016-mass-weighted-remap.md) | Momentum-conserving remap option | low |
| [024](024-leray-projection.md) | Solenoidal projection for the spectral operators | low |

## Method and calibration

| ID | Title | Priority |
|---|---|---|
| [031](031-saturation-never-reached.md) | No ladder severity level reaches the unrelated-field level | medium |
| [040](040-mean-field-anchor.md) | A mean-field anchor for metrics that cannot see the translated one | medium |
| [042](042-rank-interval-block-length-is-half-the-estimate.md) | The rank-correlation interval's fixed 10-frame blocks are half the estimated decorrelation, and its generator is shared across groups | medium |
| [039](039-h1-seminorm-is-not-monotone-under-coarsening.md) | Under `coarsen_bandlimited`, density is out of order in some frames for several metrics, unexplained; the `coarsen` decisions themselves are acted on | low |
| [041](041-subpixel-shift-drops-the-nyquist-mode.md) | A fractional Fourier shift drops the Nyquist mode of an even grid; negligible on the production data | low |
| [044](044-synthetic-ensemble-ignores-the-run-seed.md) | The synthetic ensemble is generated from its own seed, so `seed=` does not change a synthetic run and the ensemble cards cite a seed that had no effect; needs a decision | low |
| [046](046-wavenumber-magnitude-is-anisotropic-on-non-square-domains.md) | The wavenumber magnitude counts cycles across each axis's own length, so a cutoff is anisotropic on a non-square domain, and a wall on only some axes makes a square grid non-square; needs a decision on the definition of `\|k\|` | low |

## Technical debt

| ID | Title | Priority |
|---|---|---|
| [020](020-import-name-collision.md) | `metrics` is a very generic top-level import name | low |
| [032](032-prose-numbers-can-go-stale.md) | Numbers written into card prose can go stale unnoticed | medium |
| [033](033-link-rewriting-is-only-checked-for-deadness.md) | Site link rewriting is checked for dead links, not correct destinations | medium |
| [036](036-increment-flatness-is-not-monotone-under-smoothing.md) | Increment flatness is not monotone under smoothing on any field, so it fails the stated acceptance rule; needs a decision, not a fix | medium |
| [022](022-sim-config-parsing.md) | Solver configs carry executable YAML tags | low |
| [023](023-vendored-kinet-drift.md) | Vendored kinet code is pinned and may drift | low |
| [045](045-retired-tracker-ids-in-code.md) | Retired tracker IDs remain in code comments, tests and six issues | low |

**The pattern for a new defect**: reproduce it, write the test, mark it `xfail(strict=True)`
naming the issue file, and write the issue with the measurement in front of you. Strict mode is
what makes the loop close — fixing the defect makes the test pass, strict mode turns an
unexpected pass into a failure, and whoever fixed it is sent back to remove the marker and the
issue. Do not delete a marker without fixing the issue it names.

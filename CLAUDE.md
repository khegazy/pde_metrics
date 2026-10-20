# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

This repository develops and tests metrics that quantify the quality of fluid simulations (especially ML surrogates of compressible, shocked, turbulent flow), with the eventual goal of using validated metrics as evaluation panels and training losses for a scientific foundation model. It is a collaborative research repo shared by several colleagues.

## Read AGENTS.md first

[`AGENTS.md`](AGENTS.md) is the canonical instruction file for every agent working here,
whichever assistant it is. It covers how to add a metric, a degradation, a data source or a
report renderer; the testing conventions; how to treat the generated LaTeX; and a table of
traps that have already caught someone. This file carries the scientific context that
`AGENTS.md` deliberately does not duplicate.

## Commands

Commands are plain `python` and `pytest` calls, run in whatever environment the contributor
has activated — colleagues use uv, plain venvs and conda, so **do not reintroduce a `uv run`
prefix** anywhere. `uv sync --extra dev` populates `.venv` from the committed lockfile;
`pip install -e '.[dev]'` does the same elsewhere. Nothing needs the repo root as the working
directory.

```bash
python check_setup.py                        # confirm the environment before anything expensive
pytest                                       # skips the CFS-reading and LaTeX tests
pytest -m data                               # reads the real files on CFS
module load texlive/2024 && pytest -m slow   # compiles a report with latexmk
pytest tests/test_analysis.py -q -k spearman # one file, one pattern

python -m metrics                            # what metrics exist
python -m degradations                       # what degradations exist, with severity units

python evaluate.py metrics=[mse] dataset=kinet_re5e4_dev
python make_report.py results/mse_<time> --compile --zip
```

`evaluate.py` writes one `results/<metric>_<time>/` folder per metric plus a
`comparison_<time>/` when several metrics run. Each is self-contained — raw numbers, resolved
config and provenance. `evaluate.py` never renders a report: `make_report.py <folder>` writes a
`main.tex` into the folder that compiles standalone and renders on Overleaf.

Two size knobs, both recorded with the results: `dataset.time.reduction` (evaluate every Nth
frame) and `analysis_grid.resolution` (the common analysis grid every field is remapped onto). The full trajectory at
reduction 1 is roughly half an hour; the default of 50 is under a minute.

Stack: NumPy/SciPy/h5py/pandas/matplotlib with Hydra for configuration. PyTorch is an optional
extra and nothing currently needs it. Weights & Biases is not wired in yet.

## Documentation

| File | What it is |
|---|---|
| `TEST_DESCRIPTION.md` | Plain-language reference for every quantity the suite reports. A copy is placed in each run folder. A test fails if a reported column, degradation or figure is undocumented |
| `issues/` | Open items, one file per item with its evidence. `issues/README.md` is the index. Delete an issue once it is fully resolved (`AGENTS.md` §1) |
| `README.md` | Setup and the NERSC specifics |
| `docs/ideas/` | The plan for metrics not yet built: one overview table, one page per theme, one page per idea. Published on the site under Metrics |

## Source of truth: the cards in this repository

Each implemented metric and degradation documents itself in a **card** beside its
implementation, and `docs/catalog.json` is the machine-readable index of all of them. That
is the source of truth for anything implemented: what it computes, what properties it has,
and what it did on a recorded run. Read the catalog rather than parsing prose, and see
`AGENTS.md` §3 for how to add one.

The plan for metrics that do not exist yet lives in **`docs/ideas/`**: what each idea
would measure, its literature precedent and references, and the team's build priority.
`docs/ideas/README.md` holds the one table of every idea. It lists only work that is not
built: when a metric is implemented, delete its row, its page and its link on the theme page
in the same change (`docs/recipes/add-a-metric.md`, step 7). The LaTeX tracker it was
converted from, `Table_of_Ideas.tex`, is retired and recoverable from git history.

The two-letter ID prefixes (OT-, NM-, TD-, …) are **retired**. They were invented before the
cards existed, they meant nothing to a reader who had not been told the scheme, and a bundle's
directory name — which is what users type in `metrics=[...]` — is now its only identity. A
card's `category` field carries what the prefix used to gesture at, from a controlled
vocabulary in `fmeval/cards/schema.py`. Where an idea page and a card disagree, the measured
card wins.

Every implemented metric should still cite its source paper, with the equation number, in
its `## Definition` section and in `refs.bib`.

## Core problem framing

- **The central pathology is the "double penalty" / shock-shift problem**: pointwise norms like L² doubly penalize a sharp feature (shock, shocklet, eddy) that is correct in shape and amplitude but slightly displaced. The same pathology is called "double penalty" in weather verification and "cycle skipping" in seismic inversion — both fields have mature solutions this project imports rather than reinvents. Every metric here exists to capture a failure mode L² misses.
- **Organizing principle (splitting a field into smooth and sharp parts, `docs/ideas/norms/mollification_split.md`)**: decompose a field into a smooth part and a sharp/singular remainder, and apply the right metric to each — ordinary norms on the smooth part, position-tolerant metrics (Wasserstein, shock-set distances) on the sharp part. Coherent vortex extraction and the Helmholtz solenoidal/dilatational split are principled instances of the same idea. Most ideas in `docs/ideas/` slot into one side of this split.
- **The north-star test case is shocklet-populated compressible turbulence** — many small shocks embedded in turbulence, not one isolated front. Metrics that only work for isolated trackable fronts are rated accordingly.
- **Diagnostics and training losses are separate artifacts with separate requirements.** A diagnostic may be non-differentiable, expensive, and discontinuous; a training loss may not. Do not conflate the two when implementing.

## Evaluation protocol (how a metric earns its place)

Every candidate metric is validated on the degradation-ladder protocol:

1. **Reference**: DNS at Re ≈ 500, isotropic and doubly periodic shear. A Boltzmann solver is planned as the baseline predictor.
2. **Ladder**: the solver degraded in controlled steps (grid coarsening, plus an orthogonal axis such as noise or artificial viscosity).
3. **Acceptance**: a metric joins the panel only if it is monotone in degradation with high Spearman rank correlation. Non-monotone metrics are dangerous for model selection.
4. **Canary (the `gaussian_impostor` degradation)**: a Gaussian random field matched to the reference energy spectrum is included as an impostor predictor. Any metric that scores it well is phase-blind and must not be used alone.
5. Also record: sensitivity (where the metric first departs from clean vs. where a human sees degradation), wall-clock cost per evaluation, and cross-metric correlation to prune redundant panel members.

What to build next is listed, in order, under "What to build next" in `docs/ideas/README.md`. The ensemble metrics (`crps`, `spread_skill`) apply only when ensembles are available; mark them N/A for deterministic surrogates.

## Implementation conventions

- **One source of truth, least new code.** Define every value once, add no aliases, give a
  helper two callers or a reason, and search for existing code before writing new code. The
  rules and the table of where shared code lives are in `AGENTS.md` §1, and
  `tests/test_documentation.py` pins them.
- **Fix detector thresholds once in the evaluator and never tune them per model** — otherwise the metric becomes gameable. This applies to shock sensors, vortex criteria, and any thresholded quantity.
- **Known-correct estimators matter**: e.g. ensemble spread must be computed as the square root of the average ensemble variance, not the average of spreads (Fortin et al. 2014, *J. Hydrometeorology* 15(4), 1708–1713). When an idea page records a computational gotcha, follow it.
- **Cross-mesh comparison**: remap fields conservatively onto a common analysis grid, compare cell averages rather than point samples, and record the remapping operator as part of the metric definition.
- Cite the source paper and equation/table number in a comment for any equation taken from the literature; each idea page lists its references.
- Label new code as prototype or production quality; metric-evaluation code that feeds acceptance decisions should be production quality.

## What exists

Three plugin registries, all discovered by name from config, all extended by one decorated
function: **metrics** (`metrics/`), **degradations** (`degradations/`, 24 operators in 8
families), and **report renderers** (`fmeval/report/`). Readers live in `fmeval/data/` and are
a closed set with explicit imports, deliberately unlike the other two.

The mistakes that quietly corrupt results here — pooling frames for a rank correlation,
averaging a derived field after a remap, deleting k=0 in a high-pass filter, scavenging the
unrelated-field anchor, two definitions of `|k|`, and the rest — are listed once, with where
each fix lives, in `AGENTS.md` §9, "Traps that have already caught someone". Severities on the
smoothing and spectral axes are calibrated per field against a measured spectrum; how, and what
an operator author must do about it, is in `AGENTS.md` §4.

Two limits of the kinet data that calibration does not remove, because they are properties of
the fields rather than of the config: 69% of density's fluctuation energy sits in the four
diagonal modes at |k| = √2 and only 3e-5 of it in the axis modes at |k| = 1, so the cutoffs
available there are few and far apart and a *sharp* filter cannot resolve four severity levels.
The high-pass axis is squeezed between a no-op below those diagonal modes and near-total damage
above them, so it alone does not reach the factor-five damage range the other axes do.

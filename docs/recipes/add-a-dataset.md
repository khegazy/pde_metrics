# Adding a dataset

A dataset enters this repository in two distinct capacities, and the second one is easy to
forget. First the dataset must be **readable**: a configuration file and, if the file
format is new, a reader. Then the dataset must become **citable evidence**: registered
with the card system, given a window of time over which the flow is properly developed,
evaluated, and calibrated. A dataset that is readable but not registered can be
experimented on freely, but no metric's page may cite it. That is the correct state for
scratch data and the wrong one for a physical regime the pages ought to cover.

## 1. Make it readable

Add `configs/dataset/<name>.yaml`. Another trajectory of a simulation that already has a
shared fragment -- `_re5e4_simulation.yaml`, which the three Re = 5e4 configs inherit -- lists
that fragment under `defaults:` and states its `name`, `format` and `trajectory`. A new
simulation gets its own `_`-prefixed fragment holding what its configs share: `path` (under
`${paths.data}`), `fields` from the canonical vocabulary, the `time` selection, the
`complexity` block naming its family and parameters, and `notes`. State a key only to change
it: the defaults of `time`, `recompute_derived` and every `reader` option belong to the schema
in `fmeval/config.py` and to the reader's constructor, and `tests/test_configs.py` names any
value a file restates. `evaluate.py` builds the config into that schema before it reads any
data, so a run names the key an option forgot instead of defaulting silently.

If the file layout is new, add a reader in `fmeval/data/` implementing the `Trajectory`
contract in `fmeval/data/base.py`, and register it with `@register_reader`. Readers are a
deliberately closed set with explicit imports in `fmeval/data/readers.py` — unlike metrics and
degradations, there is no discovery walk. Three rules are not negotiable: channel-first
arrays with trailing `(x, y, z)`; the fixed field vocabulary, tagged primitive or derived;
never slice the time axis. Test against the shared reader contract in
`tests/test_loader_contract.py` with a small synthetic file in `tests/fixtures_h5.py` that
reproduces the real format's quirks, and keep every fixture non-square.

A dataset does not have to be on the local filesystem. When the file named by `path` is
absent, the location is resolved against `paths.data_url` instead and the reader is opened
on the published copy over HTTP byte ranges — `fmeval/data/locate.py` decides, and a local
copy always wins. Nothing is downloaded whole: opening the 166 GiB production trajectory
costs three requests. A new reader supports this by calling `fmeval.data.remote.open_h5`
when handed a URL rather than a path.

Two costs only appear remotely, and both are worth checking on a new layout. A 1-D dataset
chunked one element per chunk — which is how the kinet solver writes its clock — is
catastrophic to read whole over HTTP, so `fmeval/data/_timeaxis.py` reconstructs and then
verifies it; and the severity calibration reads several frames, so it is the slowest part
of a remote smoke run. Verify a new reader against the real published file with a
`web`-marked test.

If the data carries fields outside the canonical vocabulary — a magnetic field, say —
extend `FIELDS` in `fmeval/data/base.py` first, tagged primitive or derived. Derived
fields need a recompute rule in `fmeval/derived.py`, because they are recomputed on the
analysis grid, never block-averaged. A recompute rule may use kinematics only. Never add one
that needs an equation of state, such as pressure from density: that relation belongs to the
solver, so a dataset that does not store a quantity does not provide it.

**Declare the boundary of every axis.** A reader's `GridSpec.boundary` names one entry of
`BOUNDARIES` in `fmeval/data/base.py` per axis: `"periodic"`, or `"neumann"` for a
zero-gradient wall. Never call an axis periodic because the operators want one. On a
non-periodic axis the degradations act on the field extended by that boundary's rule, and a
metric declaring `requires_periodic` is not run at all. A boundary type the vocabulary lacks
is a new entry there, with an extension that is continuous across its seam.

**A dataset computed from a closed form** needs no file. Subclass `ClosedFormTrajectory` in
`fmeval/data/analytic.py`: build what the solution needs once in the constructor, implement
`solution(time)`, and cite the source and equation number of every formula beside it. Test it
against an independent statement of the physics, as `tests/test_analytic_datasets.py` does,
rather than against a copy of its own formula. Its config ranks below every simulated dataset.

## 2. Check the calibration

The smoothing and spectral severities are resolved per field against a spectrum measured
from the data, so a new dataset changes what every calibrated severity means there. Run
the smoke evaluation and read the calibration table it writes:

```bash
python evaluate.py metrics=[mse] dataset=<name> degradation=quick
```

Look at `data/calibration.csv` in the results folder. The characteristic length scale of
each field should have resolved to a real number rather than NaN, the spread of those
scales should be small, and the configured list of strengths should produce genuinely
distinct experiments. A strength that collapses onto a milder one, or onto an operation
that does nothing at all, is flagged `severity_degenerate`. If a whole degradation
collapses on the new data, its list of strengths needs a range suited to that dataset —
and that is a finding worth recording rather than routing around.

## 3. Decide what part of the dataset is evaluated

Every metric runs on every dataset, so the part of a dataset that is evaluated sets the cost
of the whole panel. Choose it to balance three things (Kareem, 2026-11-26):

1. **Enough evaluations for a good measurement.** The rank statistics are computed per frame
   and never pooled across frames, so their precision comes from independent frames. Frames
   closer together than the integrated autocorrelation time add cost, not information: on
   `kinet_re5e4` the 161 frames of the default window hold 7 to 12 independent samples, at an
   autocorrelation time of 13 to 23 frames (`METRIC_EVALUATION_CRITIQUE.md`, finding 2).
   Independent trajectories or seeds are independent samples outright.
2. **The most distinguishing parts.** Keep the windows, trajectories and features where the
   dataset does what it exists for, the developed flow, the shock while it is present, the
   regime a test targets, and drop transients, near-duplicates and degenerate stretches. A
   dataset that serves several purposes may keep a few named windows rather than everything.
3. **Evaluation time and disk.** Measure the cost of one frame with a cheap metric and with
   the most expensive one that runs on the dataset (for example `persistence_wasserstein`,
   `variogram_score`, `wasserstein`), project the full panel, and keep stored data to what is
   evaluated. An analytic reader stores nothing, but its grid and frame count still set the
   time.

Use the existing selectors rather than new ones: `dataset.time.start`, `stop`, `reduction`
and `max_frames`; `frame_stride` on the reader; `analysis_grid.resolution`; and, for a dataset
of many trajectories, the list of trajectories kept. A small dataset may be kept whole. Write
the choice and the reasoning, with the measured costs, as comments in the dataset's YAML file
and in its log (step 7). The agent that adds the dataset makes this decision and records it;
a person may override it.

## 4. Register it as citable evidence

Edit `configs/cards/default.yaml`:

- add the dataset to `evidence_datasets` — until then, `fmeval.cards evidence` refuses
  runs on it by name — with the phrase naming the kind of claim a run on it supports
  ("developed flow", "an analytic check: ..."), which every card citing it quotes in its
  run summary;
- add it to `evidence_dataset_properties`: whether every axis is periodic and whether every
  frame carries ensemble members, which every metric card's *Across the experiments* table and
  the site's coverage page read to say why a metric is not run on it; a test opens the dataset
  and checks both. Then run `python -m fmeval.cards catalog`, which adds the dataset's row to
  every metric card;
- record its window under `evidence_window`;
- decide whether the **one fixed snapshot every example panel is drawn from** stays where
  it is. All the panels share a single snapshot so that the gallery can be compared
  side by side. Adding a second physical regime does not move that snapshot unless the
  panels should now illustrate the new regime, which is a person's decision.

## 5. Produce the evidence

On a machine with the data:

```bash
python evaluate.py 'metrics=[<all implemented>]' dataset=<name> \
    dataset.time.start=<start> dataset.time.reduction=<n>
python -m fmeval.cards evidence --all --results results/comparison_<stamp>
python -m fmeval.cards catalog
```

Each fingerprint file records which dataset it came from, so measurements from different
datasets accumulate rather than overwrite one another in principle. Note the current
limitation, though: a page displays **one** run's numbers, so regenerating against the new
dataset replaces the tables that were shown before. If you want two regimes shown side by
side, that is an extension to `evidence.py` to propose — never a reason to hand-edit
anything.

## 6. Write its page and draw its dynamics

Every dataset config appears on the page of its physical problem, `docs/datasets/<family>.md`,
named by the config's `complexity.family`; a test enforces it. A new variation of an existing
problem joins that page's table. A new problem gets a page of its own, linked from
`docs/datasets/README.md`. Say what the problem is and what the evaluation measurably sees on
it. A computed dataset also gives its equations, each cited to its source with the equation
number. Draw its fields over time with

```bash
python -m fmeval.cards dynamics <name>
```

which writes the figures, and the numbers behind them, to `docs/datasets/_generated/`. Commit
both. Never draw or edit them by hand.

## 7. Keep the dataset's log

Every dataset has a log beside its page, `docs/datasets/logs/<page>.md`, one per page and so
one per physical problem, with a section per configuration. Its reader is the next agent who
updates the dataset: it records why the dataset is in its current form, so that agent does
not undo a deliberate choice or repeat a dead end. The log is not published on the site
(`exclude_docs` in `mkdocs.yml`), but the documentation tests check it like any page.

Write it in the same change that adds or alters the dataset, and append to it on every later
change; never rewrite an old entry, add a new one that supersedes it. It holds:

1. **What the dataset is for**: which tests, metrics or experiments need it, with the
   specification or issue that asked for it.
2. **How it is treated**: the source (path, provenance, solver and its configuration, or the
   closed form and its citation), the reader and options, fields kept and dropped, grid,
   boundary per axis, and any conversion.
3. **What part is evaluated** (step 3): the windows, stride, trajectories and analysis grid
   kept, the number of independent samples they give, the measured cost per frame with a cheap
   and an expensive metric, the projected time of the full panel, the disk used, and why this
   balance was chosen over keeping more or less.
4. **Decisions and why**: every choice a later agent might question, with the alternatives
   considered, the reason the one taken won, who made it (the user, or the agent), and how to
   reverse it.
5. **Log entries**, newest last, each dated: what was done (files, commands, data written),
   how it was verified, and what was not verified.
6. **Open points**: what is known to be missing or doubtful.

## 8. Finish

```bash
pytest                      # includes the reader contract and card checks
pytest -m data              # on a machine with the data mounted
```

Report the time window you chose and why, any strengths that collapsed on the new data,
and any physical field the fixed vocabulary did not already have.
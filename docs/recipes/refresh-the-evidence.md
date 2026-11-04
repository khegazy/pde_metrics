# Refreshing the evidence

Every measured number on every page traces back to one pinned evaluation run. Replacing
that run — after adding a metric or a degradation, changing which strengths are applied,
or adding a dataset — is routine work, but the order of the steps matters and one step is
easy to miss.

## 1. Produce the run

On a machine with the data:

```bash
python evaluate.py 'metrics=[mae,mse,rmse,vrmse,enstrophy,kinetic_energy]' \
    dataset=kinet_re5e4 dataset.time.start=2000 dataset.time.reduction=50
```

Use the time window recorded in `configs/cards/default.yaml`, adding any newly implemented
metrics to the list. Note the name of the `results/comparison_<stamp>` folder the run
writes.

Every metric is run on every evidence dataset where it makes sense (`AGENTS.md` §1, "How every
metric is evaluated"), so repeat the run for each dataset in `evidence_datasets`, with that
dataset's own window. A run over every metric on the full ladder takes hours in one process.
To spread it, run the same command several times at one clean commit, each with a different
part of the metric list, then merge the parts into the one comparison folder a single process
would have written:

```python
from fmeval import io as fio
folder = fio.combine_runs(["results/comparison_<a>", "results/comparison_<b>"],
                          fio.claim_stamp("results"), across="metrics")
```

`combine_runs` refuses parts that ran at different commits or on different ladders, or that
share a metric.

## 2. Regenerate in dependency order

```bash
python -m fmeval.cards exemplars --all                              # if operators or the
                                                                    # canonical frame changed
python -m fmeval.cards evidence --all --results results/comparison_<stamp>
python -m fmeval.cards overview --results results/comparison_<stamp>  # docs/figures/<run>/
python -m fmeval.cards catalog
```

Example panels come before measurements, because a metric's measurements may reference a
degradation's panel. The `evidence` step also redraws each card's figures (the sensitivity
profile and the response curves) into `_generated/` as SVG with the numbers behind each in
a JSON file of the same name, so a figure cannot go stale relative to the table beside it.

A card cites one run per experiment (dataset), and its fingerprint records them, the primary
run first. `--all` regenerates every card from the runs it records: each `--results` run
replaces the card's run on the same dataset, in the same place, and a run on a dataset the
card does not cite yet is added after the others. `--results` may be repeated, one run per
experiment. A card that none of the given runs contains is skipped and named, so a new kinet
comparison run leaves the ensemble and Sod-only cards alone. With no `--results`, `--all`
regenerates every card from the runs it already records, which is how a change to the
generator reaches every card. Recorded runs are looked up by name under `results/`: link a run
kept on scratch there (`ln -s $PSCRATCH/fluid_metrics_results/<run> results/<run>`). A run
replaced by a given one is never read, so it may already be archived. Run from the repository
root with a relative `--results` path, because the path is written into every block marker
as typed.

The `overview` step draws the cross-metric figures of the site's "Sensitivity at a glance"
page into `docs/figures/<run>/`; delete the previous run's directory there when you replace
the run, so the page shows one run. The catalog comes last, because it reads the fingerprint
files the other steps write. It also rewrites the *Across the experiments* table on every
metric card, which says which experiments the card cites a run on and why it cites none on
the others; run it after any change to a card's runs, to its `not_run` in `card.yaml`, or to
`evidence_datasets`. The committed catalog is compared against a freshly built one in CI, and
each card's table against the records, so forgetting that last step fails the build rather
than shipping a stale index.

## 3. The step that is easy to miss: the prose

Generated blocks update themselves. **Numbers that an author typed into sentences do
not.** The Results readings on each page cite specific values — ratios, correlations,
damage scores — from the previous run, and nothing mechanical reconciles them yet.
`issues/032` proposes that check; until it exists, reconciling them is a manual
obligation.

For every metric, compare each number in the hand-written Results text against the
regenerated tables beside it, and either correct the sentence or flag it. This has caused
real trouble before: the first pages carried damage scores of 0.80 and 0.51 for the fake
prediction, taken from a 15-snapshot run, while the reference run measured 0.90, 0.66 and
1.23. If you are an agent, list every number you changed in your report — that list is
exactly what a reviewer needs in order to re-check the work.

## 4. Signatures invalidate themselves — tell the humans

Editing prose changes the page's hash, so any signed page you corrected becomes unsigned.
That is correct behaviour: the signature attested to text that no longer exists.
Regenerating the blocks alone does **not** invalidate a signature, because generated
content is stripped out before hashing — which means a page whose tables changed but whose
prose still describes the old run keeps its signature while being wrong. That is the gap
`issues/032` describes. Until it closes, name in your report every signed page whose
tables materially changed, so that its owner can reread and re-sign.

## 5. Finish

```bash
python -m fmeval.cards check --all
pytest
```

Commit the reference to the new run folder, the regenerated `_generated/` content, the
catalog and the prose corrections together, so that the repository never holds a mixture
of numbers from two different runs.
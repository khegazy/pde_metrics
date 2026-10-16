# Verifying that a refactor changed no number

Use this procedure whenever you change code without meaning to change any results: moving
files, splitting modules, merging duplicated code, renaming things, performance work. The
standard: **any difference beyond the stated tolerance is a bug you introduced, not an
improvement.** This procedure has caught real breakage. Splitting one module once silently
lost three whole degradations — 630 rows of results — while every test still passed and the
registry still listed all 21 operators. The row-by-row comparison below is what found that.

The development dataset is the right one to use here. That dataset is banned from a page's
evidence because its physics is meaningless, but checking that two runs agree does not need
physics — it needs the same numbers twice, and a development run takes about a minute.

## The tolerance

Results must agree to a relative tolerance of `1e-12` (`np.isclose(rtol=1e-12, atol=0)`).
Bitwise identity is not demanded, because it would forbid merging two copies of a sum whose
terms were added in a different order: a reordered float64 reduction moves a value by a few
units in the last place, about `1e-15` relative. `1e-12` leaves three orders of magnitude
for that and still fails any change of formula, constant or selection, which moves a value by
far more. Text, row keys, row order and the presence of every file are compared exactly. The
comparison prints the largest relative difference it accepted, so a pass that relied on the
tolerance says so; most refactors here come out bitwise identical.

## 1. Before you change anything: capture the baseline

Three runs, because no single one exercises everything. The first is the six pointwise and
energy metrics on the default ladder. The second is every metric, with the ladder entries
that are off by default switched on (`multiplicative_noise` is in no ladder at all, so it
needs the `+`). The third is the ensemble metrics on the synthetic ensemble, which the other
two cannot reach. Put Hydra's own output inside the same directory, so that the comparison
can replace that directory with one placeholder.

```bash
D=/tmp/refactor/before      # use /tmp/refactor/after for step 3
python evaluate.py 'metrics=[mae,mse,rmse,nrmse,enstrophy,kinetic_energy]' \
    dataset=kinet_re5e4_dev degradation=default dataset.time.max_frames=3 \
    paths.results=$D/run1 hydra.run.dir=$D/run1/hydra
python evaluate.py "metrics=[$(python -c 'from metrics import registry; print(",".join(registry.available()))')]" \
    dataset=kinet_re5e4_dev dataset.time.max_frames=3 \
    degradation.ladder.disk_blur.enabled=true degradation.ladder.epanechnikov_blur.enabled=true \
    degradation.ladder.band_attenuate.enabled=true degradation.ladder.subsample.enabled=true \
    degradation.ladder.gain.enabled=true degradation.ladder.translate_y.enabled=true \
    '+degradation.ladder.multiplicative_noise={enabled:true,severities:[0.01,0.1,0.5]}' \
    paths.results=$D/run2 hydra.run.dir=$D/run2/hydra
python evaluate.py dataset=synthetic_ensemble degradation=ensemble_miscalibration \
    'metrics=[crps,spread_skill,ensemble_mean_rmse,rank_histogram]' \
    paths.results=$D/run3 hydra.run.dir=$D/run3/hydra
python -m metrics > $D/metrics.txt
python -m degradations > $D/degradations.txt
```

If you have already made your change, stop. Stash it, capture the baseline, unstash.

## 2. Make your change

## 3. Re-run and compare

Repeat step 1 with `D=/tmp/refactor/after`, from the same checkout and with otherwise
identical command lines: the recorded configuration embeds absolute paths. Then:

```bash
diff /tmp/refactor/{before,after}/metrics.txt
diff /tmp/refactor/{before,after}/degradations.txt
for r in run1 run2 run3; do
    python docs/recipes/compare_runs.py /tmp/refactor/before/$r/comparison_* \
                                        /tmp/refactor/after/$r/comparison_*
done
```

Both diffs must be empty and each comparison must end in `IDENTICAL`. The script compares
every folder an invocation wrote, the comparison folder and each per-metric folder, and every
file in each. Rows are keyed on `metric, field, degradation, level, frame_index,
variant_label`, so row order cannot hide anything, and every column is compared except
`wall_time_s`, which is a clock rather than a result. A file present on one side only is a
difference, so a file the script has never heard of is still checked. Its docstring states
the rule for each kind of file.

Degradations that draw random numbers are held to the same standard: every draw is seeded
from the run seed, the label, the snapshot and the field together, so the draws reproduce.

If a change adds a key to `run_meta.json` on purpose, name it with `--ignore <key>` and say
so in the pull request. Never use it for a key whose value you did not mean to change.

## 4. If it is not identical

- **Rows are missing** → one degradation did not run at all. This is the failure mode a
  module split produces: a private helper the operator needed was lost, or an import broke.
  Check
  `python -c "from degradations import registry; registry.discover(); print(registry._IMPORT_ERRORS)"` —
  it must print an empty dict. A code defect in an operator stops the run outright; if
  your run completed with rows missing, find out why before anything else.
- **Values differ** → your change altered what something computes. Do not accept the new
  values, do not loosen the tolerance, and do not rerun hoping the difference goes away.
  Either find and fix the unintended change, or — if you believe the new values are
  *correct* and the old ones were wrong — stop and report exactly that, listing the rows
  that differ. That decision belongs to a person.

## 5. Afterwards

Run `pytest` as well — this comparison and the test suite catch different things. If the
change touches the report, render one baseline run folder with `make_report.py` before and
after, on two copies of the same folder (it writes into the folder it is given), and compare
the copies with `--folder-only --skip-images`: the report's cost columns are wall-clock
times, so two different runs would differ there for no reason. State in your report that you
ran this procedure and what it showed. "Three runs, 10620 rows, identical" is one line, and
it is the line a reviewer most wants to see.

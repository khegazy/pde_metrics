# 019 — The PonD grid sequences are evaluated at their end time only, and `observed_order` is left as it is

**Date:** 2026-11-27. **Made by:** the dataset agent of build-order step 18, on the branch
`build_datasets`. **Reverse with:** option 1 of issue 149 (let `observed_order` pair the grids on
the frame index), then convert the runs again from scratch with a smaller `--every` (the raw runs
are on scratch until it is purged; every run is reproducible from
`docs/datasets/logs/kinet_runs/shocks_2d/`), drop `time: {start: 1}` from the two fragments in
favour of the frames wanted, update the two logs and pages, delete this file and its row.

## The question that would have been asked

kinet's finite-volume solver takes an adaptive time step, so the vortex and oblique Riemann runs
on different grids save their frames at nearby but different times, and share exactly only the
start and the end time. `fmeval.analysis.observed_order` pairs grids at equal times. Should the
analysis be extended to pair them by frame index, so each sequence gives its order at several
times, or should the datasets evaluate only the end time, with no change to the analysis?

## The choice

**Only the end time; no change to the analysis.** Each configuration's runs are converted with the
initial condition and the last frame only, and evaluated at the last frame: $t = 10$ (one period)
and $t = 2.5$ for the two vortex sequences, $t = 0.2$ for the oblique Riemann runs.

## Evidence and sources

- **Kareem's rule for this plan** (`dataset_specs/BUILD_ORDER.md`, "How code is written for this
  plan"): change the plan to fit the code rather than the code to fit the plan. Pairing by frame
  index would be a new rule in the one function every grid sequence goes through.
- **The field's own measurement.** The standard study of this vortex reports the error after one
  period (Spiegel, Huynh & DeBonis 2015, AIAA 2015-2444, Fig. 2, which plots L2 errors "after one
  period"), the time the first configuration evaluates.
- **What is lost is small.** The job that ran the vortex paired the nearest frames by hand (time
  mismatch up to a relative 7e-4) and found the rms orders between 1.84 and 2.12 at $t \approx 2.5$
  and 5 and between 1.77 and 2.13 at 10 (`checks/check_vortex.txt`): the end time is not an outlier.

## What it changes

Each sequence gives one order per metric, field and pair of grids, not one per time; the converted
files hold two frames each (26.6 MB for the vortex, 25.8 MB for the oblique runs). No existing
number moves.

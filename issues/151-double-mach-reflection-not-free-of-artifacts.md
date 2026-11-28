# The double Mach reflection's stored field is not free of numerical artifacts

**Category:** data generation
**Priority:** medium. `kinet_double_mach_reflection` is the only reference with several
interacting shocks, and a metric scored on it may respond to the solver's artifacts rather than
to the flow (Kareem, 2026-11-27: simulate fine enough that artifacts are negligible).
**Status:** open (2026-11-28). The dataset now reads a $960 \times 240$ run block-averaged to
$480 \times 120$ (`N240_coarse-480-120.h5`), which halved every artifact of the native run but
did not remove them; whether to run $1920 \times 480$, change the set-up or drop the dataset is
with the owner.

## Evidence

What remains in the stored field, at the dataset's three stored times, in cells of $1/120$, with
the native run (`N120.h5`, now the coarser run beside it) for comparison
(`docs/datasets/logs/double_mach_reflection.md`, decisions 6 and 7 and the entries of 2026-11-28):

- the incident shock trails its exact position by 0.75 to 1.16 cells (native 1.39 to 2.21), with a
  10 %-to-90 % width of 1.40 to 1.78 (native 1.66 to 2.83); on the fine grid itself it trails by 1.5
  to 2.4 of its own cells, so the lag is a fixed count of cells;
- a band of excess density left where the initial shock stood (the thin feature above the
  reflected shock) peaks 3.3 % above the post-shock density (native 5.6 %), and a band trailing the
  incident shock 4.8 % (native 8.5 %);
- the two runs differ by 2.5 to 4.8 % over density, pressure and velocity (relative L2 in the
  evaluated window), so the stored field's own error is probably of that size;
- the stored frames never fall below the unshocked state, but 12 of the run's 2997
  saved frames do (to a density of 1.23), and on the fine grid 878 frames fall more than 1 %
  below it somewhere, at the foot of the incident shock in 81 of a sample of 91.

Block-averaged to $240 \times 60$ the finer run has no such frame and its shock trails by 0.29 to
0.62 cells and is 0.97 to 1.60 cells wide, but the bands (3.1 %, 4.6 %) and the difference from the
coarser run (2.1 to 3.0 % in density) are as large as at $480 \times 120$.

## Options

1. Run $1920 \times 480$: about 12 000 steps, 15 to 32 GPU-hours on one A100 (the per-cell rate of
   the $960 \times 240$ run, or the 9.7 s per step of a 31-step throughput run). By the measured
   halving it would bring the shock to about half a cell, but the bands only to about 2 % and 3 %
   (an extrapolation).
2. Remove the bands at their source: they start at the sharp initial discontinuity and at the
   imposed top shock (read from the native run's frames; the mechanism is not checked against a
   source). A smoothed initial shock or another top-face treatment in kinet's case changes the
   problem, so it is the owner's decision.
3. Keep the present field, labelled with its remaining artifacts (done, decision 7), or drop the
   dataset.

What it affects meanwhile: a metric that places shocks against the exact front reads the lag as
about one cell of error, and a detector of features or a statistic of the uniform regions may
respond to the two bands. The metric cards' runs on this dataset predate the change of file.

The finer run's raw output and its coarse-grained tiers were deleted on the owner's instruction;
the archived configuration in `docs/datasets/logs/kinet_runs/shocks_2d/dmr_N240_t0p2/` regenerates
them.

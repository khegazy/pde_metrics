# The observed order pairs runs with an adaptive time step only at their end time

**Category:** analysis
**Priority:** low. The two vortex sequences and the two oblique Riemann sequences give their
order at one time each; more times would show whether the order holds as the flow evolves, which
is the only use of the extra frames.
**Status:** open; not built (2026-11-27).

## Context

`fmeval.analysis.observed_order` pivots the rows of a grid sequence on `(metric, field, time)`, so
two grids are paired only where their frames have exactly equal times. kinet's finite-volume PonD
solver takes an adaptive time step, so its runs save their frames at nearby but different times on
different grids; it lands exactly on the configured end time, which every grid therefore shares,
and on 0.

## Evidence

Saved times of the isentropic vortex runs near a quarter period, from the job's check
(`docs/datasets/logs/kinet_runs/shocks_2d/checks/check_vortex.txt`): 2.47998 on $64^2$, 2.47833 on
$128^2$, 2.47789 on $256^2$, 2.47780 on $512^2$; the same holds near every saved time and on the
oblique Riemann runs (0.05112 on $200^2$ against 0.04995 on $400^2$ near 0.05). The job computed
its orders at 2.5 and 5 by pairing each coarse frame with the fine frame nearest it (time
mismatch up to 0.0017, a relative 7e-4): density rms orders 1.992 and 1.917 (64 to 128), 2.003 and
1.929 (128 to 256), against 2.000 and 1.900 at the shared end time 10.

So `kinet_isentropic_vortex_mu1em5`, `kinet_isentropic_vortex_mu1em7`,
`kinet_oblique_riemann_30deg` and `kinet_oblique_riemann_45deg` evaluate only each run's last
frame (`docs/datasets/logs/isentropic_vortex.md` and `docs/datasets/logs/sod_shock_tube.md`,
their decisions), and their converted files hold nothing else.

## Options

1. Let `observed_order` pair on the frame index (`lead_step`) instead of the time, when asked,
   reporting the finest grid's time: frame `k` is the same stage of the run on every grid when the
   saving cadence scales with the grid, as on these runs (every 32, 64, 128 and 256 steps). About
   six lines and a test. The error of each run is still against the exact solution at its own
   time, so only the pairing changes; the relative time mismatch above sets how far the result can
   move.
2. Rerun with the solver writing at fixed times. Not tried: whether kinet's PonD writer can save at
   prescribed times was not checked.

Either needs the dropped frames converted again (`python -m fmeval.data.convert_kinet SRC DST
--every N` with a smaller N) while the raw runs are on scratch, which is purged after about eight
weeks; every run is reproducible from `docs/datasets/logs/kinet_runs/shocks_2d/`.

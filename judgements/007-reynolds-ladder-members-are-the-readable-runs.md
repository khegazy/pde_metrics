# 007 — The Reynolds ladder runs on the readable runs: Re = 5e4 and Re = 1e6

**Date:** 2026-11-04. **Made by:** the agent of task `data-reynolds-ladder-and-degradations`
(branch `worktree-agent-a3ca51a9796744b4c`, effort `update_metric_eval_principles`).
**Reverse with:** remove `kinet_re1e6` from `hydra.sweeper.params.dataset` in
`configs/dataset_family/reynolds_ladder_2d.yaml` (and from `evidence_datasets` in
`configs/cards/default.yaml`), delete `configs/dataset/kinet_re1e6.yaml`, its figures under
`docs/datasets/_generated/` and its row on `docs/datasets/reynolds_ladder_2d.md`; then delete
this file and its row in `README.md`.

## The question that would have been asked

The family was declared as five runs under `datasets/kinet/doubly_periodic/old/`, at Re = 5e4,
6.25e4, 7.5e4, 8.75e4 and 1e5 (issue 011). Four of them cannot be opened (below). Should the
family wait for those files, or run now on the runs that can be read? And should its Re = 5e4
member be the pinned `kinet_re5e4` or the `old/` run?

## What was measured

- **The four higher-Re files do not open.** Every `.h5` file in `old/` at Re = 6.25e4, 7.5e4 and
  8.75e4 (both the T = 10000 and the T = 20000 runs), and the 512^2, the 128^2 and two of the
  256^2 Re = 5e4 runs, fail in h5py 3.16 / HDF5 2.0 with "bad object header version number".
  Their superblock (version 0) has the file-consistency flag set to 1 and an end-of-file address
  of 2048 bytes, and the root object header at byte 0x60 is all zeros: the HDF5 metadata was
  never written, as when a writer is stopped before closing the file. The raw data appear to be
  present: each 512^2, T = 20000 file is 1,384,190,171,576 bytes, 5,528 bytes more than 33
  float64 channels of 20001 x 512^2 values, the channel count of the readable 256^2 file of the
  same layout (my inference, not checked in the unreadable files). Without the headers nothing
  says where each dataset starts. The Re = 1e5 file is owned by another user with group `jalb` and
  cannot be read from this account (permission denied).
- **`kinet_re5e4` is the same simulation as the `old/` Re = 5e4 run.** Same Re, Mach number,
  grid, length and initial-condition parameters (lambda 80, epsilon 0.05, density 1; the run
  configs `dc804f.yaml` and `734eb0.yaml`). Frame 0 is bitwise identical in velocity and density;
  the velocity differs by at most 1.9e-10 at frame 2000, 1.1e-8 at 5000 and 6.0e-9 at 10000,
  against an rms of 0.040, a re-run of the same configuration. The `old/` file also uses the
  older dataset names (`rho`, `u`, `t`), which the `kinet_raw` reader does not read.
- **A readable run at another Reynolds number exists**, in the same directory tree as
  `kinet_re5e4`: `weakly_compressible_isoT_fluids/sys_Re-1e6_Ma-1en1/`, 1024^2, 40000 steps,
  `kinet_rollout_status: complete`. Its config (`85db0e.yaml`) has the same initial-condition
  parameters and Mach number, and its clock ends at the same dimensionless time, 2.2553. At a fixed
  Mach number the lattice velocity is fixed, so the step needed per unit time scales with the
  number of cells: 1024^2 takes four steps per step of 256^2. Its frame 0, block-averaged to 256^2,
  matches `kinet_re5e4`'s frame 0 in density to 6.7e-16 and in velocity to 3.4e-3 (rms 0.040),
  the difference being the same profile sampled on a finer grid. Drawn side by side at matched
  times, the two roll up into the same pair of vortices at the same times; the Re = 1e6 run has
  thinner filaments.

## The choice

**Run the family now on `kinet_re5e4` (rank 0) and the Re = 1e6 run as `kinet_re1e6` (rank 5,
after the four unreadable members' ranks 1 to 4), and keep `kinet_re5e4` as the Re = 5e4
member.** Reasons: the comparison issue 011 asks for can be built and exercised only on data that
reads; the two runs share everything but the Reynolds number and the grid, and the grid is
removed by remapping both onto the family's 128^2 analysis grid; and the pinned `kinet_re5e4`
is the `old/` run's own simulation, so switching would change nothing but the file format.

The family's frames are put on one clock: `kinet_re1e6` reads every fourth stored frame
(`reader.frame_stride: 4`), so its frame i is the same physical time as `kinet_re5e4`'s, and the
evidence window `dataset.time.start=2000 dataset.time.reduction=50` selects the same 161 times on
both (my reasoning: comparing two Reynolds numbers at different stages of the same evolution would
confound the two).

## What it changes

Section 12 compares a 20-fold step in Reynolds number rather than the 2-fold ladder planned, and
it has two points rather than five, so it can show whether a statistic moves with Re but not how.
The Re = 1e6 run is far less resolved at its grid than Re = 5e4 is at its own; whether it is a
well-resolved simulation at all was not checked, and is not claimed (the entropic collision
stabilises under-resolved runs). The four unreadable members stay in issue 011, with the file
each should use once it can be read.

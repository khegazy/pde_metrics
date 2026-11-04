# Four members of the Reynolds ladder cannot be read

**Category:** data generation required
**Priority:** medium
**Status:** open in part. The Re = 6.25e4, 7.5e4, 8.75e4 and 1e5 runs cannot be opened, so the
ladder has two members, Re = 5e4 and Re = 1e6, rather than the five planned. The comparison
itself is built: `python evaluate.py -m dataset_family=reynolds_ladder_2d ...` runs every member
and gathers them into one folder, whose report section 12 (`complexity_response`) draws each
member's rank correlation, Gaussian-impostor damage and sensitivity level against its
complexity rank (`judgements/007`).

## Context

The question is whether a metric's behaviour holds as physical complexity rises. A metric that
is monotone at Re = 5e4 and scrambles at a higher Reynolds number is not trustworthy for a
foundation model. Two members show whether a statistic moves with Reynolds number; they cannot
show how.

## Evidence

Under `datasets/kinet/doubly_periodic/old/` (checked 2026-11-04, h5py 3.16, HDF5 2.0):

| Re | File the member should use | State |
|---|---|---|
| 6.25e4 | `WeaklyCompIsoT_Re-625e2_.../D2Q9_shape-512-512_T-20000_H-243712.h5` | does not open |
| 7.5e4 | `WeaklyCompIsoT_Re-75e3_.../D2Q9_shape-512-512_T-20000_H-a7fd0a.h5` | does not open |
| 8.75e4 | `WeaklyCompIsoT_Re-875e2_.../D2Q9_shape-512-512_T-20000_H-205256.h5` | does not open |
| 1e5 | `WeaklyCompIsoT_Re-1e5_.../D2Q9_shape-512-512_T-20000_H-3ab478.h5` | permission denied (group `jalb`) |

"Does not open" is h5py's "bad object header version number". Each such file's superblock has
the file-consistency flag set and an end-of-file address of 2048 bytes, and its root object
header is all zeros: the HDF5 metadata was never written. The T = 10000 runs at 6.25e4 and 8.75e4
(`H-a6b5d2`, `H-2a5d90`) are in the same state, as are the 512^2, 128^2 and two of the 256^2
Re = 5e4 runs there. Only the 1e5 run's 64^2 coarse-grained copy opens, which is below the
family's 128^2 analysis grid.

Why the T = 20000 files: at Mach 0.1 a 512^2 run takes two solver steps per step of a 256^2 run
over the same physical time, and the run configs (`configs/<hash>.yaml` beside each file) give
the same initial condition (lambda 80, epsilon 0.05, density 1) and a run length of 20000 steps
on 512^2, the span of `kinet_re5e4`'s 10000 on 256^2. The T = 10000 files on 512^2 cover half of
it.

## What is needed

Readable copies of the four files: from the data owner, or a recovery of the headers. Then, for
each, a config like `configs/dataset/kinet_re1e6.yaml` with `reader: {frame_stride: 2}`, the run's
rank (1 to 4) and parameters; its name in the family's sweep; and its severity calibration
checked at the 128^2 grid (`AGENTS.md` §5). The files use the old dataset names (`rho`, `u`,
`t`), which `kinet_raw` does not read, so the reader needs those names too.

## Related

`configs/dataset_family/reynolds_ladder_2d.yaml`; `judgements/007`;
`docs/datasets/reynolds_ladder_2d.md`.

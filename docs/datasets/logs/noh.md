# Log: Noh implosion (cylindrical)

This log records why the `noh` dataset is in its current form, for the next agent who changes
it. Its public page is `docs/datasets/noh.md`. Entries are appended, never rewritten.

## What the dataset is for

The six shock metrics share one detector, and before this dataset their only shock was Sod's,
one or two cells on a line, where a displacement, a size change and a rotation cannot be told
apart (`dataset_specs/03_two_dimensional_shocks.md`, Sect. 1). Noh's front is a circle, so it
crosses the grid at every angle in one frame, and its post-shock state is the same at every
time, so the jump the detector reads never changes while the radius grows: a displacement with
nothing else changing. It serves needs (a) and (c) of spec 03, Sect. 2, and need (d) through its
frame at $t = 0$. Spec 03, Sect. 3.4 specified it; build-order step 7 built it.

## How it is treated

Nothing is stored. The reader `Noh` (`fmeval/data/analytic.py`, registered as `noh`) is a
`ClosedFormTrajectory` on the square $[0, 2)^2$ with the axis at its centre, Neumann on both
axes, fields `density`, `velocity` and `pressure`. Options: `gamma`, `density` (the inflow's
$\rho_0$), `speed` ($u_0$), `pressure` (the pressure ahead of the shock), `time_offset`,
`length`, and the generic `candidate`. The closed form, Sutherland (2010), Sect. 6.1.6, Table 9,
was read on ar5iv; Noh (1987) was not opened. The configuration `configs/dataset/noh.yaml`
states nothing beyond the defaults.

## What part is evaluated

Decided by the agent on 2026-11-27 under step 3 of `docs/recipes/add-a-dataset.md`; Kareem may
override it. The frames are deterministic, so each is one known answer, not a sample.

- **Grid: $128^2$.** The ring holds 124 to 484 flagged cells, every angle sampled, and the
  shock metrics' known answers are at cell resolution, so a finer grid adds cost and no answer.
- **Window: 4 frames from $t = 0.5$ to $t = 2$** (Sutherland's end time). At $t = 0.5$ the
  ring is 11 cells in radius, wide enough that the default ladder's 16-cell translation is a
  measurable displacement against a ring 21 cells across; earlier frames would put the whole ring
  inside a blur. The frame at $t = 0$, with no shock, is left to an override, because a frame
  where every shock metric is 0 at every severity has no rank correlation.
- **Measured costs** on a Perlmutter login node (load about 30), results and logs under
  `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/blast_waves/` (`measure.sh`, `per_metric.py`):
  - every deterministic metric that runs on a bounded domain except the two persistence
    metrics (the pointwise errors, `kinetic_energy` and the six shock metrics; the spectral,
    increment, tail and transport metrics need a periodic domain and are not run), default
    ladder of 91 severity levels, all 4 frames: 31 s wall;
  - `persistence_distance`, default ladder, one frame: 5.0 s wall;
  - `persistence_wasserstein`, default ladder, one frame: 5.2 s;
  - every deterministic metric against the time-offset candidate, all 4 frames: 5.4 s wall;
  - one metric on one reference-candidate pair, all three fields: 0.01 to 0.15 s.
  Nothing is stored, so no disk is used. The whole set is cheap except as noted, so it is kept
  whole rather than thinned.

## Decisions and why

1. **A new reader, not an option on an existing one** (agent). The existing readers are Sod's
   (one-dimensional), Taylor–Green, the blobs and the random fields; none is a radial Euler
   solution, and the blobs' tanh fronts are not a flow. The radial geometry it shares with
   `sedov_taylor` is one module function, `polar`.
2. **General $\gamma$, $\rho_0$ and $u_0$** (agent). Sutherland prints only $\gamma = 5/3$,
   $\rho_0 = u_0 = 1$. The general form is derived on the page (Equations 2 and 3) and checked by
   the tests against the jump conditions and the continuity equation, so the detector's own
   $\gamma = 1.4$ is one override away. Reverse by fixing the three options.
3. **The pressure ahead of the shock is the stored constant $10^{-6}$** (agent, following
   Sutherland's Table 10). The exact solution has zero pressure there, and the detector never
   flags a cell beside a non-positive pressure. An isentropic $p_0 (\rho/\rho_0)^\gamma$ was
   rejected: it would be pressure computed from density by an equation of state, which the
   repository's rule forbids in a reader, and it is not the closed form either.
4. **The domain is the full square around the axis** (agent), not Sutherland's quarter with
   reflecting walls, so the ring is closed and no boundary type the vocabulary lacks is needed.
5. **The candidate is a time offset** (agent), the same option as on `sod_shock_tube` and
   `sedov_taylor`: the front moves out by $D\,\delta t$ at every time and nothing else changes.

## Log entries

**2026-11-27, agent (build-order step 7).**

- Code: the reader `Noh` and the function `polar` in `fmeval/data/analytic.py`; the
  configuration `configs/dataset/noh.yaml`; the page `docs/datasets/noh.md` and its row in
  `docs/datasets/README.md`; the dynamics figures, drawn by `python -m fmeval.cards dynamics
  noh`, in `docs/datasets/_generated/`.
- Tests in `tests/test_analytic_datasets.py`: Sutherland's values exactly; the jump balance at
  $\gamma = 5/3$ and $1.4$ (measured 1.4e-9, tolerance 1e-7); continuity ahead of the shock
  (3e-11 of its terms); no shock flagged at $t = 0$; a candidate at $\delta t = 0.3$ through the
  pipeline on $128 \times 96$ and $96 \times 160$: `shock_set_distance` and
  `shock_set_hausdorff` within one cell of $0.1$ at four times, every flagged cell within one
  cell of its circle, every point of either ring between $\Delta r - 2\Delta x$ and
  $\Delta r + \Delta x$ from the other; four refusals.
- Not verified: Noh's own paper.

## Open points

- Registration in `evidence_datasets` (not done, by instruction).
- Spec 03, Sect. 3.8's displaced (not enlarged) circle, ASSD near $(2/\pi)s$, is not pinned;
  the candidate here enlarges the circle.

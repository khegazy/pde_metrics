# Log: Sedov–Taylor blast wave (cylindrical)

This log records why the `sedov_taylor` dataset is in its current form, for the next agent who
changes it. Its public page is `docs/datasets/sedov_taylor.md`. Entries are appended, never
rewritten.

## What the dataset is for

The six shock metrics share one detector, and before this dataset their only shock was Sod's,
one or two cells on a line (`dataset_specs/03_two_dimensional_shocks.md`, Sect. 1). The
Sedov–Taylor front is a circle, oblique to the grid at every angle in one frame, whose radius
grows as $t^{1/2}$ and whose strength falls as $1/t$; the solution at a later time is a
physically consistent radial displacement, and a blast of another energy a pure size error. It
serves needs (a) and (c) of spec 03, Sect. 2. Spec 03, Sect. 3.1 specified it; build-order
step 7 built it.

## How it is treated

Nothing is stored. The reader `SedovTaylor` (`fmeval/data/analytic.py`, registered as
`sedov_taylor`) is a `ClosedFormTrajectory` on $[0, 2)^2$ with the blast at its centre, Neumann
on both axes, fields `density`, `velocity` and `pressure`. Options: `energy`, `density`
($\rho_0$), `pressure` (ambient, ahead of the front), `gamma` in $(1, 2)$, `time_offset`,
`length`, and the generic `candidate`. The defaults are Kamm and Timmes's (2007) standard
cylindrical case. The configuration `configs/dataset/sedov_taylor.yaml` states nothing beyond
the defaults.

**Sources.** The Kamm–Timmes report's PDF was downloaded but could not be rendered (no PDF text
tool on the login node, and the fetch tool returned the compressed stream). Their public Fortran
implementation, `sedov_library_qp.f90` in `https://cococubed.com/codes/sedov/sedov.tbz`, was read
in full; the formulas in the reader are its general expressions specialised to $j = 2$,
$\omega = 0$, and the equation numbers are those its comments give.

## What part is evaluated

Decided by the agent on 2026-11-27 under step 3 of `docs/recipes/add-a-dataset.md`; Kareem may
override it. The frames are deterministic, so each is one known answer, not a sample.

- **Grid: $128^2$.** The ring holds 268 to 540 flagged cells, every angle sampled, and the shock
  metrics' answers are at cell resolution. The interior profile is smooth on this grid: the
  detector flags nothing behind the front.
- **Window: 4 frames from $t = 0.25$ to $t = 1$.** The front grows from 24 to 48 cells, and
  the post-shock pressure falls by a factor of four, so the frames differ in both radius and
  jump. $t = 1$ is Kamm and Timmes's standard time. A front much smaller than 24 cells is within
  reach of the harsher blurs' widths.
- **Measured costs** on a Perlmutter login node (load about 30), results and logs under
  `/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/blast_waves/` (`measure.sh`, `per_metric.py`):
  - every deterministic metric that runs on a bounded domain except the two persistence
    metrics (the pointwise errors, `kinetic_energy` and the six shock metrics; the spectral,
    increment, tail and transport metrics need a periodic domain and are not run), default
    ladder of 91 severity levels, all 4 frames: 21 s wall;
  - `persistence_distance`, default ladder, one frame: 6.4 s wall;
  - `persistence_wasserstein`, default ladder, one frame: did not finish in 600 s (stopped): the input-dependent stall of framework limit 1 in `dataset_specs/BUILD_ORDER.md`, since the same metric scores the reference against its candidate in 0.15 s;
  - every deterministic metric against the time-offset candidate, all 4 frames: 5.7 s wall;
  - one metric on one reference-candidate pair, all three fields: 0.01 to 0.15 s.
  Nothing is stored, so no disk is used. The whole set is cheap except as noted, so it is kept
  whole rather than thinned.

## Decisions and why

1. **The full interior profile is built, not a front with a made-up interior** (agent). The
   parametric solution costs about 75 lines of code with its bisection, validation and energy
   integral, besides docstrings, which is
   little enough under the plan's code rule, and only the full profile is honest to call Sedov.
2. **A new reader, not an option on an existing one** (agent): none of the existing readers is
   a radial Euler solution. The radial geometry it shares with `noh` is one module function,
   `polar`.
3. **$\alpha$ is integrated, not taken from Kamm and Timmes's printed energy** (agent). The
   integral gives 0.9840740 at $\gamma = 1.4$, stable to $10^{-13}$ from 32 to 512 quadrature
   points; the same integral at $j = 3$ reproduces their spherical 0.851072. Their printed
   cylindrical energy 0.311357 and radius 0.75 imply 0.98404, $3.3 \times 10^{-5}$ lower, so the
   front at $t = 1$ is at 0.749994. The default energy is kept as printed so the configuration
   is recognisably theirs. Timmes's driver comments that this energy "should reach r=1 at t=1";
   the integral says 0.75, as the report's Sect. 4.1 (as spec 03 reads it) does.
4. **Bisection in $\log s$** (agent), because near the axis $\lambda \propto s^{(\gamma-1)/(2\gamma)}$
   ($s^{1/7}$ at $\gamma = 1.4$), so a cell at $\lambda = 10^{-3}$ needs $s \approx 10^{-21}$,
   below the resolution of $V$ itself in double precision. Kamm and Timmes used quadruple
   precision for the same reason.
5. **$\gamma$ restricted to $(1, 2)$** (agent). At $\gamma = 2$ the exponents $2/(2 - \gamma)$
   are singular (their removable case $\omega_3$), not coded; above 2 is untested.
6. **The ambient pressure is the stored constant $10^{-6}$** (agent). The similarity solution
   is the zero-pressure limit and the detector needs a positive pressure; the interior is the
   zero-pressure profile. The mismatch is of order $p_0/p_2$, below $10^{-5}$ in the window.
7. **The candidate is a time offset or an energy** (agent), so the front moves by
   $r_2(t + \delta t) - r_2(t)$ or scales by $(E'/E)^{1/4}$ with every jump exact.

## Log entries

**2026-11-27, agent (build-order step 7).**

- Code: the reader `SedovTaylor` and the function `polar` in `fmeval/data/analytic.py`; the
  configuration `configs/dataset/sedov_taylor.yaml`; the page `docs/datasets/sedov_taylor.md`
  and its row in `docs/datasets/README.md`; the dynamics figures, drawn by
  `python -m fmeval.cards dynamics sedov_taylor`, in `docs/datasets/_generated/`.
- Tests in `tests/test_analytic_datasets.py`, at $\gamma = 1.4$ and $5/3$ where they apply: the
  Euler equations (1) behind the front on a radial line of 20000 cells (residual 3e-7 of the
  terms, tolerance 1e-5); mass conservation (3e-8, tolerance 1e-6); the strong-shock flux balance
  at the front with $u_s = dr_2/dt$ (1.1e-8, tolerance 1e-6); $r_2(1) = 0.75$ to 1e-5; the time
  and energy candidates through the pipeline on $128 \times 96$ and $96 \times 160$, as for
  `noh`; six refusals.
- Not verified: the report's own equation numbers (the code's are used).

### 2026-11-27: registered as evidence (registration agent)

- **Registered:** `sedov_taylor` (`{periodic: false, ensemble: false}`, Neumann on both axes)
  in `evidence_datasets` and `evidence_dataset_properties` of `configs/cards/default.yaml`.
  Kareem decided the rule on 2026-11-26 (`dataset_specs/BUILD_ORDER.md`, "The task" and decision
  9: every dataset built in that plan is an evaluation dataset, admitted to `evidence_datasets`
  with a label naming the kind of claim it supports); the agent chose the label.
- **Label** (completes "n frames of ..." in a card's run summary): "an analytic check: the exact
  cylindrical Sedov-Taylor blast wave, a shock oblique to the grid at every angle, and nothing
  about turbulence".
- **Window:** the reader's defaults, kept whole: four frames from t = 0.25 to 1 on 128^2
  (section "What part is evaluated"); nothing needs a command-line setting.
- **Not done:** no metric was run on it for a card; every metric card's *Across the experiments*
  table shows it as *not yet run* or *not applicable* with the reason (`python -m fmeval.cards
  catalog`). Producing that evidence is its own step in `BUILD_ORDER.md` and needs compute.

## Open points

- Schaal and Springel's check of the flagged cell count against $2\pi r_2/\Delta x$ (spec 03,
  Sect. 3.1) is not pinned.

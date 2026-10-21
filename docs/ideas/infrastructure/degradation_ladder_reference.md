# Reference and solver predictor for the degradation ladder

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The degradation ladder itself is built: a trusted field is damaged in controlled steps, and
each metric's response to the damage is recorded, as described on the
[protocol page](../../protocol.md). Two pieces of the protocol as first specified are not
yet in place, and this idea is those two pieces.

1. **A reference simulation at Reynolds number $\mathrm{Re} \approx 500$.**
   - The reference is a *direct numerical simulation*, one that resolves every scale of the
     flow without a turbulence model, of isotropic and doubly periodic shear flow.
   - The reference data available today are at much higher Reynolds number. An open item in
     the repository records the mismatch and the choice it leaves: generate a reference at
     $\mathrm{Re} \approx 500$, or amend the protocol to the Reynolds numbers available and
     record why. At $\mathrm{Re} \approx 500$ the flow is barely turbulent, so several of the
     failure modes the metrics target may not be present.
2. **A trusted solver as the predictor, degraded in controlled steps.**
   - The planned solver is a Boltzmann solver, degraded through grid coarsening.
   - Ideally it is also degraded along a second, independent axis, such as added noise or
     artificial viscosity. This separates metrics that respond to resolution specifically
     from metrics that respond to any kind of error.
   - The degradations built today damage a stored reference field after the fact. A degraded
     solver would instead produce predictions whose errors arise from the solver itself.

The same solver would also make
[consistency with one step of a trusted solver](../physics_invariants/solver_consistency.md)
available at no extra cost. Run at three resolutions, it would also quantify the reference's
own discretisation uncertainty through [grid convergence](grid_convergence.md).

## Rationale

*The team's judgement.* High priority: the reference and the degraded solver are what the
protocol was specified against, and the same solver also enables
[solver consistency](../physics_invariants/solver_consistency.md), one of the high-priority
metrics that needs no reference field.

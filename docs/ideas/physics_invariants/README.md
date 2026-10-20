# Vorticity and physics invariants

These ideas test a prediction against the physics it is supposed to obey rather than only
against a reference field. Shocks set the hardest constraints. Derivatives do not exist at a
discontinuity, so the governing equations must be checked in a form that stays valid there;
physical shocks must produce entropy, and a prediction that smears them produces too little;
and near a shock the velocity gradient is dominated by compression, which contaminates any
diagnostic built on rotation. Several of these ideas need no reference at all, so they stay
meaningful after a prediction has decorrelated from every reference trajectory.

Built already, and so not listed here: enstrophy ([enstrophy](../../metrics/enstrophy.md))
and palinstrophy ([palinstrophy](../../metrics/palinstrophy.md)).

## Ideas in this theme

- [Signed entropy production](entropy_production.md): three separate scores for negative,
  mismatched and excess entropy production, so that over-smoothing is visible.
- [Residual of the equations in weak form](weak_residual.md): the finite-volume balance of
  each cell, which stays valid at shocks where the differential form does not.
- [Consistency with one step of a trusted solver](solver_consistency.md): how far the model's
  next state lies from where a trusted solver would take the same field in one step.
- [Helmholtz split into rotational and compressive parts](helmholtz_split.md): separate the
  velocity into a rotational and a compressive part, so that rotation diagnostics are not
  contaminated by shocks.
- [Admissibility checks](admissibility_checks.md): positivity, finite values, conservation
  drift, divergence, realizability and species bounds, each necessary for a physical
  prediction and none sufficient.
- [Galilean and rotational equivariance](equivariance_tests.md): whether the model's output
  transforms correctly when its input is boosted to a moving frame or rotated.
- [Goal-oriented error estimates](goal_oriented_error.md): an adjoint-weighted residual that
  estimates, and locates, the error in one output quantity without a reference field.

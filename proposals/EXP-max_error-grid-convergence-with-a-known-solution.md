---
type: "EXP"
kind: "protocol"
related: ["max_error", "rmse", "mse", "mae", "nrmse", "h1_seminorm", "docs/ideas/infrastructure/grid_convergence.md", "issues/010"]
seen_in: "Roy 2005, J. Comput. Phys. 205(1), 131-156, Sect. 2.5, Eqs. 5-8, Figs. 3-4"
doi: "10.1016/j.jcp.2004.10.036"
found_by: "update_metric_eval_principles, 2026-11-03"
---

# EXP: An order-of-accuracy test against a known solution on systematically refined grids

## What the experiment is

The code-verification test of numerical analysis, where the pointwise error norms come from.
A problem with a known exact solution is solved on a sequence of grids refined by a constant
ratio r, the discretisation error f_k - f_exact is measured on each grid in a norm, and the
observed order of accuracy is read from successive grids (Roy 2005):

1. **Error norms.** Roy's Eq. (7) defines the discrete L-infinity norm,
   max_n |f_{k,n} - f_exact,n|, and the discrete L2 norm, (sum_n |f_{k,n} - f_exact,n|^2 / N)^{1/2},
   on grid k; these are `max_error` and `rmse` of this repository.
2. **Observed order.** p = ln(L_{k+1} / L_k) / ln r (Eq. 8, p. 140), to be compared with the
   formal order of the scheme. The worked example applies it to the L-infinity and L2 norms on
   five grids with r = 2 (Figs. 3-4).
3. **Known solution.** Where no exact solution exists, the method of manufactured solutions
   supplies one: choose a smooth solution, add the source term the equations then need, and run
   the code with that source (Roy 2005, Sect. 2.5, the six steps on p. 137; Roache 2002).

Two forms suit this repository. First, the kinet solver run on a manufactured periodic
solution at 64^2, 128^2, 256^2 and 512^2. Second, the Sod shock tube, whose exact solution the
repository already computes (`fmeval/data/analytic.py`), solved by a shock-capturing solver at a sequence
of resolutions (`EXP-shock_set_distance-2d-shock-dataset.md` says kinet runs the Sod
configurations; not checked here); Roy notes that the analysis of non-smooth solutions, shocks included, is "an
open research issue" for this method (p. 141), so on Sod the observed order is measured, not
checked against a formal value.

## What it tests

It changes one thing in a controlled and known way, the grid spacing, and the expected
response is a power law with a known exponent. A pointwise norm must fall as h^p with the
scheme's order; a seminorm of the gradient such as `h1_seminorm` must fall one order more
slowly than the L2 norm on a smooth solution (the agent's reasoning from differentiating the
leading error term, not checked against a source). A metric whose observed order does not
settle, or settles at the wrong value, is measuring something other than discretisation error.

## Metrics it would test

`max_error` and `rmse` (the two norms of Roy's Eq. 7), `mse`, `mae`, `nrmse` (its normalisation
does not change the observed order), `h1_seminorm`. On the Sod form, the shock metrics as well:
`shock_set_distance` should fall with the shock's smeared width.

## Why it is helpful

No experiment here refines a grid against a known answer. The coarsening degradations
(`coarsen`, `coarsen_bandlimited`) remove resolution from a fixed reference, which is a model of
a coarse surrogate, not a coarser solve; the three resolutions of the forecast runs (issue 010)
come from one trajectory with no exact solution and are at most a partial resolution
sequence, whose asymptotic range would have to be checked first. A numerical analyst who opens
`max_error` or `rmse` expects to see the order-of-accuracy plot, error against grid spacing on
log-log axes with the formal slope drawn in, and today the card cannot draw it. The same
sequence also gives the reference's own discretisation error, which the grid-convergence idea
page asks for.

## Cost and requirements

A solver run per grid level, dominated by the finest, a manufactured source term added to the solver (not checked whether kinet supports a source
term), and a reader that pairs each level with the exact solution sampled on its grid. The
exact-solution comparison must be done on each grid's own cells, not after remapping to the
analysis grid, or the remap error enters the measured order.

## References

- Roy, C. J. (2005). Review of code and solution verification procedures for computational
  simulation. *Journal of Computational Physics* 205(1), 131-156.
  <https://doi.org/10.1016/j.jcp.2004.10.036> (read in full: Sect. 2.3 p. 134, Sect. 2.5
  pp. 136-141, Eqs. 5-8, Figs. 3-4).
- Roache, P. J. (2002). Code verification by the method of manufactured solutions. *Journal
  of Fluids Engineering* 124(1), 4-10. <https://doi.org/10.1115/1.1436090> (abstract only).

# Grid convergence of the reference

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The reference is itself a numerical solution, and carries a discretisation error. This idea
quantifies that error with the standard procedure of verification in computational fluid
dynamics, so that a surrogate's distance from the reference can be read against the
reference's own uncertainty.

1. **Three systematically refined grids.** Compute a scalar quantity of interest $\phi$ on a
   fine, a medium and a coarse grid, $\phi_1$, $\phi_2$ and $\phi_3$, with a constant
   refinement ratio $r = h_{\text{coarse}} / h_{\text{fine}} > 1$ between successive grid
   spacings $h$.
2. **Observed order of accuracy.** If the error behaves as $C h^p$, the order $p$ observed on
   these grids is

   $$
   p = \frac{\ln\left[ (\phi_3 - \phi_2) / (\phi_2 - \phi_1) \right]}{\ln r}. \tag{1}
   $$

   It should be close to the formal order of the scheme. A non-constant ratio needs the
   iterative version of this formula (Celik et al. 2008).
3. **Richardson extrapolation.** The estimate of the value at zero grid spacing is

   $$
   \phi_{\text{ext}} = \frac{r^p \phi_1 - \phi_2}{r^p - 1}. \tag{2}
   $$

4. **Grid Convergence Index.** Roache's index turns the difference between the two finest
   grids into an error band on the fine-grid value,

   $$
   \mathrm{GCI}_{\text{fine}} = \frac{F_s}{r^p - 1} \left| \frac{\phi_1 - \phi_2}{\phi_1}
   \right|, \tag{3}
   $$

   with a safety factor $F_s = 1.25$ when three or more grids are used and $F_s = 3$ when only
   two are (Roache 1997; Celik et al. 2008). It is the verification counterpart of the
   resampling intervals of [uncertainty on every metric value](metric_uncertainty.md): one
   bounds the discretisation error of the reference, the other its sampling error.

## Precedent

The procedure is standard practice for reporting discretisation uncertainty in computational
fluid dynamics, set out as a recommended procedure by Celik et al. (2008) and placed within
verification and validation more broadly by Oberkampf and Trucano (2002).

## Pitfalls

- The formulas assume all three grids lie in the *asymptotic range*, where the leading error
  term dominates. Outside it the observed order is meaningless.
- If $\phi_3 - \phi_2$ and $\phi_2 - \phi_1$ have opposite signs, convergence is
  oscillatory and Equation (1) takes the logarithm of a negative number.
- Near shocks the observed order of pointwise fields degrades and Richardson extrapolation
  of those fields is unsafe. The quantities $\phi$ should be ones that remain well defined
  there, such as shock position, integrated forces and budgets.
- For a chaotic flow, instantaneous fields on different grids decorrelate, so $\phi$ must be
  a statistic, such as a dissipation rate or a spectrum value, rather than a field value.
- For a surrogate that can be evaluated at any resolution, such as a Fourier neural
  operator, refining the evaluation grid does not refine a discretisation of the equations.
  The field guide notes that this changes the meaning of grid convergence for such models.
- Running the reference solver at three resolutions costs several times one reference run.

## Rationale

*From the field guide; the team has not yet set a priority.* The guide places grid
convergence under verification and validation as the way to quantify the discretisation
uncertainty of a reference. Without it, a surrogate that differs from the reference by less
than the reference's own discretisation error cannot be distinguished from one that matches
it.

## Keywords

grid convergence index, Richardson extrapolation, observed order of accuracy, verification
and validation, discretisation uncertainty, asymptotic range.

## References

- Celik, I. B., Ghia, U., Roache, P. J., Freitas, C. J., Coleman, H. & Raad, P. E. (2008).
  Procedure for estimation and reporting of uncertainty due to discretization in CFD
  applications. *Journal of Fluids Engineering* 130, 078001.
  <https://doi.org/10.1115/1.2960953>
- Oberkampf, W. L. & Trucano, T. G. (2002). Verification and validation in computational
  fluid dynamics. *Progress in Aerospace Sciences* 38, 209–272.
  <https://doi.org/10.1016/S0376-0421(02)00005-2>
- Roache, P. J. (1997). Quantification of uncertainty in computational fluid dynamics.
  *Annual Review of Fluid Mechanics* 29, 123–160.
  <https://doi.org/10.1146/annurev.fluid.29.1.123>

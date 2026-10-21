# Signed entropy production

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

!!! warning "Unresolved: settle this before implementing"
    The two sources this page draws on disagree about what an over-smeared shock does. The
    team's tracker says it produces too *little* entropy; the field guide says it shows
    *excessive* dissipation. Both statements appear below, and they cannot both describe the
    same error. Whoever implements this metric must look at this carefully and determine which
    is correct, from the entropy-stability references below and a direct check on a smeared
    shock, before the excess-dissipation score and the sign convention of the signed mismatch
    are fixed. Then correct this page, or state the answer in the metric's card.

## What it is

Entropy production is the rate at which entropy is generated locally in the flow. In a
shocked flow, physical shocks *must* produce entropy; spurious numerical oscillations
produce negative entropy production, destroying physical entropy; and over-smeared learned
shocks produce too *little*.

Mathematically, the condition is stated with an entropy pair $(\eta, q)$: a convex function
$\eta(U)$ of the conserved variables and a matching entropy flux $q(U)$. Admissible solutions
satisfy $\partial_t \eta + \nabla\cdot q \le 0$ in the weak sense. This mathematical entropy
$\eta$ decreases where physical entropy is produced; for the Euler equations it is a negative
multiple of $\rho s$, with $s$ the specific physical entropy. The discrete production on cell
$K$ is computed with a *declared* numerical entropy flux $\hat q_f$ leaving the cell through
each face $f$. Written in the same form as the
[residual of the equations in weak form](weak_residual.md), it reads as follows (*added during
conversion, not from the field guide or the team:* neither source gives this formula)

$$
P_{\eta,K} = \frac{|K|}{\Delta t}\big(\eta^{n+1}_K - \eta^n_K\big) + \sum_f |f|\,\hat q_f
\tag{1}
$$

and admissibility requires $P_{\eta,K} \le 0$. Because $\eta$ decreases where physical
entropy is produced, $P_{\eta,K} > 0$ is a cell that destroys physical entropy. Three cases
must be told apart: that nonphysical destruction ($P_{\eta,K} > 0$), admissible production at
shocks, and excessive dissipation, which an over-smeared shock can produce while passing a
one-sided check. Three separate numbers should therefore be reported:

1. **An entropy-violation score** $E^{+}_\eta$, capturing unphysical negative production of
   physical entropy: it collects the cells where $P_{\eta,K} > 0$, where the mathematical
   entropy $\eta$ grows.
2. **A signed mismatch** $E^{\text{signed}}_\eta$ against the entropy production of the
   reference, keeping the sign so that too much and too little production are distinguished.
3. **An excess-dissipation score.**

Alongside them, the shock-normal production profile $P_\eta(d)$ averages the production in
bins of signed distance $d$ from the surface found by the
[shock detector](../shock_geometry/shock_detector.md), the shock-aligned coordinate also used
for [shock–turbulence interaction statistics](../shock_geometry/shock_turbulence_interaction.md).
The profile shows whether production sits at the shock or is spread around it. Together these
pinpoint errors in a shock's location, speed and strength, and distinguish genuine dissipation
from spurious or over-smoothed dissipation.

## Precedent

The theoretical machinery for comparing a numerical scheme's entropy production against an
entropy-conservative reference flux, a numerical flux constructed to produce no entropy so
that a scheme's dissipation can be measured against it, is Tadmor's (Tadmor 1987, 2003).
Entropy production specifically at shocks is treated by Ismail and Roe (Ismail and Roe 2009).
Finite-volume schemes for the compressible Euler and Navier–Stokes equations that are entropy
stable and preserve kinetic energy supply another explicit numerical entropy flux that could
be declared for (1) (Chandrashekar 2013).

On the training side, weak physics-informed neural networks (wPINNs) approximate entropy
solutions of hyperbolic conservation laws by imposing the equations and the entropy condition
in weak form, against test functions, rather than pointwise (De Ryck et al. 2024).

## Pitfalls

- A one-sided check, which looks only at the sign of the production, detects only the first
  of the three errors. It is blind to an over-dissipated, smeared field.
- The scores depend on the declared entropy pair and numerical entropy flux, and the
  shock-conditioned parts depend on the shock detector and its threshold. All of these are
  fixed once by the evaluator.
- The strong-form residual of the entropy inequality is invalid at shocks, for the reason
  given under the [residual of the equations in weak form](weak_residual.md).

## Rationale

*The team's judgement.* High priority: the diagnostic is reference-free, it is the
physically correct admissibility condition for shocked flow (the condition used to rule out
non-physical solutions of the equations in weak form, such as expansion shocks), and the
three-way split directly detects the over-smoothing failure most expected from a
machine-learned surrogate.

## References

- Chandrashekar, P. (2013). Kinetic energy preserving and entropy stable finite volume schemes
  for compressible Euler and Navier–Stokes equations. *Communications in Computational
  Physics* 14, 1252–1286. <https://doi.org/10.4208/cicp.170712.010313a>
- De Ryck, T., Mishra, S. & Molinaro, R. (2024). wPINNs: weak physics-informed neural networks
  for approximating entropy solutions of hyperbolic conservation laws. *SIAM Journal on
  Numerical Analysis* 62, 811–841. <https://doi.org/10.1137/22M1522504>
- Ismail, F. & Roe, P. L. (2009). Affordable, entropy-consistent Euler flux functions II:
  Entropy production at shocks. *Journal of Computational Physics* 228(15), 5410–5436.
  <https://doi.org/10.1016/j.jcp.2009.04.021>
- Tadmor, E. (1987). The numerical viscosity of entropy stable schemes for systems of
  conservation laws. I. *Mathematics of Computation* 49(179), 91–103.
  <https://doi.org/10.1090/S0025-5718-1987-0890255-3>
- Tadmor, E. (2003). Entropy stability theory for difference approximations of nonlinear
  conservation laws and related time-dependent problems. *Acta Numerica* 12, 451–512.
  <https://doi.org/10.1017/S0962492902000156>

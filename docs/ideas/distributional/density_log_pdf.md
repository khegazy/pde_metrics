# Width of the log-density distribution

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Write the density as its logarithm relative to the mean, $s = \ln(\rho / \langle \rho
\rangle)$, and take the probability distribution of $s$ over the domain. In supersonic
turbulence the width of that distribution is tied to the root-mean-square sonic Mach number
$M_s$, the typical flow speed divided by the sound speed:

$$
\sigma_s^2 = \ln\left(1 + b^2 M_s^2\right), \tag{1}
$$

where $\sigma_s^2$ is the variance of $s$ and $b$ is a *driving parameter* set by how the
turbulence is stirred: $b \approx 1/3$ when the stirring is purely solenoidal (rotational,
divergence-free) and $b \approx 1$ when it is purely compressive (Federrath et al. 2010;
Price, Federrath & Brunt 2011).

Equation (1) gives two uses.

1. **A physical target for the width.** Given $M_s$ measured from the predicted velocity, the
   relation predicts $\sigma_s^2$ without any reference field. A surrogate that damps density
   fluctuations toward the mean narrows the distribution below the target.
2. **An inferred driving mixture.** Given both $\sigma_s^2$ and $M_s$, solving Equation (1)
   for $b$ says how compressive the forcing behaves. Comparing the $b$ inferred from a
   prediction with the $b$ inferred from the reference tests whether the surrogate has the
   right balance of compressive and rotational motion, which connects to the
   [Helmholtz split into rotational and compressive parts](../physics_invariants/helmholtz_split.md).

The diagnostic comes from astrophysics, where no phase-aligned ground truth ever exists, and
is therefore meaningful after a prediction has decorrelated from the reference trajectory.

## Pitfalls

- The width is degenerate with the magnetic field and the driving mode: different
  combinations of $M_s$, $b$ and magnetic field strength give the same $\sigma_s^2$, so a
  matched width does not identify matched physics.
- The relation was established for supersonic, isothermal turbulence (Price, Federrath &
  Brunt 2011). Whether it holds for a flow with another equation of state, or at low Mach
  number, must be checked before it is used as a target there.
- Like any one-point distribution, it is blind to where in the domain the dense and rarefied
  regions sit.

## Rationale

*From the field guide; the team has not yet set a priority.* Equation (1) turns the
log-density distribution from something that can only be compared against a reference into
something with a physical target of its own, and the field guide includes the
log-density width in its minimal panel for compressible isotropic turbulence. It costs one
pass over the density and velocity fields.

## Keywords

density variance–Mach number relation, log-normal density PDF, solenoidal versus compressive
forcing, driving parameter $b$, supersonic isothermal turbulence.

## References

- Federrath, C., Roman-Duval, J., Klessen, R. S., Schmidt, W. & Mac Low, M.-M. (2010).
  Comparing the statistics of interstellar turbulence in simulations and observations:
  solenoidal versus compressive turbulence forcing. *Astronomy & Astrophysics* 512, A81.
  <https://doi.org/10.1051/0004-6361/200912437>
- Price, D. J., Federrath, C. & Brunt, C. M. (2011). The density variance–Mach number
  relation in supersonic, isothermal turbulence. *The Astrophysical Journal Letters* 727,
  L21. <https://doi.org/10.1088/2041-8205/727/1/L21>

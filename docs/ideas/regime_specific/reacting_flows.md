# Reacting-flow and scalar-mixing diagnostics

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

In a reacting flow the questions that matter concern the flame: where reaction happens, in
which mode, and how fast reactants are mixed down to the molecular scale where they can react.
The standard diagnostics are built on a few scalar fields.

- **Mixture fraction and conditional statistics.** The mixture fraction $Z$ is a conserved
  scalar that is 0 in the oxidiser stream and 1 in the fuel stream, so it records how much of
  the local fluid came from each. Conditional means $\langle q \mid Z = \zeta\rangle$ of a
  quantity $q$, such as temperature or a species mass fraction, and conditional probability
  distributions at fixed $Z$, organise the description of nonpremixed combustion, in which
  fuel and oxidiser enter separately and burn where they meet (Peters 2000).
- **Scalar dissipation rate.** $\chi = 2D\,|\nabla Z|^2$, with $D$ the molecular diffusivity,
  measures how fast the mixture fraction is being mixed at small scales. It controls
  micromixing and, where it is large, local extinction of the flame. Its distribution is
  heavy-tailed, so a prediction is compared with a reference through a distance between
  distributions, such as the one-dimensional 1-Wasserstein distance that
  [increment_w1](../../metrics/increment_w1.md) computes, rather than through its mean.
- **Flame surface density and turbulent flame speed.** With $c$ a progress variable that runs
  from 0 in unburnt to 1 in burnt gas, the flame surface density
  $\Sigma = \langle|\nabla c|\rangle$ measures the flame area per unit volume. Together with the turbulent flame speed, the speed
  at which the flame advances into the unburnt mixture, it describes premixed combustion.
- **Flame index.** The Takeno flame index is the sign of
  $\nabla Y_{\text{fuel}}\cdot\nabla Y_{\text{ox}}$, where $Y_{\text{fuel}}$ and
  $Y_{\text{ox}}$ are the fuel and oxidiser mass fractions. It is positive where the gradients
  are aligned, as in a premixed flame, and negative where they oppose, as in a nonpremixed
  flame (Yamashita et al. 1996). The fraction of the reaction zone burning in each mode is a
  compact comparison between prediction and reference.
- **Regime placement.** The Damköhler number, the ratio of a flow time scale to a chemical time
  scale, and the Karlovitz number, the ratio of a chemical time scale to the time scale of the
  smallest eddies, place a flame in a combustion regime. A prediction and its reference should
  sit in the same regime.
- **Thermochemical bounds.** Each species mass fraction must satisfy $0 \le Y_k \le 1$, the
  mass fractions must sum to one, $\sum_k Y_k = 1$, and the temperature must be positive.
  These belong with the other
  [admissibility checks](../physics_invariants/admissibility_checks.md).

## Pitfalls

- A model can match the mean temperature while badly missing the area of the reaction surface,
  so mean thermochemical quantities alone are blind to the flame geometry.
- The flame index needs both the fuel and the oxidiser mass fractions, so it applies only to
  predictions that resolve individual species.
- The scalar dissipation rate and the flame surface density are built on gradients, and so are
  sensitive to resolution and to the differentiation stencil.

## Rationale

*From the field guide; the team has not yet set a priority.* These diagnostics identify the
mode of combustion and test whether micromixing is reproduced, which no general field metric
does.

## Keywords

mixture fraction, conditional moment, scalar dissipation rate, flame surface density, progress
variable, turbulent flame speed, Takeno flame index, Damköhler number, Karlovitz number,
premixed and nonpremixed combustion.

## References

- Peters, N. (2000). *Turbulent Combustion*. Cambridge University Press.
  <https://doi.org/10.1017/CBO9780511612701>
- Yamashita, H., Shimada, M. & Takeno, T. (1996). A numerical study on flame stability at the
  transition point of jet diffusion flames. *Symposium (International) on Combustion* 26,
  27–34. <https://doi.org/10.1016/S0082-0784(96)80196-2>

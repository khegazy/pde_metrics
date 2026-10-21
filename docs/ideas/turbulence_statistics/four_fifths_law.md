# Four-fifths law and the third-order structure function

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Let $\delta_\ell u_\parallel = [\mathbf{u}(\mathbf{x} + \boldsymbol{\ell}) -
\mathbf{u}(\mathbf{x})] \cdot \boldsymbol{\ell} / \ell$ be the longitudinal velocity increment,
the change in velocity along a separation vector $\boldsymbol{\ell}$ of length $\ell$,
projected onto that vector. Its third moment is the third-order structure function
$S_3(\ell) = \langle (\delta_\ell u_\parallel)^3 \rangle$, where $\langle \cdot \rangle$
averages over positions and directions. For homogeneous, isotropic turbulence in the limit of
infinite Reynolds number, Kolmogorov's four-fifths law states

$$
S_3(\ell) = -\frac{4}{5}\, \varepsilon\, \ell \tag{1}
$$

for separations in the inertial range, meaning much smaller than the energy-containing scale
and much larger than the scale at which viscosity acts (Frisch 1995, Eq. (6.5)). Here
$\varepsilon$ is the mean rate of energy dissipation per unit mass. The law has no adjustable
constant, and it is one of the very few exact results of inertial-range theory (Frisch 1995,
Chapter 6). Its negative sign records that energy flows on average from large scales to small
ones.

**Why a Gaussian field fails it.** An increment of a zero-mean Gaussian field is a linear
combination of Gaussian variables, so it is itself zero-mean and Gaussian. By the
Wick–Isserlis theorem every odd moment of such a variable is zero:

$$
\bigl\langle (\delta_\ell u)^{2p+1} \bigr\rangle = 0, \qquad p = 0, 1, 2, \ldots \tag{2}
$$

(Chevillard et al. 2012 discuss this property in the context of turbulence modelling). The
expected $S_3(\ell)$ of a Gaussian field is therefore zero at every separation, whatever its
energy spectrum, and Equation (1) cannot hold. A model that drifts toward a Gaussian-like
state shows $S_3 \to 0$ even when its spectrum is right.

The idea has three forms.

1. **Against a reference.** Compute $S_3(\ell)$ on the prediction and form the compensated
   ratio $-S_3(\ell) / (\tfrac{4}{5} \varepsilon \ell)$ with $\varepsilon$ taken from the
   reference. Over a declared inertial band the ratio should sit on a plateau at one; the
   score is the plateau's deviation from one.
2. **Without a reference.** Estimate the dissipation from the prediction itself,

    $$
    \hat\varepsilon = 2\nu \bigl\langle \hat S_{ij} \hat S_{ij} \bigr\rangle, \qquad
    \hat S_{ij} = \tfrac{1}{2} \bigl( \partial_i \hat u_j + \partial_j \hat u_i \bigr), \tag{3}
    $$

    where $\hat{\mathbf{u}}$ is the predicted velocity, $\hat S_{ij}$ its strain-rate tensor
    and $\nu$ the kinematic viscosity, which is a parameter of the equations rather than of
    the prediction. Then score the largest deviation of the compensated ratio from one over
    the declared inertial band $\mathcal{I}$:

    $$
    E_{4/5} = \max_{\ell \in \mathcal{I}}
    \left| \frac{-\hat S_3(\ell)}{\tfrac{4}{5} \hat\varepsilon \ell} - 1 \right| . \tag{4}
    $$

    This needs no ground truth, so it applies after the prediction has decorrelated from the
    reference trajectory and where no reference exists.
3. **The scale-by-scale budget.** Equation (1) is the inertial-range limit of the
   Kármán–Howarth–Monin relation, an exact energy budget for each separation $\ell$ that
   balances the third-order term against viscous and forcing terms (Frisch 1995, Chapter 6).
   Checking that budget on the prediction is a stronger, scale-resolved version of
   Equation (4): it shows at which separations the balance breaks, rather than only whether
   a plateau exists.

A related exact property is the *dissipation anomaly*: as the viscosity tends to zero with
the large-scale forcing fixed, $\varepsilon$ tends to a finite, nonzero constant rather than
to zero (Sreenivasan 1998). Duchon and Robert (2000) give the corresponding description of
energy dissipation for weak, non-smooth solutions of the Euler and Navier–Stokes equations.
It is what makes the right-hand side of Equation (1) independent of how small $\nu$ is.

## Precedent

The four-fifths law is the standard calibration of the inertial range in turbulence theory
(Frisch 1995). In machine learning, a multiscale generative adversarial network for turbulent
fields builds the skewness of velocity increments across scales into its training and
evaluation, as the criterion that retrieves the energy cascade (Granero Belinchon and Cabeza
Gallucci 2024).

## Pitfalls

- It needs a genuine inertial range, roughly a decade or more of separations, and tight
  confidence intervals on $S_3$. Without one the score should be reported as not applicable
  rather than forced. See
  [uncertainty on every metric value](../infrastructure/metric_uncertainty.md).
- The third moment converges slowly, so small samples give noisy values.
- $\hat\varepsilon$ in Equation (3) is biased low when the grid does not resolve the
  dissipation range, since unresolved gradients are missing from it. The resolution should be
  reported beside the score; the scales that measure it are on
  [one-point statistics and characteristic scales](one_point_statistics.md).
- The simple longitudinal form assumes near-isotropy.
- Equation (1) is derived from the incompressible Navier–Stokes equations in three
  dimensions. In two dimensions energy cascades toward large scales instead
  (Kraichnan 1967), so Equation (1) does not apply; see
  [helicity, potential vorticity and information transfer across scales](inviscid_invariants.md).
- Equation (4) is reference-free, and a reference-free score can only be trusted once it has
  been shown to track the true error. The procedure is to measure its Spearman rank
  correlation with the true error on cases where a reference exists, before relying on it
  where none does.

## Rationale

*From the field guide; the team has not yet set a priority.* The four-fifths law is one of
the very few parameter-free exact laws of the inertial range, and it fixes both the amplitude
and the slope of $S_3$. A Gaussian field with the correct spectrum fails it, and so does a constant,
laminar or over-dissipated field. Those degenerate fields can pass every
[admissibility check](../physics_invariants/admissibility_checks.md), which tests only for
non-physical states, so the law constrains exactly what the admissibility checks leave open.
Its reference-free form is one of the few scores that remain meaningful after a rollout has
decorrelated from the reference.

## Keywords

four-fifths law, third-order structure function, Kármán–Howarth–Monin equation, compensated
structure function, dissipation anomaly, energy cascade, Wick–Isserlis theorem.

## References

- Chevillard, L., Castaing, B., Arneodo, A., Lévêque, E., Pinton, J.-F. & Roux, S. G. (2012).
  A phenomenological theory of Eulerian and Lagrangian velocity fluctuations in turbulent flows. *Comptes Rendus
  Physique* 13(9–10), 899–928. <https://arxiv.org/abs/1112.1036>
- Duchon, J. & Robert, R. (2000). Inertial energy dissipation for weak solutions of
  incompressible Euler and Navier–Stokes equations. *Nonlinearity* 13, 249–255.
  <https://doi.org/10.1088/0951-7715/13/1/312>
- Frisch, U. (1995). Turbulence: The Legacy of A. N. Kolmogorov. *Cambridge University
  Press*. <https://doi.org/10.1017/CBO9781139170666>
- Granero Belinchon, C. & Cabeza Gallucci, M. (2024). A multiscale and multicriteria
  generative adversarial network to synthesize 1-dimensional turbulent fields. *Machine
  Learning: Science and Technology* 5(2), 025032. <https://doi.org/10.1088/2632-2153/ad43b3>
- Kraichnan, R. H. (1967). Inertial ranges in two-dimensional turbulence. *Physics of
  Fluids* 10, 1417–1423. <https://doi.org/10.1063/1.1762301>
- Sreenivasan, K. R. (1998). An update on the energy dissipation rate in isotropic
  turbulence. *Physics of Fluids* 10, 528–529. <https://doi.org/10.1063/1.869575>

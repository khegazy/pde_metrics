# Shock detector

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

A shock detector, or shock sensor, is a local test that flags each cell of a field as shocked
or not. The standard forms are:

- the normalised pressure gradient $S_p = |\nabla p| / (p + \epsilon)$, where $p$ is the
  pressure and $\epsilon$ is a small constant that guards against division by zero;
- a compression-gated variant,
  $S_{\text{comp}} = \max(0, -\nabla\cdot\mathbf{u}) \, |\nabla p| / (p + \epsilon)$, where
  $\mathbf{u}$ is the velocity and its divergence $\nabla\cdot\mathbf{u}$ is negative where
  the flow is being compressed. The gate switches the sensor off wherever the flow is not
  compressing, which suppresses shear layers (thin regions across which the velocity changes
  sharply) and contact discontinuities (jumps in density that move with the flow and carry no
  pressure jump);
- sensors built on the gradient of the Mach number, the ratio of flow speed to sound speed.

Edge detectors from image processing, such as the Canny and Sobel operators, are cheap ways to
localise shocks as well. They are treated as an implementation shortcut for this detector
rather than as a separate idea.

Two properties of each detected shock are direct quality measures in their own right:

- the **shock thickness** $w_{10\text{-}90}$, the distance along the shock normal over which
  the jump rises from 10% to 90% of its full size, expressed in grid cells, so that a smeared
  shock is visible as a number;
- an **overshoot and undershoot score**, measuring how far the profile across the shock
  overshoots the state on one side or undershoots the state on the other, the signature of the
  oscillations that a sharp jump excites in a numerical scheme.

A detector alone does not compare two fields. The observation that a derivative detector
"needs shock position alignment" is correct: detection is the first step, and the second is
the [distance between extracted shock sets](shock_set_distance.md), which compares the
detected sets without requiring them to line up cell by cell.

## Precedent

The canonical reference is Ducros and colleagues, whose stated objective was "to derive a
shock capturing tool able to treat turbulence with minimum dissipation out of the shock" for
large-eddy simulation, in which the large turbulent eddies are resolved on the grid and the
effect of the small ones is modelled (Ducros et al. 1999). That is the same design
requirement here: detect the shock without contaminating the surrounding turbulence.
Hendrickson, Kartha and Candler show that a Ducros-type sensor, which gates on the ratio of
dilatation to dilatation plus vorticity, misclassifies regions of the flow when used alone,
and propose an improved form (Hendrickson et al. 2018). The design consequence is to tie the
sensor to compression, as $S_{\text{comp}}$ does, and to the jump physics checked under
[shock front position, speed and jump conditions](shock_front_error.md).

## Pitfalls

- Every sensor carries a threshold. Fix the threshold once in the evaluator and never tune it
  per model, or the metric becomes gameable.

## Rationale

*The team's judgement.* High priority: the detector is the first half of measuring the
distance between shocks, a gap that the
[distance between extracted shock sets](shock_set_distance.md) then closes using metrics
imported from medical imaging. Its design goal is already stated in the shock-capturing
literature, and it is cheap to compute.

## Keywords

shock sensor, Ducros sensor, compression switch, shock-capturing detector,
dilatation–vorticity ratio.

## References

- Ducros, F., Ferrand, V., Nicoud, F., Weber, C., Darracq, D., Gacherieu, C. & Poinsot, T.
  (1999). Large-eddy simulation of the shock/turbulence interaction. *Journal of
  Computational Physics* 152(2), 517–549. <https://doi.org/10.1006/jcph.1999.6238>
- Hendrickson, T. R., Kartha, A. & Candler, G. V. (2018). An improved Ducros sensor for the
  simulation of compressible flows with shocks. *2018 Fluid Dynamics Conference*, AIAA
  2018-3710. <https://doi.org/10.2514/6.2018-3710>

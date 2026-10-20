# Shock detector

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

A shock detector, or shock sensor, is a local test that flags each cell of a field as shocked
or not. The standard forms are:

- the normalised pressure gradient $|\nabla p| / p$, where $p$ is the pressure;
- a compression-gated variant, $\max(0, -\nabla\cdot\mathbf{u}) \, |\nabla p| / p$, where
  $\mathbf{u}$ is the velocity and its divergence $\nabla\cdot\mathbf{u}$ is negative where
  the flow is being compressed. The gate switches the sensor off wherever the flow is not
  compressing, which suppresses shear layers (thin regions across which the velocity changes
  sharply) and contact discontinuities (jumps in density that move with the flow and carry no
  pressure jump);
- sensors built on the gradient of the Mach number, the ratio of flow speed to sound speed.

Edge detectors from image processing, such as the Canny and Sobel operators, are cheap ways to
localise shocks as well. They are treated as an implementation shortcut for this detector
rather than as a separate idea.

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

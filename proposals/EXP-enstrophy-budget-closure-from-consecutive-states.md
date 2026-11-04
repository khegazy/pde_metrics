---
type: "EXP"
kind: "protocol"
related: ["kinetic_energy", "enstrophy", "palinstrophy", "issues/084", "issues/010", "proposals/EXP-orchestrator-20261023-temporal-ladder.md", "proposals/EXP-nrmse-rollouts-over-many-initial-conditions.md"]
seen_in: "Boffetta & Ecke 2012, Annu. Rev. Fluid Mech. 44, 427-451, Eqs. 5-6, p. 430"
doi: "10.1146/annurev-fluid-120710-101240"
found_by: "update_metric_eval_principles, 2026-11-03"
---

# EXP: Energy and enstrophy budgets closed on densely sampled consecutive states

## What the experiment is

In unforced two-dimensional Navier-Stokes flow without friction, the energy and enstrophy
decay at rates fixed by the next quantity in the hierarchy (Boffetta & Ecke 2012, p. 430):

```
dE/dt     = -2 nu Omega      (their Eq. 5)
dOmega/dt = -2 nu P          (their Eq. 6)
```

with E the kinetic energy, Omega the enstrophy, P the palinstrophy and nu the kinematic
viscosity. The experiment computes E, Omega and P on a trajectory sampled densely enough that
dE/dt and dOmega/dt can be taken by finite differences, and reports the budget residuals

```
r_E(t) = dE/dt + 2 nu Omega,      r_Omega(t) = dOmega/dt + 2 nu P,
```

on the reference and on a candidate trajectory. The reference's residual is the floor set by
compressibility, the time differencing and the solver; a candidate's residual above that floor
measures how far its own dynamics break the budget, independently of how far its fields are
from the reference.

## What it tests

It tests whether `kinetic_energy`, `enstrophy` and `palinstrophy` are mutually consistent on a
candidate, which their usual reading, a value drifting away from the reference's, cannot
show. A surrogate can match E(t) and still decay at the wrong rate for its own enstrophy, and
the budget residual is the field's quantity that sees this. It also checks the three bundles'
normalisations against each other: `enstrophy` and `palinstrophy` both carry the factor of
one half that Boffetta and Ecke use (palinstrophy card, Definition), and `kinetic_energy` is
(1/2) times the mean of |u|^2, so Eqs. 5-6 should hold with the three bundles as they stand; a
residual near zero on the reference would confirm it on real data (the agent's reading of the
three cards, not a measurement).

## Metrics it would test

`kinetic_energy`, `enstrophy`, `palinstrophy`; and the planned weak-form residual (issue 084),
which needs the same consecutive states.

## Why it is helpful

Part of this already exists. According to `docs/datasets/reynolds_ladder_2d.md`, the 101
frames of `kinet_re5e4_dev` cover the first 100 solver steps, so `kinet_re5e4` at
`dataset.time.reduction=1` stores consecutive solver steps, and the reference's residual can be
computed today; the flow is unforced and decaying, which is the setting of Eqs. 5-6. What is
missing is a candidate with consecutive states: the ladder damages one snapshot at a time, and
the forecast pairs of issue 010 are 500 solver steps apart. Either a densely stored surrogate
rollout (the rollout proposal) or the consistent spatial damage of the temporal ladder
proposal would supply one.

## Cost and requirements

The viscosity of the run, stated on the dataset page (Re = 5e4 in the solver's dimensionless
units; the value of nu is not in the dataset config); a decision on the time-difference stencil;
a harness path that hands a metric two or three consecutive frames (the temporal-ladder
proposal and issue 084 need the same). kinet is weakly compressible at Mach 0.1, so Eqs. 5-6
hold only approximately and the reference's residual sets the floor; how large that floor is
has not been measured (the agent's reasoning, not a measurement). Reading the whole
trajectory at reduction 1 takes roughly half an hour (`CLAUDE.md`, Commands).

## References

- Boffetta, G. & Ecke, R. E. (2012). Two-dimensional turbulence. *Annual Review of Fluid
  Mechanics* 44, 427-451. <https://doi.org/10.1146/annurev-fluid-120710-101240> (read in full;
  Eqs. 5-6 on p. 430, valid with no forcing and no friction).

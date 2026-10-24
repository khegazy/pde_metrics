# Width of the log-density distribution needs supersonic isothermal turbulence and the sound speed

**Category:** data generation
**Priority:** unset — the team has not set a priority for the idea
**Status:** open, waiting on data

## Context

Idea: [Width of the log-density distribution](../docs/ideas/distributional/density_log_pdf.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

Eq. (1), $\sigma_s^2 = \ln(1 + b^2 M_s^2)$, gives the log-density width a physical target set by the sonic Mach number $M_s$ and the driving parameter $b$.

## Why it is not built

Three obstacles: $M_s$ needs the sound speed, an equation-of-state quantity that the repository's rule forbids computing from a simulated dataset (pressure and other observables are read or ignored, never derived); the page's own pitfall says the relation "was established for supersonic, isothermal turbulence" and must be checked before use at low Mach number, while `kinet_re5e4` is at Mach 0.1; and `sod_shock_tube` is not turbulence. Without the target, what remains is the variance of log density compared with a reference, a one-point statistic of the kind the page's rationale moves beyond.

## What would unblock it

Supersonic isothermal turbulence with the sound speed stored ([002](002-shocklet-dataset.md) is the closest planned dataset).

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).

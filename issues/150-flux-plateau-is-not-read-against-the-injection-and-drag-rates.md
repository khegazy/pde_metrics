# The forced dataset's energy flux is not read against its injection and drag rates

**Category:** deferred functionality
**Priority:** unset
**Status:** open. The data exists (`kinet_forced_re40k`); nothing reads the reference's flux
curve against the run's measured rates, so the field's known answer is an observation in a log,
not a check.

## Context

In stationary forced two-dimensional turbulence with a linear drag the energy flux below the
forcing wavenumber is constant and equal to minus the energy the drag removes,
$\Pi_E(k) = -\epsilon_\alpha$ with $\epsilon_\alpha = 2\alpha E$ (Boffetta 2007, *J. Fluid Mech.*
589, 253–260, text after Eq. 2, as read in `dataset_specs/04_forced_stationary_turbulence.md`,
Sect. 3.1). `spectral_energy_flux`'s field normalises the flux by the injection rate and reads
its plateau and its sign change at the forcing scale (`metrics/spectral_energy_flux/card.md`,
"How its field reports it"). `kinet_forced_re40k` (`docs/datasets/forced_turbulence_2d.md`) is
the first dataset where that reading has a known answer: its check measured
$\epsilon_\alpha = 1.535 \times 10^{-7}$ and $\epsilon_I = 2.077 \times 10^{-7}$ per step over
steps 50 000 to 220 000, and $1.548 \times 10^{-7}$ for the drag over the evaluated steps
140 000 to 220 000 (`docs/datasets/logs/kinet_runs/forced_turbulence_2d/checks/final_220000.txt`,
the drag column averaged over those rows).

## What the real run gave (an observation, not a pinned answer)

Run `spectral_energy_flux_1795830149` under
`/pscratch/sd/k/khegazy/fluid_metrics_results/build_datasets/` (21 frames, steps 140 000 to
220 000, $256^2$ analysis grid, 2026-11-27; rerun as `spectral_energy_flux_1795830583`, every
value identical). The reference's own flux curve, the clean rows of
`companions.csv`, in cells² per step³ (the reader's `cell: 1`, so directly comparable with the
rates), median over the 21 frames and the fraction of frames in which it is negative:

| $K$ | 1 | 2 | 4 | 8 | 16 | 32 | 64 | 128 |
|---|---|---|---|---|---|---|---|---|
| median $\Pi(K)$ | −1.7e-9 | −5.4e-9 | −2.7e-8 | −5.9e-8 | −1.15e-7 | −4.0e-9 | 1.08e-8 | 1.6e-9 |
| negative in | 76% | 86% | 95% | 100% | 100% | 67% | 0% | 0% |

The flux is negative, energy moving to large scales, below the forcing shell in every frame at
$K = 8$ and 16, changes sign at the forcing shell, and is small and positive above it. At
$K = 16$ its median is 0.74 of $\epsilon_\alpha$ over the evaluated steps; on the last frame,
where the whole curve is stored, it is most negative at $K = 29$, $-1.48 \times 10^{-7}$ (0.96 of
$\epsilon_\alpha$), and averages $-1.01 \times 10^{-7}$ over shells 6 to 28. So the magnitude grows
through the inverse range up to the forcing shell rather than standing on a plateau, as expected
of an inverse range of under a decade. Above the forcing shell the energy flux is 1.08e-8 at
$K = 64$, about 5% of $\epsilon_I$. These are the flux of the velocity alone at uniform density
(`judgements/003`) on the $256^2$ grid.

## Why it is not built

Two pieces are missing, both harness code (`dataset_specs/BUILD_ORDER.md`, "How code is written
for this plan"): the run's rates are not part of the dataset (a configuration states reader
options, not measured physics), and no analysis reads a reference's companion curve against a
stated value; the analysis compares a candidate's curve with the reference's.

## What would settle it

A place for a dataset's measured known answers (here $\epsilon_\alpha$, $\epsilon_I$ and $k_f$)
and a check that reads the clean curve against them, written once for every curve metric with a
known reference answer. A longer inverse range (a larger box, the dataset's log, open points)
would give the plateau the check should find.

## Related

`issues/105` (the octave sampling and summary of `spectral_energy_flux`), `issues/095` (the
base-period threshold, the other known-answer test this dataset was built for), written with
`kinet_forced_re40k`, 2026-11-27.

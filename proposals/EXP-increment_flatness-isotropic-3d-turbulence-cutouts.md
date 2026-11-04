---
type: "EXP"
kind: "benchmark suite or dataset"
related: ["increment_flatness", "increment_w1", "increment_w1_by_separation", "energy_distance", "tail_index", "tail_exceedance", "spectrum_l2", "spectral_energy_flux", "issues/005", "proposals/EXP-spectral_energy_flux-forced-2d-compressible-flux-loop.md"]
seen_in: "Li et al. 2008, J. Turbulence 9, N31 (JHU turbulence database), Sect. 2.1, Table 1; Granero-Belinchón & Cabeza Gallucci 2024, Mach. Learn.: Sci. Technol. 5(2), 025032, Sects. 2.1-2.2, 4, Figs. 6-9"
doi: "10.1080/14685240802376389"
found_by: "update_metric_eval_principles, 2026-11-03"
---

# EXP: Cutouts of forced isotropic three-dimensional turbulence with an inertial range

## What the experiment is

Read cubes of velocity from a public direct numerical simulation of forced, statistically
stationary, isotropic turbulence with a resolved inertial range, and run the increment and
spectral metrics on them with a degradation ladder applied, exactly as on `kinet_re5e4`. The
standard source is the forced isotropic dataset of the Johns Hopkins turbulence database
(Li et al. 2008): a pseudo-spectral simulation on a periodic 1024^3 grid, forced at the
lowest wavenumbers (|k| <= 2), at a Taylor-scale Reynolds number of 433, with 1024 stored
frames spanning about one large-eddy turnover time, served through a web interface (abstract,
Sect. 2.1, Table 1). Periodic cutouts, or the whole box coarsened by the existing remap, give
the metrics a periodic grid.

## What it tests

It supplies the setting in which the statistics these metrics come from are defined and have
known behaviour:

- **Flatness against separation.** In turbulence the increment flatness is 3 at the integral
  scale and grows as the separation decreases (Granero-Belinchón & Cabeza Gallucci 2024,
  Sect. 2.1; their Fig. 6c shows log(F/3) rising toward small scales on wind-tunnel data at
  R_lambda = 2500). The flatness of the longitudinal velocity gradient grows with Reynolds
  number as about 1.14 R_lambda^0.34 in isotropic DNS up to R_lambda of about 1130 (Ishihara
  et al. 2007, abstract). A reference with these known trends lets a card check that its
  metric reads them before reading a degradation.
- **Structure functions and the four-fifths law.** The structure-function analysis of
  Kolmogorov's 1941 theory (Frisch 1995, ch. 6) and its intermittency corrections (ch. 8) are
  defined for stationary, homogeneous, isotropic turbulence in three dimensions; longitudinal
  and transverse increments are distinct objects there.
- **A constant energy flux.** In a stationary forced three-dimensional flow the spectral
  energy flux is positive and roughly constant across the inertial range, so
  `spectral_energy_flux` has a known shape to recover (the agent's statement of textbook
  material; no locator checked).

## Metrics it would test

`increment_flatness`, `increment_w1`, `increment_w1_by_separation`, `energy_distance` on
increments, `tail_index` and `tail_exceedance` on increments, `spectrum_l2` and
`spectral_energy_flux`. The longitudinal and transverse split planned for the velocity
increments (Part 5 of the evaluation plan) is only meaningful against an isotropic reference.

## Why it is helpful

Every dataset here is two-dimensional (issue 005), and `kinet_re5e4` decays, is anisotropic
(a doubly periodic shear layer) and has no established scaling range. The increment bundles
cite Granero-Belinchón and Cabeza Gallucci, whose evaluation criteria are the increment
variance, skewness and flatness across scales, structure functions up to order 4, the
probability densities of standardised increments and the scaling exponents (Sect. 4,
Figs. 6-9), computed on long one-dimensional velocity records of fully developed turbulence
(ONERA Modane wind tunnel, Sect. 2.2). None of those curves has a known target on the data
here, so a card can show only that its number moves under a degradation, not that it reads
intermittency the way the field does.

## Cost and requirements

A reader for the database's cutouts (the service and its Python client are public; the terms
of use need checking), dataset configs declaring three periodic axes, and a severity
calibration of the ladder on the new spectrum (`AGENTS.md` §5). One 256^3 cutout of three
velocity components in float32 is 0.2 GB (the agent's arithmetic). The increment and spectral
bundles are written dimension-agnostically, but issue 005 records that a three-dimensional run
has never been made.

## References

- Li, Y., Perlman, E., Wan, M., Yang, Y., Meneveau, C., Burns, R., Chen, S., Szalay, A. &
  Eyink, G. (2008). A public turbulence database cluster and applications to study Lagrangian
  evolution of velocity increments in turbulence. *Journal of Turbulence* 9, N31.
  <https://doi.org/10.1080/14685240802376389>; arXiv:0804.1703 (read in full).
- Granero-Belinchón, C. & Cabeza Gallucci, M. (2024). A multiscale and multicriteria
  generative adversarial network to synthesize 1-dimensional turbulent fields. *Machine
  Learning: Science and Technology* 5(2), 025032. <https://doi.org/10.1088/2632-2153/ad43b3>;
  arXiv:2307.16580 (read in full, v2).
- Ishihara, T., Kaneda, Y., Yokokawa, M., Itakura, K. & Uno, A. (2007). Small-scale statistics
  in high-resolution direct numerical simulation of turbulence: Reynolds number dependence of
  one-point velocity gradient statistics. *Journal of Fluid Mechanics* 592, 335-366.
  <https://doi.org/10.1017/S0022112007008531> (abstract only).
- Frisch, U. (1995). *Turbulence: The Legacy of A. N. Kolmogorov*. Cambridge University Press.
  <https://doi.org/10.1017/CBO9781139170666> (table of contents only: ch. 6 "The Kolmogorov
  1941 theory", ch. 8 "Intermittency").

# The number `spectrum_l2` registers, a linear relative L2 over shells, is a convention dominated by the lowest shells

**Category:** method
**Priority:** unset
**Status:** open. The bundle registers the linear relative L2 and says so; whether a different
summary should be registered as well is open.

## Context

`spectrum_l2` compares two radial energy spectra $E(k)$ (Boffetta & Ecke 2012, *Annu. Rev.
Fluid Mech.* 44, 427–451, Eq. (3), p. 430). The spectrum itself is the field's object, drawn on
log-log axes over the reference's, and the bundle now stores it at every shell as its curve
companion. The number it registers,

$$
S = \frac{\lVert E_{\text{cand}} - E_{\text{ref}} \rVert_2}{\lVert E_{\text{ref}} \rVert_2}
$$

over the shells $k = 1, 2, \dots$ on linear values, comes from no source. The sources read for
the card's "How its field reports it" report spectra in other ways:

- Turbulence draws $E(k)$ and reads its slope and the compensated plateau (Boffetta & Ecke
  2012, Figs. 5a and 11a; Pope 2000, *Turbulent Flows*, Figs. 6.13–6.17). It does not reduce a
  comparison of two spectra to one number.
- Kochkov et al. (2021, *PNAS* 118, e2101784118) report "the absolute error of the energy
  spectrum scaled by $k^5$" (Results, "Comparison to other ML models"; Fig. 5), without a
  formula. Stachenfeld et al. (2022, ICLR, arXiv:2112.15275) report the RMSE of the logarithm
  of a spectrum (Sect. 5; Fig. 2c–d). Lienen et al. (2024, ICLR, arXiv:2306.01776) use
  $\lVert \log E_1 - \log E_2 \rVert_2$ (Sect. 6.3, Eq. (7)) as the ground distance of a
  Wasserstein distance between sets of samples.
- WeatherBench 2 (Rasp et al. 2024, arXiv:2308.15560, Sect. 4.5 and Fig. 10) draws spectra and
  scores none.

No source found registers a linear relative L2 between spectra.

## What is measured about it

A linear L2 over shells weighs each shell by its energy squared, so the shells that hold the
most energy decide the number. On `kinet_re5e4`, the share of the denominator
$\sum_k E_{\text{ref}}(k)^2$ held by the lowest shells, computed from
`radial_energy_spectrum` on the stored fields at three frames (the script is in the task log of
`metrics-spectral`, 2026-11-04):

| frame | field | shell 1 | shells 1–3 | shells 16 and up | energy share of shells 16 and up |
|---|---|---|---|---|---|
| 2000 | density | 0.9873 | 0.9997 | 1.2e-9 | 6.5e-5 |
| 2000 | velocity | 0.9887 | 0.9987 | 4.7e-7 | 1.6e-3 |
| 2000 | vorticity | 0.2827 | 0.5168 | 1.2e-2 | 0.117 |
| 6000 | density | 0.9374 | 0.9979 | 2.0e-10 | 4.0e-5 |
| 6000 | velocity | 0.9883 | 0.9995 | 1.0e-7 | 1.1e-3 |
| 6000 | vorticity | 0.6556 | 0.8560 | 1.0e-2 | 0.189 |
| 10000 | density | 0.9331 | 0.9971 | 1.5e-10 | 1.9e-5 |
| 10000 | velocity | 0.9891 | 0.9995 | 8.5e-9 | 2.9e-4 |
| 10000 | vorticity | 0.6972 | 0.8906 | 7.4e-4 | 0.059 |

On density and velocity the first three shells hold more than 99.7% of the denominator, and
every shell from 16 up less than 5e-7 of it. A prediction that loses everything above shell 16
on those fields moves the number by at most about the square root of that share (my reasoning
from the formula: the candidate's spectrum can differ there by at most the reference's, if it
loses the energy, and the shells below are unchanged). On vorticity, whose spectrum is $k^2$
times velocity's, the high shells carry more weight. The per-shell tables the analysis now
writes at the octave shells (`spectrum_l2[k]`) show what the number does not.

## What would settle it

A decision on which second summary to register, each a sibling bundle importing
`energy_spectrum`, not a change to this one:

1. A distance on the logarithm of the spectrum (Stachenfeld et al. 2022; Lienen et al. 2024).
   It weighs every shell by its relative error, and it is undefined where either spectrum is
   zero, which the anchor (the spatial mean) and the sharp low-pass filters produce on every
   shell they empty. That question is `issues/137`.
2. Kochkov et al.'s error of the $k^5$-scaled spectrum, once its formula is known; the
   exponent was chosen for their Kolmogorov flow and has no counterpart on `kinet_re5e4`.

## Related

`issues/105` (the same question for `spectral_energy_flux`), `issues/098`, `issues/118`;
`judgements/016`. Written by the `metrics-spectral` agent, 2026-11-04.

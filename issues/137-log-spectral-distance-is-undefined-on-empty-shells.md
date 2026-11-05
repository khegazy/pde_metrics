# A log-spectral distance has sources but is undefined on the shells a prediction empties

**Category:** method
**Priority:** unset
**Status:** open. Not built; the sibling waits for a decision on the shell range and on what an
empty or round-off shell contributes.

## Context

Two machine-learning papers compare energy spectra on their logarithm, the natural sibling of
`spectrum_l2` (`issues/136`):

- Stachenfeld et al. (2022, ICLR, arXiv:2112.15275), Sect. 5 and Fig. 2c–d: the RMSE of the
  logarithm of the shell spectrum of the scalar energy field. Its appendix ("Other Statistical
  Metrics") cuts the frequencies above a stated magnitude. No floor for an empty shell is
  given in what was read.
- Lienen et al. (2024, ICLR, arXiv:2306.01776), Sect. 6.3, Eq. (7):
  $d = \lVert \log E_1 - \log E_2 \rVert_2$, integrated over $k$ from 1 to 23 (App. E, Eq. (10)),
  used as the ground distance of a Wasserstein-2 distance between sets of samples.

Both restrict the wavenumbers, and neither says what a shell holding no energy, or only
round-off, contributes. On the ladder here that is not an edge case.

## What is measured about it

On `kinet_re5e4` frame 6000, velocity on its 256^2 grid, against the same field passed through a
sharp low-pass at shell 32 (the computation is the script `log_spectrum_check.py` in the task
log of `metrics-spectral`, 2026-11-04):

- The 149 emptied shells hold round-off, not zero: their energy is $1.7 \times 10^{-29}$ to
  $1.6 \times 10^{-16}$ of the reference's there (median $5.9 \times 10^{-25}$).
- The reference's own spectrum spans 19 decades, from $1.3 \times 10^{-3}$ in shell 1 down to
  $2.0 \times 10^{-22}$, so its highest shells are themselves close to round-off.
- The RMSE of $\log_{10} E$ over every shell is 22.5 decades; over shells 1–32 it is
  $3 \times 10^{-16}$. Flooring the emptied shells at $10^{-30}$ gives 16.8, at $10^{-40}$ 22.5:
  the number is set by the round-off of the filter and by the floor, not by the field.
- The damage anchor, the field's spatial mean, has $E = 0$ in every shell, so its log distance is
  infinite and the damage scale undefined.

## What would settle it

A stated shell range (the field's resolved range, below a dissipation or dealiasing cutoff) and a
stated floor, or a source that fixes both; then a sibling bundle importing
`spectrum_l2.energy_spectrum`, which leaves `spectrum_l2`'s number unchanged. A floor tied to
machine epsilon times the reference's largest shell, as `spectral_energy_flux` bounds round-off,
is one candidate; it is not a source's.

## Related

`issues/136`; `judgements/016`, which records the decision not to build it now. Written by the
`metrics-spectral` agent, 2026-11-04.

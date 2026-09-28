# `spectrum_l2` bins by exact wavevector magnitude, so it is nearly a per-mode comparison

**Category:** metric definition
**Priority:** —
**Status:** RESOLVED (2026-09-28) — option 2, integer shells

## Decision

Option 2 below, chosen by the maintainer on 2026-09-28: `spectrum_l2` now bins by
`rint(|k|)`, 182 shells on 256 x 256. The magnitude is still the one in
`fmeval/wavenumbers.py`; only the grouping is local to the metric, which is why this does not
reintroduce the filter/calibration disagreement that module was written to end. Every mode is
kept, including the partly filled corner shells. The card's evidence was regenerated from a
fresh run with the new binning, and the tests pin both the shell count and the case the change
exists for: an axis mode and a diagonal mode of equal amplitude now share shell 1 and score 0,
where the exact binning scored sqrt 2.

What the decision gives up is stated in the card's Limitations: a unit-width shell cannot see
energy move within it, which matters most at shell 1, where density keeps 69% of its
fluctuation energy in the sqrt 2 diagonal modes.

The rest of this file is the record as it stood when the decision was asked for.

## Context

`metrics/spectrum_l2` sums Fourier energy into shells and takes a relative L2 distance between
the two shell spectra. It deliberately reuses the calibration's binning
(`fmeval.calibration._magnitude_bins`) rather than defining its own, because the repository
once had two definitions of `|k|` and they disagreed about the diagonal modes (`CLAUDE.md`,
finding 5). That binning groups modes by their *exact* magnitude, `np.unique(round(|k|, 9))`,
not by rounded shells.

## Evidence

Computed from `fmeval.wavenumbers.wavenumber_magnitude((256, 256))`:

| binning | shells on 256 x 256 | modes per shell |
|---|---|---|
| exact magnitude (what `spectrum_l2` uses) | 5924 | median 8, max 48 |
| `rint(|k|)` (the textbook shell spectrum) | 182 | grows as about 2 pi k |

So the "radial spectrum" compared here pools each mode only with its images under the grid's
reflections and rotations, plus the rare accidental coincidences of magnitude. It is much closer
to comparing individual mode energies than to comparing the shell-averaged spectrum that the
turbulence literature means by E(k).

## Why it has not mattered yet

Every candidate on the degradation ladder is an operator applied to the reference itself, so
mode amplitudes change coherently and the fine binning costs nothing. The Gaussian impostor
copies the reference's amplitudes mode by mode, so it scores at round-off under either binning
(about 1e-15 on `comparison_1789632054`).

## Why it will matter

Against a prediction that is a *different realisation* of the flow — a surrogate run, or the
second seed that `issues/004` asks for — each shell's energy is an average over about eight
modes instead of hundreds, so the realisation-to-realisation scatter of individual mode
amplitudes enters the value. With integer shells it would largely average out. This is a
consequence of the binning, not a measurement; there is no second realisation to measure it on.

## Options

1. **Keep it.** One definition of `|k|` everywhere, and a metric that is stricter than a
   shell spectrum. Document that it is not E(k) — the card now does.
2. **Bin by `rint(|k|)` inside this metric only.** Matches the literature. The hazard the
   shared binning guards against is a filter and a calibration disagreeing about which side of
   a cutoff a mode falls on; a *metric* binning differently does not reintroduce that, but it
   is a second definition, and the next person to read it will have to be told why.
3. **Make the binning a parameter** and report both.

What would settle it: an independent realisation (`issues/004`), on which the two binnings'
values for a statistically identical field can be compared directly.

## Related

- `issues/037-position-blind-metrics-have-no-damage-anchor.md` — the same missing second
  realisation also blocks this metric's damage scale.

# A fractional Fourier shift drops the Nyquist mode of an even grid

**Category:** method
**Priority:** low — negligible on the production data, would matter on a field with energy at the grid scale
**Status:** open

## Context

`translate_subpixel` shifts a field by multiplying its spectrum by `exp(-2 pi i k d)` and taking
the real part of the inverse transform. On an even grid the Nyquist component is its own
conjugate; after a fractional shift it becomes complex, and `np.real` keeps only
`cos(pi d)` of it. At half a cell it is removed entirely. So the operator is not the exact
rigid shift its docstring used to claim, and it cannot declare that it preserves the amplitude
spectrum or the shape, only the spatial mean.

Found while writing `tests/test_degradation_contract.py::test_declared_preservation_is_true`: at
its harshest test severity (1.0 cell, an integer) the operator looks exact, and only the half-cell
severity exposed it.

## Evidence

On the 32 x 16 white-noise field of the contract test, half a cell changes the fluctuation's
amplitude spectrum and the shape residual by 1.7e-2 relative
(`test_a_fractional_shift_loses_the_nyquist_mode_of_an_even_grid`).

On frame 5000 of `kinet_re5e4` (256 x 256), the fraction of fluctuation energy lost:

| field | shift 0.125 | shift 0.5 | energy on the Nyquist lines |
|---|---|---|---|
| density | 5.6e-12 | 3.9e-11 | 4.6e-11 |
| velocity | 1.2e-11 | 8.2e-11 | 1.1e-10 |
| vorticity | 4.7e-14 | 3.2e-13 | 6.2e-13 |

Harmless here: the recorded displacement curves are unaffected at any number they print.

## What would settle it

Treat the Nyquist mode with the symmetric convention (shift it by `cos(pi k d)` and keep it real,
which is the band-limited interpolant's value), or zero it before shifting and say so. Either
changes every recorded `translate_subpixel` value by a round-off-sized amount, so it belongs with a
regeneration of the evidence, and it would let the operator declare `amplitude_spectrum` and
`shape`.

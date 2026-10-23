# The wavenumber magnitude is anisotropic on a non-square domain, and a wall makes one

**Category:** method
**Priority:** low now, because every dataset is square and either fully periodic or 1D; it
blocks any dataset with a non-square domain or with a wall on only some axes, such as the
kinet Sod runs on 3001 × 5 cells
**Status:** open, needs a decision on the definition of `|k|`

## Context

`fmeval/wavenumbers.py::wavenumber_magnitude(shape)` counts each axis's wavenumber in cycles
across *that axis's own* extent. The calibration and the spectral operators (`lowpass_ideal`,
`lowpass_butterworth`, `highpass_ideal`, `highpass_butterworth`, `band_attenuate`) all use it, so
they agree with each other, which is what that module exists to guarantee. But two waves of the
same physical wavelength along different axes get different `|k|` whenever the axes differ in
length, so an "isotropic" cutoff is not isotropic.

On a square, fully periodic grid that never happens. It happens on any non-square grid, and the
boundary-aware ladder now creates one from a square grid: on a grid whose x-axis is Neumann and
whose y-axis is periodic, `fmeval.ladder._call` hands the operator the field extended to twice
its length in x only (`GridSpec.extend`), so x counts cycles across twice the length y does.

## Evidence

A cosine of wavelength 16 cells along x, and the same along y, through `apply_severity_level`
with `lowpass_ideal` at an absolute cutoff; the fraction of each wave's standard deviation kept:

| grid | boundaries | cutoff | x-wave kept | y-wave kept |
|---|---|---|---|---|
| 64 × 64 | periodic, periodic | 6 | 1.0 | 1.0 |
| 64 × 64 | neumann, periodic | 6 | 0.0 | 1.0 |
| 64 × 32 | periodic, periodic | 3 | 0.0 | 1.0 |

The second row is new with the boundary-aware ladder; the third has always been so.
`lowpass_butterworth` at the same cutoff on the second grid keeps 0.091 of the x-wave and 0.962
of the y-wave. `tests/test_degradation_contract.py::test_a_low_pass_treats_both_axes_of_a_walled_square_grid_alike`
reproduces the second row and is marked `xfail(strict=True)` naming this issue.

The calibration's `characteristic_scale = grid.shape[0] / mean_wavenumber` has the same
problem: it is in cells along the first axis only.

## Remaining action

Decide what `|k|` means on a non-square domain, then change `wavenumber_magnitude` and
`calibrate_field` together. One candidate (a conjecture, not tested): count every axis in
cycles across one common physical length, for example the longest extended axis, using
`GridSpec.length`. That leaves every square fully periodic grid, and therefore every kinet
number, bitwise unchanged, but it changes the non-square test fixtures (16 × 8) and needs the
characteristic scale restated in the same unit.

## Related

`fmeval/wavenumbers.py`; `AGENTS.md` §9, "Two definitions of `|k|`"; `docs/datasets/sod_shock_tube.md`
lists the 3001 × 5 kinet runs.

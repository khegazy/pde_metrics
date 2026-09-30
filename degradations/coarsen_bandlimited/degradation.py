"""The `coarsen_bandlimited` degradation: coarsen, then reconstruct without adding edges.

The companion of ``coarsen``. Both block-average the field by the same factor and so discard
exactly the same information -- the block means of their outputs are identical to each
other and to the input's. They differ only in how each block is filled back in. ``coarsen``
repeats the block mean, which is the right control for a pointwise metric but leaves a jump
at every block edge; this reconstructs the one band-limited field whose block means are the
coarse values, so nothing sharper than the coarse grid can represent is created.

Why it exists: ``issues/039``. A metric that differentiates the field measures the staircase
``coarsen`` adds as well as the resolution it removes. Measured on ``comparison_1789632054``,
``h1_seminorm`` on vorticity was non-monotone under ``coarsen`` (rho 0.2, 0 of 161 frames in
order) and ``palinstrophy`` rose by 89% at a factor of 2. Evaluating on both operators
separates the two effects: a response to this one is a response to lost resolution alone.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from degradations.registry import degradation
from fmeval.context import FieldContext
from fmeval.remap import block_average


def _box_response(k: NDArray[np.floating], factor: int, n: int) -> NDArray[np.complexfloating]:
    """Fourier response of averaging ``factor`` consecutive cells, on a grid of ``n``.

    ``D(k) = (1/f) sum_{s=0}^{f-1} exp(2 pi i k s / n)``. With numpy's transform
    conventions, a fine field ``g`` with spectrum ``G`` has block means whose coarse
    spectrum is ``C(kappa) = (1/f) sum_{k = kappa mod M} G(k) D(k)``, where ``M = n / f``.
    ``D`` is nonzero for every ``|k| <= M / 2``, so the band-limited inversion below never
    divides by zero; its smallest modulus there tends to 2/pi, so the inversion amplifies no
    mode by more than pi/2.
    """
    s = np.arange(factor)
    return np.exp(2j * np.pi * np.outer(k, s) / n).mean(axis=1)


def _expand_axis(coarse: NDArray[np.floating], factor: int, axis: int) -> NDArray[np.floating]:
    """Band-limited expansion of block means along one axis.

    Returns the real field of length ``M * factor`` along ``axis`` that contains no Fourier
    mode above the coarse grid's Nyquist wavenumber and whose ``factor``-cell block means
    are exactly ``coarse``. For an even coarse length the coarse Nyquist coefficient
    receives contributions from both fine modes ``+M/2`` and ``-M/2``; it is split equally
    between them, which is what keeps the result real.
    """
    m = coarse.shape[axis]
    n = m * factor
    c_hat = np.moveaxis(np.fft.fft(coarse, axis=axis), axis, -1)
    kappa = np.rint(np.fft.fftfreq(m) * m).astype(np.int64)

    g_hat = np.zeros((*c_hat.shape[:-1], n), dtype=np.complex128)
    for index, k in enumerate(kappa):
        coefficient = c_hat[..., index]
        if m % 2 == 0 and k == -m // 2:
            # The self-conjugate coarse Nyquist mode: aliases of +M/2 and -M/2 both land here.
            for k_fine in (-m // 2, m // 2):
                g_hat[..., k_fine % n] += (
                    factor * coefficient / (2.0 * _box_response(np.array([k_fine]), factor, n)[0])
                )
        else:
            g_hat[..., k % n] = factor * coefficient / _box_response(np.array([k]), factor, n)[0]

    return np.moveaxis(np.fft.ifft(g_hat, axis=-1).real, -1, axis)


@degradation(
    name="coarsen_bandlimited",
    family="resolution",
    severity_name="factor",
    severity_units="",
    severity_direction="increasing",
    calibration=None,
    ordinal=True,
    stochastic=False,
    fields=("*",),
    preserves=("spatial_mean",),
)
def coarsen_bandlimited(
    field: NDArray[np.floating],
    severity: float,
    *,
    ctx: FieldContext,
) -> NDArray[np.floating]:
    """Block average by ``factor``, then the band-limited field with those block means.

    Args:
        field: The field to damage, shape ``(C, *spatial)`` on the analysis grid.
        severity: The coarsening factor, a whole number of cells per block; the same
            absolute scale as ``coarsen``. Values of 1 or less return the field unchanged.
        ctx: Unused beyond the contract; the operator needs only the array's own shape.

    Returns:
        Same shape and dtype as ``field``. Its block means equal the input's exactly, and
        along every spatial axis it holds no mode above the coarse grid's Nyquist
        wavenumber. Because block averaging is separable, expanding one axis at a time
        reproduces the full ``factor^d`` block means.
    """
    factor = int(round(severity))
    if factor <= 1:
        return field
    out = block_average(field.astype(np.float64), factor)
    for axis in range(1, field.ndim):
        out = _expand_axis(out, factor, axis)
    return out.astype(field.dtype, copy=False)

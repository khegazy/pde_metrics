"""Quadratic Wasserstein distance between two density fields on a periodic domain.

Each density, divided by its own mean, is a probability density on the torus. The quadratic
Wasserstein distance is the square root of the least mean squared distance its mass must
move to become the other: a transport cost, in units of length, rather than a difference of
values. It is computed as the continuous distance between the two densities, by solving the
Monge-Ampere equation for the optimal map with the periodic damped Newton method of Saumier,
Agueh & Khouider (2015), not as a transport between one point per cell. On a field whose
displacements are smaller than a cell, as they are for density here, a cell-to-cell transport
would measure the grid rather than the field.

Two facts about density set what this number can and cannot do, and the card measures both.
The density's mean is two to three orders of magnitude larger than its fluctuation, and a
uniform background added to a signal makes the misfit non-convex in shifts (Yang et al. 2018,
Geophysics 83(1), section "Data normalization"; in one dimension, Engquist & Yang 2022,
CPAM 75(10), Theorem 4.6), losing the property that made the Wasserstein distance attractive
for displaced features, its growth as the square of a shift. And for densities this close
to uniform the distance is, to first order, the H^-1 norm weighted by the reference density
(Peyre 2018, ESAIM:COCV 24(4), Eq. 5), within a factor close to 1 of the seminorm that
``h_minus_one`` computes (his Lemma 2).

Velocity and vorticity take both signs and are not densities, so they wait on the choice of
a signed-field formulation (issues/047).
"""

from __future__ import annotations

import warnings

import numpy as np
from numpy.typing import NDArray
from scipy import ndimage

from fmeval.context import FieldContext
from fmeval.external.kinet_spectral import physical_wavenumber_grid
from metrics.registry import REDUCTIONS, companion, metric

#: Newton iterations stop once the root mean square of the Monge-Ampere residual, on densities
#: normalised to mean 1, is below this. A fraction of the mean density, so dimensionless; set by
#: me far below the smallest density change the ladder makes (noise at 1e-3 of the fluctuation
#: RMS, about 2e-6 of the mean on kinet density) and above the round-off of a 256^2 FFT.
RESIDUAL_TOLERANCE: float = 1e-12

#: Iterations allowed before the solve is declared failed and the value is NaN. Mine: measured
#: convergence takes 4 to 7 iterations on kinet density, and 239 between two unrelated smooth
#: 64^2 densities whose maximum is four times their minimum, the slowest pair that converged.
MAX_ITERATIONS: int = 500

#: Times a step may be halved to make the residual fall while keeping I + D^2 u positive
#: definite, before the solve is declared failed. Mine: 2^-30 of a step is below the precision
#: of the potential it is added to.
MAX_HALVINGS: int = 30

#: Order of the periodic B-spline that evaluates the candidate density at the displaced points
#: x + grad u. Mine: Saumier et al. (2015), Sect. 4, use nearest neighbour and name linear
#: interpolation as the common choice; measured on kinet density, the value moves by up to
#: 1.6% from nearest neighbour to cubic and by at most 3.4e-5 from cubic to quintic.
SPLINE_ORDER: int = 3


@metric(
    name="wasserstein",
    arity="pairwise",
    fields=("density",),     # a density is a measure; signed fields wait on issues/047
    differentiable=True,     # W_2^2 has a Frechet derivative in the densities, the adjoint
                             # source of Yang et al. (2018), Geophysics 83(1), section
                             # "Compare globally", "Computation of adjoint source"
    cost="moderate",         # 0.19 to 0.23 s per 256^2 evaluation in the evidence run, a
                             # hundred times h_minus_one: 4 to 7 Newton steps of FFTs
    higher_is_better=False,
    symmetric=False,         # W_2 is symmetric (Peyre & Cuturi 2019, Prop. 2.3), but solving
                             # from the other side differs at the discretisation's error,
                             # measured 5e-6 relative on kinet density with noise
    units="length",
    reduction="sqrt_mean",
    requires_periodic=True,  # FFT derivatives and a wrapping interpolation: transport on a torus
)
def wasserstein(
    reference: NDArray[np.floating],
    candidate: NDArray[np.floating],
    *,
    ctx: FieldContext,
) -> float:
    """Quadratic Wasserstein distance between the mass-normalised densities, in length units.

    ``W_2 = (MK_{d^2})^(1/2)``, the transport cost with the squared distance raised to one half
    (Peyre & Cuturi 2019, Found. Trends Mach. Learn. 11(5-6), Eq. 2.18), which is a distance
    between probability measures (their Prop. 2.3). The cost is the mean, over the grid, of
    the per-cell map :func:`wasserstein_map` returns.

    Args:
        reference: The trusted density, shape ``(1, *spatial)`` on the analysis grid.
        candidate: The density being scored, same shape and grid.
        ctx: Supplies the analysis grid, whose spacing sets the unit of length.

    Returns:
        The distance, zero for identical densities and for two densities that differ only by a
        constant factor. NaN where either field has a cell that is not positive and finite,
        which is outside the definition, or where the solve did not converge.
    """
    return REDUCTIONS["sqrt_mean"](wasserstein_map(reference, candidate, ctx=ctx),
                                   reference.shape[0])


@companion(of="wasserstein")
def wasserstein_map(
    reference: NDArray[np.floating],
    candidate: NDArray[np.floating],
    *,
    ctx: FieldContext,
) -> NDArray[np.floating]:
    """Transport cost density ``f |grad u|^2``: where, and how far, the reference's mass moves.

    With ``f`` and ``g`` the reference and candidate divided by their means, so each is a
    probability density on the torus times its area, the optimal map is ``T(x) = x + grad u``
    with ``u`` periodic (Saumier et al. 2015, IMA J. Appl. Math. 80(1): Theorem 2.1, after
    Cordero-Erausquin, states that the map is additive, and the remark after it that this makes
    it x plus the gradient of a periodic function), and ``u`` solves the Monge-Ampere equation
    ``g(x + grad u) det(I + D^2 u) = f`` (their Eq. 4). Its mean over the grid is
    ``W_2^2 = integral of |x - T(x)|^2 f dx / |Omega|`` (their Eq. 3), so the map reduces to
    the metric by ``sqrt_mean``.

    The solve is their damped Newton iteration (Eq. 6), starting from ``u = 0``:

    1. ``f_n = g(x + grad u_n) det(I + D^2 u_n)``, then ``f_n - mean(f_n) + 1`` so that the
       residual has zero mean (their Eq. 14).
    2. Solve ``Laplacian theta = (f - f_n) / g(x + grad u_n)``, re-centred to zero mean, by
       FFT.
    3. Set ``u_{n+1} = u_n + theta / tau`` with ``tau = 1, 2, 4, ...``, the first that lowers
       the root mean square residual and keeps ``I + D^2 u`` positive definite.

    Step 2 replaces their linearised operator (Eq. 5) by its leading term ``g Laplacian``
    with ``g`` divided out cell by cell, which is mine; their Sect. 3.3 says the full operator
    can sometimes be replaced by a simpler equation. The converged ``u`` is fixed by the
    residual of step 1, not by the operator that reduces it, so the choice changes the number
    of iterations and not the answer. Dividing by ``g`` is what keeps the step from
    overshooting where the candidate density is several times its mean. Step 3 chooses their
    damping ``tau`` adaptively, which is mine: their proof needs ``tau`` large enough and
    ``I + D^2 u_n`` positive definite at every step (Sect. 3.3), and gives no value for it.
    Derivatives of ``u`` are spectral, with wavevectors from ``physical_wavenumber_grid``,
    the convention the repository's spectral derivatives and ``h_minus_one`` use; their
    Sect. 4.2 solves the linear step by FFT as well. The candidate is evaluated off the grid
    by a periodic cubic B-spline, a choice of mine (see ``SPLINE_ORDER``).

    Args:
        reference: The trusted density, shape ``(1, *spatial)``.
        candidate: The density being scored, same shape and grid.
        ctx: Supplies the analysis grid.

    Returns:
        An array of shape ``(*spatial)`` in length squared: the reference's normalised density
        times the squared displacement of its mass. All NaN where the metric is undefined.

    Raises:
        ValueError: If the shapes differ or there is more than one channel.
    """
    if reference.shape != candidate.shape:
        raise ValueError(
            f"wasserstein needs matching shapes, got {reference.shape} and {candidate.shape}")
    if reference.shape[0] != 1:
        raise ValueError(f"wasserstein takes one density channel, got {reference.shape[0]}")
    spatial = reference.shape[1:]
    fields = [np.asarray(x[0], dtype=np.float64) for x in (reference, candidate)]
    if not all(np.isfinite(x).all() and (x > 0).all() for x in fields):
        # A transport distance is defined between measures; any value given to a field with a
        # non-positive cell would be a signed-field formulation, which issues/047 leaves open.
        return np.full(spatial, np.nan)
    f, g = (x / x.mean() for x in fields)  # equal mass: Engquist & Froese (2014), Sect. 2.2

    spacing = tuple(ctx.grid.spacing)
    k = physical_wavenumber_grid(spatial, spacing)
    k_squared = sum(kj**2 for kj in k)
    inverse_laplacian = np.zeros_like(k_squared)
    inverse_laplacian[k_squared > 0] = -1.0 / k_squared[k_squared > 0]
    g_spline = ndimage.spline_filter(g, order=SPLINE_ORDER, mode="grid-wrap")
    cells = np.meshgrid(*(np.arange(n, dtype=np.float64) for n in spatial), indexing="ij")
    axes = tuple(range(len(spatial)))

    g_floor = g.min()  # the spline can undershoot between cells; never divide by less

    def evaluate(u_hat: NDArray[np.complexfloating]) -> tuple:
        """Residual of Eqs. 4 and 14 at ``u``, with grad u, g(x + grad u) and the least
        eigenvalue of I + D^2 u (positive iff ``x + grad u`` is a convex map's gradient)."""
        grad = [np.fft.ifftn(1j * kj * u_hat, axes=axes).real for kj in k]
        hessian = np.stack([np.stack([np.fft.ifftn(-ki * kj * u_hat, axes=axes).real
                                      for kj in k], axis=-1) for ki in k], axis=-2)
        eigenvalues = np.linalg.eigvalsh(np.eye(len(spatial)) + hessian)
        displaced = [c + d / h for c, d, h in zip(cells, grad, spacing)]  # in cells
        g_at = ndimage.map_coordinates(g_spline, displaced, order=SPLINE_ORDER,
                                       mode="grid-wrap", prefilter=False)
        f_n = g_at * eigenvalues.prod(axis=-1)  # g(x + grad u) det(I + D^2 u), Eq. 4
        residual = f - (f_n - f_n.mean() + 1.0)  # Eq. 14
        return residual, grad, g_at, eigenvalues.min()

    u_hat = np.zeros(spatial, dtype=np.complex128)
    residual, grad, g_at, _ = evaluate(u_hat)
    rms = np.sqrt(np.mean(residual**2))
    for iteration in range(MAX_ITERATIONS):
        if rms <= RESIDUAL_TOLERANCE:
            return f * sum(d**2 for d in grad)  # f |x - T(x)|^2, the integrand of Eq. 3
        step = residual / np.maximum(g_at, g_floor)  # leading term of Eq. 5, g divided out
        theta_hat = np.fft.fftn(step - step.mean(), axes=axes) * inverse_laplacian
        for _ in range(MAX_HALVINGS):  # the damping tau of Eq. 6, doubled until accepted
            trial = evaluate(u_hat + theta_hat)
            trial_rms = np.sqrt(np.mean(trial[0] ** 2))
            if trial_rms < rms and trial[3] > 0:  # NaN compares False, so divergence halves
                break
            theta_hat = theta_hat / 2
        else:
            stopped = (f"no step of up to 2^-{MAX_HALVINGS} of the Newton step lowered the "
                       f"residual of {rms:.1e} after {iteration} iterations")
            break
        u_hat = u_hat + theta_hat
        residual, grad, g_at, _ = trial
        rms = trial_rms
    else:
        if rms <= RESIDUAL_TOLERANCE:  # the last permitted step reached the tolerance
            return f * sum(d**2 for d in grad)
        stopped = f"the residual was still {rms:.1e} after {MAX_ITERATIONS} iterations"
    warnings.warn(
        f"wasserstein: Monge-Ampere solve did not converge on frame {ctx.frame_index}: "
        f"{stopped}; returning NaN", RuntimeWarning, stacklevel=2)
    return np.full(spatial, np.nan)

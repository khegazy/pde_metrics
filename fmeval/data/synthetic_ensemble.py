"""A generated ensemble whose right answer is known in closed form.

Every other reader in this package opens a file. This one computes its frames, because
what it exists to provide is not data but a *calibrated null*: an ensemble for which the
correct value of every probabilistic metric can be written down and checked, so a metric
that disagrees is wrong rather than merely surprising. No ensemble of real flow
realizations exists yet (see ``issues/004-independent-realizations.md``); when one does,
these metrics will already have been validated against a case with no unknowns in it.

**The construction.** For each field, frame and cell,

.. math::

    \\text{truth} = b(x, t) + \\sigma \\varepsilon_0, \\qquad
    m_i = b(x, t) + \\sigma \\varepsilon_i, \\quad i = 1 \\dots N,

with every :math:`\\varepsilon` an independent standard normal and :math:`b` a
deterministic two-scale field that evolves with ``t``. The reference uses **the same**
:math:`\\sigma` as the members and is drawn independently of all of them, which makes the
reference and the members exchangeable: the truth is statistically indistinguishable from
an :math:`(N+1)`-th member. That single property is what pins the analytic targets --

* the rank of the reference among the members is uniform on :math:`\\{0 \\dots N\\}`, so a
  rank histogram is flat and its reliability index is zero up to sampling noise;
* the RMS ensemble spread equals the RMSE of the ensemble mean, up to the finite-ensemble
  factor :math:`\\sqrt{(N+1)/N}`, so the spread-to-skill ratio is one;
* CRPS matches the closed form for a normal predictive distribution.

The deterministic part is not decoration. A field of pure noise would make blur,
coarsening and low-pass degradations indistinguishable, exactly as ``tests/conftest.py``
explains for the synthetic fields there; this generator uses the same two-scale shape so
the miscalibration ladder acts on something with structure.

**Options for other known answers** (``dataset_specs/08_synthetic_ensemble_extensions.md``,
Sect. 3). Each defaults to off, and the defaults reproduce the construction above bitwise. In
full, per field, frame and cell,

.. math::

    \\text{truth} = T\\bigl(b + \\sigma(x)\\,\\eta_0\\bigr), \\qquad
    m_i = T\\bigl(b + \\delta\\,\\sigma(x) + \\sigma(x)\\,\\eta_i\\bigr),

with ``base`` choosing :math:`b`, ``sigma_ratio`` the profile :math:`\\sigma(x)`,
``noise_length`` and ``noise_covariance`` (``member_noise_*`` for the members alone) the
spatial covariance of the unit-variance noise :math:`\\eta`, ``member_offset`` the shift
:math:`\\delta` of the members in units of :math:`\\sigma(x)`, and ``log_amplitude`` the
positive transform :math:`T(v) = e^{\\lambda v}`. The members stay exchangeable with the truth
unless ``member_offset`` or ``member_noise_*`` deliberately break it.

**This is not physical evidence.** It exercises a code path and validates estimators. Its
complexity rank is below every physical dataset for that reason.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

import numpy as np

from degradations._shared.filters import _apply_filter

from ..context import derive_rng
from ..wavenumbers import wavenumber_magnitude
from .base import FIELDS, GridSpec, NanPolicy, Trajectory, register_reader

Base = Literal["two_scale", "case_means", "zero"]
Covariance = Literal["exponential", "rational"]


def base_field(
    shape: tuple[int, ...], n_channels: int, *, phase_t: float = 0.0
) -> np.ndarray:
    """The deterministic part: a periodic, two-scale field that drifts with ``phase_t``.

    Deliberately the same shape of function as ``tests.conftest.synthetic_field`` -- one
    large scale, one small scale, a per-channel phase offset -- so that a smoothing
    degradation bites the small scale first here exactly as it does there.

    Args:
        shape: Spatial extents, in ``(x, y[, z])`` order.
        n_channels: Number of channels; each gets its own phase offset.
        phase_t: Temporal phase, advancing the pattern from frame to frame.

    Returns:
        Array of shape ``(n_channels, *shape)``, float64, periodic on every axis.
    """
    coords = np.meshgrid(*[2 * np.pi * np.arange(n) / n for n in shape], indexing="ij")
    out = np.empty((n_channels, *shape), dtype=np.float64)
    for c in range(n_channels):
        phase = 0.7 * c + phase_t
        large = np.sin(coords[0] + phase)
        small = 0.35 * np.cos(4 * coords[0] + phase)
        for axis in coords[1:]:
            large = large * np.cos(axis + phase)
            small = small + 0.35 * np.sin(3 * axis + phase)
        out[c] = large + small
    return out


@register_reader("synthetic_ensemble")
class SyntheticEnsembleTrajectory(Trajectory):
    """An exchangeable Gaussian ensemble, generated on the fly from a seed."""

    is_ensemble = True
    reads_from_disk = False

    def __init__(
        self,
        path: str | None = None,
        *,
        grid: Sequence[int] = (32, 32),
        n_members: int = 8,
        n_frames: int = 8,
        fields: Sequence[str] = ("density",),
        sigma: float = 0.15,
        omega: float = 0.35,
        seed: int = 0,
        base: Base = "two_scale",
        sigma_ratio: float = 1.0,
        noise_length: float = 0.0,
        noise_covariance: Covariance = "exponential",
        member_noise_length: float | None = None,
        member_noise_covariance: Covariance | None = None,
        member_offset: float = 0.0,
        log_amplitude: float = 0.0,
        nan_policy: NanPolicy = "error",
    ) -> None:
        """Configure the generator.

        Args:
            path: Ignored. Accepted so every reader can be constructed the same way from
                a dataset config; nothing is read from disk.
            grid: Spatial extents, in ``(x, y[, z])`` order.
            n_members: Ensemble size ``N``. At least two, since a spread needs two.
            n_frames: Number of frames to generate.
            fields: Canonical field names to expose.
            sigma: Dispersion of both the members and the reference. The knob that makes
                the ensemble wide or narrow; identical for both by construction, which is
                what exchangeability means here.
            omega: Temporal phase advance per frame of the deterministic part.
            seed: Master seed. Every draw derives from it deterministically.
            base: The deterministic part ``b``: ``two_scale`` is :func:`base_field`;
                ``case_means`` an independent N(0, 1) value per cell, frame and field, the
                case means of Gneiting, Balabdaoui & Raftery (2007, JRSS-B 69(2):243, Table 1);
                ``zero`` none, so the truth is the noise alone.
            sigma_ratio: ``R >= 1``; the noise level varies along the first axis as
                ``sigma * R ** w``, ``w = (1 + sin(2 pi i / n_x)) / 2``, for truth and members
                alike (spec 08, Eq. 3). One keeps it uniform.
            noise_length: Correlation length ``l`` of the noise, in cells; zero makes every
                cell independent. Above zero each noise field is an exactly Gaussian field
                with covariance ``noise_covariance`` in the torus distance between cells.
            noise_covariance: ``exponential``, ``C(r) = exp(-r / l)`` (Scheuerer & Hamill
                2015, MWR 143(4):1321, Eq. 5), or ``rational``, ``C(r) = 1 / (1 + r / l)``
                (their Sect. 3c, model (i)).
            member_noise_length: The members' correlation length, when it differs from the
                truth's. None means as the truth: a calibrated ensemble.
            member_noise_covariance: The members' covariance model; None means as the truth.
            member_offset: Shift ``delta`` of the members' centre, in units of the local
                noise level; zero leaves them centred on the truth's distribution.
            log_amplitude: ``lambda >= 0``; above zero, truth and members pass through
                ``exp(lambda v)``, a positive density whose ranks are unchanged.
            nan_policy: Passed through to the base validation.

        Raises:
            ValueError: On an unknown field, a degenerate ensemble size, a non-positive
                sigma, an unknown base or covariance model, a negative length, a sigma
                ratio below one, a negative log amplitude, or a covariance that is not
                positive definite on this grid.
        """
        unknown = set(fields) - set(FIELDS)
        if unknown:
            raise ValueError(f"unknown canonical field(s): {sorted(unknown)}")
        if n_members < 2:
            raise ValueError(f"n_members must be >= 2 to have a spread, got {n_members}")
        if n_frames < 1:
            raise ValueError(f"n_frames must be >= 1, got {n_frames}")
        if sigma <= 0:
            raise ValueError(f"sigma must be > 0, got {sigma}")
        if base not in ("two_scale", "case_means", "zero"):
            raise ValueError(f"base must be two_scale, case_means or zero, got {base!r}")
        if sigma_ratio < 1:
            raise ValueError(f"sigma_ratio must be >= 1, got {sigma_ratio}")
        if log_amplitude < 0:
            raise ValueError(f"log_amplitude must be >= 0, got {log_amplitude}")
        if not np.isfinite(member_offset):
            raise ValueError(f"member_offset must be finite, got {member_offset}")

        self.path = path
        self.nan_policy = nan_policy
        self._grid_shape = tuple(int(n) for n in grid)
        self._n_members = int(n_members)
        self._n_frames = int(n_frames)
        self._fields = tuple(fields)
        self._sigma = float(sigma)
        self._omega = float(omega)
        self._seed = int(seed)
        self._base = base
        self._sigma_ratio = float(sigma_ratio)
        self._member_offset = float(member_offset)
        self._log_amplitude = float(log_amplitude)
        self._noise = {"truth": (float(noise_length), noise_covariance),
                       "members": (float(noise_length if member_noise_length is None
                                         else member_noise_length),
                                   member_noise_covariance or noise_covariance)}

        # sigma(x) = sigma R^w(x) (spec 08, Eq. 3), shaped to broadcast over (C, *spatial).
        # At R = 1 every entry is sigma exactly, so the default draw is unchanged bitwise.
        n_x = self._grid_shape[0]
        w = 0.5 * (1.0 + np.sin(2 * np.pi * np.arange(n_x) / n_x))
        self._sigma_map = (self._sigma * self._sigma_ratio ** w).reshape(
            n_x, *(1,) * (len(self._grid_shape) - 1))

        # The square root of each covariance's spectrum, the transfer that colours white noise
        # into a Gaussian field with exactly that covariance on the grid (spec 08, Eq. 5):
        # lambda = FFT C(r) are the eigenvalues of the circulant covariance matrix, and
        # A^2 = lambda / mean(lambda) keeps each cell's variance at C(0) = 1. The torus
        # distance in cells is |k| of fmeval.wavenumbers, whose entries are min(i, n - i)
        # per axis.
        distance = wavenumber_magnitude(self._grid_shape)
        self._transfer: dict[str, np.ndarray | None] = {}
        for who, (length, covariance) in self._noise.items():
            if length < 0:
                raise ValueError(f"{who} noise length must be >= 0, got {length}")
            if covariance not in ("exponential", "rational"):
                raise ValueError(f"{who} noise covariance must be exponential or rational, "
                                 f"got {covariance!r}")
            if length == 0:
                self._transfer[who] = None
                continue
            c = (np.exp(-distance / length) if covariance == "exponential"
                 else 1.0 / (1.0 + distance / length))
            eigenvalues = np.real(np.fft.fftn(c))
            if eigenvalues.min() <= 0:
                raise ValueError(
                    f"the {covariance} covariance of length {length} is not positive "
                    f"definite on a {self._grid_shape} periodic grid (smallest eigenvalue "
                    f"{eigenvalues.min():.3g}); choose a shorter length or a larger grid")
            self._transfer[who] = np.sqrt(eigenvalues / eigenvalues.mean())

    # --- the Trajectory contract ------------------------------------------------------

    @property
    def fields(self) -> tuple[str, ...]:
        return self._fields

    @property
    def times(self) -> np.ndarray:
        return np.arange(self._n_frames, dtype=float)

    @property
    def grid(self) -> GridSpec:
        n = len(self._grid_shape)
        return GridSpec(
            shape=self._grid_shape,
            spacing=(1.0,) * n,
            boundary=("periodic",) * n,
            dims=("x", "y", "z")[:n],
            origin=(0.0,) * n,
        )

    @property
    def meta(self) -> dict[str, Any]:
        return {
            "format": "synthetic_ensemble",
            "path": None,
            "n_members": self._n_members,
            "n_frames": self._n_frames,
            "grid": self._grid_shape,
            "sigma": self._sigma,
            "omega": self._omega,
            "seed": self._seed,
            "base": self._base,
            "sigma_ratio": self._sigma_ratio,
            "noise": {who: {"length": length, "covariance": covariance}
                      for who, (length, covariance) in self._noise.items()},
            "member_offset": self._member_offset,
            "log_amplitude": self._log_amplitude,
            "fields": list(self._fields),
        }

    def read_frame(self, t: int, fields: Sequence[str]) -> dict[str, np.ndarray]:
        """Generate one frame: a reference realization and ``N`` members per field."""
        grid = self.grid
        out: dict[str, np.ndarray] = {}
        for name in fields:
            n_channels = FIELDS[name].n_channels(grid.n_spatial)
            if self._base == "two_scale":
                base = base_field(
                    self._grid_shape, n_channels, phase_t=self._omega * float(t)
                )
            elif self._base == "case_means":
                base = derive_rng(self._seed, "case_mean", t, name).standard_normal(
                    (n_channels, *self._grid_shape))
            else:
                base = np.zeros((n_channels, *self._grid_shape))

            # One generator per (member, frame, field), derived from content rather than
            # from call order, so a frame reads identically however the run reaches it. Each
            # draw is white noise, coloured when the option asks for a correlation.
            draws = []
            for key, who in [("reference", "truth")] + [
                    (f"member{i}", "members") for i in range(self._n_members)]:
                white = derive_rng(self._seed, key, t, name).standard_normal(base.shape)
                transfer = self._transfer[who]
                draws.append(white if transfer is None else _apply_filter(white, transfer))
            reference = base + self._sigma_map * draws[0]
            members = (base + self._member_offset * self._sigma_map
                       + self._sigma_map * np.stack(draws[1:]))
            if self._log_amplitude > 0:
                reference = np.exp(self._log_amplitude * reference)
                members = np.exp(self._log_amplitude * members)
            out[name] = reference
            out[f"{name}__members"] = members
        return out

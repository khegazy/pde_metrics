"""Registry of degradation operators.

Same shape and same discovery mechanism as the metric registry, so adding a degradation is
one decorated function in one file::

    @degradation(family="smoothing", severity_name="sigma", severity_units="cells")
    def gaussian_blur(x, severity, *, ctx):
        '''Isotropic Gaussian kernel smoothing, periodic wrap.'''
        return gaussian_filter(x, sigma=severity, mode="wrap", axes=ctx.spatial_axes)

**Operators act on one field at a time**, ``(C, *spatial) -> (C, *spatial)``. That keeps
almost every operator a two-line pure array function. The ladder builder applies the
operator to each requested field with an RNG derived from
``(seed, label, frame_index, field)``, so deterministic operators stay automatically
consistent across fields while stochastic ones get independent draws. An operator that
genuinely needs cross-field access declares ``whole_frame=True``.

Two pieces of metadata exist to stop silent corruption of every Spearman downstream:

``severity_direction``
    Whether damage rises or falls with the severity value. The builder sorts each severity
    list into increasing-damage order, so a low-pass cutoff list written ``[64, 32, 16, 8]``
    gets the right ordinal levels instead of a perfectly inverted ladder.

``ordinal``
    Whether the operator lies on a monotone axis at all. The IN-4 impostor does not; it is
    a pass/fail canary, and folding it in as "level 6" of some family would corrupt every
    rank correlation it touched.

A third, ``preserves``, is a fact rather than a safeguard: what the operator provably leaves
unchanged, measured by a contract test exactly as ``severity_direction`` is. It lets a report
say, beside a measured response, what that degradation left intact.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import Any, Literal

from metrics._registry_core import (
    Accepts,
    check_new,
    discover_package,
    lookup,
    positional_count,
    print_table,
)

Direction = Literal["increasing", "decreasing"]

#: What an operator's severity is expressed relative to. ``None`` means absolute units.
#:
#: ``"energy_above"`` / ``"energy_below"`` -- the severity is the fraction of the field's
#: fluctuation energy the operator destroys, resolved to a cutoff wavenumber against the
#: measured spectrum. The two differ by which side of the cutoff is removed: a low-pass removes
#: what lies *above* it, a high-pass what lies *below*. Declaring the wrong one silently
#: inverts the axis, which is why it is the operator's business to say and not the ladder's to
#: guess: with the sides swapped, "remove 5% of the energy" resolves to the wavenumber holding
#: 5% of it and removes 95% instead.
#: ``"scale"`` -- the severity is a fraction of the field's characteristic scale, resolved to a
#: length in cells.
#:
#: Absolute units are right where the number is already field-independent (a coarsening factor,
#: a displacement in cells) or already relative to something measured (noise as a fraction of
#: the fluctuation RMS). They are wrong for a wavenumber or a smoothing width, because those
#: land in completely different places depending on where the field keeps its energy.
Calibration = Literal["energy_above", "energy_below", "scale"]

#: Coarse grouping, used for plot colour and for the "worst axis" summary. NOT the unit of
#: rank correlation -- that is the ladder entry, since `gaussian_blur` and `median_blur`
#: are separate ordinal axes even though both are `smoothing`.
FAMILIES = (
    "identity",
    "smoothing",
    "spectral",
    "geometric",
    "resolution",
    "stochastic",
    "pointwise",
    "ensemble",
)

#: What an operator can declare it PROVABLY leaves unchanged, a closed vocabulary. Each word is a
#: fact about the operator, verified at every test severity by
#: tests/test_degradation_contract.py::test_declared_preservation_is_true. It is never a statement
#: about any metric: docs/decisions.md "There are no predictions" still holds.
#:
#: ``single_point_statistics``  the multiset of cell values (the sorted values are identical)
#: ``amplitude_spectrum``       |FFT| of the fluctuation at every nonzero wavenumber
#: ``spatial_mean``             the mean of each channel (the zero wavenumber)
#: ``shape``                    the pattern, up to a rigid displacement of any size and an
#:                              increasing affine map of the values
#: ``ensemble_mean``            the member mean of an ``(N, C, *spatial)`` stack, cell by cell;
#:                              the one word an ``ensemble=True`` operator may declare
PRESERVED: tuple[str, ...] = (
    "single_point_statistics", "amplitude_spectrum", "spatial_mean", "shape",
    "ensemble_mean",
)

#: The one word of :data:`PRESERVED` that describes a member stack rather than a field, so the only
#: one an ``ensemble=True`` operator may declare, and one a field operator may not.
ENSEMBLE_WORDS: frozenset[str] = frozenset({"ensemble_mean"})


@dataclass(frozen=True)
class DegradationSpec(Accepts):
    """Everything the harness knows about one degradation operator."""

    name: str
    fn: Callable[..., Any]
    family: str
    severity_name: str
    severity_units: str
    severity_direction: Direction
    calibration: Calibration | None
    ordinal: bool
    stochastic: bool
    fields: tuple[str, ...]
    whole_frame: bool
    doc: str
    module: str
    takes_ctx: bool
    defaults: dict[str, Any] = dc_field(default_factory=dict)
    ensemble: bool = False
    """Whether the operator acts on the whole ``(N, C, *spatial)`` member stack.

    An ordinary operator is applied to each member independently, which is the right
    thing for anything that models a per-member fault -- bias, noise, smoothing. An
    operator that changes the ensemble's *dispersion* cannot work that way, because
    scaling one member about its own value is meaningless; it needs to see the members
    together, and declares this.
    """
    preserves: tuple[str, ...] = ()
    """What the operator provably leaves unchanged, from :data:`PRESERVED`."""
    zero_is_identity: bool = True
    """Whether severity 0 returns the input unchanged; verified both ways by a contract test."""

    def sort_severities(self, severities: Sequence[float]) -> list[float]:
        """Order a severity list by increasing damage.

        A ``decreasing`` operator (low-pass cutoff, say) is sorted descending, so index 0
        is always the mildest severity level whatever order the config author wrote.
        """
        return sorted(severities, reverse=self.severity_direction == "decreasing")

    def describe(self) -> dict[str, Any]:
        """What the decorator declares, as plain data: the catalog entry and run provenance."""
        return {
            "family": self.family, "severity_name": self.severity_name,
            "severity_units": self.severity_units, "severity_direction": self.severity_direction,
            "calibration": self.calibration, "ordinal": self.ordinal,
            "stochastic": self.stochastic, "ensemble": self.ensemble,
            "fields": list(self.fields), "preserves": list(self.preserves),
            "defaults": dict(self.defaults),
        }


REGISTRY: dict[str, DegradationSpec] = {}
CARD_VALIDATOR: Callable[[Any], None] | None = None
"""Optional check run when a degradation is requested by name.

:mod:`fmeval.cards` installs a validator here that reads the degradation's card and refuses
to hand back a spec whose documentation is missing or contradicts the code. It is a hook
rather than a direct import for two reasons: this module would otherwise depend on the
whole harness (and its pandas and matplotlib dependencies) when it needs only numpy, and
validating at *lookup* rather than at *import* means a half-written card in one bundle
cannot break an unrelated run. See ``fmeval/cards/loader.py``.
"""

_IMPORT_ERRORS: dict[str, Exception] = {}
_DISCOVERED = False


def degradation(
    *,
    name: str | None = None,
    family: str = "stochastic",
    severity_name: str = "severity",
    severity_units: str = "",
    severity_direction: Direction = "increasing",
    calibration: Calibration | None = None,
    ordinal: bool = True,
    stochastic: bool = False,
    fields: Sequence[str] = ("*",),
    whole_frame: bool = False,
    ensemble: bool = False,
    preserves: Sequence[str] = (),
    zero_is_identity: bool = True,
) -> Callable[[Callable], Callable]:
    """Register a degradation operator.

    Args:
        name: Registry key. Defaults to the function name.
        family: One of :data:`FAMILIES`. Grouping only, never the correlation unit.
        severity_name: What the severity number means, e.g. ``"sigma"``, ``"cutoff"``.
            Used as the axis label wherever the ladder is plotted.
        severity_units: e.g. ``"cells"``, ``"wavenumber"``, ``"fraction of rms"``.
        severity_direction: ``"increasing"`` if larger severity means more damage,
            ``"decreasing"`` if smaller does.
        calibration: What the severity is relative to, or None for absolute units. See
            :data:`Calibration`. A calibrated severity is resolved per field against a
            measured spectrum, so the same config number means the same thing on a smooth
            field and a broadband one.
        ordinal: Whether this operator participates in monotonicity and Spearman. False
            for the IN-4 canary.
        stochastic: Whether to redraw the RNG per frame. A frozen noise field would be a
            systematic bias rather than noise.
        fields: Canonical field names it can act on; ``("*",)`` means any.
        whole_frame: Receive the whole ``dict[str, ndarray]`` instead of one array. For
            the rare operator needing cross-field access.
        ensemble: Receive one field's ``(N, C, *spatial)`` member stack instead of a
            single array. For an operator that changes the ensemble's dispersion, which
            cannot be expressed member by member. Mutually exclusive with
            ``whole_frame``. Operators that do not declare it are applied to each member
            independently when the frame carries an ensemble.
        preserves: What the operator provably leaves unchanged, words from :data:`PRESERVED`.
            Verified by measurement at every test severity; declare only what holds on any
            field, never what you expect a metric to do.
        zero_is_identity: Whether the config-facing severity 0 returns the input unchanged.
            True for most operators; False where 0 still damages the field -- a Butterworth
            filter's soft edge attenuates even at the mildest cutoff -- or carries no meaning,
            as for the probes. Verified both ways by the contract test, so it cannot be used to
            skip a check.

    Returns:
        The undecorated function.
    """

    def _decorate(fn: Callable) -> Callable:
        key = name or fn.__name__
        check_new(REGISTRY, key, "degradation", fn.__module__)
        if family not in FAMILIES:
            raise ValueError(
                f"{key}: unknown family {family!r}; expected one of {FAMILIES}"
            )
        unknown = sorted(set(preserves) - set(PRESERVED))
        if unknown:
            raise ValueError(
                f"{key}: preserves={unknown} is outside the vocabulary PRESERVED = {PRESERVED}"
            )
        words = set(preserves)
        misplaced = sorted(words - ENSEMBLE_WORDS if ensemble else words & ENSEMBLE_WORDS)
        if misplaced:
            raise ValueError(
                f"{key}: preserves={misplaced} describes "
                f"{'a field' if ensemble else 'a member stack'}, but the operator "
                f"{'acts on the member stack' if ensemble else 'acts on one field'}"
            )
        if ensemble and whole_frame:
            raise ValueError(
                f"{key}: declares both ensemble and whole_frame; one receives the member "
                "stack of a single field, the other the field mapping of a whole frame"
            )

        params = inspect.signature(fn).parameters
        n_pos = positional_count(fn)
        if n_pos != 2:
            raise TypeError(
                f"{key}: a degradation takes 2 positional arguments (field, severity), "
                f"found {n_pos}"
            )

        REGISTRY[key] = DegradationSpec(
            name=key,
            fn=fn,
            family=family,
            severity_name=severity_name,
            severity_units=severity_units,
            severity_direction=severity_direction,
            calibration=calibration,
            ordinal=ordinal,
            stochastic=stochastic,
            fields=tuple(fields),
            whole_frame=whole_frame,
            doc=(fn.__doc__ or "").strip(),
            module=fn.__module__,
            takes_ctx="ctx" in params,
            # Per-entry options are the operator's keyword-only parameters, and their defaults
            # are the signature's, so each default is written once. A ladder entry overrides
            # them with `options:` in config.
            defaults={p.name: p.default for p in params.values()
                      if p.kind == p.KEYWORD_ONLY and p.name != "ctx"
                      and p.default is not p.empty},
            ensemble=ensemble,
            preserves=tuple(word for word in PRESERVED if word in preserves),
            zero_is_identity=zero_is_identity,
        )
        return fn

    return _decorate


def discover(force: bool = False) -> dict[str, Exception]:
    """Import every module under ``degradations/`` so the decorators fire.

    Returns the import failures, collected rather than raised; see
    :func:`metrics._registry_core.discover_package`.
    """
    global _DISCOVERED
    if _DISCOVERED and not force:
        return _IMPORT_ERRORS
    discover_package("degradations", _IMPORT_ERRORS)
    _DISCOVERED = True
    return _IMPORT_ERRORS


def get(name: str) -> DegradationSpec:
    """Look up a degradation by name, running discovery first if needed, and validate it."""
    return lookup(name, REGISTRY, "degradation", discover, CARD_VALIDATOR)


def available() -> list[str]:
    """Names of every registered degradation, after discovery."""
    discover()
    return sorted(REGISTRY)


def _main() -> None:
    """Print the registry as a table. Entry point for ``python -m degradations``."""
    discover()
    rows = [
        (
            s.name,
            s.family,
            f"{s.severity_name} [{s.severity_units}]" if s.severity_units
            else s.severity_name,
            s.calibration or "absolute",
            s.severity_direction,
            "yes" if s.ordinal else "NO (canary)",
            "yes" if s.stochastic else "-",
            ",".join(s.fields),
            ",".join(s.preserves) or "-",
        )
        for s in sorted(REGISTRY.values(), key=lambda s: (s.family, s.name))
    ]
    print_table(("degradation", "family", "severity", "relative to", "direction", "ordinal",
                 "stoch", "fields", "preserves"), rows, _IMPORT_ERRORS,
                "no degradations registered")

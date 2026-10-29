"""Registry of metric functions.

A metric is an ordinary function decorated with :func:`metric`. The decorator records
metadata and returns the function *unwrapped*, so metrics stay directly importable and
testable without the harness and carry no per-call indirection.

Three arities are supported:

* ``arity="pairwise"`` -- ``fn(reference, candidate)``, both ``(C, *spatial)``
* ``arity="single"``   -- ``fn(x)``, ``(C, *spatial)``
* ``arity="ensemble"`` -- ``fn(reference, members)``, ``(C, *spatial)`` and
  ``(N, C, *spatial)``: one reference realization and the ensemble standing in for a
  predictive distribution over it. Same positional count as ``pairwise``, so the arity
  rather than the signature is what distinguishes them.

Most metrics are best at zero. A metric whose best value is elsewhere -- the spread-to-
skill ratio, which is calibrated at one and wrong in both directions -- declares
``target=``, and the analysis layer orients its ordering statistics by distance from that
target instead of assuming monotone damage. The metric keeps reporting the quantity the
literature reports.

If a function additionally declares a keyword-only parameter named ``ctx``, the pipeline
passes a :class:`~fmeval.context.FieldContext` carrying grid spacing, periodicity, the
field name and the physical time. Detection happens once, here, via :mod:`inspect`, so the
common case needs no boilerplate.

A metric returns one float, the number the literature reports. The object behind that number
is its **companion**, declared with :func:`companion`: a per-cell map (``kind="field"``) whose
declared ``reduction`` gives back the number, which the contract test verifies as
``R(map(a, b)) == metric(a, b)``; or a curve on a named coordinate (``kind="curve"``), the
literature's own values, which the pipeline stores on every result row and the analysis
evaluates coordinate by coordinate beside the panel.
"""

from __future__ import annotations

import dataclasses
import inspect
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

from metrics._registry_core import (
    Accepts,
    check_new,
    discover_package,
    lookup,
    positional_count,
    print_table,
)

Arity = Literal["pairwise", "single", "ensemble"]

#: Positional arguments each arity's function must declare.
ARITY_POSITIONAL: dict[str, int] = {"pairwise": 2, "single": 1, "ensemble": 2}
Cost = Literal["cheap", "moderate", "expensive"]
Measures = Literal["error", "calibration"]
CompanionKind = Literal["field", "curve"]

#: How a pointwise map reduces to the metric's scalar value. ``C`` is the channel count of
#: the *input* field, because maps are summed over channels before reduction.
REDUCTIONS: dict[str, Callable[[np.ndarray, int], float]] = {
    "mean": lambda m, c: float(m.mean() / c),
    "sum": lambda m, c: float(m.sum()),
    "sqrt_mean": lambda m, c: float(np.sqrt(m.mean() / c)),
}


@dataclass(frozen=True)
class Companion:
    """The object behind a metric's number, declared with :func:`companion`."""

    fn: Callable[..., Any]
    kind: CompanionKind
    """``"field"``: a per-cell map, ``(*spatial)``, stored on chosen frames. ``"curve"``: a pair
    ``(coordinates, values)``, stored on every row."""
    coordinate: tuple[str, str] | None
    """``(name, units)`` of a curve's coordinate; None for a field map."""
    one_field: bool
    """Whether the companion takes one field where its metric takes two: a property of one
    field, called on the candidate of every variant, which on the clean level is the reference
    (the member mean on an ensemble dataset, whose ladder degrades the prediction). Inferred from
    the signature."""
    takes_ctx: bool

    def describe(self) -> dict[str, Any]:
        return {"kind": self.kind, "coordinate": list(self.coordinate or []) or None,
                "one_field": self.one_field}


@dataclass(frozen=True)
class MetricSpec(Accepts):
    """Everything the harness knows about one metric."""

    name: str
    fn: Callable[..., Any]
    arity: Arity
    fields: tuple[str, ...]
    differentiable: bool
    cost: Cost
    higher_is_better: bool
    symmetric: bool
    #: Declared, never inferred; see the ``monotone_under_smoothing`` argument of :func:`metric`.
    monotone_under_smoothing: bool
    units: str
    doc: str
    module: str
    takes_ctx: bool
    reduction: str
    companion: Companion | None = None
    target: float | None = None
    """The value a perfectly calibrated prediction attains, if it is not zero.

    ``None`` for the usual case, where the metric is an error and zero is best. Set to
    ``1.0`` by the spread-to-skill ratio, whose response to damage is U-shaped rather
    than monotone.
    """
    measures: Measures = "error"
    """What kind of wrongness this metric sees.

    ``"error"`` metrics fall to zero as the prediction approaches the reference.
    ``"calibration"`` metrics judge whether an ensemble's *dispersion* is honest, and do
    not: an ensemble collapsed onto the exact truth is maximally overconfident, so a
    calibration metric is right to score it badly. The contract tests use this to decide
    which generic assumptions apply.
    """
    requires_periodic: bool = False
    """Whether the metric assumes every axis wraps -- a Fourier transform, a spectral
    derivative, a wrap-around increment. Such a metric is not run on a dataset with a
    non-periodic axis (:func:`fmeval.pipeline.run`)."""

    def reduce(self, map_: np.ndarray, n_channels: int) -> float:
        """Apply this metric's declared reduction to a pointwise map."""
        return REDUCTIONS[self.reduction](map_, n_channels)

    def describe(self) -> dict[str, Any]:
        """What the decorator declares, as plain data: the catalog entry and run provenance."""
        return {
            "arity": self.arity, "fields": list(self.fields),
            "units": self.units, "cost": self.cost, "differentiable": self.differentiable,
            "symmetric": self.symmetric, "higher_is_better": self.higher_is_better,
            "target": self.target, "measures": self.measures, "reduction": self.reduction,
            "companion": None if self.companion is None else self.companion.describe(),
            "requires_periodic": self.requires_periodic,
        }


REGISTRY: dict[str, MetricSpec] = {}
CARD_VALIDATOR: Callable[[Any], None] | None = None
"""Optional check run when a metric is requested by name.

:mod:`fmeval.cards` installs a validator here that reads the metric's card and refuses
to hand back a spec whose documentation is missing or contradicts the code. It is a hook
rather than a direct import for two reasons: this module would otherwise depend on the
whole harness (and its pandas and matplotlib dependencies) when it needs only numpy, and
validating at *lookup* rather than at *import* means a half-written card in one bundle
cannot break an unrelated run. See ``fmeval/cards/loader.py``.
"""

_IMPORT_ERRORS: dict[str, Exception] = {}


def metric(
    *,
    name: str | None = None,
    arity: Arity = "pairwise",
    fields: Sequence[str] = ("*",),
    differentiable: bool = True,
    cost: Cost = "cheap",
    higher_is_better: bool = False,
    symmetric: bool = True,
    monotone_under_smoothing: bool = True,
    units: str = "field",
    reduction: str = "mean",
    target: float | None = None,
    measures: Measures = "error",
    requires_periodic: bool = False,
) -> Callable[[Callable], Callable]:
    """Register a metric function under ``name`` (defaults to the function name).

    Args:
        name: Registry key, and the metric's identity everywhere: the directory name of
            its bundle, the key in its card, and what users type in ``metrics=[...]``.
            Defaults to ``fn.__name__``.
        arity: ``"pairwise"`` for ``fn(reference, candidate)``, ``"single"`` for
            ``fn(x)``, ``"ensemble"`` for ``fn(reference, members)`` with members
            ``(N, C, *spatial)``.
        fields: Canonical field names this metric accepts; ``("*",)`` means any.
        differentiable: Whether it could serve as a training loss. Declared, not inferred.
        cost: Advisory tier; the pipeline warns on expensive metrics over many frames.
        higher_is_better: Whether larger values mean a better match.
        symmetric: Pairwise only. Enables the symmetry contract test.
        monotone_under_smoothing: Whether the value is expected to change monotonically
            as the field is smoothed. True for error metrics and for energy-like
            single-field quantities such as enstrophy. Set it False only for a statistic
            of distribution shape, which carries no such guarantee: measured on the real
            trajectory, increment flatness rises and falls under increasing blur on all
            three fields. The contract test checks the declaration both ways, so False
            asserts non-monotonicity rather than skipping the check, and a metric cannot
            use it to slip past a gate it would otherwise have passed.
        units: Free text, e.g. ``"field"``, ``"field^2"``, ``"dimensionless"``.
        reduction: How a pointwise map reduces to the scalar. Key of :data:`REDUCTIONS`.
        target: The value a perfectly calibrated prediction attains, when that is not
            zero. Mutually exclusive with ``higher_is_better``: they are two different
            models of what "better" means.
        measures: ``"error"`` (default) if the metric falls to zero as the prediction
            approaches the reference, ``"calibration"`` if it judges the honesty of an
            ensemble's dispersion instead, where a collapsed ensemble is the worst case
            rather than the best.
        requires_periodic: Whether the metric assumes every spatial axis wraps: it takes a
            Fourier transform, a spectral derivative or a wrap-around difference. Declared,
            never inferred, and checked against the source by a contract test. Such a metric
            is not run on a dataset with a non-periodic axis.

    Returns:
        The undecorated function, so it stays a plain callable.

    Raises:
        ValueError: On a duplicate name, an unknown reduction, or a contradictory or
            non-finite target.
        TypeError: If the positional-argument count does not match ``arity``.
    """

    def _decorate(fn: Callable) -> Callable:
        key = name or fn.__name__
        check_new(REGISTRY, key, "metric", fn.__module__)
        if reduction not in REDUCTIONS:
            raise ValueError(
                f"{key}: unknown reduction {reduction!r}; expected one of {sorted(REDUCTIONS)}"
            )
        if target is not None:
            if not np.isfinite(target):
                raise ValueError(
                    f"{key}: target must be finite, got {target!r}; a non-finite target "
                    "would silently disable the orientation it exists for"
                )
            if higher_is_better:
                raise ValueError(
                    f"{key}: declares both target={target!r} and higher_is_better; these "
                    "are different models of what 'better' means, so pick one"
                )

        takes_ctx = "ctx" in inspect.signature(fn).parameters
        n_pos = positional_count(fn)
        expected = ARITY_POSITIONAL[arity]
        if n_pos != expected:
            raise TypeError(
                f"{key}: arity={arity!r} needs {expected} positional argument(s), "
                f"found {n_pos}"
            )

        REGISTRY[key] = MetricSpec(
            name=key,
            fn=fn,
            arity=arity,
            fields=tuple(fields),
            differentiable=differentiable,
            cost=cost,
            higher_is_better=higher_is_better,
            symmetric=symmetric,
            monotone_under_smoothing=monotone_under_smoothing,
            units=units,
            doc=(fn.__doc__ or "").strip(),
            module=fn.__module__,
            takes_ctx=takes_ctx,
            reduction=reduction,
            target=None if target is None else float(target),
            measures=measures,
            requires_periodic=requires_periodic,
        )
        return fn

    return _decorate


def companion(*, of: str, kind: CompanionKind = "field",
              coordinate: tuple[str, str] | None = None) -> Callable[[Callable], Callable]:
    """Attach the object behind a metric's number to an already-registered metric.

    One companion per metric. A second number from the literature is a sibling bundle that
    imports the function, as ``rmse`` imports ``mse``.

    * ``kind="field"``: a per-cell density taking the metric's arguments and returning
      ``(*spatial)``, the channel axis summed away. Reducing it with the metric's declared
      ``reduction`` must reproduce the metric's number; the contract test enforces that. Stored
      on the frames ``report.error_map`` names.
    * ``kind="curve"``: returns ``(coordinates, values)``, two 1-D arrays of one length with fixed
      coordinates and the literature's own values, untransformed. It takes either the metric's
      arguments, and is then itself a comparison, or one field where the metric takes two, and is
      then a property of one field. The pipeline calls it before the metric on every row, stores
      the curve, and hands it to the metric in ``ctx.cache[COMPANION_KEY]``
      (:data:`fmeval.context.COMPANION_KEY`), so a metric that reads it there computes the curve
      once per row.

    Args:
        of: Name of the metric. Must already be registered, so the companion is defined *after*
            its metric in the same module.
        kind: ``"field"`` or ``"curve"``.
        coordinate: ``(name, units)`` of a curve's coordinate, e.g. ``("separation", "cells")``;
            required for a curve and refused for a field map.

    Raises:
        ValueError: If the metric is unknown or already has a companion, or the kind and the
            coordinate disagree.
        TypeError: If the positional-argument count fits neither form.
    """

    def _decorate(fn: Callable) -> Callable:
        if of not in REGISTRY:
            raise ValueError(
                f"companion(of={of!r}): metric is not registered; define the companion "
                "after the metric it belongs to"
            )
        spec = REGISTRY[of]
        if spec.companion is not None:
            raise ValueError(f"metric {of!r} already has a companion")
        if kind not in ("field", "curve"):
            raise ValueError(f"companion(of={of!r}): unknown kind {kind!r}")
        if (kind == "curve") != (coordinate is not None):
            raise ValueError(
                f"companion(of={of!r}): a curve names its coordinate as (name, units) and a "
                f"field map does not; got kind={kind!r}, coordinate={coordinate!r}"
            )
        n_pos, expected = positional_count(fn), ARITY_POSITIONAL[spec.arity]
        allowed = {expected, 1} if kind == "curve" and spec.arity == "pairwise" else {expected}
        if n_pos not in allowed:
            raise TypeError(
                f"companion(of={of!r}): takes {n_pos} positional argument(s); a {kind} "
                f"companion of a {spec.arity} metric takes {sorted(allowed)}"
            )
        REGISTRY[of] = dataclasses.replace(spec, companion=Companion(
            fn=fn, kind=kind, coordinate=None if coordinate is None else tuple(coordinate),
            one_field=n_pos < expected, takes_ctx="ctx" in inspect.signature(fn).parameters))
        return fn

    return _decorate


def discover(force: bool = False) -> dict[str, Exception]:
    """Import every module under ``metrics/`` so the decorators fire; returns the import
    failures. See :func:`metrics._registry_core.discover_package`."""
    return discover_package("metrics", _IMPORT_ERRORS, force)


def get(name: str) -> MetricSpec:
    """Look up a metric by name, running discovery first if needed, and validate its card."""
    return lookup(name, REGISTRY, "metric", discover, CARD_VALIDATOR)


def available() -> list[str]:
    """Names of every registered metric, after discovery."""
    discover()
    return sorted(REGISTRY)


def _main() -> None:
    """Print the registry as a table. Entry point for ``python -m metrics``."""
    discover()
    rows = [
        (
            s.name,
            s.arity,
            ",".join(s.fields),
            s.units,
            s.cost,
            s.companion.kind if s.companion else "-",
            "yes" if s.differentiable else "-",
        )
        for s in sorted(REGISTRY.values(), key=lambda s: s.name)
    ]
    print_table(("metric", "arity", "fields", "units", "cost", "companion", "diff'able"),
                rows, _IMPORT_ERRORS, "no metrics registered")

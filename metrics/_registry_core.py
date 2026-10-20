"""Machinery shared by the metric and the degradation registries.

Both registries are a module-level ``REGISTRY`` dict filled by a decorator, discovered by
importing every bundle, and looked up by name with the card validator applied. Everything
that is the same between them is here once; each registry keeps its own spec, decorator,
vocabulary and listing columns.

This module lives in ``metrics/`` (its leading underscore keeps discovery out of it) rather
than in ``fmeval``, deliberately. Importing ``fmeval`` runs ``fmeval/__init__``, which installs
the card validator onto both registry modules; if a registry imported ``fmeval`` while it was
itself still being imported, its own ``CARD_VALIDATOR = None`` would then overwrite the hook,
and card validation would be silently off for every ``evaluate.py`` run while the test suite
still passed. ``tests/test_robustness.py`` pins that the validator survives ``import evaluate``.
The registries must also stay importable without the harness and its dependencies.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from collections.abc import Callable, Mapping, Sequence
from typing import Any


class Accepts:
    """Mixin for a spec that declares the canonical ``fields`` it works on."""

    fields: tuple[str, ...]

    def accepts(self, field: str) -> bool:
        """Whether this plugin works on ``field``; ``("*",)`` means any field."""
        return self.fields == ("*",) or field in self.fields


def positional_count(fn: Callable) -> int:
    """How many positional parameters ``fn`` declares, which is what its arity is checked on."""
    return sum(p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
               for p in inspect.signature(fn).parameters.values())


def check_new(registry: Mapping[str, Any], key: str, kind: str, module: str) -> None:
    """Refuse a second registration under one name, naming both modules."""
    if key in registry:
        raise ValueError(f"duplicate {kind} {key!r}: {registry[key].module} vs {module}")


#: Packages already walked by :func:`discover_package`, so a second call is free.
_WALKED: set[str] = set()


def discover_package(package: str, errors: dict[str, Exception],
                     force: bool = False) -> dict[str, Exception]:
    """Import every module under ``package`` so its decorators fire, collecting failures.

    Import failures are collected rather than raised: one colleague's broken work-in-progress
    file must not abort everyone's run. The collected errors surface in :func:`lookup`'s message
    when a lookup actually misses.

    Args:
        package: Top-level package to walk, ``"metrics"`` or ``"degradations"``.
        errors: The registry's own record of import failures, filled in place.
        force: Walk again even if this package has already been walked.

    Returns:
        ``errors``: module name to the exception it raised, empty if all imported.
    """
    if package in _WALKED and not force:
        return errors
    root = importlib.import_module(package)
    for mod in pkgutil.walk_packages(root.__path__, prefix=f"{package}."):
        # Every component after the package name is checked, not just the last one: a bundle
        # directory named `_template` must not be entered even though the modules inside it
        # have ordinary names. Leading underscores mark templates and shared helpers; `test_`
        # marks the tests that live inside each bundle, which would otherwise drag pytest into
        # every evaluation run.
        parts = mod.name.split(".")[1:]
        if any(p.startswith(("_", "test_")) for p in parts) or parts[-1] == "registry":
            continue
        try:
            importlib.import_module(mod.name)
        except Exception as exc:  # noqa: BLE001 - deliberately broad, see docstring
            errors[mod.name] = exc
    _WALKED.add(package)
    return errors


def lookup(name: str, registry: Mapping[str, Any], kind: str,
           discover: Callable[[], dict[str, Exception]],
           validator: Callable[[Any], None] | None) -> Any:
    """Look ``name`` up, discovering first if needed, and validate its card.

    Raises:
        KeyError: If no such plugin exists. The message lists what is available and, if any
            bundle failed to import, what went wrong with it.
    """
    if name not in registry:
        errors = discover()
        if name not in registry:
            hint = ""
            if errors:
                broken = ", ".join(f"{m}: {e!r}" for m, e in errors.items())
                hint = f"\n(modules that failed to import: {broken})"
            raise KeyError(f"unknown {kind} {name!r}; available: {sorted(registry)}{hint}")
    spec = registry[name]
    if validator is not None:
        validator(spec)
    return spec


def print_table(head: Sequence[str], rows: Sequence[Sequence[str]],
                errors: Mapping[str, Exception], empty: str) -> None:
    """Print a registry listing as aligned columns, then any bundle that failed to import."""
    if not rows:
        print(empty)
        return
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(head)]
    line = "  ".join(h.ljust(w) for h, w in zip(head, widths))
    print(line)
    print("-" * len(line))
    for r in rows:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)))
    for mod, exc in errors.items():
        print(f"\n!! {mod} failed to import: {exc!r}")

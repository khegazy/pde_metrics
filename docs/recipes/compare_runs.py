"""Compare two ``evaluate.py`` invocations, file by file, at a stated numerical tolerance.

    python docs/recipes/compare_runs.py BEFORE_FOLDER AFTER_FOLDER [--rtol 1e-12]

Each argument is one run folder, e.g. ``<dir>/before/comparison_<stamp>``; every sibling
folder written by the same invocation (the per-metric folders) is compared too. Exit status
0 means every file agrees, 1 means a difference was printed. See ``verify-a-refactor.md``.

What "agrees" means:

* ``results.csv`` is compared row by row, keyed so that row order cannot hide a change, on
  every column but ``wall_time_s``. Numbers must agree to ``np.isclose(rtol, atol=0)``, with
  NaN equal only to NaN. Text is compared exactly, which also catches a type change such as
  ``True`` becoming ``1.0``. Cells are read as text and parsed with Python's correctly
  rounded ``float``: pandas' default parser is not round-trip exact and hid a one-ulp change
  in half the cells of a real file.
* Every other CSV row by row, the same way; ``error_maps.npz`` array by array.
* ``run_meta.json`` leaf by leaf, without the keys that differ between two runs of the same
  code (git state, the folder stamp, wall-clock timings, the host, the config hash); ``--ignore``
  drops further keys a change adds or alters on purpose, which the change must declare.
* Every other file byte for byte, after replacing each side's results directory with one
  placeholder and wall-clock stamps with another. A file present on one side only is a
  difference, so a file this script does not know about is still checked.

The largest relative difference among numbers that were not bitwise equal is printed, so a
pass that relied on the tolerance says so.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KEYS = ["metric", "field", "degradation", "level", "frame_index", "variant_label"]
EXCLUDED_COLUMNS = {"wall_time_s"}
VOLATILE_META = {"git", "run_id", "timings", "host", "config_hash"}
_STAMP = re.compile(r"\d{4}-\d\d-\d\d \d\d:\d\d(:\d\d)?")


class Comparison:
    """One before/after comparison: the tolerance, the placeholders, and what it has seen."""

    def __init__(self, rtol: float, roots: tuple[Path, Path], ignore: set[str],
                 skip_images: bool) -> None:
        self.rtol, self.roots, self.ignore, self.skip_images = rtol, roots, ignore, skip_images
        self.max_rel, self.n_inexact = 0.0, 0

    # --- numbers --------------------------------------------------------------------

    def _note(self, b: np.ndarray, a: np.ndarray) -> None:
        moved = np.isfinite(b) & np.isfinite(a) & (b != a)
        if moved.any():
            rel = np.abs(a[moved] - b[moved]) / np.maximum(np.abs(b[moved]), np.abs(a[moved]))
            self.max_rel = max(self.max_rel, float(rel.max()))
            self.n_inexact += int(moved.sum())

    def _close(self, b: np.ndarray, a: np.ndarray) -> np.ndarray:
        self._note(b, a)
        return np.isclose(b, a, rtol=self.rtol, atol=0.0, equal_nan=True)

    def text(self, value: str, side: int) -> str:
        """A recorded string with this side's results directory and clock stamps replaced."""
        return _STAMP.sub("<STAMP>", value.replace(str(self.roots[side]), "<RESULTS>"))

    # --- one file -------------------------------------------------------------------

    def cells(self, b: pd.DataFrame, a: pd.DataFrame, where: str) -> list[str]:
        """Aligned frames of raw text: numeric columns at tolerance, everything else exact."""
        out = []
        for column in b.columns:
            if column in EXCLUDED_COLUMNS:
                continue
            xb, xa = b[column].astype(str), a[column].astype(str)
            try:
                nb, na = ([float(v) if v else np.nan for v in x] for x in (xb, xa))
                # "16" -> "16.0" or "True" -> "1.0" is a change of type, not of rounding.
                kind = [x.str.contains(r"[.eEn]", regex=True) | (x == "") for x in (xb, xa)]
                same = self._close(np.array(nb), np.array(na)) & (kind[0] == kind[1]).to_numpy()
            except ValueError:
                same = np.array([self.text(u, 0) == self.text(v, 1) for u, v in zip(xb, xa)])
            bad = np.flatnonzero(~same)
            if len(bad):
                i = bad[0]
                out.append(f"{where} column {column!r}: {len(bad)} of {len(b)} differ, "
                           f"e.g. {xb.iloc[i]!r} -> {xa.iloc[i]!r}")
        return out

    def results(self, before: Path, after: Path) -> list[str]:
        raw = [pd.read_csv(p, dtype=str, keep_default_na=False) for p in (before, after)]
        if list(raw[0].columns) != list(raw[1].columns):
            return [f"columns differ: {list(raw[0].columns)} vs {list(raw[1].columns)}"]
        repeated = [f"{side}: {n} rows repeat a key" for side, df in zip(("before", "after"), raw)
                    if (n := int(df.duplicated(KEYS).sum()))]
        if repeated:
            return repeated
        out = []
        if len(raw[0]) == len(raw[1]) and not raw[0][KEYS].equals(raw[1][KEYS]):
            out.append("row order differs (same keys, different sequence)")
        merged = raw[0].merge(raw[1], on=KEYS, how="outer", suffixes=("_b", "_a"),
                              indicator=True)
        for side, label in (("left_only", "missing from after"), ("right_only", "new in after")):
            rows = merged[merged["_merge"] == side]
            if len(rows):
                out.append(f"{label}: {len(rows)} rows, e.g. {rows[KEYS].head(3).values.tolist()}")
        both = merged[merged["_merge"] == "both"]
        columns = [c for c in raw[0].columns if c not in KEYS]
        b, a = (both[[f"{c}{s}" for c in columns]].fillna("").set_axis(columns, axis=1)
                for s in ("_b", "_a"))
        return out + self.cells(b, a, "results")

    def csv(self, before: Path, after: Path) -> list[str]:
        raw = [pd.read_csv(p, dtype=str, keep_default_na=False) for p in (before, after)]
        if list(raw[0].columns) != list(raw[1].columns) or len(raw[0]) != len(raw[1]):
            return [f"shape or columns differ: {raw[0].shape} vs {raw[1].shape}"]
        return self.cells(raw[0], raw[1], before.name)

    def json(self, before: Path, after: Path, drop: set[str]) -> list[str]:
        def leaves(path: Path, side: int) -> dict[str, object]:
            data = json.loads(path.read_text())
            if isinstance(data, dict):
                data = {k: v for k, v in data.items() if k not in drop}
            return {k: (self.text(v, side) if isinstance(v, str) else v)
                    for k, v in _flatten(data).items() if not k.endswith("duration_s")}

        b, a = leaves(before, 0), leaves(after, 1)
        out = []
        for key in sorted(b.keys() | a.keys()):
            x, y = b.get(key, "<absent>"), a.get(key, "<absent>")
            numeric = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (x, y))
            if numeric and type(x) is type(y):
                if not self._close(np.array([float(x)]), np.array([float(y)]))[0]:
                    out.append(f"{key}: {x!r} -> {y!r}")
            elif x != y or type(x) is not type(y):
                out.append(f"{key}: {x!r} -> {y!r}")
        return out

    def maps(self, before: Path, after: Path) -> list[str]:
        with np.load(before) as nb, np.load(after) as na:
            out = [f"keys only {side}: {sorted(keys)[:3]} ({len(keys)})"
                   for side, keys in (("before", set(nb.files) - set(na.files)),
                                      ("after", set(na.files) - set(nb.files))) if keys]
            for key in sorted(set(nb.files) & set(na.files)):
                x, y = nb[key], na[key]
                if x.dtype != y.dtype or x.shape != y.shape:
                    out.append(f"{key}: {x.dtype}{x.shape} vs {y.dtype}{y.shape}")
                elif not self._close(x.ravel().astype(float), y.ravel().astype(float)).all():
                    out.append(f"{key}: values differ beyond rtol={self.rtol}")
        return out

    def raw(self, before: Path, after: Path) -> list[str]:
        b, a = before.read_bytes(), after.read_bytes()
        if b == a:
            return []
        try:
            lines = [self.text(t.decode(), side).splitlines() for side, t in enumerate((b, a))]
        except UnicodeDecodeError:
            return [f"bytes differ ({len(b)} vs {len(a)} bytes)"]
        if lines[0] == lines[1]:
            return []
        diff = list(difflib.unified_diff(*lines, lineterm="", n=0))[2:6]
        return ["text differs"] + [f"    {line[:160]}" for line in diff]

    def file(self, before: Path, after: Path) -> list[str]:
        name = before.name
        if name == "config_hash.txt" or (self.skip_images and before.suffix in {".pdf", ".png"}):
            return []      # a hash of the config, which is compared itself; or rendered pixels
        if name.startswith("results.csv"):
            return self.results(before, after)
        if name.endswith(".csv"):
            return self.csv(before, after)
        if name.endswith(".json"):
            drop = VOLATILE_META | self.ignore if name == "run_meta.json" else set()
            return self.json(before, after, drop)
        if name.endswith(".npz"):
            return self.maps(before, after)
        return self.raw(before, after)

    def folder(self, before: Path, after: Path) -> list[str]:
        files = [{p.relative_to(r).as_posix(): p for p in r.rglob("*") if p.is_file()}
                 for r in (before, after)]
        out = [f"{path}: only {side}"
               for side, mine, other in (("before", *files), ("after", files[1], files[0]))
               for path in sorted(mine.keys() - other.keys())]
        for path in sorted(files[0].keys() & files[1].keys()):
            out += [f"{path}: {line}" for line in self.file(files[0][path], files[1][path])]
        return out


def _flatten(obj, prefix: str = "") -> dict[str, object]:
    """Nested JSON as ``{dotted.path: leaf}``, so a difference names its exact location."""
    items = (obj.items() if isinstance(obj, dict)
             else enumerate(obj) if isinstance(obj, list) else None)
    if items is None:
        return {prefix.rstrip("."): obj}
    out: dict[str, object] = {}
    for key, value in items:
        out.update(_flatten(value, f"{prefix}{key}."))
    return out or {prefix.rstrip("."): obj}


def invocation(folder: Path) -> dict[str, Path]:
    """Every run folder the invocation that wrote ``folder`` wrote, keyed by its name."""
    name, _, stamp = folder.name.rpartition("_")
    if not (name and stamp.isdigit() and (folder / "data").is_dir()):
        raise SystemExit(f"{folder} is not a run folder named <name>_<stamp> holding data/")
    return {p.name.rpartition("_")[0]: p for p in sorted(folder.parent.glob(f"*_{stamp}"))
            if (p / "data").is_dir()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--rtol", type=float, default=1e-12)
    parser.add_argument("--ignore", nargs="*", default=[],
                        help="further run_meta.json keys the change alters on purpose")
    parser.add_argument("--folder-only", action="store_true",
                        help="compare the two folders alone, e.g. two rendered reports")
    parser.add_argument("--skip-images", action="store_true",
                        help="skip PDF/PNG files, whose bytes embed dates")
    args = parser.parse_args(argv)
    before, after = args.before.resolve(), args.after.resolve()
    runs = ([{"folder": before}, {"folder": after}] if args.folder_only
            else [invocation(before), invocation(after)])
    check = Comparison(args.rtol, (before.parent, after.parent), set(args.ignore),
                       args.skip_images)
    differences = [f"run folder {name}_*: only {side}"
                   for side, mine, other in (("before", *runs), ("after", runs[1], runs[0]))
                   for name in sorted(mine.keys() - other.keys())]
    for name in sorted(runs[0].keys() & runs[1].keys()):
        found = check.folder(runs[0][name], runs[1][name])
        print(f"{name}: {'identical' if not found else f'{len(found)} differences'}")
        differences += [f"{name}/{line}" for line in found]
    for line in differences:
        print("  " + line)
    print(f"largest relative difference among numbers not bitwise equal: {check.max_rel:.3e} "
          f"({check.n_inexact} values)")
    print(f"IDENTICAL (rtol={args.rtol})" if not differences
          else f"DIFFERS ({len(differences)} items)")
    return 0 if not differences else 1


if __name__ == "__main__":
    sys.exit(main())

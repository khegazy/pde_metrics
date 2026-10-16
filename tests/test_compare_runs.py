"""The refactor check in ``docs/recipes/compare_runs.py`` must catch what it claims to.

It is the gate every refactor of this repository passes through, and the snippet it replaced
missed eight of ten deliberate mutations, among them a one-ulp change and a boolean column
turning into floats. Each test below builds two tiny run folders and makes one change.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

_SCRIPT = Path(__file__).resolve().parent.parent / "docs" / "recipes" / "compare_runs.py"
_spec = importlib.util.spec_from_file_location("compare_runs", _SCRIPT)
compare_runs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(compare_runs)


def _run(root: Path) -> Path:
    """One invocation: a comparison folder and a per-metric folder with the same stamp."""
    rows = pd.DataFrame({
        "metric": ["mse", "mse"], "field": ["density"] * 2, "degradation": ["blur"] * 2,
        "level": [1, 2], "frame_index": [0, 0], "variant_label": ["blur_l1", "blur_l2"],
        "value": [0.1234567890123, 2.0], "severity_degenerate": [False, True],
        "wall_time_s": [0.01, 0.02],
    })
    for name in ("comparison", "mse"):
        data = root / f"{name}_1700000000" / "data"
        data.mkdir(parents=True)
        rows.to_csv(data / "results.csv", index=False)
        (data / "run_meta.json").write_text(json.dumps(
            {"git": {"sha": "abc"}, "n_rows": 2, "command": f"evaluate.py paths.results={root}"}))
        (data / "config.yaml").write_text(f"paths:\n  results: {root}\n")
    return root / "comparison_1700000000"


@pytest.fixture
def pair(tmp_path):
    return _run(tmp_path / "before"), _run(tmp_path / "after")


def _edit_results(folder: Path, column: str, row: int, value) -> None:
    path = folder / "data" / "results.csv"
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.loc[row, column] = value
    df.to_csv(path, index=False)


def test_two_copies_of_one_run_compare_identical(pair, capsys):
    assert compare_runs.main([str(p) for p in pair]) == 0
    assert "IDENTICAL" in capsys.readouterr().out


def test_a_change_beyond_the_tolerance_is_caught(pair):
    _edit_results(pair[1], "value", 0, repr(0.1234567890123 * (1 + 1e-10)))
    assert compare_runs.main([str(p) for p in pair]) == 1


def test_a_change_within_the_tolerance_passes_and_is_reported(pair, capsys):
    _edit_results(pair[1], "value", 0, repr(0.1234567890123 * (1 + 1e-14)))
    assert compare_runs.main([str(p) for p in pair]) == 0
    assert "(1 values)" in capsys.readouterr().out


def test_a_boolean_column_turning_into_floats_is_caught(pair):
    _edit_results(pair[1], "severity_degenerate", 0, "0.0")
    assert compare_runs.main([str(p) for p in pair]) == 1


def test_a_missing_row_a_wall_clock_change_and_a_sibling_folder_are_handled(pair):
    _edit_results(pair[1], "wall_time_s", 0, "9.9")      # a clock, not a result
    assert compare_runs.main([str(p) for p in pair]) == 0
    sibling = pair[1].parent / "mse_1700000000" / "data" / "results.csv"
    pd.read_csv(sibling).iloc[:1].to_csv(sibling, index=False)
    assert compare_runs.main([str(p) for p in pair]) == 1


def test_an_extra_file_is_a_difference(pair):
    shutil.copy(pair[1] / "data" / "config.yaml", pair[1] / "data" / "unexpected.yaml")
    assert compare_runs.main([str(p) for p in pair]) == 1

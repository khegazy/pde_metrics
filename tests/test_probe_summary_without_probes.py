"""A run whose ladder contains no probe must not report a probe.

The trap tests -- the phase-scrambled impostor and the unrelated-field anchor -- are
ordinary ladder entries, and a custom ladder is free to omit them. The miscalibration
ladder does: an impostor built by scrambling the phases of one field says nothing about
whether an *ensemble* is honestly dispersed, so it is not on that axis.

When it is omitted, `probe_summary` returns no row at all. A bare row carrying the group
keys and no probe columns would become a "trap test: fake prediction, right spectrum" line
on the card reading `damage —`, and a reader would have no way to tell that from a trap
test that ran and could not be scored, which is a different and much more interesting
claim. Absent must look absent.
"""

from __future__ import annotations

from fmeval.analysis import normalisation, probe_summary
from tests.conftest import make_frame


def test_no_probe_row_when_the_ladder_has_no_probe():
    df = make_frame(axes={"gaussian_blur": [0.1, 0.2]}, n_frames=3)
    summary = probe_summary(df, normalisation(df))
    assert summary.empty, (
        "a ladder with no probe produced a probe row; the card generator renders one "
        f"trap-test line per row here. Got:\n{summary}"
    )


def test_the_empty_result_still_carries_the_key_columns():
    """Empty must still be filterable.

    Every consumer selects on metric or field before reading this frame. A frame with no
    rows *and* no columns would raise a KeyError on that filter, turning a cosmetic defect
    into a crash in `cards evidence`.
    """
    df = make_frame(axes={"gaussian_blur": [0.1, 0.2]}, n_frames=3)
    summary = probe_summary(df, normalisation(df))
    assert {"dataset", "metric", "field"} <= set(summary.columns)
    assert summary[summary["metric"] == "m"].empty  # the filter itself must not raise


def test_a_probe_row_still_appears_when_the_probe_ran():
    df = make_frame(axes={"gaussian_blur": [0.1, 0.2], "gaussian_impostor": [0.5],
                          "mean_field": [1.0]}, n_frames=3)
    summary = probe_summary(df, normalisation(df))
    assert len(summary) == 1
    assert "gaussian_impostor_damage" in summary.columns

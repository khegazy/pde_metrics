"""Figures of each dataset's dynamics, for its page under ``docs/datasets/``.

``python -m fmeval.cards dynamics <dataset>`` opens the dataset as ``evaluate.py`` does, takes
:data:`N_SNAPSHOTS` frames spread evenly over the time selection its config makes, and draws
each field at those times. A two-dimensional field is one panel per time on shared colour
limits, through the same :func:`fmeval.cards.figures.exemplar_panel` the degradation gallery
uses; a one-dimensional dataset is one axes per field with the times overlaid. Every figure is
written with the numbers behind it in a JSON beside it, as the committed card figures are,
and none is ever drawn or edited by hand.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import rc_context

from fmeval import REPO
from fmeval.config import build_job, compose_config, load_cards_config
from fmeval.data.readers import open_trajectory
from fmeval.report import style

from .figures import Column, exemplar_panel
from .loader import write_strict_json

#: Where the figures go: beside the dataset pages, as a bundle's figures sit beside its card.
#: Not ``docs/figures/``, which holds one directory per evaluation run for the overview page.
FIGURES = REPO / "docs" / "datasets" / "_generated"

#: Snapshots per figure: enough to show the evolution, few enough to read side by side.
N_SNAPSHOTS = 5


def generate(name: str, *, out: Path = FIGURES) -> list[Path]:
    """Draw the dynamics of one dataset config and return the figures written.

    Args:
        name: A ``configs/dataset/`` option.
        out: Directory to write into.

    Raises:
        FileNotFoundError: If a file-backed dataset has no local copy; figures are drawn where
            the data lives, never over the network.
        ValueError: If the time selection holds fewer than two frames.
    """
    job = build_job(compose_config(f"dataset={name}"))
    with open_trajectory(job.dataset, job.paths, allow_url=False) as trajectory:
        indices = job.dataset.time.resolve(len(trajectory))
        if len(indices) < 2:
            raise ValueError(f"{name}: its time selection holds {len(indices)} frame(s); a "
                             "picture of the dynamics needs at least two")
        chosen = indices[np.unique(np.linspace(0, len(indices) - 1, N_SNAPSHOTS).astype(int))]
        frames = [trajectory.frame(int(i), job.dataset.fields) for i in chosen]
    grid = frames[0].grid
    dpi = load_cards_config().figures.dpi
    out.mkdir(parents=True, exist_ok=True)
    record = {"dataset": name, "frame_index": [f.index for f in frames],
              "time": [f.time for f in frames]}

    if grid.n_spatial == 1:
        path = out / f"{name}.png"
        styling = style.Style.build(style.DEFAULT_THEME)
        names = list(job.dataset.fields)
        colours = styling.level_colours(style.okabe("blue"), len(frames))
        panels: dict[str, dict[str, dict[str, float]]] = {}
        with rc_context(styling.rc):
            fig, axes = plt.subplots(len(names), 1, sharex=True, squeeze=False,
                                     figsize=(2 * styling.panel_w, styling.panel_h * len(names)))
            x = grid.origin[0] + (np.arange(grid.shape[0]) + 0.5) * grid.spacing[0]
            for ax, field in zip(axes[:, 0], names):
                panels[field] = {}
                for frame, colour in zip(frames, colours):
                    values = frame.fields[field][0]
                    ax.plot(x, values, color=colour, lw=1.2, label=f"t = {frame.time:.3g}")
                    panels[field][f"t = {frame.time:.3g}"] = {
                        "min": float(values.min()), "max": float(values.max()),
                        "mean": float(values.mean())}
                ax.set_ylabel(field)
            axes[-1, 0].set_xlabel(grid.dims[0])
            axes[0, 0].legend(fontsize="x-small", loc="upper right")
            fig.suptitle(f"{name}: each field at {len(frames)} times", fontsize="medium")
            fig.set_layout_engine("tight")
            fig.savefig(path, dpi=dpi, metadata={"Software": None})
            plt.close(fig)
        write_strict_json(path.with_suffix(".json"), {**record, "panels": panels})
        return [path]

    written = []
    for field in job.dataset.fields:
        n_channels = frames[0].fields[field].shape[0]
        for c in range(n_channels):
            label = field if n_channels == 1 else f"{field}_{grid.dims[c]}"
            path = out / f"{name}_{label}.png"
            columns = [Column(title=f"t = {f.time:.3g}", data=f.fields[field][c:c + 1])
                       for f in frames]
            panel = exemplar_panel(columns, ["field"], path=path,
                                   title=f"{name}: {label} at {len(frames)} times",
                                   grid=grid, dpi=dpi, limits_from_every_column=True)
            write_strict_json(path.with_suffix(".json"), {**record, "field": label,
                                                         "panels": panel.statistics})
            written.append(path)
    return written

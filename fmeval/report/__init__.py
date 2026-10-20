"""Report generation: figures, tables, and the LaTeX document that holds them.

Add a figure or table by writing one decorated function in ``plots.py`` or ``tables.py``
and choosing a section number; the writer groups by section and emits the narrative in
order, so no dispatch list needs editing::

    from fmeval.report.registry import plot

    @plot(section=3, order=20, scope="per_metric_field", title="...")
    def my_figure(ctx, df, opts):
        '''One line, used as the caption fallback.'''
        fig, grid = ctx.style.figure(1, 1)
        ...
        return PlotResult([FigureItem(fig, {"field": field}, caption="...")])

Renderers arrange precomputed numbers and never write files; see ``context.py``.
"""

# Imported for its side effect only: `style` selects matplotlib's non-interactive Agg
# backend, and importing it here guarantees that happens before any module of this
# package imports pyplot. Nothing is re-exported; import modules by their full path.
from . import style  # noqa: F401

# The number `persistence_distance` registers combines homology dimensions by a convention

**Category:** method
**Priority:** unset
**Status:** open. The metric is built with the convention labelled; what would replace it is open.

## Context

`persistence_distance` computes one sublevel-set persistence diagram per homology dimension
$k = 0, \dots, n$ for each field (connected pieces, loops and, in two dimensions on a periodic
grid, the one enclosed cavity of the torus), and compares the two fields dimension by dimension
with the bottleneck distance. The stability theorem it rests on is stated for one dimension at a
time (Cohen-Steiner, Edelsbrunner and Harer 2005, *Proc. 21st Symp. Comput. Geom.*, 263–271,
Sect. 2 and the Main Theorem of Sect. 3.1). The panel needs one number per comparison, so the
metric registers

$$
\mathrm{PD}(f, g) = \max_{0 \le k \le n} d_B\bigl(D_k(f), D_k(g)\bigr),
$$

and no source fixes that reduction. Software differs: giotto-tda's `PairwiseDistance` takes a
norm of order `order` (default 2) across the homology dimensions, or keeps one distance per
dimension when `order=None` (`gtda/diagrams/distance.py`, v0.4.0, read through a search
summary of the source).

A second choice enters the same number. The classes that never die (death $+\infty$) are kept
and matched among themselves, `gudhi.bottleneck_distance`'s default. Their number is fixed by the
grid's topology (on a doubly periodic two-dimensional grid one piece, two loops and one cavity),
so both diagrams always hold the same number and the distance stays finite; but their births
include the global minimum and the global maximum, so a single cell that overshoots the
reference's extreme sets a floor under the value. Dropping them would make the metric blind to
the field's range.

## Why this convention

The maximum keeps the stability bound exactly: each dimension's distance is at most the largest
pointwise difference $\lVert f - g \rVert_\infty$, so their maximum is too, and the metric never
exceeds `max_error`. A 2-norm over the $n + 1$ dimensions is bounded only by
$\sqrt{n + 1}\,\lVert f - g \rVert_\infty$. The maximum is also the bottleneck distance of the two
graded diagrams with points matched only within one dimension, so it is a single bottleneck
distance rather than a summary of several. That reasoning is the building agent's, not a source's.

## What would settle it

A published comparison of fields by diagram distance that fixes a reduction over dimensions, or
a decision to register a different one for a stated purpose (one dimension alone, say $H_1$ on
vorticity as a census of vortices of one sign, or a $p$-norm). Either is a sibling bundle
importing `persistence_diagram`, not a change to this one. Measuring which dimension sets the
maximum on the evidence run would show how much the choice matters in practice.

## Related

Written with the point-set companion and `persistence_distance`, 2026-10-31.

# Several fields handed to one metric

**Category:** deferred functionality
**Priority:** unset
**Status:** open, no customer yet

## Context

A metric is called once per field (`fmeval/pipeline.py::run`), and `fields=` on the decorator
says which fields it accepts, one at a time. Several planned ideas compare a relation *between*
fields: the mass flux needs density and velocity together; an entropy needs density and
pressure; vorticity–strain alignment needs velocity and vorticity on the same cells. A metric
can read only the one field it is handed. Degradations have a whole-frame path
(`whole_frame=True`, `AGENTS.md` §4) and metrics do not.

## The choice to be made

`fields=` already means "which fields this metric accepts", and reusing it to mean "which fields
it receives together" would give one argument two meanings. A separate declaration is needed,
naming the fields a metric reads together, and with it a rule for the result row's `field`
column, which today holds one canonical name. Which form that declaration takes, and whether the
row's field becomes a joined label or a new column, is undecided.

## Why it is not built

No metric that needs it is ready to build, and the row-key question changes every grouping in
`fmeval/analysis.py` (`GROUP_KEYS`), so it is decided with its first customer.

## What would unblock it

The first such metric, with the form of its result row decided beside it.

## Related

Written with the harness change of the metric-evaluation design (rev. 4, §3.9), 2026-10-28.

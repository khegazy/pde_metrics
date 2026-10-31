# A run records the git state at its end, not the code it started with

**Category:** technical debt
**Priority:** medium — it can hide a code change from the pre-registration check
**Status:** open.

## Context

`evaluate.py` calls `fio.write_run_meta` inside `write_folder`, after the evaluation has finished,
and `write_run_meta` (`fmeval/io.py`) reads the git state through `_git_state` at that moment. A
commit made while a long run is going is therefore recorded as the run's code, with `dirty`
false, although the run executed the earlier commit.

That matters for the check the metric-building agents pass: `git.sha` must descend from the commit
holding the pre-registration. A metric change committed mid-run descends from it and passes,
though the numbers came from different code.

Found by the agent that built `persistence_distance` (finding 023, adversarial review
2026-10-31).

## Evidence

`results/persistence_distance_1793439285` started 11 s after commit 3f9d2b6 and ran for 7684 s.
Its `run_meta.json` records 125c9a5, `dirty` false, the third commit made during the run.
`git diff 3f9d2b6 125c9a5` changes only docstrings, the card, `refs.bib` and the report's colour
scale, so no number is affected in this case.

## Options

1. Read the git state when the run starts and pass it to `write_run_meta`.
2. Read it at both ends, record both, and flag a run whose code changed while it ran.

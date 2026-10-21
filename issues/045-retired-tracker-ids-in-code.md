# Retired tracker IDs remain in code comments, tests and issues

**Category:** technical debt
**Priority:** low
**Status:** open — nothing reads these identifiers; they are words in comments and prose that
no longer lead anywhere

## Context

The LaTeX tracker's two-letter identifiers (`IN-2`, `IN-3`, `IN-4`, `SH-1`, `PS-3`, …) are
retired (`docs/decisions.md`, "There are no metric IDs"). The tracker itself was converted to
`docs/ideas/` and deleted, so an identifier in a comment now points at a document a reader can
recover only from git history. `CLAUDE.md`, `AGENTS.md`, the recipes and the site no longer use
them; the places below still do.

## Evidence

On the commit that added `docs/ideas/`, this search

```bash
git grep -nE '\b(OT|SH|NM|CG|PH|PD|TD|BD|PS|IN)-[0-9]' -- ':!docs/decisions.md' ':!tests/test_documentation.py'
```

finds them in:

- `fmeval/remap.py`, `fmeval/pipeline.py`, `fmeval/analysis.py`, `fmeval/ladder.py`,
  `fmeval/config.py`, `fmeval/report/registry.py`;
- `degradations/registry.py` and the `coarsen`, `gaussian_impostor` and `band_attenuate`
  degradation modules; `configs/degradation/default.yaml`;
- `tests/test_capabilities.py`, `test_robustness.py`, `test_remap.py`, `test_analysis.py`,
  `test_metric_contract.py`, `test_degradation_contract.py`;
- issues 001, 002, 011, 012, 016 and 023.

## Remaining action

Replace each identifier with what it names, in words: `IN-2` is the common analysis grid,
`IN-3` the degradation ladder, `IN-4` the Gaussian-impostor canary, and so on. Where a comment
points at the tracker for a rationale, point at the idea page if the idea is unbuilt, or state
the rationale in the comment. Then extend the retired-ID check in
`tests/test_documentation.py` from `docs/ideas/` to the whole repository, so they cannot
return.

## Related

`docs/decisions.md`, "There are no metric IDs"; `docs/ideas/README.md`.

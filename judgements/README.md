# Judgements

The consequential method choices an agent made without asking, one file each. Kareem's rule
(2026-10-29): agents research standard practice and decide method questions themselves, and
record **only the judgements on which they would otherwise have stopped to ask him**. A log of
every choice would not be read, so routine choices never appear here.

Each file states the question as it would have been put to him, the choice, the evidence and
its sources, what the choice changes, and how to reverse it. A judgement that is reversed is
deleted, with the reason in the commit message, as for a resolved issue (`AGENTS.md` §1).

| # | Question | Choice | Date |
|---|---|---|---|
| [001](001-damage-anchor-is-the-spatial-mean.md) | What should damage 1 mean, now that the large translation is shown not to be an unrelated field? | The field's spatial mean, the climatological reference; the translation stays as a probe | 2026-10-29 |
| [002](002-hill-estimator-without-a-power-law-tail.md) | Should a Hill estimate be reported on fields whose increments may have no power-law tail? | Yes, at the fixed order sqrt(n), read as the mean log-ratio at that order and not as an exponent; `tail_index` | 2026-10-30 |
| [003](003-spectral-flux-from-velocity-alone.md) | Should the spectral energy flux on weakly compressible data be built from the velocity alone, or wait until density and pressure can be handed to one metric? | Velocity alone, the uniform-density limit of the cross-scale transfer, labelled on the card | 2026-10-30 |
| [004](004-variogram-score-uses-the-fair-estimator.md) | Should the variogram score use Scheuerer and Hamill's plug-in ensemble estimate, which rewards overconfidence at small ensemble sizes, or the unbiased one? | The unbiased (fair) kernel-score estimate, as `crps` and `energy_score` use | 2026-10-31 |
| [006](006-contract-tests-give-a-density-metric-a-positive-field.md) | The contract tests run every metric on a signed field; should a metric defined only on density get an invented value there, or a positive input? | A positive input (the synthetic field moved up by 3) for a metric that declares only density, as issue 101 proposes; `wasserstein` returns NaN outside its domain | 2026-10-31 |

# `tail_index`'s card overstates what Clauset et al. say about the square-root rule

**Category:** documentation
**Priority:** low
**Status:** open.

## Context

`metrics/tail_index/card.md` says Clauset, Shalizi & Newman (2009, SIAM Rev. 51(4), 661-703)
"name" keeping the largest √n observations as one of two fixed rules. Their Sect. 3.5 calls it "an
alternative approach, quite common in the quantitative finance literature", and says the
Kolmogorov-Smirnov method of their Sect. 3.3 gives estimates "at least as good while being simple
to implement". The card omits that they do not recommend it.

Found by the adversarial review of `tail_exceedance` (finding 029, 2026-10-31), from the arXiv
HTML of the paper, version 2; that bundle's card now says so.

## What would settle it

Reword the sentence on `tail_index`'s card, by its owner. The registered √n choice stands as the
bundle's convention either way.

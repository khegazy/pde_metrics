# The CRPS card says ensemble sizes compare fairly, which fails at one member

**Category:** method
**Priority:** low — a one-member "ensemble" is a deterministic forecast, scored by other metrics
**Status:** open. Reproduced, not fixed.

## Context

`metrics/crps/card.md` (Definition) says the plain estimator makes "the same model evaluated with
more members ... look worse", and that excluding self-pairs, the fair estimator of Ferro (2014),
removes that bias. Equation (3)'s second term has the factor 1/(M(M-1)) and is empty at M = 1, so
at one member the score is the mean absolute error alone, whose expectation for a calibrated
forecast is twice the CRPS. The fair estimator is unbiased only from two members.

Found by the agent that built `energy_score`, whose card made the same claim and now states the
two-member bound (finding 020, adversarial review 2026-10-30).

## Evidence

A standard-normal reference on 16 x 16 cells against independent standard-normal members, 200
draws each (`crps` as registered):

| members | mean score |
|---|---|
| 1 | 1.1376 |
| 2 | 0.5722 |
| 8 | 0.5727 |

For independent standard normals, X - Y has variance 2, so E|X - Y| = E|X - X'| = 2/sqrt(pi). The
calibrated CRPS is E|X - Y| - E|X - X'|/2 = 1/sqrt(pi) = 0.5642, and the one-member score, which
keeps only the first term, has expectation 2/sqrt(pi) = 1.1284.

## What would settle it

State on the card that the comparison across ensemble sizes holds from two members, and either
refuse one member or say what it scores.
